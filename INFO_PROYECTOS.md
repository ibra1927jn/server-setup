# INFO_PROYECTOS — Desktop Projects Overview
> Generado: 2026-03-27 | Proyectos analizados: 7 | Excluidos: navegador, limine

---

## Crypto-Trading-Bot4

- **Stack:** Python 3.13 · FastAPI · CCXT · Pandas / Pandas-TA · WebSockets · python-telegram-bot

- **Dependencias clave (requirements.txt):**
  ```
  uvicorn>=0.30.0
  fastapi>=0.110.0
  ccxt>=4.2.0
  websockets>=12.0
  python-dotenv>=1.0.1
  aiosqlite>=0.20.0
  pandas>=2.2.0
  pandas-ta>=0.3.14b0
  pytest>=8.0.0
  pytest-asyncio>=0.23.5
  aiohttp>=3.9.0
  python-telegram-bot>=21.0
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  Crypto-Trading-Bot4/
  ├── api/
  ├── config/
  ├── db/
  ├── docs/
  ├── engines/
  │   ├── alpha_engine.py
  │   ├── backtest_engine.py
  │   ├── data_engine.py
  │   ├── execution_engine.py
  │   ├── monitor_engine.py
  │   ├── news_engine.py
  │   ├── risk_engine.py
  │   └── telegram_engine.py
  ├── logs/
  ├── scoring_ai/
  ├── scripts/
  ├── tests/
  ├── utils/
  ├── web/
  ├── venv/
  ├── main.py
  └── requirements.txt
  ```

- **README.md (primeras 30 líneas):**
  ```
  CT4 — Crypto Trading Bot v4
  Quantitative Sniper Strategy • RSI Pullback • Binance Testnet

  Python 3.13 | Binance Testnet | RSI35 Pullback | Live Testing | Dashboard Premium v4

  Overview:
  CT4 is an algorithmic trading bot designed for BTC/USDT on Binance Testnet.
  It implements a "Sniper" RSI Pullback strategy that only opens long positions
  when all 4 confluence laws are met simultaneously, ensuring extremely
  high-probability entries.

  The bot runs 24/7, monitoring the market via WebSocket, evaluating conditions
  every 5-minute candle, and executing trades when the moment is perfect.

  Philosophy: The Sniper
  "A sniper doesn't shoot at everything that moves. They wait for the perfect shot."

  The bot rejects 95%+ of market conditions. It only fires when 4 independent
  filters align — this is by design, not a bug.

  The 4 Laws of the Sniper
  ```

- **Git log (últimos 5 commits):**
  ```
  cc60a9a Fix 6 audit bugs: kill switch reset, trailing pct, dynamic balance, price format, strategy log
  6b389ef v2: AllIn RSI<15 strategy + MomBurst+ (lab-validated with REAL Binance data)
  680958d feat: Inyeccion de estrategia RSI35 ganadora y documentacion Quant V1.0
  ```
  *(Solo 3 commits encontrados en el historial)*

- **Git status (archivos modificados):**
  ```
   M api/server.py
   M config/settings.py
   M engines/alpha_engine.py
   M engines/backtest_engine.py
   M engines/data_engine.py
   M engines/execution_engine.py
   M main.py
   M requirements.txt
   M scripts/strategy_compare.py
  + 70+ archivos sin trackear (scripts de lab, logs, dashboards experimentales)
  ```

- **Archivos principales (engines/, por tamaño):**
  ```
  execution_engine.py    ~27 KB
  backtest_engine.py     ~19 KB
  monitor_engine.py      ~14 KB
  data_engine.py         ~13 KB
  news_engine.py         ~12 KB
  ```

- **Variables de entorno (.env — solo nombres):**
  ```
  EXCHANGE_ID
  EXCHANGE_SANDBOX
  API_KEY
  API_SECRET
  SYMBOL
  SYMBOLS
  TIMEFRAME
  ACTIVE_STRATEGY
  CRYPTOPANIC_TOKEN
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  TRADING_MODE
  CAPITAL
  DAILY_LOSS_LIMIT
  MAX_DRAWDOWN_LIMIT
  SLIPPAGE_MAX
  ```

---

## alze

- **Stack:** C++17 · CMake 3.20+ · Ninja/MinGW · SDL2 2.30.12 · OpenGL (GLAD) · Custom ECS · Custom Physics · Custom Renderer

