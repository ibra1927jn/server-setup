# ERRORES.md — Lo que no volvemos a hacer

## Formato
[YYYY-MM-DD] | [archivo afectado] | [error] | [fix aplicado]

---

## Errores registrados
- [2026-03-28] | index.html | GA4 se disparaba sin consentimiento GDPR (dos bloques gtag duplicados, ambos sin check) | Se eliminaron ambos bloques, se creo initGA4() que solo carga gtag.js tras consentimiento. acceptCookies() ahora llama initGA4()
- [2026-03-28] | index.html | HTML roto: `< 24h` en hero stats se interpretaba como tag HTML | Escapado a `&lt; 24h`
- [2026-03-28] | index.html, contact.html | Copyright footer mostraba 2025 en vez de 2026 | Actualizado a 2026
- [2026-03-28] | cookies.html, privacy.html, terms.html | Fecha "ultima actualizacion" decia 2025 | Actualizado a 28 de marzo de 2026
- [2026-03-28] | index.html | Imagenes below-fold (ai-analysis.png, footer logo) sin loading="lazy" ni dimensiones | Agregado loading="lazy" + width/height
- [2026-03-28] | blog-cro-basico.html, blog-landing-page.html | CSS completo duplicado inline en cada blog, no reutilizaban styles.css | Reemplazado con link a styles.css + bloque style solo con overrides de blog
- [2026-03-28] | sitemap.xml | URLs apuntaban a privacidad.html y terminos.html (archivos no existen, se llaman privacy.html y terms.html) | Corregido a privacy.html y terms.html
- [2026-03-28] | blog-cro-basico.html, blog-landing-page.html | Footer links apuntaban a /privacidad.html (archivo inexistente) | Corregido a /privacy.html
- [2026-03-28] | todos los .html | Sin favicon SVG, solo PNG | Agregado favicon SVG inline con texto "ALZ" y gradiente de marca como primary, PNG como fallback
- [2026-03-28] | cookies.html, privacy.html, terms.html | No tenian favicon en absoluto | Agregado SVG + PNG favicon
