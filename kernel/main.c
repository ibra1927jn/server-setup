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

    /* 7. Spinlock self-test */
    {
        spinlock_t test_lock = SPINLOCK_INIT;
        KASSERT(spin_trylock(&test_lock));   /* Should succeed */
        spin_unlock(&test_lock);
        LOG_OK("Spinlock self-test passed");
    }

    /* 8. memset/memcpy self-test */
    {
        uint8_t test_buf[16];
        memset(test_buf, 0xAA, sizeof(test_buf));
        KASSERT(test_buf[0] == 0xAA && test_buf[15] == 0xAA);

        uint8_t copy_buf[16];
        memcpy(copy_buf, test_buf, sizeof(test_buf));
        KASSERT(memcmp(test_buf, copy_buf, sizeof(test_buf)) == 0);

        LOG_OK("memset/memcpy/memcmp self-test passed");
    }

    /* 9. PHYS2VIRT demo */
    LOG_DEBUG("PHYS2VIRT(0x0) = %p", PHYS2VIRT(0x0));

    /* 10. Memory map */
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

    /* PMM self-test: alloc and free a page */
    {
        uint64_t p = pmm_alloc_pages(0);
        KASSERT(p != 0);
        KASSERT((p & (PAGE_SIZE - 1)) == 0);  /* Must be page-aligned */
        pmm_free_pages(p, 0);
        LOG_OK("PMM alloc/free self-test passed");
    }

    /* PMM self-test: alloc order-5 (128KB) */
    {
        uint64_t p = pmm_alloc_pages(5);
        KASSERT(p != 0);
        KASSERT((p % (32 * PAGE_SIZE)) == 0);  /* 128KB aligned */
        pmm_free_pages(p, 5);
        LOG_OK("PMM order-5 alloc/free self-test passed");
    }

    /* ─────────────────────────────────────────────────────────────
     * 12. kmalloc — Kernel Heap Allocator
     * ───────────────────────────────────────────────────────────── */

    /* Small alloc: 64-byte struct */
    {
        void *p = kmalloc(64);
        KASSERT(p != NULL);
        memset(p, 0xBB, 64);
        kfree(p);
        LOG_OK("kmalloc(64) + kfree passed");
    }

    /* Large alloc: 8KB (falls back to PMM pages) */
    {
        void *p = kmalloc(8192);
        KASSERT(p != NULL);
        memset(p, 0xCC, 8192);
        kfree(p);
        LOG_OK("kmalloc(8192) large alloc + kfree passed");
    }

    /* kzmalloc: verify zeroing */
    {
        uint8_t *p = kzmalloc(128);
        KASSERT(p != NULL);
        int all_zero = 1;
        for (int i = 0; i < 128; i++) {
            if (p[i] != 0) { all_zero = 0; break; }
        }
        KASSERT(all_zero);
        kfree(p);
        LOG_OK("kzmalloc(128) zeroing verified");
    }

    kmalloc_dump_stats();

    /* 13. Banner */
    kprintf("\n==============================\n");
    kprintf("  Anykernel OS v0.2.1\n");
    kprintf("  Sprint 2: PMM + Heap!\n");
    kprintf("==============================\n");

    kprintf("\n");
    LOG_INFO("System halted.");
    halt();
}

