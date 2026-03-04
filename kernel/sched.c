/*
 * Anykernel OS — O(1) Preemptive Priority Scheduler
 *
 * Features (v0.4.5):
 *   - 64-level priority queues with O(1) bitmap scheduling (BSF)
 *   - task_sleep(ms) with sleep queue and PIT-driven wakeup
 *   - task_join(tid) with sleeping wait
 *   - CPU tick accounting per task
 *   - Stack canary verification on every schedule()
 *   - Idle task with dead-task reaper
 *   - Wait queue integration via sched_add_ready()
 *
 * TRAP HANDLING:
 *   1. EOI before schedule (in idt.c)
 *   2. sched_lock released in trampoline
 *   3. sti in trampoline
 *   4. Deferred stack free via reaper
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
#include "pic.h"
#include "waitqueue.h"

#include <stdint.h>
#include <stdbool.h>

/* ── External: context_switch(old, new) in ASM ────────────────── */
extern void context_switch(struct task *old, struct task *new_task);

/* ── Constants ────────────────────────────────────────────────── */

#define TASK_STACK_PAGES  4
#define TASK_STACK_SIZE   (TASK_STACK_PAGES * PAGE_SIZE)
#define MAX_TASKS         64

/* ── Scheduler state ─────────────────────────────────────────── */

static spinlock_t sched_lock = SPINLOCK_INIT;

/* O(1) bitmap scheduler: 64 priority queues + bitmap */
static struct list_head prio_queues[TASK_PRIO_LEVELS];
static volatile uint64_t prio_bitmap = 0;  /* bit N set = queue N non-empty */
static struct list_head sleep_queue = LIST_HEAD_INIT(sleep_queue);

/* O(1) helpers: BSF finds lowest set bit = highest priority */
static inline int bitmap_find_first(uint64_t bm) {
    uint64_t result;
    asm volatile("bsfq %1, %0" : "=r"(result) : "r"(bm));
    return (int)result;
}

static inline void bitmap_enqueue(struct task *t) {
    list_push_back(&prio_queues[t->priority], &t->run_node);
    prio_bitmap |= (1ULL << t->priority);
}

static inline struct task *bitmap_dequeue(void) {
    int p = bitmap_find_first(prio_bitmap);
    struct list_node *node = prio_queues[p].sentinel.next;
    struct task *t = container_of(node, struct task, run_node);
    list_remove_node(node);
    if (list_empty(&prio_queues[p]))
        prio_bitmap &= ~(1ULL << p);
    return t;
}
static struct list_head dead_queue  = LIST_HEAD_INIT(dead_queue);

static struct task  task_pool[MAX_TASKS];
static uint32_t     task_pool_used = 0;
static uint32_t     next_tid = 0;

static struct task *current_task = 0;
static struct task *idle_task    = 0;

static volatile int need_resched = 0;

/* ── Allocate a TCB — recycles dead slots first ──────────────── */

static struct task *alloc_tcb(void) {
    /* First pass: recycle a DEAD slot */
    for (uint32_t i = 0; i < task_pool_used; i++) {
        if (task_pool[i].state == TASK_DEAD && task_pool[i].stack_phys == 0) {
            struct task *t = &task_pool[i];
            memset(t, 0, sizeof(*t));
            return t;
        }
    }
    /* Second pass: extend pool */
    if (task_pool_used >= MAX_TASKS) return 0;
    struct task *t = &task_pool[task_pool_used++];
    memset(t, 0, sizeof(*t));
    return t;
}

/* ── Find task by TID ────────────────────────────────────────── */

static struct task *find_task(uint32_t tid) {
    for (uint32_t i = 0; i < task_pool_used; i++) {
        if (task_pool[i].tid == tid) return &task_pool[i];
    }
    return 0;
}

/* ── Stack canary ────────────────────────────────────────────── */

static void stack_canary_set(struct task *t) {
    if (t->stack_phys == 0) return;  /* boot stack */
    uint64_t *canary = (uint64_t *)PHYS2VIRT(t->stack_phys);
    *canary = TASK_STACK_CANARY;
}

