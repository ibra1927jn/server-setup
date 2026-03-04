/*
 * Anykernel OS — Kernel Log Ring Buffer
 *
 * 4KB circular buffer. Every kprintf character is also stored here.
 * When the buffer wraps, oldest messages are silently overwritten.
 * On panic, klog_dump() can replay recent log history.
 */

#include "klog.h"
#include "uart.h"
#include <stdint.h>

#define KLOG_SIZE 4096

static char    klog_buf[KLOG_SIZE];
static uint32_t klog_head = 0;  /* next write position */
static uint32_t klog_count = 0; /* total chars written */

void klog_putchar(char c) {
    klog_buf[klog_head] = c;
    klog_head = (klog_head + 1) % KLOG_SIZE;
    if (klog_count < KLOG_SIZE) klog_count++;
}

void klog_write(const char *msg) {
    while (*msg) klog_putchar(*msg++);
}

void klog_dump(void) {
    if (klog_count == 0) return;

    /* Start from oldest message */
    uint32_t start;
    uint32_t len;
    if (klog_count < KLOG_SIZE) {
        start = 0;
        len = klog_count;
    } else {
        start = klog_head; /* oldest = current write position */
        len = KLOG_SIZE;
    }

    uart_puts("\n--- Kernel Log Dump (last 4KB) ---\n");
    for (uint32_t i = 0; i < len; i++) {
        char c = klog_buf[(start + i) % KLOG_SIZE];
        uart_putc(c);
    }
    uart_puts("\n--- End Log Dump ---\n");
}

const char *klog_get_buffer(uint32_t *out_size, uint32_t *out_head) {
    if (out_size) *out_size = klog_count < KLOG_SIZE ? klog_count : KLOG_SIZE;
    if (out_head) *out_head = klog_head;
    return klog_buf;
}
