;; ──────────────────────────────────────────────────────────────────
;; Anykernel OS v2.1 — Interrupt Service Routine Stubs (NASM)
;;
;; Pure assembly ISR stubs — ZERO compiler dependency.
;; Each stub pushes a uniform interrupt frame and jumps to the
;; common handler, which saves all GPRs and calls the C handler.
;;
;; Why not inline asm?
;;   C compilers insert invisible prologues (push rbp, sub rsp).
;;   In an ISR, the stack layout MUST be exact or iretq will
;;   triple-fault. Assembly gives us 100% control.
;;
;; Frame layout when C handler is called (stack grows down):
;;
;;   [RSP+0x78]  SS           ← pushed by CPU
;;   [RSP+0x70]  RSP          ← pushed by CPU
;;   [RSP+0x68]  RFLAGS       ← pushed by CPU
;;   [RSP+0x60]  CS           ← pushed by CPU
;;   [RSP+0x58]  RIP          ← pushed by CPU
;;   [RSP+0x50]  Error Code   ← pushed by CPU (or dummy 0)
;;   [RSP+0x48]  Vector #     ← pushed by our stub
;;   [RSP+0x40]  RAX          ← pushed by isr_common
;;   [RSP+0x38]  RBX
;;   [RSP+0x30]  RCX
;;   [RSP+0x28]  RDX
;;   [RSP+0x20]  RSI
;;   [RSP+0x18]  RDI
;;   [RSP+0x10]  RBP
;;   [RSP+0x08]  R8..R15      ← pushed by isr_common
;;   [RSP+0x00]  R15 (top)    ← RSP points here = struct interrupt_frame*
;; ──────────────────────────────────────────────────────────────────

[BITS 64]
[DEFAULT REL]

;; ── External: C exception handler ───────────────────────────────
extern exception_handler_c

;; ── Macro: ISR stub WITHOUT error code (CPU doesn't push one) ───
%macro ISR_NOERRCODE 1
global isr_stub_%1
isr_stub_%1:
    push    qword 0          ; dummy error code
    push    qword %1         ; vector number
    jmp     isr_common
%endmacro

;; ── Macro: ISR stub WITH error code (CPU already pushed it) ─────
%macro ISR_ERRCODE 1
global isr_stub_%1
isr_stub_%1:
    ; error code is already on the stack from CPU
    push    qword %1         ; vector number
    jmp     isr_common
%endmacro

;; ── Generate the 5 critical stubs ───────────────────────────────
ISR_NOERRCODE 0              ; #DE — Divide Error
ISR_NOERRCODE 6              ; #UD — Invalid Opcode
ISR_ERRCODE   8              ; #DF — Double Fault (error = always 0)
ISR_ERRCODE   13             ; #GP — General Protection Fault
ISR_ERRCODE   14             ; #PF — Page Fault

;; ── Common handler: save state → call C → halt ──────────────────
global isr_common
isr_common:
    ;; Save all general-purpose registers
    push    rax
    push    rbx
    push    rcx
    push    rdx
    push    rsi
    push    rdi
    push    rbp
    push    r8
    push    r9
    push    r10
    push    r11
    push    r12
    push    r13
    push    r14
    push    r15

    ;; First argument (RDI) = pointer to interrupt frame on stack
    mov     rdi, rsp

    ;; Call C handler (never returns for exceptions)
    call    exception_handler_c

    ;; Safety net — should never reach here
    cli
    hlt
    jmp     $
