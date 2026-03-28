# Resumen Global de Proyectos, Herramientas y Configuraciones

Basado en el historial de desarrollo, infraestructura técnica y sistemas operativos en los que trabajamos, aquí tienes un mapa completo de todas las herramientas, lenguajes, arquitecturas y configuraciones que conforman tu ecosistema.

---

## 1. Crypto-Trading-Bot4 (CT4)
**Descripción:** Ecosistema automatizado de trading cuantitativo operando en tiempo real. Utiliza una arquitectura avanzada separada en 4 motores (Data, Alpha, Risk, Execution) para asegurar el aislamiento de fallos y escalabilidad.

### Herramientas y Tecnologías
*   **Lenguaje Core:** Python 3.
*   **Análisis y Datos:** `pandas` para análisis de backtests y manejo de DataFrames, `plotly` y `matplotlib` para la creación de gráficas interactivas de rendimiento (PnL).
*   **Conectividad y APIs:** API de Binance, `paramiko` para acceso asíncrono SSH/SFTP y sincronización de estado remoto-local en vivo. Dashboard local montado mediante `http.server`.
*   **Arquitectura Algorítmica:** Score AI Collector, Evaluadores Walk-Forward (validación científica con modelado de comisiones/slippage), múltiples bots en paralelo (Grid Bot, V14 Monitor, V15 Scalper).
*   **Infraestructura:** Despliegue en **Hetzner VPS**, gestionado a través de procesos demonizados en background (`nohup`), manejo de estados en formato JSON (`v12_paper_state.json`) y recuperación contra fallos.

---

## 2. Ecosistema de Automatización "AgenticOS" (ALZ)
**Descripción:** Plataforma robusta orientada a la gestión de prospectos CRM, embudos empresariales y respuestas automatizadas auto-hospedadas (Self-Hosted).

### Herramientas y Tecnologías
*   **Motor de Automatización:** **n8n** (desplegado en instancias propias, no en la nube de n8n).
*   **Red y Seguridad:** **Nginx** (proxy inverso configurado de manera estricta para websockets y certificados SSL/HTTPS).
*   **Stack Backend / Web:** Migración reciente del paradigma Dockerizado múltiple hacia un "Custom Ultra System" unificado en **Node.js** para mayor ligereza.
*   **Integraciones y APIs (Pipelines de Venta):** 
    *   Webhooks de web e integraciones de widgets de Chat (Custom Dashboard).
    *   Bots de Telegram (procesamiento SSL estricto).
    *   WhatsApp Auto-replies, rastreo Meta Ads, Google Analytics (GA4) y sincronización con bases de datos en Google Sheets/CRM.

---

## 3. HarvestPro NZ (Plataforma UI/UX y Web App)
**Descripción:** Aplicación agrícola moderna migrada de un cliente pesado hacia una gestión autoritativa desde servidor utilizando un patrón 'API Gateway'.

### Herramientas y Tecnologías
*   **Frontend y Estado:** **React**, **TypeScript**. Uso extensivo del patrón 'Observable State' manejado a través de **Zustand** para coordinar lógica compleja (nóminas de empleados, sincronización offline).
*   **Testeo (Framework de QA robusto):** **Vitest**. Con una cobertura cercana al 50% de líneas con más de 2400+ pruebas pasando (Unitarias, Mocking agresivo de Edge Functions y Pruebas de Integración).
*   **Infraestructura Backend:** Edge Functions (Supabase o Vercel), Patrones de resiliencia fuera de línea, Exportaciones seguras y algoritmos de escaneo eficientes de Alto Rendimiento UI.

---

## 4. Computación de Bajo Nivel y Renderizado (Anykernel OS y PhysicsEngine2D)
**Descripción:** Investigación y desarrollo a nivel más bajo del sistema y procesamiento multicore de alta concurrencia.

### Herramientas y Tecnologías
*   **Anykernel OS:** Lenguajes **C** y **Ensamblador (Assembly x86)**. Desarrollo usando el emulador o hypervisor **QEMU**, depuración sobre puerto Serial/UART. Utiliza rutinas avanzadas y complejas como Multiprocesamiento Simétrico (SMP), inicialización de CPU (`gdt_init_ap`), y primitivas híbridas nativas IPC.
*   **PhysicsEngine2D:** Framework escrito en **C++**. Utiliza el patrón arquitectónico **ECS** (Entity Component System). Técnicas rigurosas de optimización como Lookups cacheadas `O(1)`, listas libres (free-lists) y ordenamiento de materiales de renderizados, permitiendo una escalabilidad teórica >5,000 entidades con prevención de cuellos de botella por sub-sistemas de memoria/audio.

---

## Conclusión Ejecutiva

Tu ecosistema abarca un espectro excepcionalmente técnico que va desde el **bajo nivel puro** (manejo de apuntadores, triple-faults de arranque OS) hasta la **alta infraestructura cloud de negocios y finanzas** (Sistemas Node.js sin servidor, AI bots transaccionando en exchanges de forma autónoma).
La configuración dominante hoy es: **Servidores VPS en Hetzner**, contenedores progresivamente reemplazados por runtimes crudos y eficientes (Python VENVs y Node.js), e infraestructuras orientadas a extrema resiliencia (Manejo de errores webhooks y kill-switches adaptativos).
