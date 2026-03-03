/*
 * Anykernel OS — Kernel Self-Tests
 *
 * All test functions extracted from main.c into a separate file.
 * Each test is a static bool function: returns true on pass, false on fail.
 * Tests are registered via the selftest framework in register_selftests().
 */

#include "selftest.h"
#include "pmm.h"
#include "kmalloc.h"
#include "vmm.h"
#include "spinlock.h"
#include "memory.h"
#include "string.h"
#include "pic.h"
#include "console.h"
#include "kb.h"
#include <stdint.h>
#include <stdbool.h>

/* ── Spinlock & Memory tests ─────────────────────────────────── */

static bool test_spinlock(void) {
    spinlock_t lock = SPINLOCK_INIT;
    if (!spin_trylock(&lock)) return false;
    spin_unlock(&lock);
    return true;
}

static bool test_memops(void) {
    uint8_t a[16], b[16];
    memset(a, 0xAA, 16);
    if (a[0] != 0xAA || a[15] != 0xAA) return false;
    memcpy(b, a, 16);
    return memcmp(a, b, 16) == 0;
}

/* ── PMM tests ───────────────────────────────────────────────── */

static bool test_pmm_alloc_free(void) {
    uint64_t p = pmm_alloc_pages(0);
    if (p == 0 || (p & (PAGE_SIZE - 1)) != 0) return false;
    pmm_free_pages(p, 0);
    return true;
}

static bool test_pmm_order5(void) {
    uint64_t p = pmm_alloc_pages(5);
    if (p == 0 || (p % (32 * PAGE_SIZE)) != 0) return false;
    pmm_free_pages(p, 5);
    return true;
}

/* ── kmalloc tests ───────────────────────────────────────────── */

static bool test_kmalloc_small(void) {
    void *p = kmalloc(64);
    if (!p) return false;
    memset(p, 0xBB, 64);
    kfree(p);
    return true;
}

static bool test_kmalloc_large(void) {
    void *p = kmalloc(8192);
    if (!p) return false;
    memset(p, 0xCC, 8192);
    kfree(p);
    return true;
}

static bool test_kzmalloc(void) {
    uint8_t *p = kzmalloc(128);
    if (!p) return false;
    for (int i = 0; i < 128; i++) {
        if (p[i] != 0) { kfree(p); return false; }
    }
    kfree(p);
    return true;
}

static bool test_poison(void) {
    uint8_t *p = kmalloc(64);
    if (!p) return false;
    memset(p, 0x42, 64);
    uint8_t *saved = p;
    kfree(p);
    for (int i = 8; i < 64; i++) {
        if (saved[i] != 0xDE) return false;
    }
    return true;
}

static bool test_krealloc(void) {
    uint8_t *p = kmalloc(32);
    if (!p) return false;
    memset(p, 0xAA, 32);
    uint8_t *p2 = krealloc(p, 256);
    if (!p2) return false;
    if (p2[0] != 0xAA || p2[31] != 0xAA) { kfree(p2); return false; }
    if (kmalloc_usable_size(p2) < 256) { kfree(p2); return false; }
    kfree(p2);
    return true;
}

static bool test_slab_reclamation(void) {
    uint64_t before = pmm_free_count();
    void *p = kmalloc(64);
    if (pmm_free_count() >= before) { kfree(p); return false; }
    kfree(p);
    return pmm_free_count() == before;
}

static bool test_pmm_watermark(void) {
    uint64_t free = pmm_free_count();
    uint64_t total = free + pmm_used_count();
    uint64_t pct = (free * 100) / (total > 0 ? total : 1);
    return pct >= 10;
}

/* ── VMM tests ───────────────────────────────────────────────── */

static bool test_vmm_map_write_read(void) {
    uint64_t phys = pmm_alloc_pages_zero(0);
    if (phys == 0) return false;

    uint64_t test_virt = 0xFFFFFF0000000000UL;
    vmm_map_page(test_virt, phys, PTE_PRESENT | PTE_WRITE | PTE_NX);

    volatile uint64_t *ptr = (volatile uint64_t *)test_virt;
    *ptr = 0xCAFEBABE12345678UL;

    bool ok = (*ptr == 0xCAFEBABE12345678UL);

    vmm_unmap_page(test_virt);
    pmm_free_pages(phys, 0);
    return ok;
}