- **Dependencias clave (CMakeLists.txt):**
  ```
  SDL2 (FetchContent o MSYS2 local, v2.30.12)
  GLAD (OpenGL loader, incluido en src/renderer/glad/)
  cgltf (glTF model loader, incluido en src/renderer/)
  Módulos internos: engine_math, engine_physics, engine_renderer, engine_core, engine_ecs
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  alze/
  ├── assets/
  │   ├── hdri/
  │   └── models/
  ├── build/
  ├── build_msvc/
  ├── src/
  │   ├── ai/
  │   ├── core/
  │   ├── ecs/
  │   │   └── systems/
  │   ├── game/
  │   ├── math/
  │   ├── physics/
  │   ├── renderer/
  │   │   └── glad/
  │   └── scene/
  └── tests/
  ```

- **README.md (primeras 30 líneas):**
  ```
  # ALZE — Game Engine

  Motor gráfico de propósito general construido desde cero en C++17.

  ## Visión
  ALZE es un motor de videojuegos diseñado para ser comercialmente viable,
  con arquitectura profesional, alto rendimiento y flexibilidad total.
  No es un proyecto educativo — es un motor real con la ambición de crear juegos reales.

  ## Estado Actual — Fase 3.2 (3D Materials + Shaders)

  | Métrica      | Valor        |
  |--------------|--------------|
  | Archivos     | 72+          |
  | Líneas código| ~11,000      |
  | Tests        | 436/436 ✅   |
  | Lenguaje     | C++17 (sin RTTI, sin excepciones) |
  | Dependencias | SDL2 (local MSYS2 o FetchContent) |
  | Build        | CMake + Ninja/MinGW |
  | Score audit  | 4.6/5.0      |
  ```

- **Git log (últimos 5 commits):**
  ```
  bacabc5 v0.7.0: Phase 0.5 Foundation Hardening - tickless timer, W^X, cpuidle, quarantine (46 tests)
  20c4efc v0.6.3: macOS/Linux patterns - bitmap TCB O(1), VFS rwlock, kprintf ratelimit (47 tests)
  a0f7a86 v0.6.2: Full errno adoption (18 codes), percpu test, version consistency (42+5=47 tests)
  4ff8c4b v0.6.1: Sprint 4.9 Pre-SMP Hardening - percpu GS, sched refactor, cli audit, TLB abstraction
  61bb5e1 v0.6.0: Audit fixes - atomic VFS refcount, errno adoption, VFS locking, klog spinlock
  ```
  *(Nota: estos commits corresponden al historial del repo de alze OS, que comparte repositorio git con este directorio)*

- **Git status:** Limpio — sin cambios sin commitear

- **Archivos principales (src/, por tamaño):**
  ```
  src/renderer/glad/include/glad/gl.h    ~873 KB  (generado - OpenGL loader)
  src/renderer/glad/src/gl.c             ~605 KB  (generado - OpenGL loader)
  src/renderer/cgltf.h                   ~201 KB  (single-header glTF parser)
  src/game/Play3DState.cpp               ~ 56 KB
  src/renderer/ImageDecoder.cpp          ~ 37 KB
  ```

- **Variables de entorno:** No se encontró archivo .env

---

## alze os

- **Stack:** C (kernel) · x86-64 Assembly (NASM) · Make · Clang/LLD · Limine (bootloader) · QEMU (emulación/tests)

- **Dependencias (toolchain, sin dependencias externas de paquetes):**
  ```
  Compilador : Clang (target x86_64-unknown-none, -ffreestanding)
  Linker     : ld.lld (LLVM)
  Ensamblador: NASM
  ISO        : xorriso
  Emulador   : QEMU x86_64
  Debugger   : GDB
  Flags clave: -fstack-protector-strong, -mcmodel=kernel,
               -mno-sse -mno-sse2 -mno-mmx, -Wall -Wextra -Werror
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  alze os/
  ├── build/
  ├── kernel/
  │   ├── main.c
  │   └── [~100+ módulos .c/.h]
  ├── limine/        (submódulo - bootloader)
  ├── userland/
  │   ├── init.c
  │   ├── shell.c
  │   └── hello.c
  ├── tests/
  │   ├── test_ecs.cpp
  │   ├── test_math.cpp
  │   ├── test_memory.cpp
  │   ├── test_phase*.cpp
  │   └── test_pmm.c
  ├── Makefile
  ├── build.sh
  ├── run.sh
  ├── linker.ld
  └── limine.conf
  ```

