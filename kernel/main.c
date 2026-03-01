/*
 * Anykernel OS v2.1 — Kernel Entry Point
 *
 * Limine hands control here in Long Mode (64-bit), Ring 0.
 * We initialize all subsystems and print diagnostics.
 */

#include <stdint.h>
#include <stddef.h>

#include "uart.h"
#include "gdt.h"
#include "panic.h"
#include "kprintf.h"

/* Limine protocol */
#include "../limine/limine.h"

/* SSP init (defined in ssp.c) */
extern void ssp_init(void);

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
        case LIMINE_MEMMAP_BOOTLOADER_RECLAIMABLE: return "Bootloader Reclaimable";
        case LIMINE_MEMMAP_FRAMEBUFFER:            return "Framebuffer";
        default:                                   return "Unknown";
    }
}

/* ── Kernel main ──────────────────────────────────────────────── */

void _start(void) {
    /* 1. UART — must be first (all diagnostics depend on it) */
    uart_init();
    kprintf("[UART] COM1 initialized at 115200 baud\n");

    /* 2. SSP — randomize stack canary before any function with buffers */
    ssp_init();
    kprintf("[SSP]  Stack canary randomized (RDTSC)\n");

    /* 3. Verify Limine protocol */
    KASSERT(LIMINE_BASE_REVISION_SUPPORTED);
    kprintf("[BOOT] Limine base revision OK\n");

    /* 4. GDT + TSS */
    gdt_init();
    kprintf("[GDT]  Loaded (7 entries, TSS with RSP0 + IST1)\n");

    /* 5. HHDM offset */
    KASSERT(hhdm_request.response != NULL);
    kprintf("[HHDM] Offset: %p\n", (void *)hhdm_request.response->offset);

    /* 6. Full memory map dump */
    KASSERT(memmap_request.response != NULL);
    uint64_t entry_count = memmap_request.response->entry_count;
    kprintf("[MMAP] %lu entries:\n", entry_count);

    uint64_t usable_bytes = 0;
    for (uint64_t i = 0; i < entry_count; i++) {
        struct limine_memmap_entry *e = memmap_request.response->entries[i];
        kprintf("  [%lu] %p - %p (%lu KB) %s\n",
                i,
                (void *)e->base,
                (void *)(e->base + e->length),
                e->length / 1024,
                memmap_type_str(e->type));
        if (e->type == LIMINE_MEMMAP_USABLE) {
            usable_bytes += e->length;
        }
    }
    kprintf("[MMAP] Total usable: %lu KB (%lu MB)\n",
            usable_bytes / 1024, usable_bytes / (1024 * 1024));

    /* 7. Banner */
    kprintf("\n==============================\n");
    kprintf("  Hola Mundo - Anykernel OS\n");
    kprintf("  Sprint 1.5 — Hardened!\n");
    kprintf("==============================\n");

    /* 8. Halt */
    kprintf("\n[KERN] System halted.\n");
    halt();
}