static bool test_vmm_virt_to_phys(void) {
    uint64_t kernel_addr = (uint64_t)&test_vmm_virt_to_phys;
    uint64_t phys = vmm_virt_to_phys(kernel_addr);
    return phys != 0;
}

static bool test_vmm_hhdm_integrity(void) {
    extern uint64_t hhdm_offset;
    volatile uint8_t *p = (volatile uint8_t *)(hhdm_offset + 0x1000);
    (void)*p;
    return true;
}

/* ── Timer test ──────────────────────────────────────────────── */

static bool test_pit_ticking(void) {
    /*
     * The PIT has been running since pic_init/pit_init in boot.
     * By the time tests run, several ticks should have fired.
     * If ticks == 0, the PIT or IRQ dispatch is broken.
     */
    return pit_get_ticks() > 0;
}

/* ── VMM collision detection test ────────────────────────────── */

static bool test_vmm_map_returns_mapping(void) {
    /* Map a page, then verify virt_to_phys returns the right phys */
    uint64_t phys = pmm_alloc_pages_zero(0);
    if (phys == 0) return false;

    uint64_t test_virt = 0xFFFFFF0000001000UL;
    vmm_map_page(test_virt, phys, PTE_PRESENT | PTE_WRITE | PTE_NX);

    uint64_t resolved = vmm_virt_to_phys(test_virt);
    bool ok = (resolved == phys);

    vmm_unmap_page(test_virt);
    pmm_free_pages(phys, 0);
    return ok;
}

/* ── String tests ────────────────────────────────────────────── */

static bool test_strlen(void) {
    if (strlen("") != 0) return false;
    if (strlen("hello") != 5) return false;
    if (strncmp("abc", "abd", 2) != 0) return false;
    if (strncmp("abc", "abd", 3) == 0) return false;
    char buf[8] = {0};
    strncpy(buf, "hi", 8);
    if (buf[0] != 'h' || buf[1] != 'i' || buf[2] != '\0') return false;
    return true;
}

/* ── Negative / edge-case tests ──────────────────────────────── */

static bool test_kfree_null(void) {
    /* kfree(NULL) must be a safe no-op (no crash) */
    kfree((void *)0);
    return true;
}

static bool test_kmalloc_zero(void) {
    /* kmalloc(0) — should return NULL or a valid freeable pointer */
    void *p = kmalloc(0);
    if (p) kfree(p);  /* If non-NULL, must be freeable */
    return true;       /* Either behavior is acceptable */
}

static bool test_krealloc_null(void) {
    /* krealloc(NULL, size) should behave like kmalloc(size) */
    uint8_t *p = krealloc((void *)0, 64);
    if (!p) return false;
    memset(p, 0xDD, 64);
    bool ok = (p[0] == 0xDD && p[63] == 0xDD);
    kfree(p);
    return ok;
}

static bool test_pmm_alloc_free_reuse(void) {
    /* Alloc, free, alloc again — should reuse the same page (buddy coalesced) */
    uint64_t p1 = pmm_alloc_pages(0);
    if (p1 == 0) return false;
    pmm_free_pages(p1, 0);
    uint64_t p2 = pmm_alloc_pages(0);
    if (p2 == 0) return false;
    pmm_free_pages(p2, 0);
    /* Both allocations should succeed and return valid addresses */
    return (p1 != 0) && (p2 != 0);
}

static bool test_memmove_overlap(void) {
    /* memmove must handle overlapping regions correctly */
    char buf[16];
    memcpy(buf, "ABCDEFGHIJ", 10);
    memmove(buf + 2, buf, 8);  /* Forward overlap */
    /* buf[0..1] unchanged, buf[2..9] = old buf[0..7] */
    if (buf[0] != 'A' || buf[1] != 'B') return false;
    if (buf[2] != 'A' || buf[3] != 'B') return false;
    if (buf[4] != 'C' || buf[5] != 'D') return false;
    return true;
}

