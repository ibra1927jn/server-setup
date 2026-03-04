/*
 * Anykernel OS v2.1 — Freestanding kprintf
 *
 * Lightweight kernel printf using <stdarg.h> (compiler-provided).
 * Triple output: UART serial + framebuffer console + klog ring buffer.
 * No heap allocation, no floating point.
 *
 * Supported format specifiers:
 *   %s   — string
 *   %d   — signed decimal (int)
 *   %u   — unsigned decimal (uint32_t / uint64_t with 'l')
 *   %x   — hexadecimal (lowercase, no prefix)
 *   %p   — pointer (0x-prefixed hex, always 16 digits)
 *   %c   — single character
 *   %%   — literal '%'
 *   %ld / %lu / %lx — 64-bit variants
 */

#ifndef KPRINTF_H
#define KPRINTF_H

#include <stdarg.h>
#include <stddef.h>

/* Print formatted output to UART + console + klog */
void kprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

/* Format into a buffer (like snprintf). Returns chars written (excl NUL). */
int ksnprintf(char *buf, size_t size, const char *fmt, ...)
    __attribute__((format(printf, 3, 4)));

/* va_list variant of ksnprintf */
int kvsnprintf(char *buf, size_t size, const char *fmt, va_list args);

#endif /* KPRINTF_H */
