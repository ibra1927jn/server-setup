# RESUMEN: alze (Game Engine / 3D Renderer)

**Stack:** C++ con CMake
**Última modificación:** Mar 24, 2026

## Descripción
Motor de juego / renderer 3D en C++ desde cero. Incluye sistema ECS (Entity-Component-System), física, renderer, IA, y una demo 3D completa.

## Estructura clave
```
alze/
├── src/
│   ├── main.cpp            # Entry point
│   ├── demo_3d.cpp         # Demo 3D completa (22k)
│   ├── benchmark.cpp       # Benchmarks
│   ├── ai/                 # Módulo de IA
│   ├── core/               # Core del engine
│   ├── ecs/                # Entity-Component-System
│   ├── game/               # Lógica de juego
│   ├── math/               # Matemáticas (vectores, matrices)
│   ├── physics/            # Simulación física
│   ├── renderer/           # Renderizado
│   └── scene/              # Gestión de escenas
├── build/                  # Artefactos de compilación (CMake)
└── README.md
```

## Build
```bash
mkdir -p build && cd build
cmake ..
make
```

## Notas
- Proyecto separado del OS (ver RESUMEN_alze-os.md)
- No tiene dependencias externas de npm/pip
- ECS actualizado Mar 24 — rama activa de desarrollo
