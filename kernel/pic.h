/*
 * Anykernel OS — PIC (8259A) + PIT Timer Driver
 *
 * The 8259A PIC maps hardware IRQs to CPU interrupt vectors.
 * Default mapping conflicts with CPU exceptions (IRQ0 = INT 0x08 = #DF).
 * We remap: Master PIC IRQ 0-7  → INT 0x20-0x27
 *           Slave  PIC IRQ 8-15 → INT 0x28-0x2F
 *
 * PIT (Programmable Interval Timer, channel 0) generates IRQ0
 * at a configurable frequency for preemptive scheduling.
 */

#ifndef PIC_H
#define PIC_H

#include <stdint.h>

/* Remapped IRQ vector base */
#define PIC_IRQ_BASE_MASTER  0x20
#define PIC_IRQ_BASE_SLAVE   0x28

/* IRQ numbers */
#define IRQ_TIMER    0
#define IRQ_KEYBOARD 1

/* Interrupt vector for a given IRQ */
#define IRQ_VECTOR(irq) (PIC_IRQ_BASE_MASTER + (irq))

/*
 * Initialize the 8259A PIC with remapped vectors.
 * After this, hardware IRQs fire at vectors 0x20-0x2F.
 * All IRQs are masked (disabled) until explicitly enabled.
 */
void pic_init(void);

/*
 * Send End-Of-Interrupt to PIC. Must be called at the
 * end of every IRQ handler.
 */
void pic_eoi(uint8_t irq);

/*
 * Enable (unmask) a specific IRQ line.
 */
void pic_unmask(uint8_t irq);

/*
 * Disable (mask) a specific IRQ line.
 */
void pic_mask(uint8_t irq);

/*
 * Initialize PIT channel 0 at the given frequency (Hz).
 * Common values: 100 Hz (10ms tick), 1000 Hz (1ms tick).
 */
void pit_init(uint32_t frequency_hz);

/*
 * Get the current tick count since boot.
 */
uint64_t pit_get_ticks(void);

/*
 * Called from IRQ0 handler to increment tick counter.
 */
void pit_tick(void);

/* ── Dynamic IRQ handlers ────────────────────────────────────── */

typedef void (*irq_handler_fn)(uint8_t irq);

/*
 * Register a handler for a specific IRQ (0-15).
 * Only one handler per IRQ. Returns previous handler (or NULL).
 */
irq_handler_fn irq_register(uint8_t irq, irq_handler_fn handler);

/* ── Timer callbacks ─────────────────────────────────────────── */

typedef void (*timer_callback_fn)(void);

#define MAX_TIMER_CALLBACKS 8

/*
 * Register a function to be called every `interval_ticks` PIT ticks.
 * Returns 0 on success, -1 if table full.
 */
int timer_register(timer_callback_fn fn, uint32_t interval_ticks);

#endif /* PIC_H */
