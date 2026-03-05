/*
 * Anykernel OS — Virtual File System Implementation
 *
 * Global device table + per-system fd table (TODO: per-task fds).
 * Dispatches read/write/ioctl through file_ops vtable.
 */

#include "vfs.h"
#include "string.h"
#include "kprintf.h"
#include "log.h"
#include "compiler.h"
#include "spinlock.h"
#include "bitmap_alloc.h"
#include "errno.h"

/* ── Device registry ─────────────────────────────────────────── */

static struct vnode devices[VFS_MAX_DEVICES];
static uint32_t    device_count = 0;
static spinlock_t  vfs_lock = SPINLOCK_INIT;

/* ── Global fd table (future: per-task) ──────────────────────── */

static struct file fd_table[VFS_MAX_FDS];
static struct id_pool fd_pool;  /* O(1) fd allocation via bitmap */

/* ── Init ────────────────────────────────────────────────────── */

void vfs_init(void) {
    memset(devices, 0, sizeof(devices));
    memset(fd_table, 0, sizeof(fd_table));
    device_count = 0;
    id_pool_init(&fd_pool);  /* All fd slots free */
    LOG_OK("VFS initialized (%d fd slots, %d device slots)",
           VFS_MAX_FDS, VFS_MAX_DEVICES);
}

/* ── Register a device ───────────────────────────────────────── */

int vfs_register_device(const char *name, enum vnode_type type,
                        struct file_ops *ops, void *private_data) {
    uint64_t irq_flags;
    spin_lock_irqsave(&vfs_lock, &irq_flags);

    if (device_count >= VFS_MAX_DEVICES) {
        spin_unlock_irqrestore(&vfs_lock, irq_flags);
        return -ENOSPC;
    }

    struct vnode *vn = &devices[device_count++];
    strncpy(vn->name, name, VN_NAME_MAX - 1);
    vn->name[VN_NAME_MAX - 1] = '\0';
    vn->type = type;
    vn->ops = ops;
    vn->private_data = private_data;
    vn->refcount = 0;

    spin_unlock_irqrestore(&vfs_lock, irq_flags);

    LOG_OK("VFS: registered '%s' (type=%d)", name, type);
    return 0;
}

/* ── Lookup device by name ───────────────────────────────────── */

struct vnode *vfs_lookup(const char *name) {
    for (uint32_t i = 0; i < device_count; i++) {
        if (strcmp(devices[i].name, name) == 0) {
            return &devices[i];
        }
    }
    return 0;
}

/* ── Open ────────────────────────────────────────────────────── */

int vfs_open(const char *path, int flags) {
    struct vnode *vn = vfs_lookup(path);
    if (!vn) return -ENOENT;

    uint64_t irq_flags;
    spin_lock_irqsave(&vfs_lock, &irq_flags);

    /* O(1) fd allocation via bitmap BSF */
    int fd = id_alloc(&fd_pool);
    if (fd < 0 || fd >= VFS_MAX_FDS) {
        spin_unlock_irqrestore(&vfs_lock, irq_flags);
        return -EMFILE;
    }

    fd_table[fd].vnode = vn;
    fd_table[fd].flags = flags;
    fd_table[fd].offset = 0;
    fd_table[fd].in_use = true;
    __sync_fetch_and_add(&vn->refcount, 1);  /* Atomic increment */

    spin_unlock_irqrestore(&vfs_lock, irq_flags);

    /* Call device open if provided (outside lock — may sleep) */
    if (vn->ops && vn->ops->open) {
        int ret = vn->ops->open(vn, flags);
        if (ret < 0) {
            spin_lock_irqsave(&vfs_lock, &irq_flags);
            fd_table[fd].in_use = false;
            __sync_fetch_and_sub(&vn->refcount, 1);
            id_free(&fd_pool, fd);
            spin_unlock_irqrestore(&vfs_lock, irq_flags);
            return -EIO;
        }
    }
    return fd;
}

/* ── Close ───────────────────────────────────────────────────── */

int vfs_close(int fd) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -EBADF;

    uint64_t irq_flags;
    spin_lock_irqsave(&vfs_lock, &irq_flags);

    if (!fd_table[fd].in_use) {
        spin_unlock_irqrestore(&vfs_lock, irq_flags);
        return -EBADF;
    }

    struct vnode *vn = fd_table[fd].vnode;
    fd_table[fd].in_use = false;
    fd_table[fd].vnode = 0;
    __sync_fetch_and_sub(&vn->refcount, 1);  /* Atomic decrement */
    id_free(&fd_pool, fd);

    spin_unlock_irqrestore(&vfs_lock, irq_flags);

    /* Call device close outside lock */
    if (vn->ops && vn->ops->close) {
        vn->ops->close(vn);
    }
    return 0;
}

/* ── Read ────────────────────────────────────────────────────── */

int64_t vfs_read(int fd, void *buf, uint64_t count) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -EBADF;
    if (!fd_table[fd].in_use) return -EBADF;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->read) return -ENOTSUP;

    return vn->ops->read(vn, buf, count);
}

/* ── Write ───────────────────────────────────────────────────── */

int64_t vfs_write(int fd, const void *buf, uint64_t count) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -EBADF;
    if (!fd_table[fd].in_use) return -EBADF;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->write) return -ENOTSUP;

    return vn->ops->write(vn, buf, count);
}

/* ── Ioctl ───────────────────────────────────────────────────── */

int vfs_ioctl(int fd, uint32_t cmd, void *arg) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -EBADF;
    if (!fd_table[fd].in_use) return -EBADF;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->ioctl) return -ENOTSUP;

    return vn->ops->ioctl(vn, cmd, arg);
}
