/*
 * Anykernel OS — PS/2 Keyboard Driver
 *
 * Scan Code Set 1 → ASCII translation.
 * Ring buffer for async key input.
 */

#include "kb.h"
#include "io.h"
#include "pic.h"
#include "log.h"
#include <stdint.h>

/* ── Scancode Set 1 → ASCII table (US QWERTY) ───────────────── */

static const char scancode_to_ascii[128] = {
    0,   27, '1','2','3','4','5','6','7','8','9','0','-','=', '\b',
    '\t','q','w','e','r','t','y','u','i','o','p','[',']','\n',
    0,   'a','s','d','f','g','h','j','k','l',';','\'','`',
    0,   '\\','z','x','c','v','b','n','m',',','.','/', 0,
    '*', 0,  ' ', 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 0, 0,
    0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 0, 0,
    0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 0, 0,
    0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 0, 0
};

/* ── Ring buffer ─────────────────────────────────────────────── */

#define KB_BUF_SIZE 64

static char    kb_buffer[KB_BUF_SIZE];
static uint8_t kb_head = 0;
static uint8_t kb_tail = 0;

static void kb_buf_push(char c) {
    uint8_t next = (kb_head + 1) % KB_BUF_SIZE;
    if (next == kb_tail) return;  /* Buffer full, drop */
    kb_buffer[kb_head] = c;
    kb_head = next;
}

/* ── Public API ──────────────────────────────────────────────── */

void kb_init(void) {
    /* Flush any pending scancodes */
    while (inb(0x64) & 0x01) {
        inb(0x60);
    }
    pic_unmask(IRQ_KEYBOARD);
    LOG_OK("Keyboard initialized (PS/2, Set 1)");
}

void kb_irq_handler(void) {
    uint8_t scancode = inb(0x60);

    /* Ignore key releases (bit 7 set) and extended scancodes */
    if (scancode & 0x80) return;
    if (scancode == 0xE0 || scancode == 0xE1) return;

    char c = scancode_to_ascii[scancode];
    if (c != 0) {
        kb_buf_push(c);
    }
}

char kb_getchar(void) {
    if (kb_head == kb_tail) return 0;
    char c = kb_buffer[kb_tail];
    kb_tail = (kb_tail + 1) % KB_BUF_SIZE;
    return c;
}

bool kb_has_input(void) {
    return kb_head != kb_tail;
}
