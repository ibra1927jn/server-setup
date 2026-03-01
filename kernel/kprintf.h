/*
 * Anykernel OS v2.1 — Freestanding kprintf
 *
 * Lightweight kernel printf using <stdarg.h> (compiler-provided).
 * Outputs to UART COM1. No heap allocation, no floating point.
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

/* Print formatted output to UART */
void kprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

#endif /* KPRINTF_H */
