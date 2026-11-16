# Herramientas de Finanzas y Tarjetas MX

Páginas públicas en GitHub Pages. Los datos de Banxico (inflación y CETES) y el comparativo a 10 años se actualizan en días hábiles. Los precios de FIBRAs se actualizan después del cierre (15:30, hora de la Ciudad de México) con Yahoo Finance; las distribuciones se cargan a mano desde avisos de la BMV y BIVA en `data/fibras.json`.

- Probar local: `python3 -m http.server` y abrir http://localhost:8000
- Banxico: `BANXICO_TOKEN=... python3 scripts/fetch_banxico.py`
- FIBRAs (precios): `python3 scripts/fetch_fibras.py`
- Tabla para el blog: `python3 scripts/wp_fibras_table.py` (ver el comentario del script)
