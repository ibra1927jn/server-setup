/*
 * Anykernel OS v2.1 — Freestanding String/Memory Functions
 *
 * These are mandatory for freestanding C. The compiler assumes they
 * exist and emits implicit calls for struct init, array copies, etc.
 *
 * Uses x86_64 `rep stosb` / `rep movsb` for hardware-accelerated
 * bulk memory operations (ERMS — Enhanced REP MOVSB/STOSB on modern CPUs).
 */

#include "string.h"
#include <stdint.h>

void *memset(void *dest, int val, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    uint8_t v = (uint8_t)val;

    /*
     * rep stosb: fill RCX bytes at [RDI] with AL.
     * On modern x86_64 with ERMS, this is faster than a C loop
     * and often faster than manual unrolling for large sizes.
     */
    asm volatile(
        "rep stosb"
        : "+D"(d), "+c"(n)   /* RDI = dest (updated), RCX = count (zeroed) */
        : "a"(v)             /* AL = fill byte */
        : "memory"
    );

    return dest;
}

void *memcpy(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;

    /*
     * rep movsb: copy RCX bytes from [RSI] to [RDI].
     * Requires direction flag = 0 (forward), which is the default in SysV ABI.
     */
    asm volatile(
        "rep movsb"
        : "+D"(d), "+S"(s), "+c"(n)
        :
        : "memory"
    );

    return dest;
}

void *memmove(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;

    if (d == s || n == 0) {
        return dest;
    }

    if (d < s || d >= s + n) {
        /* No overlap or dest is before src — forward copy is safe */
        return memcpy(dest, src, n);
    }

    /* Overlap with dest > src — must copy backwards */
    d += n;
    s += n;
    while (n--) {
        *(--d) = *(--s);
    }

    return dest;
}

int memcmp(const void *a, const void *b, size_t n) {
    const uint8_t *pa = (const uint8_t *)a;
    const uint8_t *pb = (const uint8_t *)b;

    while (n--) {
        if (*pa != *pb) {
            return (int)*pa - (int)*pb;
        }
        pa++;
        pb++;
    }

    return 0;
}
