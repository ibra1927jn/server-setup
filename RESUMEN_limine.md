# RESUMEN: limine

**Tipo:** Dependencia binaria (NO es un proyecto propio)
**Contenido:** Binarios del bootloader Limine

## Descripción
Carpeta con los binarios precompilados del bootloader **Limine** usado por el proyecto `alze os`. No es código propio — es una dependencia externa.

## Contenido
```
limine/
├── BOOTX64.EFI             # EFI para x86_64
├── BOOTIA32.EFI            # EFI para x86
├── BOOTAA64.EFI            # EFI para ARM64
├── BOOTRISCV64.EFI         # EFI para RISC-V
├── BOOTLOONGARCH64.EFI     # EFI para LoongArch
├── limine-bios.sys         # BIOS stage 2
├── limine-bios-cd.bin      # ISO BIOS
├── limine-bios-pxe.bin     # PXE BIOS
├── limine-uefi-cd.bin      # ISO UEFI
├── limine.c / limine.h     # Librería de instalación
└── limine.exe              # Instalador Windows
```

## Notas
- Versión fija en git (último commit Mar 1)
- Usada por `alze os` como bootloader
- No tocar — es una dependencia, no código fuente propio
