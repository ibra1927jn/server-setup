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

#include "selftest.h"
#include "pic.h"

/* Tests are in kernel/tests.c */
extern void register_selftests(void);

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

    /* 5. IDT — catch exceptions + handle IRQs */
    idt_init();
    LOG_OK("IDT loaded (#DE #UD #DF #GP #PF + IRQ0/1)");

    /* 6. PIC + PIT — hardware interrupt infrastructure */
    pic_init();
    pit_init(100);  /* 100 Hz = 10ms tick */
    pic_unmask(IRQ_TIMER);  /* Enable timer IRQ */
    asm volatile("sti");    /* ENABLE INTERRUPTS! */
    LOG_OK("PIC remapped, PIT at 100 Hz, interrupts ENABLED");

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
    vmm_dump_tables();

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
    kprintf("  Anykernel OS v0.3.2\n");
    kprintf("  %d tests, %d failures\n", selftest_count(), failures);
    kprintf("  PIT ticks: %lu\n", pit_get_ticks());
    kprintf("==============================\n");

    kprintf("\n");
    if (failures > 0) {
        LOG_ERROR("SELF-TEST FAILURES: %d", failures);
    }
    LOG_INFO("System halted (interrupts active).");
    for (;;) {
        asm volatile("hlt");
    }
}
