/*
 * Anykernel OS v2.1 — Spinlock (Ticket-less, Test-and-Set)
 *
 * The simplest correct spinlock for x86_64 using GCC atomics.
 * Used to protect shared kernel structures (PMM free lists, etc.)
 * from concurrent access when interrupts or multi-core are enabled.
 *
 * While we currently run single-core with interrupts disabled,
 * building the PMM with locking from day 1 means we won't have to
 * retrofit it later — a common source of subtle corruption bugs.
 *
 * Uses:
 *   __atomic_test_and_set — single atomic read-modify-write (XCHG on x86)
 *   __atomic_clear        — atomic store with release semantics
 *   pause                 — reduces power + avoids memory order violations
 */

#ifndef SPINLOCK_H
#define SPINLOCK_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    volatile bool locked;
} spinlock_t;

#define SPINLOCK_INIT { .locked = false }

/*
 * Acquire the lock. Spins until successful.
 * ACQUIRE semantics: no loads/stores can be reordered before this point.
 */
static inline void spin_lock(spinlock_t *lock) {
    while (__atomic_test_and_set(&lock->locked, __ATOMIC_ACQUIRE)) {
        /* Busy-wait hint: reduces power consumption and allows
         * the memory subsystem to handle the pending store from
         * the other core faster. Essential on real hardware. */
        asm volatile("pause");
    }
}

/*
 * Release the lock.
 * RELEASE semantics: all prior stores become visible before the unlock.
 */
static inline void spin_unlock(spinlock_t *lock) {
    __atomic_clear(&lock->locked, __ATOMIC_RELEASE);
}

/*
 * Try to acquire without spinning. Returns true if acquired.
 */
static inline bool spin_trylock(spinlock_t *lock) {
    return !__atomic_test_and_set(&lock->locked, __ATOMIC_ACQUIRE);
}

/*
 * IRQ-safe lock: save RFLAGS, disable interrupts, THEN acquire.
 *
 * WHY: If an IRQ fires while we hold a spinlock, and the IRQ handler
 * tries to acquire the SAME lock (e.g., timer IRQ calls kmalloc while
 * pmm_alloc_pages holds the PMM lock), we deadlock on a single core.
 *
 * Solution: disable IRQs first, so no handler can preempt us.
 * The saved flags let us restore the previous interrupt state
 * (which might already have been disabled by a caller above us).
 *
 * Usage:
 *   uint64_t flags;
 *   spin_lock_irqsave(&my_lock, &flags);
 *   // ... critical section ...
 *   spin_unlock_irqrestore(&my_lock, flags);
 */
static inline void spin_lock_irqsave(spinlock_t *lock, uint64_t *flags) {
    uint64_t rflags;
    asm volatile("pushfq; pop %0" : "=r"(rflags));  /* Save RFLAGS */
    asm volatile("cli");                              /* Disable IRQs */
    *flags = rflags;
    spin_lock(lock);
}

/*
 * IRQ-safe unlock: release lock, THEN restore RFLAGS (re-enabling
 * interrupts only if they were enabled before the lock was taken).
 */
static inline void spin_unlock_irqrestore(spinlock_t *lock, uint64_t flags) {
    spin_unlock(lock);
    if (flags & (1UL << 9)) {   /* Bit 9 = IF (Interrupt Flag) */
        asm volatile("sti");     /* Re-enable only if was enabled before */
    }
}

#endif /* SPINLOCK_H */
