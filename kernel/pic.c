/*
 * Anykernel OS — PIC (8259A) + PIT Timer Implementation
 *
 * PIC remapping: IRQ 0-7 → vectors 0x20-0x27
 *                IRQ 8-15 → vectors 0x28-0x2F
 *
 * PIT: Channel 0, rate generator mode, ~100 Hz default.
 */

#include "pic.h"
#include "io.h"
#include "kprintf.h"
#include "log.h"
#include <stdint.h>

/* ── PIC ports ───────────────────────────────────────────────── */

#define PIC1_CMD   0x20
#define PIC1_DATA  0x21
#define PIC2_CMD   0xA0
#define PIC2_DATA  0xA1

/* ICW1: initialization + ICW4 needed */
#define ICW1_INIT  0x11
/* ICW4: 8086 mode */
#define ICW4_8086  0x01
/* OCW2: End of Interrupt */
#define PIC_EOI    0x20

/* ── PIC initialization ─────────────────────────────────────── */

void pic_init(void) {
    /* Save current masks */
    uint8_t mask1 = inb(PIC1_DATA);
    uint8_t mask2 = inb(PIC2_DATA);

    /* ICW1: Start initialization sequence (cascade mode, ICW4 needed) */
    outb(PIC1_CMD, ICW1_INIT); io_wait();
    outb(PIC2_CMD, ICW1_INIT); io_wait();

    /* ICW2: Vector offset */
    outb(PIC1_DATA, PIC_IRQ_BASE_MASTER); io_wait();  /* Master: IRQ 0-7 → 0x20-0x27 */
    outb(PIC2_DATA, PIC_IRQ_BASE_SLAVE);  io_wait();  /* Slave:  IRQ 8-15 → 0x28-0x2F */

    /* ICW3: Cascade wiring */
    outb(PIC1_DATA, 0x04); io_wait();  /* Master: slave on IRQ2 (bit 2) */
    outb(PIC2_DATA, 0x02); io_wait();  /* Slave:  cascade identity = 2 */

    /* ICW4: 8086 mode */
    outb(PIC1_DATA, ICW4_8086); io_wait();
    outb(PIC2_DATA, ICW4_8086); io_wait();

    /* Mask ALL IRQs initially — we unmask individually as needed */
    outb(PIC1_DATA, 0xFF);
    outb(PIC2_DATA, 0xFF);

    (void)mask1;
    (void)mask2;
}

void pic_eoi(uint8_t irq) {
    if (irq >= 8) {
        outb(PIC2_CMD, PIC_EOI);  /* Slave PIC */
    }
    outb(PIC1_CMD, PIC_EOI);      /* Always send to master */
}

void pic_unmask(uint8_t irq) {
    uint16_t port;
    if (irq < 8) {
        port = PIC1_DATA;
    } else {
        port = PIC2_DATA;
        irq -= 8;
    }
    uint8_t mask = inb(port);
    mask &= ~(1 << irq);
    outb(port, mask);
}

void pic_mask(uint8_t irq) {
    uint16_t port;
    if (irq < 8) {
        port = PIC1_DATA;
    } else {
        port = PIC2_DATA;
        irq -= 8;
    }
    uint8_t mask = inb(port);
    mask |= (1 << irq);
    outb(port, mask);
}

/* ── PIT Timer ───────────────────────────────────────────────── */

#define PIT_CHANNEL0   0x40
#define PIT_CMD        0x43
#define PIT_BASE_FREQ  1193182UL  /* PIT oscillator frequency */

static volatile uint64_t pit_ticks = 0;
static uint32_t pit_freq = 0;

void pit_init(uint32_t frequency_hz) {
    pit_freq = frequency_hz;
    uint16_t divisor = (uint16_t)(PIT_BASE_FREQ / frequency_hz);

    /* Channel 0, Access: lobyte/hibyte, Mode 2 (rate generator) */
    outb(PIT_CMD, 0x34);
    outb(PIT_CHANNEL0, (uint8_t)(divisor & 0xFF));
    outb(PIT_CHANNEL0, (uint8_t)((divisor >> 8) & 0xFF));
}

uint64_t pit_get_ticks(void) {
    return pit_ticks;
}

/*
 * Called from the IRQ0 handler (isr_stub_32) via irq_handler_c.
 */
void pit_tick(void) {
    pit_ticks++;
}
