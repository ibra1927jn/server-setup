/*
 * Anykernel OS v2.1 — Kernel Entry Point
 *
 * Limine hands control here in Long Mode (64-bit), Ring 0.
 * Initializes all subsystems and prints diagnostics.
 */

#include <stdint.h>
#include <stddef.h>

#include "uart.h"
#include "gdt.h"
#include "idt.h"
#include "panic.h"
#include "kprintf.h"
#include "log.h"
#include "memory.h"
#include "string.h"
#include "spinlock.h"
#include "pmm.h"
#include "kmalloc.h"
#include "vmm.h"

/* Limine protocol */
#include "../limine/limine.h"

/* SSP init (defined in ssp.c) */
extern void ssp_init(void);

/* ── Global: HHDM offset (used by PHYS2VIRT / VIRT2PHYS) ─────── */

uint64_t hhdm_offset = 0;

/* ── Limine requests ──────────────────────────────────────────── */

__attribute__((used, section(".limine_requests_start")))
static volatile LIMINE_REQUESTS_START_MARKER

__attribute__((used, section(".limine_requests_end")))
static volatile LIMINE_REQUESTS_END_MARKER

__attribute__((used, section(".limine_requests")))
static volatile LIMINE_BASE_REVISION(3)

__attribute__((used, section(".limine_requests")))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_memmap_request memmap_request = {
    .id = LIMINE_MEMMAP_REQUEST,
    .revision = 0
};

/* ── Helpers ──────────────────────────────────────────────────── */

static void halt(void) {
    asm volatile("cli");
    for (;;) {
        asm volatile("hlt");
    }
}

static const char *memmap_type_str(uint64_t type) {
    switch (type) {
        case LIMINE_MEMMAP_USABLE:                 return "Usable";
        case LIMINE_MEMMAP_RESERVED:               return "Reserved";
        case LIMINE_MEMMAP_ACPI_RECLAIMABLE:       return "ACPI Reclaimable";
        case LIMINE_MEMMAP_ACPI_NVS:               return "ACPI NVS";
        case LIMINE_MEMMAP_BAD_MEMORY:             return "Bad Memory";
        case LIMINE_MEMMAP_BOOTLOADER_RECLAIMABLE: return "Bootloader Reclaim";
        case LIMINE_MEMMAP_KERNEL_AND_MODULES:     return "Kernel & Modules";
        case LIMINE_MEMMAP_FRAMEBUFFER:            return "Framebuffer";
        default:                                   return "Unknown";
    }
}

/* ── Self-test functions (registered via selftest framework) ── */

#include "selftest.h"

static bool test_spinlock(void) {
    spinlock_t lock = SPINLOCK_INIT;
    if (!spin_trylock(&lock)) return false;
    spin_unlock(&lock);
    return true;
}

static bool test_memops(void) {
    uint8_t a[16], b[16];
    memset(a, 0xAA, 16);
    if (a[0] != 0xAA || a[15] != 0xAA) return false;
    memcpy(b, a, 16);
    return memcmp(a, b, 16) == 0;
}

static bool test_pmm_alloc_free(void) {
    uint64_t p = pmm_alloc_pages(0);
    if (p == 0 || (p & (PAGE_SIZE - 1)) != 0) return false;
    pmm_free_pages(p, 0);
    return true;
}

static bool test_pmm_order5(void) {
    uint64_t p = pmm_alloc_pages(5);
    if (p == 0 || (p % (32 * PAGE_SIZE)) != 0) return false;
    pmm_free_pages(p, 5);
    return true;
}

static bool test_kmalloc_small(void) {
    void *p = kmalloc(64);
    if (!p) return false;
    memset(p, 0xBB, 64);
    kfree(p);
    return true;
}

static bool test_kmalloc_large(void) {
    void *p = kmalloc(8192);
    if (!p) return false;
    memset(p, 0xCC, 8192);
    kfree(p);
    return true;
}

static bool test_kzmalloc(void) {
    uint8_t *p = kzmalloc(128);
    if (!p) return false;
    for (int i = 0; i < 128; i++) {
        if (p[i] != 0) { kfree(p); return false; }
    }
    kfree(p);
    return true;
}

