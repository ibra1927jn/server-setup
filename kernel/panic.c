/*
 * Anykernel OS v2.1 — Kernel Panic Implementation
 */

#include "panic.h"
#include "uart.h"

__attribute__((noreturn))
void kernel_panic(const char *msg, const char *file, int line) {
    /* Print panic banner */
    uart_puts("\n\n");
    uart_puts("!!! KERNEL PANIC !!!\n");
    uart_puts("  Message: ");
    uart_puts(msg);
    uart_puts("\n  File:    ");
    uart_puts(file);
    uart_puts("\n  Line:    ");

    /* Print line number as decimal (no kprintf dependency) */
    char buf[12];
    int i = 0;
    int n = line;
    if (n == 0) {
        buf[i++] = '0';
    } else {
        char tmp[12];
        int j = 0;
        while (n > 0) {
            tmp[j++] = '0' + (n % 10);
            n /= 10;
        }
        while (j > 0) {
            buf[i++] = tmp[--j];
        }
    }
    buf[i] = '\0';
    uart_puts(buf);

    uart_puts("\n\n  System halted. Check serial log for details.\n");

    /* Freeze: disable interrupts and halt forever */
    asm volatile("cli");
    for (;;) {
        asm volatile("hlt");
    }
}
