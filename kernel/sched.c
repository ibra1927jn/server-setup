/*
 * Anykernel OS — Preemptive Round-Robin Scheduler
 *
 * Manages kernel threads with cooperative context_switch() called
 * from PIT IRQ handler or sched_yield().
 *
 * CRITICAL DESIGN NOTES (the 4 traps):
 *   1. EOI is sent BEFORE schedule() in pit_tick() — otherwise the
 *      PIC freezes after the first context switch.
 *   2. The sched_lock is released by the NEW thread after context_switch
 *      returns (or in task_entry_trampoline for first-run threads).
 *   3. New threads start with interrupts disabled (no iretq path).
 *      The trampoline executes sti explicitly.
 *   4. task_exit() does NOT free the stack — the reaper does that
 *      from a different execution context (idle task).
 */

#include "sched.h"
#include "task.h"
#include "list.h"
#include "spinlock.h"
#include "pmm.h"
#include "memory.h"
#include "string.h"
#include "kprintf.h"
#include "log.h"

#include <stdint.h>
#include <stdbool.h>

/* ── External: context_switch(old, new) in ASM ────────────────── */
extern void context_switch(struct task *old, struct task *new_task);

/* ── Constants ────────────────────────────────────────────────── */

#define TASK_STACK_PAGES  4          /* 16KB per thread stack */
#define TASK_STACK_SIZE   (TASK_STACK_PAGES * PAGE_SIZE)
#define MAX_TASKS         32

/* ── Scheduler state ─────────────────────────────────────────── */

static spinlock_t sched_lock = SPINLOCK_INIT;

static struct list_head ready_queue = LIST_HEAD_INIT(ready_queue);
static struct list_head dead_queue  = LIST_HEAD_INIT(dead_queue);

static struct task  task_pool[MAX_TASKS];
static uint32_t     task_pool_used = 0;
static uint32_t     next_tid = 0;

static struct task *current_task = 0;
static struct task *idle_task    = 0;

/* ── Need-reschedule flag ────────────────────────────────────── */

static volatile int need_resched = 0;

/* ── Allocate a TCB from the pool ────────────────────────────── */

static struct task *alloc_tcb(void) {
    if (task_pool_used >= MAX_TASKS) return 0;
    struct task *t = &task_pool[task_pool_used++];
    memset(t, 0, sizeof(*t));
    return t;
}

/* ── Trampoline: first function run by a new thread ──────────── */

/*
 * All new threads enter here after their first context_switch.
 * entry_fn is read from the current task's TCB.
 */
static void task_entry_trampoline(void) {
    /* Trap 2: Release the scheduler lock that schedule() held */
    spin_unlock(&sched_lock);

    /* Trap 3: Re-enable interrupts (we arrived via ret, not iretq) */
    asm volatile("sti");

    /* Run the actual thread function */
    task_entry_fn fn = current_task->entry;
    fn();

    /* Trap 4: Don't free stack here — just mark dead */
    task_exit();
}

/* ── Idle task ───────────────────────────────────────────────── */

static void idle_fn(void) {
    for (;;) {
        sched_reap_dead();
        asm volatile("sti; hlt");
    }
}

/* ── Create a new task ───────────────────────────────────────── */

int task_create(const char *name, task_entry_fn entry) {
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    struct task *t = alloc_tcb();
    if (!t) {
        spin_unlock_irqrestore(&sched_lock, irq_flags);
        return -1;
    }

    /* Allocate stack pages (order 2 = 4 pages = 16KB) */
    uint64_t stack_phys = pmm_alloc_pages_zero(2);
    if (stack_phys == 0) {
        spin_unlock_irqrestore(&sched_lock, irq_flags);
        return -1;
    }

    t->stack_phys = stack_phys;
    t->tid = next_tid++;
    t->state = TASK_READY;
    t->entry = entry;
    strncpy(t->name, name, sizeof(t->name) - 1);
    t->name[sizeof(t->name) - 1] = '\0';

    /*
     * Set up initial stack frame for context_switch.
     *
     * context_switch pops: r15, r14, r13, r12, rbx, rbp, then ret.
     * We fake this so when context_switch "restores" this task,
     * it returns to task_entry_trampoline.
     *
     * Stack layout (grows down from top):
     *   [task_entry_trampoline]  ← ret target
     *   [0]                      ← rbp
     *   [0]                      ← rbx
     *   [0]                      ← r12
     *   [0]                      ← r13
     *   [0]                      ← r14
     *   [0]                      ← r15
     *   ↑ rsp saved here
     */
    uint64_t stack_virt = (uint64_t)PHYS2VIRT(stack_phys);
    uint64_t stack_top = stack_virt + TASK_STACK_SIZE;

    uint64_t *sp = (uint64_t *)stack_top;

    *(--sp) = (uint64_t)task_entry_trampoline;  /* ret address */
    *(--sp) = 0;   /* rbp */
    *(--sp) = 0;   /* rbx */
    *(--sp) = 0;   /* r12 */
    *(--sp) = 0;   /* r13 */
    *(--sp) = 0;   /* r14 */
    *(--sp) = 0;   /* r15 */

    t->rsp = (uint64_t)sp;

    /* Add to ready queue */
    list_push_back(&ready_queue, &t->run_node);

    spin_unlock_irqrestore(&sched_lock, irq_flags);

    LOG_OK("Task '%s' created (TID %u, stack 0x%lx)", t->name, t->tid, stack_phys);
    return (int)t->tid;
}

