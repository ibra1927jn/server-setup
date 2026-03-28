# RESUMEN: Crypto-Trading-Bot4

**Stack:** Python (sin package.json)
**Última modificación:** Mar 27, 2026

## Descripción
Bot de trading de criptomonedas con múltiples versiones (v12, v15), backtesting, scoring con IA, y dashboard web. Desplegado en servidor remoto (Hetzner).

## Estructura clave
```
Crypto-Trading-Bot4/
├── v15_scalper.py          # Bot principal v15 (23k)
├── v12_shadow_bot.py       # Bot shadow v12 (41k)
├── main.py                 # Entry point original
├── monitor_server.py       # Monitor del servidor (64k)
├── dashboard.html          # Dashboard web (34k)
├── api_dashboard.py        # API del dashboard
├── backtest_v12/v14.py     # Scripts de backtesting
├── scoring_ai/
│   └── vector_db.json      # Base vectorial para scoring IA
├── engines/                # Motores de estrategia
├── config/                 # Configuración
├── db/                     # Base de datos local
├── logs/                   # Logs de trades reales
├── scripts/                # Scripts auxiliares
└── web/                    # Web assets
```

## Dependencias
- Ver `requirements.txt`
- Python virtual env en `venv/`

## Variables de entorno
- `.env.example` presente → copiar a `.env`
- Claves de API de exchange, servidor SSH

## Estado actual
- Versión activa: **v15** (v15_scalper.py)
- Datos reales: `v15_remote_trades_full.csv` (~37k líneas)
- Chart interactivo: `v15_chart.html`
- Archivos de estado: `current_status.txt`, `states_out.txt`

## Comandos útiles
```bash
python v15_scalper.py       # Ejecutar bot v15
python api_dashboard.py     # API del dashboard
python check_bot_current.py # Ver estado actual
python get_pnl.py           # Ver P&L
python fetch_v15_full.py    # Descargar trades del servidor
```

## Docs
- `README.md` — documentación principal
- `docs/bot_documentation.md` — doc del bot
- `docs/strategy_catalog.md` — catálogo de estrategias
- `future_ideas.md` — roadmap