static bool test_poison(void) {
    uint8_t *p = kmalloc(64);
    if (!p) return false;
    memset(p, 0x42, 64);
    uint8_t *saved = p;
    kfree(p);
    for (int i = 8; i < 64; i++) {
        if (saved[i] != 0xDE) return false;
    }
    return true;
}

static bool test_krealloc(void) {
    uint8_t *p = kmalloc(32);
    if (!p) return false;
    memset(p, 0xAA, 32);
    uint8_t *p2 = krealloc(p, 256);
    if (!p2) return false;
    if (p2[0] != 0xAA || p2[31] != 0xAA) { kfree(p2); return false; }
    if (kmalloc_usable_size(p2) < 256) { kfree(p2); return false; }
    kfree(p2);
    return true;
}

static bool test_slab_reclamation(void) {
    uint64_t before = pmm_free_count();
    void *p = kmalloc(64);
    if (pmm_free_count() >= before) { kfree(p); return false; }
    kfree(p);
    return pmm_free_count() == before;
}

static bool test_pmm_watermark(void) {
    uint64_t free = pmm_free_count();
    uint64_t total = free + pmm_used_count();
    uint64_t pct = (free * 100) / (total > 0 ? total : 1);
    return pct >= 10;
}

/* VMM tests */
static bool test_vmm_map_write_read(void) {
    /* Allocate a physical page, map it at a known virtual address, write, read */
    uint64_t phys = pmm_alloc_pages_zero(0);
    if (phys == 0) return false;

    /* Use a virtual address in the "scratch" region above HHDM */
    uint64_t test_virt = 0xFFFFFF0000000000UL;
    vmm_map_page(test_virt, phys, PTE_PRESENT | PTE_WRITE | PTE_NX);

    /* Write via the mapped address */
    volatile uint64_t *ptr = (volatile uint64_t *)test_virt;
    *ptr = 0xCAFEBABE12345678UL;

    /* Read back */
    bool ok = (*ptr == 0xCAFEBABE12345678UL);

    vmm_unmap_page(test_virt);
    pmm_free_pages(phys, 0);
    return ok;
}

static bool test_vmm_virt_to_phys(void) {
    /* Walk kernel's own mapping — should resolve */
    uint64_t kernel_addr = (uint64_t)&test_vmm_virt_to_phys;
    uint64_t phys = vmm_virt_to_phys(kernel_addr);
    return phys != 0;
}

static bool test_vmm_hhdm_integrity(void) {
    /* The HHDM should still work after CR3 switch */
    extern uint64_t hhdm_offset;
    /* Access physical 0x1000 via HHDM — should not fault */
    volatile uint8_t *p = (volatile uint8_t *)(hhdm_offset + 0x1000);
    (void)*p;  /* Just read — if HHDM is broken this triple-faults */
    return true;
}

static void register_selftests(void) {
    selftest_register("Spinlock trylock/unlock",        test_spinlock);
    selftest_register("memset/memcpy/memcmp",           test_memops);
    selftest_register("PMM alloc/free order-0",         test_pmm_alloc_free);
    selftest_register("PMM alloc/free order-5 (128KB)", test_pmm_order5);
    selftest_register("kmalloc(64) + kfree",            test_kmalloc_small);
    selftest_register("kmalloc(8192) large alloc",      test_kmalloc_large);
    selftest_register("kzmalloc zeroing",               test_kzmalloc);
    selftest_register("Poison 0xDE on kfree",           test_poison);
    selftest_register("krealloc data preservation",     test_krealloc);
    selftest_register("Slab reclamation to PMM",        test_slab_reclamation);
    selftest_register("PMM watermark >= 10%",           test_pmm_watermark);
    selftest_register("VMM map/write/read",             test_vmm_map_write_read);
    selftest_register("VMM virt_to_phys walk",          test_vmm_virt_to_phys);
    selftest_register("VMM HHDM integrity post-CR3",    test_vmm_hhdm_integrity);
}

/* ── Kernel main ──────────────────────────────────────────────── */

