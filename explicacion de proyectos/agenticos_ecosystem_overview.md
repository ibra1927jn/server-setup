# 🌌 The AgenticOS Ecosystem (2026)

Este documento es el mapa definitivo de la arquitectura **AgenticOS**, un ecosistema de desarrollo autónomo diseñado para operar 7 proyectos técnicos simultáneos desde un portátil con Windows 11, delegando la carga pesada a una infraestructura en Hetzner (N8N, PostgreSQL, Docker) y gestionando el código mediante Claude Code + Ollama.

---

## 1. 🧠 Core de Inteligencia Artificial (El "Cerebro")

El ecosistema utiliza un modelo híbrido para maximizar la velocidad y minimizar el coste de tokens:

*   **Claude Code (Anthropic CLI):** Motor principal (v2.1.85) conectado a la API de Anthropic (Claude 3.7 Sonnet). Actúa como el desarrollador principal ("Allan") con acceso completo al sistema de archivos local y autorización de cobro por uso.
*   **Ollama Local (Fallback & Tareas Rápidas):**
    *   `deepseek-r1:8b` (Razonamiento profundo sin coste).
    *   `qwen2.5-coder:7b` (Snippets rápidos y refactorización off-grid).
*   **GLM-4.5 Air (Vía OpenRouter):** Integrado en N8N para automatización conversacional y clasificación de leads desde Telegram/Web a un coste ínfimo ($0.13/M tokens).

### Model Context Protocol (MCP) Instalados
*   🔌 **GitHub MCP:** Acceso directo a repositorios, lectura de issues, y creación de PRs sin cambiar de ventana.
*   🔌 **Context7 MCP:** Base de datos vectorial/RAG para leer la documentación oficial más reciente de librerías (Supabase, NextJS, etc.) evitando alucinaciones con código antiguo.

---

## 2. 🏗️ Infraestructura Cloud & Automatización (Hetzner VPS)

La nube privada (`95.217.158.7`) sirve como el backend operativo de todos los proyectos:

*   **N8N (Docker):** Centro neurálgico de automatización. Maneja Chatbots E2E vía webhooks, clasificación de CRM y enrutamiento con IA abierta.
*   **Nginx Reverse Proxy:** Separa el PWA de N8N del Dashboard personalizado (`/var/www/dashboard`) gestionando cabeceras seguras (`N8N_PROXY_HOPS`).
*   **Supabase / PostgreSQL Local:** En proceso de migración para **HarvestPro NZ** tras agotar el Free Tier de la nube pública, retomando la soberanía de los datos agrícolas.

---

## 3. 📂 El Sistema de Memoria "Camaleón" de AgenticOS

Cada uno de los 7 proyectos comparte un ADN estructural idéntico que aísla la memoria de la IA. Claude Code sabe exactamente dónde está y qué falló en el pasado leyendo:

*   `CLAUDE.md`: Las reglas locales del proyecto (ej: "No usar `any` en TypeScript").
*   `PROGRESS.md`: El estado actual (Completado, En progreso, Pendiente, Bloqueado). **Es el punto de guardado tras cada sesión.**
*   `ERRORES.md`: Memoria inmunológica. Errores del pasado que Claude debe leer para no volver a cometer (ej: cierres de BD no controlados).
*   `.claude/commands/`: Comandos *slash* personalizados inyectados:
    *   `/resume`: Permite retomar una sesión instantáneamente leyendo el contexto.
    *   `/spec`: Obliga a la IA a planificar antes de programar.
    *   `/review`: Verifica tests, console.logs y reglas antes de hacer commit.
    *   `/deploy`: Ejecuta `build` y tests en verde antes de dar la orden final.

---

## 4. 🗂️ Los 7 Proyectos Concurrentes (Auditoría Técnica)

He inspeccionado el árbol de archivos de cada uno de los 7 proyectos. A continuación, el desglose quirúrgico de tu ecosistema activo:

