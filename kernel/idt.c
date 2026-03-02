/*
 * Anykernel OS v2.1 — Early IDT Implementation
 *
 * Sets up a minimal IDT to catch the 5 most critical x86_64 exceptions:
 *
 *   Vector | Name                | Error Code | Why it matters
 *   -------|---------------------|------------|---------------------------
 *   0      | #DE Divide Error    | No         | Division by zero
 *   6      | #UD Invalid Opcode  | No         | SSE/wrong instruction
 *   8      | #DF Double Fault    | Yes (0)    | Exception during exception
 *   13     | #GP General Protect | Yes        | Segment/privilege violation
 *   14     | #PF Page Fault      | Yes        | Bad memory access (CR2!)
 *
 * Each handler pushes a uniform interrupt frame, reads CR2 (for #PF),
 * and calls the C panic handler with full diagnostics.
 *
 * IDT Entry format (16 bytes in Long Mode):
 *   Bytes 0-1:  offset[15:0]
 *   Bytes 2-3:  segment selector (CS)
 *   Byte  4:    IST (0 = no IST, or 1-7)
 *   Byte  5:    type_attr (0x8E = present, DPL=0, 64-bit interrupt gate)
 *   Bytes 6-7:  offset[31:16]
 *   Bytes 8-11: offset[63:32]
 *   Bytes 12-15: reserved (0)
 */

#include "idt.h"
#include "kprintf.h"
#include "panic.h"
#include "gdt.h"
#include "string.h"
#include <stdint.h>

/* ── IDT structures ───────────────────────────────────────────── */

struct idt_entry {
    uint16_t offset_low;      /* offset bits 0..15 */
    uint16_t selector;        /* code segment selector */
    uint8_t  ist;             /* IST offset (0 = none) */
    uint8_t  type_attr;       /* type and attributes */
    uint16_t offset_mid;      /* offset bits 16..31 */
    uint32_t offset_high;     /* offset bits 32..63 */
    uint32_t reserved;
} __attribute__((packed));

