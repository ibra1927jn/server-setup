/*
 * Anykernel OS v2.1 — Freestanding String/Memory Functions
 *
 * Required because clang/GCC may emit implicit calls to memset/memcpy
 * even in freestanding mode (e.g. struct initialization, aggregate copies).
 */

#ifndef STRING_H
#define STRING_H

#include <stddef.h>

/* Fill n bytes of memory at dest with byte val */
void *memset(void *dest, int val, size_t n);

/* Copy n bytes from src to dest (must not overlap) */
void *memcpy(void *dest, const void *src, size_t n);

/* Copy n bytes from src to dest (may overlap safely) */
void *memmove(void *dest, const void *src, size_t n);

/* Compare n bytes of a and b. Returns 0 if equal. */
int memcmp(const void *a, const void *b, size_t n);

#endif /* STRING_H */