### 🌾 1. HarvestPro NZ (Industrial Orchard Management)
*   **Stack:** TypeScript 5.3, React 19, Vite 7.3, Supabase/PostgreSQL, Zustand, Dexie (Offline), Capacitor 8.2.
*   **Volumen:** ~92,000 líneas de código, >3,800 tests pasando (~50% cobertura).
*   **Estado:** `Producción / Migración Local`. Pwa offline-first con motor de sincronización (Sync Engine + DLQ) resistente a caídas de red.
*   **Tooling AgenticOS:** Integramos un robusto sistema `Husky pre-commit` para forzar a Claude a validar lint y tests antes de poder hacer push de cualquier feature. 

### 📈 2. Crypto-Trading-Bot4 (CT4)
*   **Stack:** Python 3.13, FastAPI, CCXT, Pandas/Pandas-TA, WebSockets.
*   **Volumen:** Motores de ejecución pesados (execution_engine ~27KB, backtest_engine ~19KB).
*   **Estado:** `Live Testing / Binance Testnet`. Estrategia Cuantitativa "Sniper" (RSI Pullback). Funciona 24/7 evaluando velas de 5 minutos y aplicando 4 leyes de confluencia.
*   **Tooling AgenticOS:** Arquitectura modularizada en 4 motores (Data, Risk, Alpha, Exec). Fuerte aislamiento con `.gitignore` para no exponer las claves de Binance o Telegram.

### 🎮 3. alze (Game Engine 2D/3D)
*   **Stack:** C++17, CMake, OpenGL (GLAD), SDL2. Construido sin dependencias externas pesadas, orientado a alto rendimiento.
*   **Volumen:** ~11,000 líneas de código, 436 tests (100% pasando). Score de auditoría: 4.6/5.0.
*   **Estado:** `Fase 3.2 (3D Materials + Shaders)`. Posee un ECS propio ultra-rápido evaluado en 5K entidades a 259 FPS.
*   **Tooling AgenticOS:** Claude opera este entorno utilizando C++ moderno (sin RTTI y sin excepciones), garantizando tiempos de respuesta ultrabajos.

### 💻 4. alze os (Bare-metal x86_64 SMP Kernel)
*   **Stack:** C, x86-64 Assembly (NASM), Bootloader Limine, QEMU.
*   **Volumen:** ~19,000 líneas. Kernel pesa solo 76 KB con un tiempo de boot de 90ms. 
*   **Estado:** `Fase 0.7.0 (Core hardening)`. Tiene filesystem ext2 propio, virtual memory manager, y primitive SMP/IPC listos. Compilación `-Werror` sin warnings permitidos.
*   **Tooling AgenticOS:** Código monolítico de extrema complejidad. Claude utiliza el emulador QEMU y GDB para debuggear excepciones Triple Fault generadas por rutinas Ring 0.

### 🤖 5. vida, control (ULTRA SYSTEM - Personal OS)
*   **Stack:** Node.js, Express, PostgreSQL 16, Tesseract.js (OCR), Cheerio (Scraping), Telegram Bots.
*   **Volumen:** Código hiper-optimizado divido en módulos core (OCR, Scraper, RSS, Telegram). Reducido de 8 contenedores a solo 2 (DB + Backend).
*   **Estado:** `Activo`. Lee noticias automáticamente, notifica burocracia por OCR, raspea portales y notifica todo a Telegram en tiempo real vía Hetzner VPS.

### 💸 6. money (Agencia CRO & Frontend)
*   **Stack:** HTML5, CSS3, Vanilla JS, Three.js (Efectos Core), GA4, Firebase Hosting.
*   **Estado:** `Despliegue inicial`. Integrado con webhooks REST de n8n para la recolección de Leads y un script propio en Google Apps Script para almacenar datos en el CRM (Google Sheets).

### ⚙️ 7. set up (El "Workspace Raíz")
*   **Stack:** 138 scripts Python de automatización, JSON workflows n8n, Bash scripts.
*   **Estado:** Centro de control maestro desde donde orquestamos todo el ecosistema Hetzner (Proxies, Backups, Dashboards UI, GLM-4.5 Air) y AgenticOS de Windows.

