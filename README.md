# Anykernel OS

A minimal x86_64 kernel built from scratch — UEFI boot via Limine, higher-half design, freestanding C with clang.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Anykernel OS v0.3.8                │
├──────────┬──────────┬──────────┬─────────────────────┤
│ Console  │ Keyboard │  CPUID   │  kprintf dual-out   │
│ 1280x800 │  PS/2    │ vendor,  │  UART + framebuffer │
│ 8x16 fnt │ US-QWER  │ features │  ANSI colors        │
├──────────┴──────────┴──────────┴─────────────────────┤
│   kmalloc    │     VMM        │   PIC/PIT Timer      │
│  Slab alloc  │  4-level page  │  8259A + 100 Hz      │
│  krealloc    │  tables, NX,   │  IRQ dispatch        │
│  poisoning   │  huge pages    │  sti enabled         │
├──────────────┴───────┬────────┴──────────────────────┤
│                     PMM                              │
│          Buddy allocator (4KB-4MB)                   │
│        IRQ-safe spinlocks, watermarks                │
├──────────────────────────────────────────────────────┤
│  GDT/TSS │ IDT │ UART │ SSP │ kprintf │ strings     │
├──────────────────────────────────────────────────────┤
│            Limine Bootloader (UEFI/BIOS)             │
└──────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Inside MSYS2 MinGW64 shell
make iso         # Build kernel + ISO
make run         # Build + launch QEMU
make test        # Build + run QEMU + check serial for failures
make test-userspace  # Run PMM unit tests natively
make clean
```

## Requirements

- **Toolchain**: clang (cross `x86_64-unknown-none`), nasm, ld.lld
- **Emulator**: QEMU with `qemu-system-x86_64`
- **Boot**: Limine 8.x (included in `limine/`)
- **Build**: GNU Make, xorriso

## Memory Layout

| Virtual Range | Maps To | Size | Notes |
|---|---|---|---|
| `0xFFFFFFFF80000000` | Kernel | ~64 KB | .text=RX, .rodata=RO, .data/.bss=RW+NX |
| `0xFFFF800000000000` | HHDM | ~4 GB | 2MB huge pages, usable/kernel/FB regions only |
| `0xFFFFFF0000101000` | RSP0 stack | 16 KB | TSS privilege transition stack + guard page |
| `0xFFFFFF0000201000` | IST1 stack | 8 KB | Double Fault (#DF) stack + guard page |
| Boot stack guard | Unmapped | 4 KB | #PF on stack overflow |

## Boot Sequence (15 steps)

1. UART serial (115200 baud)
2. Stack canary (RDTSC)
3. CPUID detection (vendor, features, brand)
4. Limine protocol check
5. GDT + TSS (RSP0 + IST1)
6. IDT (exceptions + IRQs)
7. PIC remap + PIT 100 Hz + `sti`
8. HHDM offset
9. Memory map parse
10. PMM init (buddy allocator)
11. VMM init (PML4, kernel map, HHDM, CR3 switch, perms, guard pages)
12. Framebuffer console (1280x800, 8x16 font, ANSI colors)
13. PS/2 keyboard (scancode→ASCII, ring buffer)
14. Self-tests (26 registered)
15. Boot report + banner

## Self-Tests

26 automated kernel tests + 29 userspace PMM tests = **55 total tests**:

| # | Test | Subsystem |
|---|------|-----------|
| 1-2 | Spinlock, memops | Core |
| 3-4 | PMM alloc/free order-0, order-5 | PMM |
| 5-11 | kmalloc, kzmalloc, poison, krealloc, slab reclamation, watermark | kmalloc |
| 12-15 | VMM map/write/read, virt_to_phys, HHDM integrity, map resolves | VMM |
| 16 | PIT timer ticking | Timer |
| 17 | strlen/strncmp/strncpy | String |
| 18-24 | kfree(NULL), kmalloc(0), krealloc(NULL), PMM reuse, memmove overlap, spinlock irqsave, VMM unmap | Negative/edge |
| 25-26 | Framebuffer console active, keyboard buffer empty | I/O |

## Version History

| Version | Changes |
|---------|---------|
| v0.1.0 | Boot + UART + GDT + IDT |
| v0.2.0 | Buddy allocator PMM (29 userspace tests) |
| v0.2.1 | Slab allocator (kmalloc/kfree) |
| v0.2.2 | IRQ-safe spinlocks + memory poisoning |
| v0.2.3 | krealloc, slab reclamation, watermarks |
| v0.2.4 | Selftest framework, `make test` |
| v0.3.0 | VMM — CR3 switch, own page tables |
| v0.3.1 | Per-section perms, stack guard, VMM diagnostics |
| v0.3.2 | PIC 8259A + PIT timer + `sti` + tests.c refactor |
| v0.3.3 | io.h, string functions, boot numbering, README |
| v0.3.4 | VMM collision detection, HHDM from memmap, TSS RSP0 |
| v0.3.5 | IST1 VMM stack (8KB+guard), tss_set_ist1, 7 negative tests |
| v0.3.6 | Framebuffer console (8x16 font), PS/2 keyboard, HHDM optimized |
| v0.3.7 | Dual kprintf output, ANSI colors, CPUID, improved panic, KB echo |
| v0.3.8 | Boot numbering fix, uptime display, console/KB tests (26 total) |

## Project Structure

```
kernel/
  main.c       — Boot sequence (15 steps) + init
  pmm.c/h      — Physical memory manager (buddy)
  kmalloc.c/h  — Slab allocator + krealloc
  vmm.c/h      — Virtual memory manager (x86_64 paging)
  pic.c/h      — PIC 8259A + PIT timer
  idt.c/h      — IDT + exception/IRQ handlers
  gdt.c/h      — GDT + TSS (RSP0, IST1)
  selftest.c/h — Test registration framework
  tests.c      — All 26 self-test functions
  kprintf.c/h  — Kernel printf (dual: serial + framebuffer)
  console.c/h  — Framebuffer text console (8x16, ANSI colors)
  kb.c/h       — PS/2 keyboard driver (scancode→ASCII)
  cpuid.c/h    — CPU identification (vendor, features)
  string.c/h   — memset, memcpy, memmove, strlen, strncmp...
  io.h         — Port I/O primitives (outb/inb)
  memory.h     — Page constants, PHYS2VIRT
  spinlock.h   — IRQ-safe spinlocks
  uart.c/h     — Serial UART driver
  panic.c/h    — KASSERT + kernel_panic (with CR2 dump)
  ssp.c        — Stack smashing protection
  log.h        — LOG_OK/INFO/WARN/ERROR/FAIL macros
  interrupts.asm — ISR/IRQ stubs (NASM)
tests/
  test_pmm.c   — 29 userspace PMM tests
linker.ld      — Higher-half linker script with section symbols
limine.conf    — Bootloader config
Makefile       — Build system
```