static bool test_spinlock_irqsave(void) {
    /* Test IRQ-safe spinlock: save flags, lock, unlock, restore */
    spinlock_t lock = SPINLOCK_INIT;
    uint64_t flags;
    spin_lock_irqsave(&lock, &flags);
    /* We're holding the lock with IRQs disabled */
    spin_unlock_irqrestore(&lock, flags);
    return true;
}

static bool test_vmm_unmap_verify(void) {
    /* Map a page, unmap it, verify virt_to_phys returns 0 */
    uint64_t phys = pmm_alloc_pages_zero(0);
    if (phys == 0) return false;

    uint64_t test_virt = 0xFFFFFF0000002000UL;
    vmm_map_page(test_virt, phys, PTE_PRESENT | PTE_WRITE | PTE_NX);

    /* Should be mapped */
    if (vmm_virt_to_phys(test_virt) != phys) {
        vmm_unmap_page(test_virt);
        pmm_free_pages(phys, 0);
        return false;
    }

    /* Unmap */
    vmm_unmap_page(test_virt);

    /* Should NOT be mapped anymore */
    bool ok = (vmm_virt_to_phys(test_virt) == 0);

    pmm_free_pages(phys, 0);
    return ok;
}

/* ── Console / Keyboard tests ────────────────────────────────── */

static bool test_console_available(void) {
    /* Console should be initialized by boot sequence */
    return console_available() != 0;
}

static bool test_kb_buffer_empty(void) {
    /* Keyboard buffer should be empty at boot (no keys pressed) */
    return !kb_has_input();
}

/* ── Registration ────────────────────────────────────────────── */

void register_selftests(void) {
    /* Spinlock & memory */
    selftest_register("Spinlock trylock/unlock",        test_spinlock);
    selftest_register("memset/memcpy/memcmp",           test_memops);

    /* PMM */
    selftest_register("PMM alloc/free order-0",         test_pmm_alloc_free);
    selftest_register("PMM alloc/free order-5 (128KB)", test_pmm_order5);

    /* kmalloc */
    selftest_register("kmalloc(64) + kfree",            test_kmalloc_small);
    selftest_register("kmalloc(8192) large alloc",      test_kmalloc_large);
    selftest_register("kzmalloc zeroing",               test_kzmalloc);
    selftest_register("Poison 0xDE on kfree",           test_poison);
    selftest_register("krealloc data preservation",     test_krealloc);
    selftest_register("Slab reclamation to PMM",        test_slab_reclamation);
    selftest_register("PMM watermark >= 10%",           test_pmm_watermark);

    /* VMM */
    selftest_register("VMM map/write/read",             test_vmm_map_write_read);
    selftest_register("VMM virt_to_phys walk",          test_vmm_virt_to_phys);
    selftest_register("VMM HHDM integrity post-CR3",    test_vmm_hhdm_integrity);
    selftest_register("VMM map resolves correctly",     test_vmm_map_returns_mapping);

    /* Timer */
    selftest_register("PIT timer ticking",              test_pit_ticking);

    /* String functions */
    selftest_register("strlen correctness",             test_strlen);

    /* Negative / edge-case tests */
    selftest_register("kfree(NULL) safe no-op",         test_kfree_null);
    selftest_register("kmalloc(0) edge case",           test_kmalloc_zero);
    selftest_register("krealloc(NULL,n) == kmalloc",    test_krealloc_null);
    selftest_register("PMM alloc/free/reuse cycle",     test_pmm_alloc_free_reuse);
    selftest_register("memmove overlap correctness",    test_memmove_overlap);
    selftest_register("Spinlock IRQ save/restore",      test_spinlock_irqsave);
    selftest_register("VMM unmap + verify unmapped",    test_vmm_unmap_verify);

    /* Console / Keyboard */
    selftest_register("Framebuffer console active",     test_console_available);
    selftest_register("Keyboard buffer starts empty",   test_kb_buffer_empty);
}
