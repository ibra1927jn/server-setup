/*
 * Anykernel OS v2.1 — Kernel Entry Point
 *
 * Limine hands control here in Long Mode (64-bit), Ring 0.
 * Initializes all subsystems and prints diagnostics.
 */

#include <stdint.h>
#include <stddef.h>

#include "uart.h"
#include "gdt.h"
#include "idt.h"
#include "panic.h"
#include "kprintf.h"
#include "log.h"
#include "memory.h"
#include "string.h"
#include "spinlock.h"
#include "pmm.h"
#include "kmalloc.h"
#include "vmm.h"
#include "kb.h"
#include "console.h"
#include "cpuid.h"
#include "sched.h"
#include "task.h"
#include "vfs.h"

/* Limine protocol */
#include "../limine/limine.h"

/* SSP init (defined in ssp.c) */
extern void ssp_init(void);

/* ── Global: HHDM offset (used by PHYS2VIRT / VIRT2PHYS) ─────── */

uint64_t hhdm_offset = 0;

/* ── Limine requests ──────────────────────────────────────────── */

__attribute__((used, section(".limine_requests_start")))
static volatile LIMINE_REQUESTS_START_MARKER

__attribute__((used, section(".limine_requests_end")))
static volatile LIMINE_REQUESTS_END_MARKER

__attribute__((used, section(".limine_requests")))
static volatile LIMINE_BASE_REVISION(3)