- **README.md (primeras 30 líneas — extracto):**
  ```
  Anykernel OS — Bare-metal x86_64 OS kernel en C y Assembly

  Versión  : v0.7.0
  Código   : ~19,000+ líneas (C + NASM)
  Kernel   : 76 KB
  Boot time: 90 ms
  Tests    : 46 kernel + 5 runtime
  Warnings : 0 (compilación estricta con -Werror)

  Arquitectura:
  Boot (Limine) → GDT/TSS → IDT → PIC/PIT → PMM (buddy allocator)
  → VMM (4-level paging) → kmalloc (slab) → Scheduler (preemptive, 3-level priority)
  → Sync primitives → IPC → VFS → ext2 → Network → SMP
  ```

- **Git log (últimos 5 commits):**
  ```
  bacabc5 v0.7.0: Phase 0.5 Foundation Hardening - tickless timer, W^X, cpuidle, quarantine (46 tests)
  20c4efc v0.6.3: macOS/Linux patterns - bitmap TCB O(1), VFS rwlock, kprintf ratelimit (47 tests)
  a0f7a86 v0.6.2: Full errno adoption (18 codes), percpu test, version consistency (42+5=47 tests)
  4ff8c4b v0.6.1: Sprint 4.9 Pre-SMP Hardening - percpu GS, sched refactor, cli audit, TLB abstraction
  61bb5e1 v0.6.0: Audit fixes - atomic VFS refcount, errno adoption, VFS locking, klog spinlock
  ```

- **Git status:** Limpio — sin cambios sin commitear

- **Archivos principales (kernel/, por líneas):**
  ```
  kernel/sched.c    1,182 líneas  (scheduler preemptivo)
  kernel/tests.c    1,119 líneas  (suite de tests)
  kernel/syscall.c    884 líneas  (system calls)
  kernel/vmm.c        829 líneas  (virtual memory manager)
  kernel/ext2.c       789 líneas  (filesystem ext2)
  ```

- **Variables de entorno:** No se encontró archivo .env

---

## harvestpro-nz

- **Stack:** TypeScript 5.3 · React 19 · Vite 7.3.1 · Capacitor 8.2.0 (Android) · Supabase/PostgreSQL · Zustand · TanStack React Query · Dexie (IndexedDB offline) · Tailwind CSS 3.4.0 · Vitest · Playwright · Storybook

- **Dependencias clave (package.json — selección):**
  ```
  @capacitor/android, @capacitor/cli, @capacitor/core  ^8.2.0
  @sentry/react                                         ^10.39.0
  @supabase/supabase-js                                 ^2.39.0
  @tanstack/react-query                                 ^5.90.21
  crypto-js                                             ^4.2.0
  dexie                                                 ^3.2.4
  html5-qrcode                                          ^2.3.8
  papaparse                                             ^5.5.3
  posthog-js                                            ^1.345.3
  react-router-dom                                      ^7.13.0
  react-virtuoso                                        ^4.18.1
  zod                                                   ^4.3.6
  zustand                                               ^5.0.11
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  harvestpro-nz/
  ├── .github/
  │   └── workflows/
  ├── .husky/
  ├── .storybook/
  ├── android/
  ├── dist/
  ├── src/
  ├── .env
  ├── .env.example
  ├── .env.local
  ├── capacitor.config.ts
  ├── CHANGELOG.md
  └── package.json
  ```

- **README.md (primeras 30 líneas — extracto):**
  ```
  HarvestPro NZ v9.9.0 — Industrial Orchard Management Platform

  Tests    : 3800+ passing
  Cobertura: ~50%
  Código   : ~92,000 líneas
  Lint     : 0 errores
  A11y     : WCAG 2.1

  Pilares:
  - Real-Time Ledger  : QR móvil, registros inmutables de bins/buckets
  - Wage Shield       : Auditoría de nómina, compliance salario mínimo NZ
  - Offline-First     : Dexie sync engine + DLQ + Zod + JWT silent refresh
  - Central Command   : Importación CSV, exportación multi-plataforma (Xero, PaySauce)
  - HR & Contracts    : Gestión empleados, compliance tracking
  ```

