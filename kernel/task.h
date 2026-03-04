/*
 * Anykernel OS — Task Control Block (TCB)
 *
 * Each kernel thread has a TCB that stores its saved state,
 * stack, identity, and queue linkage.
 */

#ifndef TASK_H
#define TASK_H

#include <stdint.h>
#include "list.h"

/* ── Task states ─────────────────────────────────────────────── */

enum task_state {
    TASK_READY,       /* In the ready queue, waiting for CPU */
    TASK_RUNNING,     /* Currently executing on the CPU */
    TASK_DEAD         /* Finished, waiting for reap */
};

/* ── Thread entry point signature ────────────────────────────── */

typedef void (*task_entry_fn)(void);

/* ── Task Control Block ──────────────────────────────────────── */

struct task {
    uint64_t         rsp;           /* Saved stack pointer (MUST be first field) */
    uint64_t         stack_phys;    /* Physical address of stack allocation */
    uint32_t         tid;           /* Unique thread ID */
    enum task_state  state;
    task_entry_fn    entry;         /* Entry function (for trampoline) */
    char             name[16];
    struct list_node run_node;      /* Linkage in ready/dead queue */
};

/* ── API ─────────────────────────────────────────────────────── */

/*
 * Create a new kernel thread.
 * Allocates a 16KB stack via PMM, sets up initial context.
 * Returns TID, or -1 on failure.
 */
int task_create(const char *name, task_entry_fn entry);

/*
 * Exit the current thread. Marks as DEAD, calls schedule().
 * Stack is freed by the reaper (idle task), NOT here.
 */
__attribute__((noreturn))
void task_exit(void);

/*
 * Get the currently running task.
 */
struct task *task_current(void);

#endif /* TASK_H */
