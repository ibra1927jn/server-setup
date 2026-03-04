/*
 * Anykernel OS — Mutex (Sleeping Lock)
 *
 * Unlike spinlocks which burn CPU while waiting, mutexes put the
 * waiting thread to sleep and wake it when the lock is released.
 *
 * Use spinlocks for: short critical sections, IRQ handlers
 * Use mutexes for: longer critical sections, I/O waits, anything
 *                  where the holder might sleep or take a while
 *
 * WARNING: Mutexes MUST NOT be used in interrupt context.
 *          Use spinlocks with IRQ save for that.
 */

#ifndef MUTEX_H
#define MUTEX_H

#include "waitqueue.h"
#include <stdbool.h>
#include <stdint.h>

struct mutex {
    volatile bool     locked;
    struct wait_queue  waiters;
    uint32_t           owner_tid;  /* TID of holding thread (debug) */
};

#define MUTEX_INIT(name) {              \
    .locked  = false,                   \
    .waiters = WAIT_QUEUE_INIT((name).waiters), \
    .owner_tid = 0                      \
}

/* Initialize a mutex at runtime */
static inline void mutex_init(struct mutex *m) {
    m->locked = false;
    wq_init(&m->waiters);
    m->owner_tid = 0;
}

/*
 * Acquire the mutex. Sleeps if already held.
 * MUST NOT be called from interrupt context.
 */
void mutex_lock(struct mutex *m);

/*
 * Release the mutex. Wakes one waiter if any.
 */
void mutex_unlock(struct mutex *m);

/*
 * Try to acquire without sleeping. Returns true if acquired.
 */
bool mutex_trylock(struct mutex *m);

#endif /* MUTEX_H */