- **Git log (últimos 5 commits):**
  ```
  e618f0a refactor(sprint-19): audit improvements — type safety, Manager.tsx extraction
  0ffcc30 feat(v9.9.0): Sprint 18 — technical debt remediation, all tests green
  0f750c8 fix: onboarding UI (Tailwind), provision-orchard Edge Function, offline.service type
  6f9cbb4 style: lint-staged auto-format (LF line endings)
  529a56c feat: market readiness — legal, onboarding, security, multi-tenancy
  ```

- **Git status:**
  ```
  ?? .context.md   (único archivo sin trackear)
  ```

- **Archivos principales (src/, por tamaño):**
  ```
  src/index.css                                    ~38 KB  (estilos globales)
  src/types/database.types.ts                      ~35 KB  (tipos generados Supabase)
  src/repositories/batch-repos.test.ts             ~25 KB
  src/utils/weeklyReportSections.ts                ~22 KB
  src/services/__tests__/payroll.service.test.ts   ~21 KB
  ```

- **Variables de entorno (.env — solo nombres):**
  ```
  GEMINI_API_KEY
  VITE_SUPABASE_ANON_KEY
  VITE_SUPABASE_URL
  VITE_VAPID_PUBLIC_KEY
  ```

---

## money

- **Stack:** HTML5 · CSS3 · JavaScript (vanilla) · Three.js (CDN) · Firebase Hosting · Google Analytics GA4 · n8n (webhooks externos) · Google Apps Script (CRM)

- **Dependencias:** Sin package.json ni requirements.txt. Dependencias externas vía CDN:
  ```
  Three.js          (efectos de partículas 3D en hero)
  Google Analytics  GA4 (tracking)
  Firebase SDK      (hosting deployment)
  n8n webhooks      (procesamiento de formularios)
  Google Apps Script (integración CRM)
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  money/
  ├── docs/
  │   ├── email-templates.md
  │   ├── mega-prompt.md
  │   └── n8n-workflow-guide.md
  ├── n8n-workflows/
  │   └── lead-capture.json
  ├── ALZ_Google_Sheets_Script.js
  ├── blog-cro-basico.html
  ├── blog-landing-page.html
  ├── contact.html
  ├── cookies.html
  ├── effects.js
  ├── firebase.json
  ├── index.html
  ├── n8n_CRM_Node.json
  ├── privacy.html
  ├── robots.txt
  ├── script.js
  ├── sitemap.xml
  ├── styles.css
  └── terms.html
  ```

- **README.md:** No existe. El archivo `.context.md` indica:
  ```
  ALZ Agency — Agencia CRO
  Estado: Producción — Web activa
  GA4: configurado | n8n: Webhook HTTPS en Hetzner
  Próximo: Activar CRM Google Sheets (código listo, falta pegar script)
  ```

- **Git log (últimos commits):**
  ```
  1be8ef1 Initial commit of ALZ Landing Page
  ```
  *(Solo 1 commit — proyecto con git recién inicializado)*

- **Git status:**
  ```
   M audit-dashboard.png
   M effects.js
   M index.html
   M styles.css
  ?? .context.md
  ?? .firebase/
  ?? .firebaserc
  ?? ALZ_Google_Sheets_Script.js
  ?? blog-cro-basico.html
  ?? blog-landing-page.html
  ?? contact.html
  ?? cookies.html
  ?? firebase.json
  ?? n8n-workflows/
  ?? n8n_CRM_Node.json
  ?? privacy.html
  ?? robots.txt
  ?? sitemap.xml
  ?? terms.html
  ```
  *(4 archivos modificados, la mayoría del proyecto nunca committeado)*

- **Archivos principales (fuente, por tamaño):**
  ```
  styles.css     ~53 KB
  index.html     ~42 KB
  effects.js     ~13 KB
  contact.html   ~10 KB
  blog-cro-basico.html ~9.6 KB
  ```

- **Variables de entorno:** No se encontró archivo .env
  *(Configuración vía .firebaserc + IDs hardcodeados en HTML)*

---

## set up

- **Stack:** Node.js · Python 3 (138 scripts de automatización) · JSON (workflows n8n) · HTML/CSS (dashboards)

- **Dependencias clave (package.json):**
  ```json
  {
    "dependencies": {
      "ssh2": "^1.17.0"
    }
  }
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  set up/
  ├── node_modules/
  ├── scripts/
  │   ├── [138 scripts Python de automatización]
  │   ├── [workflows JSON para n8n]
  │   ├── dashboard.html
  │   └── [scripts de configuración]
  ├── env_temp.txt
  ├── package-lock.json
  └── package.json
  ```