void _start(void) {
    /* 1. UART — must be first */
    uart_init();
    LOG_OK("UART COM1 initialized at 115200 baud");

    /* 2. SSP — randomize stack canary */
    ssp_init();
    LOG_OK("Stack canary randomized (RDTSC)");

    /* 3. Verify Limine protocol */
    KASSERT(LIMINE_BASE_REVISION_SUPPORTED);
    LOG_OK("Limine base revision OK");

    /* 4. GDT + TSS */
    gdt_init();
    LOG_OK("GDT loaded (7 entries, TSS with RSP0 + IST1)");

    /* 5. IDT — catch exceptions */
    idt_init();
    LOG_OK("IDT loaded (#DE #UD #DF #GP #PF)");

    /* 6. HHDM */
    KASSERT(hhdm_request.response != NULL);
    hhdm_offset = hhdm_request.response->offset;
    LOG_INFO("HHDM offset: 0x%016lx", hhdm_offset);

    /* 7. Memory map */
    KASSERT(memmap_request.response != NULL);
    uint64_t entry_count = memmap_request.response->entry_count;
    LOG_INFO("Memory map: %lu entries", entry_count);

    uint64_t usable_bytes = 0;
    uint64_t usable_pages = 0;
    for (uint64_t i = 0; i < entry_count; i++) {
        struct limine_memmap_entry *e = memmap_request.response->entries[i];

        uint64_t aligned_base = PAGE_ALIGN_UP(e->base);
        uint64_t aligned_end  = PAGE_ALIGN_DOWN(e->base + e->length);
        uint64_t pages = (aligned_end > aligned_base)
                         ? (aligned_end - aligned_base) / PAGE_SIZE : 0;

        kprintf("  [%2lu] %p-%p %8lu KB %-22s",
                i, (void *)e->base, (void *)(e->base + e->length),
                e->length / 1024, memmap_type_str(e->type));

        if (e->type == LIMINE_MEMMAP_USABLE) {
            kprintf(" (%lu pages)", pages);
            usable_bytes += e->length;
            usable_pages += pages;
        }
        kprintf("\n");
    }
    LOG_INFO("Total usable: %lu KB (%lu MB) = %lu pages",
             usable_bytes / 1024, usable_bytes / (1024 * 1024), usable_pages);

    /* ─────────────────────────────────────────────────────────────
     * 11. PMM — Physical Memory Manager (Buddy Allocator)
     * ───────────────────────────────────────────────────────────── */
    pmm_init(memmap_request.response, hhdm_offset);
    pmm_dump_stats();

    /* ─────────────────────────────────────────────────────────────
     * 12. VMM — Virtual Memory Manager (Paging)
     * ───────────────────────────────────────────────────────────── */
    vmm_init();

    /* ─────────────────────────────────────────────────────────────
     * 13. Self-tests (registered via selftest framework)
     * ───────────────────────────────────────────────────────────── */
    register_selftests();
    int failures = run_all_selftests();

    /* ─────────────────────────────────────────────────────────────
     * 13. Boot memory report
     * ───────────────────────────────────────────────────────────── */
    kprintf("\n--- Boot Memory Report ---\n");
    {
        extern char __kernel_start, __kernel_end;
        uint64_t kernel_size = (uint64_t)&__kernel_end - (uint64_t)&__kernel_start;
        uint64_t free_pg = pmm_free_count();
        uint64_t used_pg = pmm_used_count();
        uint64_t total = free_pg + used_pg;
        uint64_t pct = (free_pg * 100) / (total > 0 ? total : 1);

        kprintf("  Kernel:   %lu KB (0x%lx - 0x%lx)\n",
                kernel_size / 1024, (uint64_t)&__kernel_start, (uint64_t)&__kernel_end);
        kprintf("  RAM:      %lu pages (%lu MB)\n", total, total * 4 / 1024);
        kprintf("  Free:     %lu pages (%lu KB) [%lu%%]\n", free_pg, free_pg * 4, pct);
        kprintf("  Used:     %lu pages (%lu KB)\n", used_pg, used_pg * 4);
    }

    kmalloc_dump_stats();

    /* 14. Banner */
    kprintf("\n==============================\n");
    kprintf("  Anykernel OS v0.3.0\n");
    kprintf("  %d tests, %d failures\n", 14 - failures + failures, failures);
    kprintf("==============================\n");

    kprintf("\n");
    if (failures > 0) {
        LOG_ERROR("SELF-TEST FAILURES: %d", failures);
    }
    LOG_INFO("System halted.");
    halt();
}