static void stack_canary_check(struct task *t) {
    if (t->stack_phys == 0) return;  /* boot stack */
    uint64_t *canary = (uint64_t *)PHYS2VIRT(t->stack_phys);
    if (*canary != TASK_STACK_CANARY) {
        kprintf(ANSI_RED "\n!!! STACK OVERFLOW DETECTED !!!\n" ANSI_RESET);
        kprintf("  Task: '%s' (TID %u)\n", t->name, t->tid);
        kprintf("  Expected canary: 0x%016lx\n", (uint64_t)TASK_STACK_CANARY);
        kprintf("  Found:           0x%016lx\n", *canary);
        for (;;) asm volatile("cli; hlt");
    }
}

/* ── Trampoline ──────────────────────────────────────────────── */

static void task_entry_trampoline(void) {
    spin_unlock(&sched_lock);       /* Trap 2 */
    asm volatile("sti");            /* Trap 3 */

    task_entry_fn fn = current_task->entry;
    fn();

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

    uint64_t stack_phys = pmm_alloc_pages_zero(2);
    if (stack_phys == 0) {
        spin_unlock_irqrestore(&sched_lock, irq_flags);
        return -1;
    }

    t->stack_phys = stack_phys;
    t->tid = next_tid++;
    t->state = TASK_READY;
    t->priority = TASK_PRIO_NORMAL;
    t->entry = entry;
    t->ticks_used = 0;
    t->sleep_until = 0;
    t->finished = false;
    strncpy(t->name, name, sizeof(t->name) - 1);
    t->name[sizeof(t->name) - 1] = '\0';

    /* Set stack canary at bottom of stack */
    stack_canary_set(t);

    /* Build initial context_switch frame */
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

    bitmap_enqueue(t);

    spin_unlock_irqrestore(&sched_lock, irq_flags);

    LOG_OK("Task '%s' created (TID %u, stack 0x%lx)", t->name, t->tid, stack_phys);
    return (int)t->tid;
}

/* ── task_exit ───────────────────────────────────────────────── */

__attribute__((noreturn))
void task_exit(void) {
    asm volatile("cli");

    current_task->state = TASK_DEAD;
    current_task->finished = true;

    /* Wake ALL threads waiting to join us — instant, no polling */
    if (current_task->join_wq) {
        wq_wake_all(current_task->join_wq);
    }

    list_push_back(&dead_queue, &current_task->run_node);

    LOG_INFO("Task '%s' (TID %u) exiting, used %lu ticks",
             current_task->name, current_task->tid, current_task->ticks_used);

    asm volatile("sti");
    schedule();

    for (;;) asm volatile("hlt");
}

/* ── task_current ────────────────────────────────────────────── */

struct task *task_current(void) {
    return current_task;
}

/* ── task_sleep ──────────────────────────────────────────────── */

void task_sleep(uint64_t ms) {
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    uint64_t ticks = ms / 10;  /* 100 Hz PIT = 10ms/tick */
    if (ticks == 0) ticks = 1;

    current_task->sleep_until = pit_get_ticks() + ticks;
    current_task->state = TASK_SLEEPING;
    list_push_back(&sleep_queue, &current_task->run_node);

    spin_unlock_irqrestore(&sched_lock, irq_flags);
    schedule();
}

/* ── task_join ───────────────────────────────────────────────── */

int task_join(uint32_t tid) {
    struct task *target = find_task(tid);
    if (!target) return -1;

    /* Already finished? Return immediately */
    if (target->finished) return 0;

    /* Allocate a wait queue on-demand for joiners */
    struct wait_queue join_wq;
    wq_init(&join_wq);

    if (!target->join_wq) {
        target->join_wq = &join_wq;
    }

    /* Sleep until target calls task_exit → wq_wake_all */
    while (!target->finished) {
        wq_wait(target->join_wq);
    }
    return 0;
}