__attribute__((used, section(".limine_requests")))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_memmap_request memmap_request = {
    .id = LIMINE_MEMMAP_REQUEST,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_framebuffer_request fb_request = {
    .id = LIMINE_FRAMEBUFFER_REQUEST,
    .revision = 0
};

/* ── Helpers ──────────────────────────────────────────────────── */

static const char *memmap_type_str(uint64_t type) {
    switch (type) {
        case LIMINE_MEMMAP_USABLE:                 return "Usable";
        case LIMINE_MEMMAP_RESERVED:               return "Reserved";
        case LIMINE_MEMMAP_ACPI_RECLAIMABLE:       return "ACPI Reclaimable";
        case LIMINE_MEMMAP_ACPI_NVS:               return "ACPI NVS";
        case LIMINE_MEMMAP_BAD_MEMORY:             return "Bad Memory";
        case LIMINE_MEMMAP_BOOTLOADER_RECLAIMABLE: return "Bootloader Reclaim";
        case LIMINE_MEMMAP_KERNEL_AND_MODULES:     return "Kernel & Modules";
        case LIMINE_MEMMAP_FRAMEBUFFER:            return "Framebuffer";
        default:                                   return "Unknown";
    }
}

#include "selftest.h"
#include "pic.h"

/* Tests are in kernel/tests.c */
extern void register_selftests(void);

/* Saved for VMM to determine HHDM size from actual memory map */
struct limine_memmap_response *memmap_resp_saved = 0;

/* ── Phase 4 Final Test Suite ────────────────────────────────── */
#include "msgqueue.h"

/* Stress test */
#define STRESS_THREADS   10
#define STRESS_ITERS     10000
#define STRESS_EXPECTED  (STRESS_THREADS * STRESS_ITERS)
static volatile uint64_t shared_counter = 0;
static spinlock_t counter_lock = SPINLOCK_INIT;

static void stress_thread_fn(void) {
    for (int i = 0; i < STRESS_ITERS; i++) {
        uint64_t flags;
        spin_lock_irqsave(&counter_lock, &flags);
        shared_counter++;
        spin_unlock_irqrestore(&counter_lock, flags);
        if (i % 1000 == 0) sched_yield();
    }
}

/* RDTSC for benchmarks */
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    asm volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

/* Context switch benchmark */
#define BENCH_SWITCHES 1000
static void bench_ping_fn(void) {
    for (int i = 0; i < BENCH_SWITCHES; i++) sched_yield();
}

/* IPC benchmark */
static struct msg_queue bench_mq;
#define IPC_MSGS 500
static void ipc_sender_fn(void) {
    uint32_t msg = 0xCAFE;
    for (int i = 0; i < IPC_MSGS; i++) mq_send(&bench_mq, &msg, sizeof(msg));
}
static void ipc_receiver_fn(void) {
    uint32_t buf, len;
    for (int i = 0; i < IPC_MSGS; i++) mq_recv(&bench_mq, &buf, &len, 0);
}

/* Timer accuracy */
static volatile uint64_t sleep_start_tick = 0;
static volatile uint64_t sleep_end_tick = 0;
static void timer_test_fn(void) {
    sleep_start_tick = pit_get_ticks();
    task_sleep(200);
    sleep_end_tick = pit_get_ticks();
}

/* ── Kernel main ──────────────────────────────────────────────── */

void _start(void) {

    /* 1. UART — must be first */
    uart_init();
    LOG_OK("UART COM1 initialized at 115200 baud");

    /* 2. SSP — randomize stack canary */
    ssp_init();
    LOG_OK("Stack canary randomized (RDTSC)");

    /* 3. CPU identification */
    cpuid_detect();

    /* 4. Verify Limine protocol */
    KASSERT(LIMINE_BASE_REVISION_SUPPORTED);
    LOG_OK("Limine base revision OK");

    /* 5. GDT + TSS */
    gdt_init();
    LOG_OK("GDT loaded (7 entries, TSS with RSP0 + IST1)");

    /* 6. IDT — catch exceptions + handle IRQs */
    idt_init();
    LOG_OK("IDT loaded (#DE #UD #DF #GP #PF + IRQ0/1)");

    /* 7. PIC + PIT — hardware interrupt infrastructure */
    pic_init();
    pit_init(100);  /* 100 Hz = 10ms tick */
    pic_unmask(IRQ_TIMER);  /* Enable timer IRQ */
    asm volatile("sti");    /* ENABLE INTERRUPTS! */
    LOG_OK("PIC remapped, PIT at 100 Hz, interrupts ENABLED");

    /* 8. HHDM */
    KASSERT(hhdm_request.response != NULL);
    hhdm_offset = hhdm_request.response->offset;
    LOG_INFO("HHDM offset: 0x%016lx", hhdm_offset);

    /* 9. Memory map */
    KASSERT(memmap_request.response != NULL);
    memmap_resp_saved = memmap_request.response;
    uint64_t entry_count = memmap_request.response->entry_count;
    LOG_INFO("Memory map: %lu entries", entry_count);

    uint64_t usable_bytes = 0;
    uint64_t usable_pages = 0;
    for (uint64_t i = 0; i < entry_count; i++) {
        struct limine_memmap_entry *e = memmap_request.response->entries[i];

        uint64_t aligned_base = PAGE_ALIGN_UP(e->base);
        uint64_t aligned_end  = PAGE_ALIGN_DOWN(e->base + e->length);
        uint64_t pages = (aligned_end > aligned_base)
                         ? (aligned_end - aligned_base) / PAGE_SIZE : 0;

        kprintf("  [%2lu] %p-%p %8lu KB %-22s",
                i, (void *)e->base, (void *)(e->base + e->length),
                e->length / 1024, memmap_type_str(e->type));

        if (e->type == LIMINE_MEMMAP_USABLE) {
            kprintf(" (%lu pages)", pages);
            usable_bytes += e->length;
            usable_pages += pages;
        }
        kprintf("\n");
    }
    LOG_INFO("Total usable: %lu KB (%lu MB) = %lu pages",
             usable_bytes / 1024, usable_bytes / (1024 * 1024), usable_pages);

    /* ─────────────────────────────────────────────────────────────
     * 10. PMM — Physical Memory Manager (Buddy Allocator)
     * ───────────────────────────────────────────────────────────── */
    pmm_init(memmap_request.response, hhdm_offset);
    pmm_dump_stats();

    /* ─────────────────────────────────────────────────────────────
     * 11. VMM — Virtual Memory Manager (Paging)
     * ───────────────────────────────────────────────────────────── */
    vmm_init();
    vmm_dump_tables();

    /* ─────────────────────────────────────────────────────────────
     * 12. Framebuffer Console
     * ───────────────────────────────────────────────────────────── */
    if (fb_request.response && fb_request.response->framebuffer_count > 0) {
        struct limine_framebuffer *fb = fb_request.response->framebuffers[0];
        console_init(fb->address, fb->width, fb->height, fb->pitch, fb->bpp);
        LOG_OK("Framebuffer console: %lux%lu, %u bpp",
               fb->width, fb->height, fb->bpp);
    }

    /* ─────────────────────────────────────────────────────────────
     * 13. Keyboard
     * ───────────────────────────────────────────────────────────── */
    kb_init();

    /* ─────────────────────────────────────────────────────────────
     * 13b. VFS — Virtual File System
     * ───────────────────────────────────────────────────────────── */
    vfs_init();
    extern void devfs_init(void);
    devfs_init();

    /* ─────────────────────────────────────────────────────────────
     * 14. Self-tests
     * ───────────────────────────────────────────────────────────── */
    register_selftests();
    int failures = run_all_selftests();

    /* ─────────────────────────────────────────────────────────────
     * 15. Boot memory report
     * ───────────────────────────────────────────────────────────── */
    kprintf("\n--- Boot Memory Report ---\n");
    {
        extern char __kernel_start, __kernel_end;
        uint64_t kernel_size = (uint64_t)&__kernel_end - (uint64_t)&__kernel_start;
        uint64_t free_pg = pmm_free_count();
        uint64_t used_pg = pmm_used_count();
        uint64_t total = free_pg + used_pg;
        uint64_t pct = (free_pg * 100) / (total > 0 ? total : 1);

        kprintf("  Kernel:   %lu KB (0x%lx - 0x%lx)\n",
                kernel_size / 1024, (uint64_t)&__kernel_start, (uint64_t)&__kernel_end);
        kprintf("  RAM:      %lu pages (%lu MB)\n", total, total * 4 / 1024);
        kprintf("  Free:     %lu pages (%lu KB) [%lu%%]\n", free_pg, free_pg * 4, pct);
        kprintf("  Used:     %lu pages (%lu KB)\n", used_pg, used_pg * 4);
        kprintf("  Peak:     %lu pages (%lu KB)\n", pmm_peak_used(), pmm_peak_used() * 4);
    }

    kmalloc_dump_stats();

    /* Banner */
    uint64_t uptime_ms = pit_get_ticks() * 10;  /* 100 Hz = 10ms per tick */
    kprintf("\n==============================\n");
    kprintf("  Anykernel OS v0.5.0\n");
    kprintf("  %d tests, %d failures\n", selftest_count(), failures);
    kprintf("  Boot time: %lu ms\n", uptime_ms);
    kprintf("==============================\n");

    kprintf("\n");
    if (failures > 0) {
        LOG_ERROR("SELF-TEST FAILURES: %d", failures);
    }

    /* ── Step 16: Scheduler ──────────────────────────────────── */
    sched_init();
    LOG_OK("Scheduler initialized");

    /* Record PMM free count before tests */
    uint64_t pmm_free_before = pmm_free_count();

    /* ══ TEST 1: Stress — 10 threads × 10,000 = 100,000 ═══════ */
    kprintf("\n--- [TEST 1] Stress: %d threads x %d ---\n",
            STRESS_THREADS, STRESS_ITERS);
    shared_counter = 0;
    int stress_tids[STRESS_THREADS];
    for (int i = 0; i < STRESS_THREADS; i++) {
        char name[16];
        ksnprintf(name, sizeof(name), "stress-%d", i);
        stress_tids[i] = task_create(name, stress_thread_fn);
    }
    for (int i = 0; i < STRESS_THREADS; i++)
        task_join((uint32_t)stress_tids[i]);

    if (shared_counter == STRESS_EXPECTED)
        LOG_OK("Stress PASSED: %lu/%d", shared_counter, STRESS_EXPECTED);
    else
        LOG_ERROR("Stress FAILED: %lu/%d", shared_counter, STRESS_EXPECTED);

    /* ══ TEST 2: Context switch benchmark ═════════════════════ */
    kprintf("\n--- [TEST 2] Context switch benchmark ---\n");
    int bench_tid = task_create("bench-ping", bench_ping_fn);
    uint64_t ts_start = rdtsc();
    for (int i = 0; i < BENCH_SWITCHES; i++) sched_yield();
    uint64_t ts_end = rdtsc();
    task_join((uint32_t)bench_tid);
    uint64_t per_switch = (ts_end - ts_start) / (BENCH_SWITCHES * 2);
    LOG_OK("Context switch: %lu cycles/switch (%d pairs)", per_switch, BENCH_SWITCHES);

    /* ══ TEST 3: IPC message queue benchmark ══════════════════ */
    kprintf("\n--- [TEST 3] IPC benchmark ---\n");
    mq_init(&bench_mq);
    uint64_t ipc_start = rdtsc();
    int ipc_s = task_create("ipc-send", ipc_sender_fn);
    int ipc_r = task_create("ipc-recv", ipc_receiver_fn);
    task_join((uint32_t)ipc_s);
    task_join((uint32_t)ipc_r);
    uint64_t per_msg = (rdtsc() - ipc_start) / IPC_MSGS;
    LOG_OK("IPC: %lu cycles/msg (%d messages)", per_msg, IPC_MSGS);

    /* ══ TEST 4: Timer accuracy — sleep(200ms) ═══════════════ */
    kprintf("\n--- [TEST 4] Timer accuracy ---\n");
    int tt = task_create("timer-test", timer_test_fn);
    task_join((uint32_t)tt);
    uint64_t sleep_ms = (sleep_end_tick - sleep_start_tick) * 10;
    if (sleep_ms >= 190 && sleep_ms <= 250)
        LOG_OK("Timer PASSED: sleep(200ms) = %lu ms", sleep_ms);
    else
        LOG_ERROR("Timer FAILED: sleep(200ms) = %lu ms", sleep_ms);

    /* ══ TEST 5: Memory leak check ════════════════════════════ */
    kprintf("\n--- [TEST 5] Memory leak check ---\n");
    /* Let reaper clean up dead tasks */
    for (int i = 0; i < 5; i++) task_sleep(20);
    uint64_t pmm_free_after = pmm_free_count();
    int64_t leak = (int64_t)pmm_free_before - (int64_t)pmm_free_after;
    if (leak <= 0)
        LOG_OK("Leak check PASSED: %lu → %lu pages (no leak)", pmm_free_before, pmm_free_after);
    else
        LOG_ERROR("LEAK: %ld pages (%ld KB) not freed", leak, leak * 4);

    /* ══ Final Report ═════════════════════════════════════════ */
    kprintf("\n══════════════════════════════════════\n");
    kprintf("  Phase 4 COMPLETE  (v0.4.4)\n");
    kprintf("  35 kernel + 5 runtime tests\n");
    kprintf("══════════════════════════════════════\n\n");

    LOG_INFO("System ready. Init task handling keyboard.");

    for (;;) {
        asm volatile("hlt");
        char c;
        while ((c = kb_getchar()) != 0) {
            if (console_available()) {
                console_putchar(c);
            }
        }
    }
}
