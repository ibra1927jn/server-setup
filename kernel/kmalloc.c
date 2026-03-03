/*
 * Anykernel OS v2.1 — Kernel Heap Allocator Implementation
 *
 * Slab allocator with 8 size classes:
 *
 *   Class 0: 16B   (256 slots per 4KB page)
 *   Class 1: 32B   (128 slots)
 *   Class 2: 64B   (64 slots)
 *   Class 3: 128B  (32 slots)
 *   Class 4: 256B  (16 slots)
 *   Class 5: 512B  (8 slots)
 *   Class 6: 1024B (4 slots)
 *   Class 7: 2048B (2 slots)
 *
 * Each slab page layout:
 *   [slab_header (32B)] [slot0] [slot1] [slot2] ...
 *
 * Free slots use an intrusive linked list: the first 8 bytes
 * of each free slot point to the next free slot.
 *
 * For allocations > 2048B: allocate full pages from PMM directly.
 * The size is stored in the first 8 bytes of the page (hidden header).
 */

#include "kmalloc.h"
#include "pmm.h"
#include "memory.h"
#include "string.h"
#include "spinlock.h"
#include "kprintf.h"
#include "log.h"
#include "panic.h"

/* ── Constants ────────────────────────────────────────────────── */

#define SLAB_NUM_CLASSES  8
#define SLAB_MIN_SIZE     16
#define SLAB_MAX_SIZE     2048

/* Poison pattern: written to freed memory to detect use-after-free.
 * If you see 0xDEADBEEF in a register dump, you freed too early. */
#define POISON_PATTERN    0xDEADBEEFDEADBEEFULL
#define POISON_BYTE       0xDE

/* ── Slab header (at the start of each slab page) ─────────────── */

struct slab_header {
    struct slab_header *next;     /* Next slab page in this class */
    void               *free;    /* Head of free slot list */
    uint32_t           obj_size; /* Size of each slot */
    uint32_t           used;     /* Number of allocated slots */
    uint32_t           total;    /* Total slots in this slab */
    uint32_t           _pad;     /* Align to 32 bytes */
};

_Static_assert(sizeof(struct slab_header) == 32, "slab_header must be 32B");

/* ── Per-class state ──────────────────────────────────────────── */

struct slab_class {
    uint32_t            obj_size;    /* Slot size for this class */
    struct slab_header *slabs;       /* Linked list of slab pages */
    uint64_t            total_allocs;
    uint64_t            total_frees;
};

static struct slab_class classes[SLAB_NUM_CLASSES];
static spinlock_t heap_lock = SPINLOCK_INIT;
static uint64_t large_allocs = 0;
static uint64_t large_frees  = 0;

/* ── Helpers ──────────────────────────────────────────────────── */

/* Find the size class index (log2 of rounded-up-to-power-of-2) */
static int size_to_class(uint64_t size) {
    if (size <= 16)   return 0;
    if (size <= 32)   return 1;
    if (size <= 64)   return 2;
    if (size <= 128)  return 3;
    if (size <= 256)  return 4;
    if (size <= 512)  return 5;
    if (size <= 1024) return 6;
    if (size <= 2048) return 7;
    return -1;  /* Too large for slab → page alloc */
}

/* Convert physical address to virtual via HHDM */
static inline void *phys_to_virt(uint64_t phys) {
    extern uint64_t hhdm_offset;
    return (void *)(phys + hhdm_offset);
}

static inline uint64_t virt_to_phys(void *virt) {
    extern uint64_t hhdm_offset;
    return (uint64_t)virt - hhdm_offset;
}

/* Create a new slab page for a given class */
static struct slab_header *slab_new(struct slab_class *cls) {
    /* Allocate a zeroed page from PMM */
    uint64_t phys = pmm_alloc_pages_zero(0);  /* Order 0 = 1 page */
    if (phys == 0) return NULL;

    struct slab_header *slab = (struct slab_header *)phys_to_virt(phys);

    /* Initialize header */
    slab->next = NULL;
    slab->obj_size = cls->obj_size;
    slab->used = 0;

    /* Calculate slots: skip the header at the beginning */
    uint64_t data_start = (uint64_t)(slab + 1);  /* After header */
    uint64_t page_end   = (uint64_t)slab + PAGE_SIZE;
    slab->total = (uint32_t)((page_end - data_start) / cls->obj_size);

    /* Build free list: chain all slots together */
    slab->free = NULL;
    for (uint32_t i = 0; i < slab->total; i++) {
        void *slot = (void *)(data_start + (uint64_t)i * cls->obj_size);
        *(void **)slot = slab->free;  /* Point to previous head */
        slab->free = slot;
    }

    return slab;
}

/* Find which slab owns a given pointer */
static struct slab_header *slab_from_ptr(void *ptr) {
    /* Slab header is at the page-aligned base of the pointer */
    return (struct slab_header *)((uint64_t)ptr & ~(PAGE_SIZE - 1));
}

/* ── Init ─────────────────────────────────────────────────────── */

/* Called implicitly by first kmalloc — lazy init */
static int initialized = 0;

