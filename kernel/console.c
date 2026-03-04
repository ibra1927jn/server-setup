/*
 * Anykernel OS — Framebuffer Text Console
 *
 * Minimal 8x16 built-in font. 32-bit pixel direct rendering.
 * Scrolling by memory copy when cursor reaches bottom.
 */

#include "console.h"
#include "string.h"
#include <stdint.h>

/* ── State ───────────────────────────────────────────────────── */

static uint32_t *fb = 0;
static uint64_t fb_width = 0;
static uint64_t fb_height = 0;
static uint64_t fb_pitch = 0;  /* bytes per row */
static int      fb_ready = 0;

static uint32_t cursor_x = 0;  /* character column */
static uint32_t cursor_y = 0;  /* character row */
static uint32_t cols = 0;      /* max columns */
static uint32_t rows = 0;      /* max rows */

#define FONT_W 8
#define FONT_H 16
#define BG_COLOR 0x00101010    /* Near-black background */

/* Current foreground color (changeable via ANSI codes) */
static uint32_t fg_color = 0x00E0E0E0;  /* Default: light gray */

/* ANSI escape sequence state machine */
#define ANSI_STATE_NORMAL  0
#define ANSI_STATE_ESC     1  /* Got ESC */
#define ANSI_STATE_BRACKET 2  /* Got ESC[ */

static int  ansi_state = ANSI_STATE_NORMAL;
static int  ansi_param = 0;

/* ── Built-in 8x16 font (printable ASCII 32-126) ────────────── */
/*    Each glyph = 16 bytes (one byte per row, MSB = leftmost) */

#include "font8x16.h"

/* ── Internal: draw a glyph at pixel position ────────────────── */

static inline void draw_glyph(uint32_t px, uint32_t py, char c) {
    int idx = (int)c - 32;
    if (idx < 0 || idx >= 95) idx = 0; /* fallback to space */

    const uint8_t *glyph = font_data[idx];
    uint32_t ppitch = fb_pitch / 4;  /* pitch in uint32_t */

    for (int y = 0; y < FONT_H; y++) {
        uint8_t row = glyph[y];
        uint32_t *line = fb + (py + y) * ppitch + px;
        for (int x = 0; x < FONT_W; x++) {
            line[x] = (row & (0x80 >> x)) ? fg_color : BG_COLOR;
        }
    }
}

/* ── Scroll one line up ──────────────────────────────────────── */

static void scroll_up(void) {
    uint32_t line_bytes = fb_pitch * FONT_H;
    uint32_t total = fb_pitch * fb_height;

    /* Move everything up by one text line */
    memmove(fb, (uint8_t *)fb + line_bytes, total - line_bytes);

    /* Clear the last line */
    uint8_t *last = (uint8_t *)fb + total - line_bytes;
    memset(last, 0x10, line_bytes);  /* BG_COLOR approximation */
}

/* ── Public API ──────────────────────────────────────────────── */

void console_init(void *fb_addr, uint64_t width, uint64_t height,
                  uint64_t pitch, uint16_t bpp) {
    if (!fb_addr || bpp != 32) return;

    fb = (uint32_t *)fb_addr;
    fb_width = width;
    fb_height = height;
    fb_pitch = pitch;
    cols = width / FONT_W;
    rows = height / FONT_H;
    cursor_x = 0;
    cursor_y = 0;
    fb_ready = 1;

    console_clear();
}

void console_clear(void) {
    if (!fb_ready) return;
    /* Fill entire framebuffer with background color */
    uint32_t ppitch = fb_pitch / 4;
    for (uint64_t y = 0; y < fb_height; y++) {
        for (uint64_t x = 0; x < fb_width; x++) {
            fb[y * ppitch + x] = BG_COLOR;
        }
    }
    cursor_x = 0;
    cursor_y = 0;
}

static void ansi_set_color(int code) {
    switch (code) {
        case 0:  fg_color = 0x00E0E0E0; break;  /* Reset */
        case 31: fg_color = 0x00FF4444; break;  /* Red */
        case 32: fg_color = 0x0044FF44; break;  /* Green */
        case 33: fg_color = 0x00FFFF44; break;  /* Yellow */
        case 34: fg_color = 0x006666FF; break;  /* Blue */
        case 35: fg_color = 0x00FF44FF; break;  /* Magenta */
        case 36: fg_color = 0x0044FFFF; break;  /* Cyan */
        case 37: fg_color = 0x00E0E0E0; break;  /* White */
        default: break;
    }
}

void console_putchar(char c) {
    if (!fb_ready) return;

    /* ANSI escape sequence parser */
    if (ansi_state == ANSI_STATE_ESC) {
        if (c == '[') {
            ansi_state = ANSI_STATE_BRACKET;
            ansi_param = 0;
            return;
        }
        ansi_state = ANSI_STATE_NORMAL;
        /* Fall through to print the char */
    } else if (ansi_state == ANSI_STATE_BRACKET) {
        if (c >= '0' && c <= '9') {
            ansi_param = ansi_param * 10 + (c - '0');
            return;
        }
        if (c == 'm') {
            ansi_set_color(ansi_param);
            ansi_state = ANSI_STATE_NORMAL;
            return;
        }
        /* Unknown sequence end — ignore */
        ansi_state = ANSI_STATE_NORMAL;
        return;
    }

    if (c == 0x1B) {  /* ESC */
        ansi_state = ANSI_STATE_ESC;
        return;
    }

    if (c == '\n') {
        cursor_x = 0;
        cursor_y++;
    } else if (c == '\r') {
        cursor_x = 0;
    } else if (c == '\b') {
        if (cursor_x > 0) {
            cursor_x--;
            draw_glyph(cursor_x * FONT_W, cursor_y * FONT_H, ' ');
        }
    } else if (c == '\t') {
        cursor_x = (cursor_x + 4) & ~3;
    } else if (c >= 32 && c < 127) {
        draw_glyph(cursor_x * FONT_W, cursor_y * FONT_H, c);
        cursor_x++;
    }

    /* Wrap */
    if (cursor_x >= cols) {
        cursor_x = 0;
        cursor_y++;
    }

    /* Scroll */
    if (cursor_y >= rows) {
        scroll_up();
        cursor_y = rows - 1;
    }
}

void console_puts(const char *s) {
    while (*s) console_putchar(*s++);
}

int console_available(void) {
    return fb_ready;
}
