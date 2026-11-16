#!/usr/bin/env python3
"""Genera la tabla HTML estática para la página del blog.

Uso (desde la raíz del repo, después de scripts/fetch_fibras.py):

    python3 scripts/wp_fibras_table.py > /tmp/fibras-tabla-wp.html

Copia el HTML entre los comentarios
    <!-- TABLA-FIBRAS:INICIO -->
    ...
    <!-- TABLA-FIBRAS:FIN -->
y pégalo en la página de WordPress
https://finanzasytarjetasmx.wordpress.com/fibras-mexico-dividendos/
para refrescar la tabla (recomendado: cada semana, junto con la revisión
de avisos oficiales en data/fibras.json).

No publica en WordPress; solo imprime el fragmento.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def mxn(n, dec=2):
    if n is None:
        return "—"
    s = f"{n:,.{dec}f}"
    return "$" + s.replace(",", "X").replace(".", ",").replace("X", ",")


def pct(n, dec=2):
    if n is None:
        return "—"
    return f"{n:.{dec}f}%".replace(".", ",")


def fecha(s):
    if not s:
        return "—"
    try:
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return s


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def main():
    man = json.loads((ROOT / "data" / "fibras.json").read_text(encoding="utf-8"))
    pre = json.loads((ROOT / "data" / "fibras_precios.json").read_text(encoding="utf-8"))
    precios = pre.get("precios") or {}
    act = pre.get("actualizado") or man.get("actualizado_distribuciones") or ""
    rows = []
    for f in man.get("fibras") or []:
        p = precios.get(f["clave"]) or {}
        precio, fprecio = p.get("precio"), p.get("fecha")
        aviso_p = p.get("aviso") or (p.get("error") if p.get("obsoleto") else "")
        dist, fdist = f.get("dist"), f.get("fuente_dist")
        if f.get("estado") == "deslistada":
            dist_cell = "No aplica (deslistada)"
        elif dist is None:
            dist_cell = "por confirmar"
        elif fdist:
            dist_cell = f'<a href="{esc(fdist)}">{mxn(dist, 4)}</a>'
        else:
            dist_cell = mxn(dist, 4)
        periodo = esc(f.get("periodo") or "—")
        yld = pct(p.get("yield_12m"))
        nav = f.get("nav")
        prima = None
        if isinstance(precio, (int, float)) and isinstance(nav, (int, float)) and nav:
            prima = (precio / nav - 1) * 100
        if nav is None:
            nav_cell = "por confirmar"
        else:
            nav_cell = mxn(nav, 2) + (f" ({fecha(f.get('fecha_nav'))})" if f.get("fecha_nav") else "")
            if prima is not None:
                nav_cell += f"; prima/desc. {pct(prima)}"
        precio_cell = "—" if f.get("estado") == "deslistada" else (mxn(precio) if precio is not None else "por confirmar")
        if fprecio and f.get("estado") != "deslistada":
            precio_cell += f" ({fecha(fprecio)})"
        if aviso_p:
            precio_cell += " *"
        nombre = esc(f.get("nombre") or "")
        clave = esc(f["clave"])
        rows.append(
            f"<tr><td>{nombre}<br><small>{clave}</small></td>"
            f"<td>{precio_cell}</td>"
            f"<td>{dist_cell}</td>"
            f"<td>{periodo}</td>"
            f"<td>{yld}</td>"
            f"<td>{nav_cell}</td></tr>"
        )
    html = []
    html.append("<!-- TABLA-FIBRAS:INICIO -->")
    html.append(f'<p><strong>Fecha de actualización:</strong> {esc(fecha(act))} (hora de la Ciudad de México).</p>')
    html.append('<figure class="wp-block-table"><table>')
    html.append("<thead><tr><th>FIBRA</th><th>Precio (fecha)</th><th>Última distribución por CBFI</th><th>Periodo</th><th>Rendimiento bruto 12 meses</th><th>NAV y prima/descuento</th></tr></thead>")
    html.append("<tbody>")
    html.extend(rows)
    html.append("</tbody></table></figure>")
    html.append("<!-- TABLA-FIBRAS:FIN -->")
    print("\n".join(html))


if __name__ == "__main__":
    main()
