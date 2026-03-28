# RESUMEN: money (ALZ Marketing + CRM)

**Stack:** HTML/CSS/JS estático + Firebase Hosting + n8n
**Última modificación:** Mar 26, 2026

## Descripción
Landing page de marketing para ALZ (agencia/servicio) con integración CRM via n8n y Google Sheets. Desplegado en Firebase Hosting.

## Estructura
```
money/
├── index.html              # Landing page principal (42k)
├── styles.css              # Estilos (53k)
├── effects.js              # Efectos visuales (13k)
├── translations.js         # i18n (35k)
├── script.js               # JS principal
├── contact.html            # Página de contacto
├── blog-*.html             # Artículos del blog
├── privacy.html / terms.html / cookies.html
├── favicon.png / alz-logo.png / hero-bg.png
├── firebase.json           # Config Firebase Hosting
├── .firebaserc             # Proyecto Firebase
├── sitemap.xml / robots.txt
├── ALZ_Google_Sheets_Script.js  # Script Apps Script para CRM
├── n8n-workflows/
│   └── lead-capture.json   # Workflow captura de leads
└── n8n_CRM_Node.json       # Nodo CRM n8n
```

## Deploy
```bash
firebase deploy             # Desplegar a Firebase
```

## Automatizaciones n8n
- **lead-capture**: Captura formularios → Google Sheets → email
- **CRM Node**: Integración con CRM

## Docs
- `docs/email-templates.md` — plantillas de email
- `docs/mega-prompt.md` — prompts de IA
- `docs/n8n-workflow-guide.md` — guía de workflows
