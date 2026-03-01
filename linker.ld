/* Linker script for Anykernel OS v2.1 — x86_64 Higher Half */

ENTRY(_start)

PHDRS {
    requests PT_LOAD FLAGS((1 << 0) | (1 << 1) | (1 << 2)); /* RWX */
    text     PT_LOAD FLAGS((1 << 0) | (1 << 2));             /* R-X */
    rodata   PT_LOAD FLAGS((1 << 0));                        /* R-- */
    data     PT_LOAD FLAGS((1 << 0) | (1 << 1));             /* RW- */
}

SECTIONS {
    /* Higher Half base address */
    . = 0xffffffff80000000;

    /* Limine request markers — must be in their own section */
    .limine_requests : {
        KEEP(*(.limine_requests_start))
        KEEP(*(.limine_requests))
        KEEP(*(.limine_requests_end))
    } :requests

    . = ALIGN(4096);
    .text : {
        *(.text .text.*)
    } :text

    . = ALIGN(4096);
    .rodata : {
        *(.rodata .rodata.*)
    } :rodata

    . = ALIGN(4096);
    .data : {
        *(.data .data.*)
    } :data

    . = ALIGN(4096);
    .bss : {
        *(.bss .bss.*)
        *(COMMON)
    } :data

    /DISCARD/ : {
        *(.eh_frame*)
        *(.note .note.*)
        *(.comment)
    }
}
