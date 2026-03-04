/*
 * Anykernel OS — Mutex Implementation
 */

#include "mutex.h"
#include "task.h"
#include "sched.h"
#include "spinlock.h"

/* ── mutex_lock ──────────────────────────────────────────────── */

void mutex_lock(struct mutex *m) {
    while (1) {
        uint64_t irq_flags;
        spin_lock_irqsave(&m->waiters.lock, &irq_flags);

        if (!m->locked) {
            /* Acquired! */
            m->locked = true;
            m->owner_tid = task_current()->tid;
            spin_unlock_irqrestore(&m->waiters.lock, irq_flags);
            return;
        }

        /* Already locked — sleep on wait queue */
        struct task *cur = task_current();
        cur->state = TASK_SLEEPING;
        list_push_back(&m->waiters.waiters, &cur->run_node);

        spin_unlock_irqrestore(&m->waiters.lock, irq_flags);
        schedule();
        /* When we wake, loop back to try again */
    }
}

/* ── mutex_unlock ────────────────────────────────────────────── */

void mutex_unlock(struct mutex *m) {
    uint64_t irq_flags;
    spin_lock_irqsave(&m->waiters.lock, &irq_flags);

    m->locked = false;
    m->owner_tid = 0;

    /* Wake one waiter if any */
    if (!list_empty(&m->waiters.waiters)) {
        struct list_node *node = m->waiters.waiters.sentinel.next;
        list_remove_node(node);
        struct task *t = container_of(node, struct task, run_node);
        t->state = TASK_READY;

        extern void sched_add_ready(struct task *t);
        sched_add_ready(t);
    }

    spin_unlock_irqrestore(&m->waiters.lock, irq_flags);
}

/* ── mutex_trylock ───────────────────────────────────────────── */

bool mutex_trylock(struct mutex *m) {
    uint64_t irq_flags;
    spin_lock_irqsave(&m->waiters.lock, &irq_flags);

    if (!m->locked) {
        m->locked = true;
        m->owner_tid = task_current()->tid;
        spin_unlock_irqrestore(&m->waiters.lock, irq_flags);
        return true;
    }

    spin_unlock_irqrestore(&m->waiters.lock, irq_flags);
    return false;
}