/* ── Wake sleeping tasks ─────────────────────────────────────── */

static void wake_sleepers(void) {
    /* Called with sched_lock held */
    uint64_t now = pit_get_ticks();
    struct list_node *pos, *tmp;

    list_for_each_safe(pos, tmp, &sleep_queue) {
        struct task *t = container_of(pos, struct task, run_node);
        if (now >= t->sleep_until) {
            list_remove_node(pos);
            t->state = TASK_READY;
            bitmap_enqueue(t);
        }
    }
}

/* ── Schedule ────────────────────────────────────────────────── */

void schedule(void) {
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    need_resched = 0;

    /* Wake any sleeping tasks whose time has come */
    wake_sleepers();

    /* Check stack canary of current task */
    stack_canary_check(current_task);

    /* O(1) pick: BSF on bitmap finds highest priority in 1 cycle */
    struct task *next;
    if (prio_bitmap != 0) {
        next = bitmap_dequeue();
    } else {
        next = idle_task;
    }

    if (next == current_task) {
        spin_unlock_irqrestore(&sched_lock, irq_flags);
        return;
    }

    struct task *old = current_task;
    if (old->state == TASK_RUNNING) {
        old->state = TASK_READY;
        bitmap_enqueue(old);
    }

    next->state = TASK_RUNNING;
    current_task = next;

    context_switch(old, next);

    /* We resume here when switched back to this thread */
    spin_unlock_irqrestore(&sched_lock, irq_flags);
}

/* ── sched_yield ─────────────────────────────────────────────── */

void sched_yield(void) {
    schedule();
}

/* ── sched_tick — called from PIT handler ────────────────────── */

void sched_tick(void) {
    /* Guard: PIT fires before sched_init sets current_task */
    if (!current_task) return;

    need_resched = 1;

    /* CPU accounting */
    current_task->ticks_used++;
}

int sched_need_resched(void) {
    if (!current_task) return 0;
    return need_resched;
}

/* ── sched_add_ready — used by wait queues to re-enqueue ─────── */

void sched_add_ready(struct task *t) {
    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);
    bitmap_enqueue(t);
    spin_unlock_irqrestore(&sched_lock, irq_flags);
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

        if (stack_phys) {
            pmm_free_pages(stack_phys, 2);
        }
        LOG_INFO("Reaped task '%s' (TID %u)", dead_name, dead_tid);
    }
}

/* ── sched_init ──────────────────────────────────────────────── */

void sched_init(void) {
    /* Initialize all 64 priority queues */
    for (int i = 0; i < TASK_PRIO_LEVELS; i++)
        list_head_init(&prio_queues[i]);
    prio_bitmap = 0;

    struct task *init_task = alloc_tcb();
    init_task->tid = next_tid++;
    init_task->state = TASK_RUNNING;
    init_task->stack_phys = 0;
    init_task->priority = TASK_PRIO_HIGH;
    init_task->entry = 0;
    init_task->ticks_used = 0;
    init_task->finished = false;
    strncpy(init_task->name, "init", sizeof(init_task->name));
    current_task = init_task;

    int idle_tid = task_create("idle", idle_fn);
    (void)idle_tid;

    uint64_t irq_flags;
    spin_lock_irqsave(&sched_lock, &irq_flags);

    struct list_node *pos;
    list_for_each(pos, &prio_queues[TASK_PRIO_NORMAL]) {
        struct task *t = container_of(pos, struct task, run_node);
        if (t == &task_pool[1]) {
            idle_task = t;
            list_remove_node(pos);
            if (list_empty(&prio_queues[TASK_PRIO_NORMAL]))
                prio_bitmap &= ~(1ULL << TASK_PRIO_NORMAL);
            idle_task->state = TASK_READY;
            break;
        }
    }

    spin_unlock_irqrestore(&sched_lock, irq_flags);

    LOG_OK("Scheduler initialized (init TID=%u, idle TID=%u)",
           init_task->tid, idle_task->tid);
}
