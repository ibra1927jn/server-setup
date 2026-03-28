# Inventario Global de Proyectos y Herramientas (Workspace AI)

Este documento centraliza y clasifica todos los proyectos, herramientas, infraestructuras y configuraciones que hemos desplegado y estabilizado a lo largo de nuestras sesiones de trabajo conjunto.

---

## 1. Ecosistema de Proyectos (Project Portfolio)

### 🌿 HarvestPro NZ (AgriTech & Logística)
Aplicación offline-first y server-authoritative diseñada para la gestión agrícola, nóminas, y control de calidad en tiempo real.
*   **Estado:** Refactorización UI (ResponsiveLayout) finalizada. Migración exitosa de Supabase Cloud a Docker Local.
*   **Arquitectura:** API Gateway, Estado Observable (*Zustand*), Sincronización offline-to-online.
*   **Archivos clave:** `ResponsiveLayout.tsx`, `gateway.service.ts`, `docker-supabase/`.

### 📉 Ecosystema Crypto-Trading-Bot 4 (CT4)
Plataforma algorítmica de Trading (Versiones v1 a v15) desplegada en servidores Hetzner.
*   **Estado:** Estabilidad y auditoría de kill-switches lograda (Monitor v11, Supervivientes v15). 
*   **Arquitectura:** 4 Motores desacoplados (Data, Alpha, Risk, Execution). Sistema *Ojo de Dios* (Scoring 0-100 para *cheap coins*).
*   **Estrategia:** Validación con datos reales, simulador PaperTrader automático, backtests rigurosos.

### 🤖 AgenticOS & ALZ Automation
Infraestructura de automatización robótica y captura de leads.
*   **Estado:** Operativo.
*   **Componentes integrados:** n8n, Webhooks de Telegram con SSL/HTTPS, Auto-respuestas en WhatsApp, CRM y Google Sheets.

### ⚙️ Alze OS / Anykernel (OS de Bajo Nivel)
Desarrollo de un Sistema Operativo desde cero (Sprint v0.5.x).
*   **Estado:** Estabilización del arranque SMP (Symmetric Multiprocessing) y resolución de fallos triple fault per-CPU (GDT/TSS).
*   **Arquitectura:** Primitivas híbridas, optimización IPC por transferencia directa.
*   **Herramientas de bajo nivel:** QEMU, Raw Serial Debugging.

### 🚀 Ultra System
Arquitectura ultraligera en backend.
*   **Estado:** Migración completada.
*   **Arquitectura:** Remplazo de 8 microservicios Docker pesados por un motor unificado auto-hospedado en Node.js puro.

### 🎮 PhysicsEngine2D (Fase 2.5)
Motor de físicas 2D escalable preparado para dar el salto al 3D.
*   **Arquitectura:** ECS (Entity-Component-System) con búsquedas hash-to-array, O(1) free-list memory allocations.
*   **Rendimiento:** 5,000 entidades estables a 259 FPS, cero deuda técnica.

---

## 2. Inventario de Herramientas y Tecnologías (Tool Stack)

### 🔹 Infraestructura y Despliegue (DevOps)
1.  **Hetzner Cloud VPS / SCP:** Servidores dedicados y comandos de copia segura para despliegue de los motores de trading y AgenticOS.
2.  **Docker & Docker Compose:** Contenerización de microservicios. Utilizado activamente en HarvestPro (13 contenedores: Postgres, GoTrue, Kong, Studio, etc.) y en ecosistemas legacy.
3.  **WSL 2 (Windows Subsystem for Linux):** Entorno bridge esencial de kernel 2.6.3 para ejecutar demonios nativos de Docker en la máquina host.
4.  **Nginx (con SSL / Let's Encrypt HTTPS):** Proxy inverso necesario para habilitar Webhooks de Telegram y asegurar el tráfico en JetBots/n8n.

### 🔹 Bases de Datos (Databases & Storage)
1.  **PostgreSQL:** Motor SQL principal, tanto en CT4 (análisis cuantitativo) como en la base Supabase local de HarvestPro.
2.  **Supabase (Local / Cloud):** Autenticación (GoTrue), Realtime (WebSockets multi-usuario), API REST automática y administración RLS (Row Level Security).
3.  **Redis (implícito en colas y gateways):** Estructura transitoria y rate-limiters si aplica.

### 🔹 Desarrollo Frontend & UI (Frontend Stack)
1.  **React.js (con Vite.js):** Renderizado de las vistas de usuario y roles en HarvestPro y los Dashboards de AgenticOS.
2.  **Zustand:** Sistema de manejo de estado sin fricción, utilizado en HarvestPro para encolamiento asíncrono y mensajes.
3.  **Tailwind CSS / Vanilla CSS:** Diseño UI unificado, condicionado al requerimiento dinámico o "Glassmorphism" con animaciones interactivas.

### 🔹 Automatización y Redes de Agentes (AI & Automation)
1.  **n8n (No-Code/Low-Code):** Cerebro central logístico para procesamiento de flujos de eventos entre APIs.
2.  **Telegram Bot API:** Capa de interacción directa Usuario-Máquina con webhooks encriptados.
3.  **Google Analytics 4 (GA4):** Embudos y telemetría de capación.

### 🔹 Ecosistema de Integración y Tests (QA)
1.  **Playwright / Vitest:** Tests exhaustivos end-to-end e integración funcional para HarvestPro (>2400 tests).
2.  **QEMU:** Emulación de hardware x86 para debugeo directo del kernel Anykernel.

---

## 3. Configuraciones Destacadas Logradas

*   **Evasión de Limitaciones de Red WSL:** Creado un script auto-ejecutable iterativo en PowerShell (`Pull-Images.ps1`) para sortear el error `TLS Handshake timeout` y permitir bajadas seguras en infraestructuras débiles.
*   **Traducción de Ficheros (CRLF a LF):** Solución de compatibilidad de Windows `CRLF` contra el entorno Unix de Docker para permitir el arranque del orquestador Elixir Supavisor y Kong.
*   **Matriz de Roles UI Unificada:** Fusión de lógica móvil/desktop condicional (`@media` reactivos) sobre shells monolíticos (`Manager`, `Payroll`, `HHRR`) previniendo código duplicado en HarvestPro.
*   **Reestructuración de CT4 v15:** Arquitectura de *Ojo de Dios* resucitada y desbugueada del modo "Kill-switch", restaurando logs históricos de rendimiento sin truncamientos JSON.

> **Resumen del estado actual:** 
> Todos estos proyectos han sido estabilizados superando las bases críticas (deuda técnica). Tenemos la infraestructura lista desde la emulación a bajo nivel (C / ASM), hasta agentes de IA conversacional y portales offline-first corporativos en pleno funcionamiento local y productivo.
