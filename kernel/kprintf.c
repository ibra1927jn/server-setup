/*
 * Anykernel OS v2.1 — Freestanding kprintf Implementation
 *
 * Zero-allocation printf for kernel diagnostics.
 * All output goes through uart_putc().
 */

#include "kprintf.h"
#include "uart.h"
#include <stdarg.h>
#include <stdint.h>
#include <stdbool.h>

/* ── Internal helpers ─────────────────────────────────────────── */

static void kprint_char(char c) {
    if (c == '\n') {
        uart_putc('\r');
    }
    uart_putc(c);
}

static void kprint_string(const char *s) {
    if (!s) s = "(null)";
    while (*s) {
        kprint_char(*s++);
    }
}

static void kprint_unsigned(uint64_t val, int base, int width, char pad, bool uppercase) {
    static const char digits_lower[] = "0123456789abcdef";
    static const char digits_upper[] = "0123456789ABCDEF";
    const char *digits = uppercase ? digits_upper : digits_lower;

    char buf[20]; /* max uint64 decimal = 20 digits */
    int i = 0;

    if (val == 0) {
        buf[i++] = '0';
    } else {
        while (val > 0) {
            buf[i++] = digits[val % base];
            val /= base;
        }
    }

    /* Padding */
    while (i < width) {
        kprint_char(pad);
        width--;
    }

    /* Print digits in reverse */
    while (i > 0) {
        kprint_char(buf[--i]);
    }
}

static void kprint_signed(int64_t val, int width, char pad) {
    if (val < 0) {
        kprint_char('-');
        if (width > 0) width--;
        kprint_unsigned((uint64_t)(-val), 10, width, pad, false);
    } else {
        kprint_unsigned((uint64_t)val, 10, width, pad, false);
    }
}

/* ── kprintf ──────────────────────────────────────────────────── */

void kprintf(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);

    while (*fmt) {
        if (*fmt != '%') {
            kprint_char(*fmt++);
            continue;
        }

        fmt++; /* skip '%' */

        /* Parse padding */
        char pad = ' ';
        if (*fmt == '0') {
            pad = '0';
            fmt++;
        }

        /* Parse width */
        int width = 0;
        while (*fmt >= '0' && *fmt <= '9') {
            width = width * 10 + (*fmt - '0');
            fmt++;
        }

        /* Parse length modifier */
        bool is_long = false;
        if (*fmt == 'l') {
            is_long = true;
            fmt++;
        }

        /* Format specifier */
        switch (*fmt) {
        case 's':
            kprint_string(va_arg(args, const char *));
            break;

        case 'd':
            if (is_long) {
                kprint_signed(va_arg(args, int64_t), width, pad);
            } else {
                kprint_signed(va_arg(args, int), width, pad);
            }
            break;

        case 'u':
            if (is_long) {
                kprint_unsigned(va_arg(args, uint64_t), 10, width, pad, false);
            } else {
                kprint_unsigned(va_arg(args, unsigned int), 10, width, pad, false);
            }
            break;

        case 'x':
            if (is_long) {
                kprint_unsigned(va_arg(args, uint64_t), 16, width, pad, false);
            } else {
                kprint_unsigned(va_arg(args, unsigned int), 16, width, pad, false);
            }
            break;

        case 'X':
            if (is_long) {
                kprint_unsigned(va_arg(args, uint64_t), 16, width, pad, true);
            } else {
                kprint_unsigned(va_arg(args, unsigned int), 16, width, pad, true);
            }
            break;

        case 'p':
            kprint_string("0x");
            kprint_unsigned((uint64_t)va_arg(args, void *), 16, 16, '0', false);
            break;

        case 'c':
            kprint_char((char)va_arg(args, int));
            break;

        case '%':
            kprint_char('%');
            break;

        default:
            /* Unknown specifier — print as-is */
            kprint_char('%');
            kprint_char(*fmt);
            break;
        }

        fmt++;
    }

    va_end(args);
}