struct idt_pointer {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

/* Interrupt frame pushed by our stubs */
struct interrupt_frame {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;
    uint64_t rbp, rdi, rsi, rdx, rcx, rbx, rax;
    uint64_t vector;          /* pushed by our stub */
    uint64_t error_code;      /* pushed by CPU or dummy 0 */
    uint64_t rip;             /* pushed by CPU */
    uint64_t cs;
    uint64_t rflags;
    uint64_t rsp;
    uint64_t ss;
};

/* ── IDT table (256 entries, but we only populate a few) ──────── */

static struct idt_entry idt[256];
static struct idt_pointer idtr;

/* ── Exception names ──────────────────────────────────────────── */

static const char *exception_name(uint64_t vector) {
    switch (vector) {
        case 0:  return "Divide Error (#DE)";
        case 6:  return "Invalid Opcode (#UD)";
        case 8:  return "Double Fault (#DF)";
        case 13: return "General Protection (#GP)";
        case 14: return "Page Fault (#PF)";
        default: return "Unknown Exception";
    }
}

/* ── C exception handler (called from assembly stubs) ─────────── */

void exception_handler_c(struct interrupt_frame *frame) {
    /* Read CR2 (faulting address) — only meaningful for #PF */
    uint64_t cr2;
    asm volatile("movq %%cr2, %0" : "=r"(cr2));

    kprintf("\n\n!!! CPU EXCEPTION !!!\n");
    kprintf("  Vector:     %lu — %s\n", frame->vector, exception_name(frame->vector));
    kprintf("  Error Code: 0x%lx\n", frame->error_code);
    kprintf("  RIP:        0x%016lx\n", frame->rip);
    kprintf("  CS:         0x%lx\n", frame->cs);
    kprintf("  RFLAGS:     0x%016lx\n", frame->rflags);
    kprintf("  RSP:        0x%016lx\n", frame->rsp);
    kprintf("  CR2:        0x%016lx\n", cr2);
    kprintf("\n  Registers:\n");
    kprintf("    RAX=%016lx  RBX=%016lx\n", frame->rax, frame->rbx);
    kprintf("    RCX=%016lx  RDX=%016lx\n", frame->rcx, frame->rdx);
    kprintf("    RSI=%016lx  RDI=%016lx\n", frame->rsi, frame->rdi);
    kprintf("    RBP=%016lx  R8 =%016lx\n", frame->rbp, frame->r8);
    kprintf("    R9 =%016lx  R10=%016lx\n", frame->r9, frame->r10);
    kprintf("    R11=%016lx  R12=%016lx\n", frame->r11, frame->r12);
    kprintf("    R13=%016lx  R14=%016lx\n", frame->r13, frame->r14);
    kprintf("    R15=%016lx\n", frame->r15);

    if (frame->vector == 14) {
        /* Decode Page Fault error code */
        kprintf("\n  Page Fault details:\n");
        kprintf("    %s\n", (frame->error_code & 1) ? "Protection violation" : "Page not present");
        kprintf("    %s access\n", (frame->error_code & 2) ? "Write" : "Read");
        kprintf("    %s mode\n", (frame->error_code & 4) ? "User" : "Kernel");
        if (frame->error_code & 8) kprintf("    Reserved bit set\n");
        if (frame->error_code & 16) kprintf("    Instruction fetch\n");
    }

    /* Freeze */
    asm volatile("cli");
    for (;;) {
        asm volatile("hlt");
    }
}

/* ── Assembly stubs ───────────────────────────────────────────── */

/*
 * We need tiny assembly stubs that:
 *   1. Push a dummy error code (0) if the CPU didn't push one
 *   2. Push the vector number
 *   3. Save all general-purpose registers
 *   4. Call exception_handler_c with pointer to the frame
 *
 * We define these as raw bytes using .byte/.quad in inline asm
 * because we can't write standalone .S files from here easily.
 */

/* Common handler body: save regs → call C → (never returns) */
#define ISR_STUB_NO_ERR(vec)                                        \
    asm volatile(                                                    \
        ".global isr_stub_" #vec "\n\t"                             \
        "isr_stub_" #vec ":\n\t"                                    \
        "pushq $0\n\t"              /* dummy error code */          \
        "pushq $" #vec "\n\t"       /* vector number */             \
        "jmp isr_common\n\t"                                        \
    )

#define ISR_STUB_ERR(vec)                                           \
    asm volatile(                                                    \
        ".global isr_stub_" #vec "\n\t"                             \
        "isr_stub_" #vec ":\n\t"                                    \
        /* CPU already pushed error code */                         \
        "pushq $" #vec "\n\t"       /* vector number */             \
        "jmp isr_common\n\t"                                        \
    )

/* Common ISR body */
__attribute__((used))
static void _isr_common_asm(void) {
    asm volatile(
        ".global isr_common\n\t"
        "isr_common:\n\t"
        /* Save all GPRs */
        "pushq %rax\n\t"
        "pushq %rbx\n\t"
        "pushq %rcx\n\t"
        "pushq %rdx\n\t"
        "pushq %rsi\n\t"
        "pushq %rdi\n\t"
        "pushq %rbp\n\t"
        "pushq %r8\n\t"
        "pushq %r9\n\t"
        "pushq %r10\n\t"
        "pushq %r11\n\t"
        "pushq %r12\n\t"
        "pushq %r13\n\t"
        "pushq %r14\n\t"
        "pushq %r15\n\t"
        /* Pass frame pointer (RSP points to struct interrupt_frame) */
        "movq %rsp, %rdi\n\t"
        "call exception_handler_c\n\t"
        /* Should never return, but just in case... */
        "cli\n\t"
        "hlt\n\t"
    );
}

/* Generate the stubs */
__attribute__((used))
static void _isr_stubs_gen(void) {
    ISR_STUB_NO_ERR(0);   /* #DE — no error code */
    ISR_STUB_NO_ERR(6);   /* #UD — no error code */
    ISR_STUB_ERR(8);      /* #DF — error code (always 0) */
    ISR_STUB_ERR(13);     /* #GP — error code */
    ISR_STUB_ERR(14);     /* #PF — error code */
}

/* External symbols for the stubs */
extern void isr_stub_0(void);
extern void isr_stub_6(void);
extern void isr_stub_8(void);
extern void isr_stub_13(void);
extern void isr_stub_14(void);

/* ── IDT setup ────────────────────────────────────────────────── */

static void idt_set_gate(int vector, void (*handler)(void), uint8_t ist) {
    uint64_t addr = (uint64_t)handler;

    idt[vector].offset_low  = addr & 0xFFFF;
    idt[vector].selector    = GDT_KERNEL_CODE;
    idt[vector].ist         = ist;
    idt[vector].type_attr   = 0x8E;   /* Present, DPL=0, 64-bit Interrupt Gate */
    idt[vector].offset_mid  = (addr >> 16) & 0xFFFF;
    idt[vector].offset_high = (addr >> 32) & 0xFFFFFFFF;
    idt[vector].reserved    = 0;
}

void idt_init(void) {
    /* Zero the entire IDT */
    memset(idt, 0, sizeof(idt));

    /* Install exception handlers */
    idt_set_gate(0,  isr_stub_0,  0);  /* #DE — Divide Error */
    idt_set_gate(6,  isr_stub_6,  0);  /* #UD — Invalid Opcode */
    idt_set_gate(8,  isr_stub_8,  1);  /* #DF — Double Fault (uses IST1!) */
    idt_set_gate(13, isr_stub_13, 0);  /* #GP — General Protection */
    idt_set_gate(14, isr_stub_14, 0);  /* #PF — Page Fault */

    /* Load the IDT */
    idtr.limit = sizeof(idt) - 1;
    idtr.base  = (uint64_t)&idt;

    asm volatile("lidt %0" : : "m"(idtr));
}
