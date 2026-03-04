/*
 * Anykernel OS — Kernel Panic (improved)
 *
 * Uses kprintf for colored output on both serial and framebuffer.
 * Dumps CR2 on page faults for immediate diagnosis.
 */

#include "panic.h"
#include "kprintf.h"
#include "log.h"
#include "klog.h"
#include <stdint.h>

__attribute__((noreturn))
void kernel_panic(const char *msg, const char *file, int line) {
    /* Disable interrupts immediately */
    asm volatile("cli");

    /* Read CR2 (faulting address for page faults) */
    uint64_t cr2;
    asm volatile("mov %%cr2, %0" : "=r"(cr2));

    /* Dump ring buffer to serial for post-mortem */
    klog_dump();

    /* Print panic banner with colors */
    kprintf("\n\n");
    kprintf(ANSI_RED "╔══════════════════════════════════╗" ANSI_RESET "\n");
    kprintf(ANSI_RED "║      !!! KERNEL PANIC !!!        ║" ANSI_RESET "\n");
    kprintf(ANSI_RED "╚══════════════════════════════════╝" ANSI_RESET "\n");
    kprintf(ANSI_RED "  Message: " ANSI_RESET "%s\n", msg);
    kprintf(ANSI_RED "  File:    " ANSI_RESET "%s\n", file);
    kprintf(ANSI_RED "  Line:    " ANSI_RESET "%d\n", line);
    kprintf(ANSI_YELLOW "  CR2:     " ANSI_RESET "0x%016lx\n", cr2);
    kprintf("\n  System halted.\n");

    /* Halt forever */
    for (;;) {
        asm volatile("hlt");
    }
}