/* ── task_exit ───────────────────────────────────────────────── */

__attribute__((noreturn))
void task_exit(void) {
    asm volatile("cli");

    current_task->state = TASK_DEAD;
    list_push_back(&dead_queue, &current_task->run_node);

    LOG_INFO("Task '%s' (TID %u) exiting", current_task->name, current_task->tid);

    /* Schedule will pick the next task — we won't return */
    asm volatile("sti");
    schedule();

    /* Should never reach here */
    for (;;) asm volatile("hlt");
}

/* ── task_current ────────────────────────────────────────────── */

struct task *task_current(void) {
    return current_task;
}

/* ── Schedule ────────────────────────────────────────────────── */

void schedule(void) {
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    need_resched = 0;

    /* Pick next from ready queue, or idle */
    struct task *next;

    if (list_empty(&ready_queue)) {
        next = idle_task;
    } else {
        struct list_node *node = ready_queue.sentinel.next;
        next = container_of(node, struct task, run_node);
        list_remove_node(node);
    }

    /* If same task, just return */
    if (next == current_task) {
        spin_unlock_irqrestore(&sched_lock, irq_flags);
        return;
    }

    /* Put current back in ready queue if still runnable */
    struct task *old = current_task;
    if (old->state == TASK_RUNNING) {
        old->state = TASK_READY;
        list_push_back(&ready_queue, &old->run_node);
    }

    next->state = TASK_RUNNING;
    current_task = next;

    /*
     * CONTEXT SWITCH
     *
     * Critical locking protocol:
     * - We hold sched_lock across the switch.
     * - When context_switch "returns" on the NEW thread's stack:
     *   - If it's resuming: it returns into this function (schedule),
     *     and the spin_unlock_irqrestore below releases the lock.
     *   - If it's a first-run: it returns into task_entry_trampoline,
     *     which explicitly releases sched_lock.
     */
    context_switch(old, next);

    /*
     * We resume here when someone switches BACK to this thread.
     * Release the lock that the OTHER thread's schedule() acquired.
     */
    spin_unlock_irqrestore(&sched_lock, irq_flags);
}

/* ── sched_yield ─────────────────────────────────────────────── */

void sched_yield(void) {
    schedule();
}

/* ── Set need-reschedule flag (called from PIT) ──────────────── */

void sched_tick(void) {
    need_resched = 1;
}

int sched_need_resched(void) {
    return need_resched;
}

/* ── Reap dead tasks ─────────────────────────────────────────── */

void sched_reap_dead(void) {
    while (!list_empty(&dead_queue)) {
        uint64_t irq_flags;
        spin_lock_irqsave(&sched_lock, &irq_flags);

        if (list_empty(&dead_queue)) {
            spin_unlock_irqrestore(&sched_lock, irq_flags);
            break;
        }

        struct list_node *node = dead_queue.sentinel.next;
        list_remove_node(node);

        struct task *dead = container_of(node, struct task, run_node);
        uint64_t stack_phys = dead->stack_phys;
        char dead_name[16];
        strncpy(dead_name, dead->name, sizeof(dead_name));
        uint32_t dead_tid = dead->tid;

        spin_unlock_irqrestore(&sched_lock, irq_flags);

        /* Free the stack (safe — we're on a different stack) */
        if (stack_phys) {
            pmm_free_pages(stack_phys, 2); /* order 2 = 4 pages */
        }
        LOG_INFO("Reaped task '%s' (TID %u)", dead_name, dead_tid);
    }
}

/* ── sched_init ──────────────────────────────────────────────── */

void sched_init(void) {
    /* Task 0: wrap the current execution context ("init") */
    struct task *init_task = alloc_tcb();
    init_task->tid = next_tid++;
    init_task->state = TASK_RUNNING;
    init_task->stack_phys = 0;  /* boot stack, not PMM-allocated */
    init_task->entry = 0;
    strncpy(init_task->name, "init", sizeof(init_task->name));
    current_task = init_task;

    /* Create idle task */
    int idle_tid = task_create("idle", idle_fn);
    (void)idle_tid;

    /* Remove idle from ready queue — it's special, only runs
     * when nothing else is READY */
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    struct list_node *pos;
    list_for_each(pos, &ready_queue) {
        struct task *t = container_of(pos, struct task, run_node);
        if (t == &task_pool[1]) {
            idle_task = t;
            list_remove_node(pos);
            idle_task->state = TASK_READY;
            break;
        }
    }

    spin_unlock_irqrestore(&sched_lock, irq_flags);

    LOG_OK("Scheduler initialized (init TID=%u, idle TID=%u)",
           init_task->tid, idle_task->tid);
}
