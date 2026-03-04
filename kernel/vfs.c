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
        return -1;
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
    if (!vn) return -1;

    /* O(1) fd allocation via bitmap BSF */
    int fd = id_alloc(&fd_pool);
    if (fd < 0 || fd >= VFS_MAX_FDS) return -1;

    fd_table[fd].vnode = vn;
    fd_table[fd].flags = flags;
    fd_table[fd].offset = 0;
    fd_table[fd].in_use = true;
    vn->refcount++;

    /* Call device open if provided */
    if (vn->ops && vn->ops->open) {
        int ret = vn->ops->open(vn, flags);
        if (ret < 0) {
            fd_table[fd].in_use = false;
            vn->refcount--;
            id_free(&fd_pool, fd);
            return -1;
        }
    }
    return fd;
}

/* ── Close ───────────────────────────────────────────────────── */

int vfs_close(int fd) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -1;
    if (!fd_table[fd].in_use) return -1;

    struct vnode *vn = fd_table[fd].vnode;
    if (vn->ops && vn->ops->close) {
        vn->ops->close(vn);
    }

    vn->refcount--;
    fd_table[fd].in_use = false;
    fd_table[fd].vnode = 0;
    id_free(&fd_pool, fd);  /* O(1) return fd to bitmap */
    return 0;
}

/* ── Read ────────────────────────────────────────────────────── */

int64_t vfs_read(int fd, void *buf, uint64_t count) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -1;
    if (!fd_table[fd].in_use) return -1;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->read) return -1;

    return vn->ops->read(vn, buf, count);
}

/* ── Write ───────────────────────────────────────────────────── */

int64_t vfs_write(int fd, const void *buf, uint64_t count) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -1;
    if (!fd_table[fd].in_use) return -1;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->write) return -1;

    return vn->ops->write(vn, buf, count);
}

/* ── Ioctl ───────────────────────────────────────────────────── */

int vfs_ioctl(int fd, uint32_t cmd, void *arg) {
    if (fd < 0 || fd >= VFS_MAX_FDS) return -1;
    if (!fd_table[fd].in_use) return -1;

    struct vnode *vn = fd_table[fd].vnode;
    if (!vn->ops || !vn->ops->ioctl) return -1;

    return vn->ops->ioctl(vn, cmd, arg);
}
