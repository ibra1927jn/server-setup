# RESUMEN: alze os (Kernel / Sistema Operativo)

**Stack:** C / Assembly, Makefile, QEMU, Limine bootloader
**Última modificación:** Mar 26, 2026

## Descripción
Kernel de sistema operativo propio escrito desde cero. Usa el bootloader Limine para arrancar. Se ejecuta en QEMU para desarrollo. Tiene userland y tests.

## Estructura clave
```
alze os/
├── kernel/                 # Código del kernel
├── userland/               # Programas de usuario
├── user/                   # Utilidades de usuario
├── tests/                  # Tests del kernel
├── limine/                 # Bootloader Limine
├── limine.conf             # Configuración de arranque
├── linker.ld               # Script del linker
├── Makefile                # Build principal (9k)
├── build.sh                # Script de compilación
├── run.sh                  # Lanzar en QEMU (4k)
└── build/                  # Artefactos compilados
```

## Comandos clave
```bash
make                        # Compilar kernel
./run.sh                    # Ejecutar en QEMU
```

## Docs
- `README.md` — descripción del proyecto
- `ALZE.md` — especificaciones del OS

## Estado
- Git activo, último commit Mar 22
- Build artifacts presentes en `build/`
- `qemu.log` — log de ejecución reciente
