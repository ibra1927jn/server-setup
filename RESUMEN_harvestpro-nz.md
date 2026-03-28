# RESUMEN: harvestpro-nz

**Stack:** React 19 + TypeScript + Vite + Supabase + Tailwind CSS
**Versión:** 9.9.0
**Última modificación:** Mar 24, 2026

## Descripción
Aplicación PWA de gestión de fuerza laboral / nómina para Nueva Zelanda. Incluye escaneo QR para asistencia, aprobación de nómina, y panel de administrador. También tiene build para Android vía Capacitor.

## Stack completo
| Capa | Tecnología |
|------|-----------|
| UI | React 19, Tailwind CSS, Lucide |
| Estado | Zustand + TanStack Query v5 |
| Backend | Supabase (auth + DB) |
| Offline | Dexie (IndexedDB) |
| Mobile | Capacitor (Android) |
| Routing | React Router v7 |
| Validación | Zod v4 |
| Tests | Vitest + Playwright |
| Docs | Storybook |
| Analytics | PostHog + Sentry |

## Estructura src/
```
src/
├── components/     # Componentes UI
├── config/         # Configuración
├── constants/      # Constantes
├── context/        # React context
├── hooks/          # Custom hooks
├── i18n/           # Internacionalización
├── integration/    # Integraciones externas
├── pages/          # Páginas de la app
├── repositories/   # Capa de datos
├── schemas/        # Schemas Zod
├── services/       # Lógica de negocio
├── stores/         # Zustand stores
├── types/          # TypeScript types
└── utils/          # Utilidades
```

## Comandos
```bash
npm run dev           # Desarrollo
npm run build         # Build producción
npm run test          # Tests unitarios
npm run test:e2e      # Tests Playwright
npm run storybook     # Storybook
```

## Variables de entorno
- `.env.example` presente → copiar a `.env`
- Necesita: Supabase URL + anon key, Sentry DSN, PostHog key

## Docs
- `docs/ARCHITECTURE.md` — arquitectura
- `docs/DEPLOYMENT.md` — despliegue
- `docs/API_REFERENCE.md` — referencia API
- `docs/MANUAL_OPERACIONES.md` — manual operativo
- `docs/legal/` — ToS, Privacy Policy, DPA