---
## 5. 🛡️ Capa de Seguridad (Sandboxing)

1.  **Aislamiento de Entorno:** Ningún archivo `.env` o credencial (`env_temp.txt`) se rastrea en Git en ninguno de los 7 proyectos.
2.  **Git Worktrees:** Sistema configurado (ej: `alze`) para que Claude trabaje en ramas paralelas (ej: *distracted-bell*, *intelligent-mccarthy*) sin romper el código de producción.
3.  **Workspace Validation:** El entorno base protege a Claude Code de salirse de los directorios aprobados o modificar archivos del sistema Windows.
## 6. 🧰 Caja de Herramientas Transversal (Global Toolkit)

Para hacer que todo este ecosistema respire y compile, AgenticOS se apoya en una navaja suiza de herramientas puras de DevOps, Testing, e Infraestructura:

### 🧩 IA & Agents
*   **Claude Code:** CLI base (Autonomía de edición y comandos Shell).
*   **Ollama:** Motor local (`qwen2.5-coder:7b` / `deepseek-r1:8b`).
*   **GLM-4.5 Air:** Modelo remoto hiperbarato vía **OpenRouter** (Para chat y N8N).

### ⚙️ Automatización & DevOps
*   **n8n:** Orquestador visual de flujos (Webhooks, Cron jobs, bots de Telegram).
*   **Docker & Docker Compose:** Contenedorización de PostgreSQL, n8n y el Ultra System.
*   **Husky:** Git hooks (intercepta `git commit` para forzar tests y linters).
*   **Git Worktrees:** Árboles de código paralelos para evitar colisiones en `alze`.
*   **PM2 / Systemd:** Administradores de procesos en segundo plano (VPS).

### 🛠️ Compiladores & Build Systems
*   **Vite:** Bundler ultrarrápido (Frontend HarvestPro).
*   **CMake & Ninja/MinGW:** Sistema constructivo multiplataforma (`alze` engine 3D).
*   **Make & Clang/LLD:** Toolchain de bajo nivel para compilación *freestanding* (`alze os`).
*   **NASM:** Ensamblador de los vectores de interrupción y boot (`alze os`).
*   **Capacitor:** Compilación web-a-móvil para Android (`harvestpro-nz`).

### 🛡️ Infraestructura & Seguridad
*   **Hetzner Cloud VPS:** Servidor Linux dedicado (`95.217.158.7`).
*   **Nginx:** Reverse proxy que maneja enrutamiento, certificados y headers (`N8N_PROXY_HOPS`).
*   **UFW (Uncomplicated Firewall):** Bloqueo total de puertos excepto los túneles estrictamente necesarios.
*   **Supabase CLI:** Herramienta local para levantar PostgreSQL de desarrollo con Migrations y RLS.

### 🧪 Testing & Debugging
*   **Vitest:** Pruebas unitarias ultrarrápidas de JS/TS.
*   **Playwright:** E2E web testing para `harvestpro-nz`.
*   **QEMU & GDB:** Emulador bare-metal y debugger remoto en tiempo real para el Kernel OS.
*   **PyTest & Asyncio:** Benchmarks y testing cuantitivo intensivo del Bot de criptomonedas.

---

> [!TIP]
> **El Loop Diario del Solo-Developer (SOP):**
> 1. Abres terminal en tu proyecto (`cd desktop/harvestpro-nz`).
> 2. Ejecutas `claude /resume` → Claude lee `PROGRESS.md` y te dice qué toca.
> 3. Hacéis el código. Claude usa `github-mcp` o `context7` si hace falta.
> 4. Escribes `/review` → Pasan los tests (Husky asegura pre-commit).
> 5. Al terminar, le ordenas a Claude actualizar `PROGRESS.md` y si hubo fallos raros, añadirlos a `ERRORES.md`.
> 6. Cierras terminal sin perder hilos.
