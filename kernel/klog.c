/*
 * Anykernel OS — Kernel Log Ring Buffer
 *
 * 4KB circular buffer backed by ringbuf.h (Linux kfifo-inspired).
 * Every kprintf character is stored here for post-mortem debugging.
 * When the buffer fills, oldest data is silently overwritten.
 *
 * Uses the SPSC lock-free ring buffer primitive — same design as
 * Linux dmesg / printk ring buffer.
 */

#include "klog.h"
#include "ringbuf.h"
#include "uart.h"
#include <stdint.h>

/* 4KB ring buffer (power-of-2 for branchless modulo) */
RING_BUF_DEFINE(klog_ring, 4096);

void klog_putchar(char c) {
    if (ring_full(&klog_ring)) {
        /* Overwrite oldest: advance tail by 1 */
        uint8_t discard;
        ring_read(&klog_ring, &discard, 1);
    }
    ring_write(&klog_ring, &c, 1);
}

void klog_write(const char *msg) {
    while (*msg) klog_putchar(*msg++);
}

void klog_dump(void) {
    uint32_t used = ring_used(&klog_ring);
    if (used == 0) return;

    uart_puts("\n--- Kernel Log Dump (last 4KB) ---\n");

    /* Read without consuming: peek at buffer internals */
    for (uint32_t i = 0; i < used; i++) {
        char c = klog_ring.data[(klog_ring.tail + i) & klog_ring.mask];
        uart_putc(c);
    }

    uart_puts("\n--- End Log Dump ---\n");
}

const char *klog_get_buffer(uint32_t *out_size, uint32_t *out_head) {
    if (out_size) *out_size = ring_used(&klog_ring);
    if (out_head) *out_head = klog_ring.head & klog_ring.mask;
    return (const char *)klog_ring.data;
}