static void kmalloc_init(void) {
    uint32_t size = SLAB_MIN_SIZE;
    for (int i = 0; i < SLAB_NUM_CLASSES; i++) {
        classes[i].obj_size = size;
        classes[i].slabs = NULL;
        classes[i].total_allocs = 0;
        classes[i].total_frees = 0;
        size *= 2;
    }
    initialized = 1;
}

/* ── kmalloc ──────────────────────────────────────────────────── */

void *kmalloc(uint64_t size) {
    if (size == 0) return NULL;

    uint64_t irq_flags;
    spin_lock_irqsave(&heap_lock, &irq_flags);

    if (!initialized) kmalloc_init();

    int cls_idx = size_to_class(size);

    if (cls_idx < 0) {
        /* Large allocation: use full pages from PMM */
        uint32_t order = 0;
        uint64_t needed = size + 8;  /* +8 for size header */
        while ((1UL << order) * PAGE_SIZE < needed && order <= PMM_MAX_ORDER) {
            order++;
        }

        uint64_t phys = pmm_alloc_pages_zero(order);
        if (phys == 0) {
            spin_unlock_irqrestore(&heap_lock, irq_flags);
            return NULL;
        }

        void *virt = phys_to_virt(phys);
        /* Store order in first 8 bytes */
        *(uint64_t *)virt = order;
        large_allocs++;
        spin_unlock_irqrestore(&heap_lock, irq_flags);
        return (void *)((uint64_t)virt + 8);
    }

    struct slab_class *cls = &classes[cls_idx];

    /* Find a slab with free slots */
    struct slab_header *slab = cls->slabs;
    while (slab && slab->free == NULL) {
        slab = slab->next;
    }

    /* No slab available — create a new one */
    if (slab == NULL) {
        slab = slab_new(cls);
        if (slab == NULL) {
            spin_unlock_irqrestore(&heap_lock, irq_flags);
            return NULL;
        }
        /* Prepend to class list */
        slab->next = cls->slabs;
        cls->slabs = slab;
    }

    /* Pop from free list */
    void *slot = slab->free;
    slab->free = *(void **)slot;
    slab->used++;
    cls->total_allocs++;

    spin_unlock_irqrestore(&heap_lock, irq_flags);
    return slot;
}

/* ── kfree ────────────────────────────────────────────────────── */

void kfree(void *ptr) {
    if (ptr == NULL) return;

    uint64_t irq_flags;
    spin_lock_irqsave(&heap_lock, &irq_flags);

    /* Check if this is a large allocation (page-aligned - 8 bytes) */
    uint64_t addr = (uint64_t)ptr;

    /* If ptr-8 is page-aligned, it's a large alloc */
    if (((addr - 8) & (PAGE_SIZE - 1)) == 0) {
        void *base = (void *)(addr - 8);
        uint32_t order = (uint32_t)(*(uint64_t *)base);
        /* Poison the entire allocation before freeing */
        memset(base, POISON_BYTE, (1UL << order) * PAGE_SIZE);
        uint64_t phys = virt_to_phys(base);
        pmm_free_pages(phys, order);
        large_frees++;
        spin_unlock_irqrestore(&heap_lock, irq_flags);
        return;
    }

    /* Slab allocation — find the slab header */
    struct slab_header *slab = slab_from_ptr(ptr);
    KASSERT(slab->used > 0);

    /* Poison the slot (except first 8 bytes — used for free list link) */
    if (slab->obj_size > 8) {
        memset((uint8_t *)ptr + 8, POISON_BYTE, slab->obj_size - 8);
    }

    /* Push back onto free list */
    *(void **)ptr = slab->free;
    slab->free = ptr;
    slab->used--;

    /* Find the class (by obj_size) and update stats */
    int cls_idx = size_to_class(slab->obj_size);
    if (cls_idx >= 0) {
        classes[cls_idx].total_frees++;
    }

    spin_unlock_irqrestore(&heap_lock, irq_flags);
}

/* ── kzmalloc ─────────────────────────────────────────────────── */

void *kzmalloc(uint64_t size) {
    void *ptr = kmalloc(size);
    if (ptr) {
        memset(ptr, 0, size);
    }
    return ptr;
}

/* ── Diagnostics ──────────────────────────────────────────────── */

void kmalloc_dump_stats(void) {
    LOG_INFO("Kernel Heap Stats:");
    for (int i = 0; i < SLAB_NUM_CLASSES; i++) {
        if (classes[i].total_allocs > 0) {
            uint32_t in_use = (uint32_t)(classes[i].total_allocs - classes[i].total_frees);

            /* Count slabs */
            uint32_t slab_count = 0;
            struct slab_header *s = classes[i].slabs;
            while (s) { slab_count++; s = s->next; }

            kprintf("  [%4u B] %u active, %lu allocs, %lu frees, %u slabs\n",
                    classes[i].obj_size, in_use,
                    classes[i].total_allocs, classes[i].total_frees,
                    slab_count);
        }
    }
    if (large_allocs > 0) {
        kprintf("  [Large ] %lu allocs, %lu frees\n", large_allocs, large_frees);
    }
}