- **README.md:** No existe

- **Git log:** No tiene repositorio git propio
  *(El comando git traversó hasta el repositorio padre)*

- **Git status:** No tiene repositorio git propio

- **Archivos principales (scripts/, por tamaño):**
  ```
  dashboard.html                          ~9.4 KB
  create_telegram_ai_bot_v3.py            ~3.4 KB
  ai_agent_dump.json                      ~4.9 KB
  crypto_portfolio_alerts_fixed.json      ~3.2 KB
  daily_briefing_fixed.json               ~2.5 KB
  ```

- **Variables de entorno (env_temp.txt — solo nombres):**
  ```
  N8N_PROXY_HOPS
  ```

---

## vida, control

- **Stack:** Node.js · Express ^5.1.0 · PostgreSQL 16 · HTML/CSS/JS (dashboard) · Tesseract.js (OCR) · node-telegram-bot-api · Docker (2 contenedores: db + engine)

- **Dependencias clave (ultra-engine/package.json):**
  ```
  express               ^5.1.0
  pg                    ^8.13.0
  node-cron             ^3.0.3
  node-telegram-bot-api ^0.66.0
  tesseract.js          ^5.1.1
  rss-parser            ^3.13.0
  cheerio               ^1.0.0
  multer                ^1.4.5-lts.1
  dotenv                ^16.4.0
  pdf-parse             ^1.1.1
  ```

- **Estructura de carpetas (profundidad 2):**
  ```
  vida, control/
  ├── db/
  │   └── init.sql
  ├── docs/
  │   ├── ARCHITECTURE.md
  │   └── ULTRA_SYSTEM_AUDIT.md
  ├── scripts/
  │   ├── backup.sh
  │   └── deploy.sh
  ├── ultra-engine/
  │   ├── Dockerfile
  │   ├── package.json
  │   ├── public/
  │   ├── server.js
  │   ├── src/
  │   │   ├── db.js
  │   │   ├── ocr.js
  │   │   ├── rss.js
  │   │   ├── scraper.js
  │   │   ├── scheduler.js
  │   │   ├── telegram.js
  │   │   └── routes/
  │   └── uploads/
  ├── .env
  ├── .env.example
  ├── docker-compose.yml
  ├── deploy.tar.gz
  ├── deploy_hetzner.js
  └── README.md
  ```

- **README.md (primeras 30 líneas):**
  ```
  # ULTRA SYSTEM — Sistema de Inteligencia Personal

  "Una extensión de tu cerebro en la nube — 100% código propio"

  Sistema operativo personal para nómadas digitales. Diseñado para automatizar la
  burocracia, vigilar oportunidades y tomar el control del caos del día a día desde
  un VPS de 4€. Sin herramientas de terceros.

  Stack:
  Backend    | Node.js + Express | API REST + Scheduler + Bot
  Dashboard  | HTML/CSS/JS       | Dark theme premium
  OCR        | Tesseract.js      | ESP + ENG bilingüe
  RSS        | rss-parser        | Reemplaza Miniflux
  Scraper    | Cheerio           | Reemplaza Changedetection
  Bot        | node-telegram-bot-api | Reemplaza n8n
  Base datos | PostgreSQL 16     | Única dependencia externa
  Contenedores | 2 (db + engine) | Antes eran 8

  Los 7 Pilares:
  1. Noticias      ✅ ACTIVO — RSS reader propio → dashboard
  2. Empleo Físico ✅ ACTIVO — Web scraper propio → alertas
  4. Burocracia    ✅ ACTIVO — OCR + alertas documentos
  ```

- **Git log:** No tiene repositorio git propio
  *(El comando git traversó hasta el repositorio padre)*

- **Git status:** No tiene repositorio git propio

- **Archivos principales (ultra-engine/src/, por tamaño):**
  ```
  src/telegram.js           ~6.6 KB
  src/routes/documents.js   ~5.2 KB
  src/scheduler.js          ~5.7 KB
  src/scraper.js            ~4.7 KB
  src/routes/status.js      ~3.8 KB
  ```

- **Variables de entorno (.env — solo nombres):**
  ```
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DB
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  TZ
  ```

---

*Fin del reporte — INFO_PROYECTOS.md*
