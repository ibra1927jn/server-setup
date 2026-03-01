/*
 * Anykernel OS v2.1 — Kernel Entry Point
 *
 * This is where Limine hands control to our kernel.
 * We operate in Long Mode (64-bit), Ring 0, with basic paging enabled.
 */

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#include "uart.h"
#include "gdt.h"

/* Copy of limine.h protocol definitions to avoid stdint path issues */
#include "../limine/limine.h"

/* ── Limine requests ──────────────────────────────────────────── */

/*
 * Limine requires these markers to find our requests in the binary.
 * They must be placed in the .limine_requests_start / .limine_requests / 
 * .limine_requests_end sections as defined in our linker script.
 */

__attribute__((used, section(".limine_requests_start")))
static volatile LIMINE_REQUESTS_START_MARKER

__attribute__((used, section(".limine_requests_end")))
static volatile LIMINE_REQUESTS_END_MARKER

/* Base revision: tell Limine which protocol revision we support */
__attribute__((used, section(".limine_requests")))
static volatile LIMINE_BASE_REVISION(3)

/* Request: Higher Half Direct Map offset */
__attribute__((used, section(".limine_requests")))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST,
    .revision = 0
};

/* Request: Memory map (for future PMM use) */
__attribute__((used, section(".limine_requests")))
static volatile struct limine_memmap_request memmap_request = {
    .id = LIMINE_MEMMAP_REQUEST,
    .revision = 0
};

/* ── Halt helper ──────────────────────────────────────────────── */

static void halt(void) {
    for (;;) {
        asm volatile("hlt");
    }
}

/* ── Kernel main ──────────────────────────────────────────────── */

void _start(void) {
    /* 1. Initialize UART — our only debug output channel */
    uart_init();
    uart_puts("[UART] Initialized COM1 at 115200 baud\n");

    /* 2. Verify Limine base revision was accepted */
    if (!LIMINE_BASE_REVISION_SUPPORTED) {
        uart_puts("[BOOT] ERROR: Limine base revision not supported!\n");
        halt();
    }
    uart_puts("[BOOT] Limine base revision OK\n");

    /* 3. Install our own GDT + TSS */
    gdt_init();
    uart_puts("[GDT]  Loaded (7 entries)\n");
    uart_puts("[TSS]  Loaded (RSP0 set)\n");

    /* 4. Report HHDM offset if available */
    if (hhdm_request.response != NULL) {
        uart_puts("[HHDM] Offset: ");
        uart_put_hex(hhdm_request.response->offset);
        uart_puts("\n");
    }

    /* 5. Report memory map if available */
    if (memmap_request.response != NULL) {
        uart_puts("[MMAP] ");
        uint64_t count = memmap_request.response->entry_count;

        /* Count usable memory */
        uint64_t usable_bytes = 0;
        for (uint64_t i = 0; i < count; i++) {
            struct limine_memmap_entry *entry = memmap_request.response->entries[i];
            if (entry->type == LIMINE_MEMMAP_USABLE) {
                usable_bytes += entry->length;
            }
        }

        uart_put_hex(usable_bytes);
        uart_puts(" bytes usable RAM\n");
    }

    /* 6. Print the milestone message */
    uart_puts("\n");
    uart_puts("==============================\n");
    uart_puts("  Hola Mundo - Anykernel OS   \n");
    uart_puts("  Sprint 1 Complete!          \n");
    uart_puts("==============================\n");

    /* 7. Halt — nothing more to do */
    uart_puts("\n[KERN] System halted.\n");
    halt();
}
