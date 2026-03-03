# Anykernel OS

A minimal x86_64 kernel built from scratch — UEFI boot via Limine, higher-half design, freestanding C with clang.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                 Anykernel OS                     │
├──────────────┬───────────────┬───────────────────┤
│   kmalloc    │     VMM       │   PIC/PIT Timer   │
│  Slab alloc  │  4-level page │  8259A + 100 Hz   │
│  krealloc    │  tables, NX,  │  IRQ dispatch     │
│  poisoning   │  huge pages   │  sti enabled      │
├──────────────┴───────┬───────┴───────────────────┤
│                     PMM                          │
│          Buddy allocator (4KB-4MB)               │
│        IRQ-safe spinlocks, watermarks            │
├──────────────────────────────────────────────────┤
│  GDT/TSS │ IDT │ UART │ SSP │ kprintf │ strings │
├──────────────────────────────────────────────────┤
│            Limine Bootloader (UEFI)              │
└──────────────────────────────────────────────────┘
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
| `0xFFFFFFFF80000000` | Kernel | ~56 KB | .text=RX, .rodata=RO, .data/.bss=RW+NX |
| `0xFFFF800000000000` | HHDM | 256 MB | 2MB huge pages, all physical RAM |
| Stack guard | Unmapped | 4 KB | #PF on stack overflow |

## Boot Sequence

1. UART serial (115200 baud)
2. Stack canary (RDTSC)
3. Limine protocol check
4. GDT + TSS (RSP0 + IST1)
5. IDT (exceptions + IRQs)
6. PIC remap + PIT 100 Hz + `sti`
7. HHDM offset
8. Memory map parse
9. PMM init (buddy allocator)
10. VMM init (PML4, kernel map, HHDM huge pages, CR3 switch, per-section perms, stack guard)
11. Self-tests (16 registered)
12. Boot report + banner

## Self-Tests

16 automated tests run every boot:

| # | Test | Subsystem |
|---|------|-----------|
| 1-2 | Spinlock, memops | Core |
| 3-4 | PMM alloc/free order-0, order-5 | PMM |
| 5-10 | kmalloc, kzmalloc, poison, krealloc, slab reclamation, watermark | kmalloc |
| 11-15 | VMM map/write/read, virt_to_phys, HHDM integrity, map resolves | VMM |
| 16 | PIT timer ticking | Timer |

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

## Project Structure

```
kernel/
  main.c       — Boot sequence + init
  pmm.c/h      — Physical memory manager (buddy)
  kmalloc.c/h  — Slab allocator + krealloc
  vmm.c/h      — Virtual memory manager (x86_64 paging)
  pic.c/h      — PIC 8259A + PIT timer
  idt.c/h      — IDT + exception/IRQ handlers
  gdt.c/h      — GDT + TSS
  selftest.c/h — Test registration framework
  tests.c      — All 16 self-test functions
  kprintf.c/h  — Kernel printf (serial output)
  string.c/h   — memset, memcpy, strlen, strncmp...
  io.h         — Port I/O primitives (outb/inb)
  memory.h     — Page constants, PHYS2VIRT
  spinlock.h   — IRQ-safe spinlocks
  uart.c/h     — Serial UART driver
  panic.c/h    — KASSERT + kernel_panic
  ssp.c        — Stack smashing protection
  log.h        — LOG_OK/INFO/WARN/ERROR/FAIL macros
  interrupts.asm — ISR/IRQ stubs (NASM)
tests/
  test_pmm.c   — 29 userspace PMM tests
linker.ld      — Higher-half linker script with section symbols
limine.conf    — Bootloader config
Makefile       — Build system
```
