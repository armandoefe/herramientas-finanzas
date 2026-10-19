#!/usr/bin/env python3
"""Genera datos-del-dia.png (600x700) con FIX (SF43718), CETES 28d (SF43936) e inflación anual (SP30578) de Banxico."""
import os, json, urllib.request, datetime as dt
from zoneinfo import ZoneInfo
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
tok = os.environ["BANXICO_TOKEN"]
u = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718,SF43936,SP30578/datos/oportuno"
r = urllib.request.Request(u, headers={"Bmx-Token": tok, "Accept": "application/json"})
S = {s["idSerie"]: s["datos"][0] for s in json.load(urllib.request.urlopen(r, timeout=60))["bmx"]["series"]}
MES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
def f(d): dd, mm, yy = d.split("/"); return f"{int(dd)} de {MES[int(mm)-1]} de {yy}"
def m(d): _, mm, yy = d.split("/"); return f"{MES[int(mm)-1]} de {yy}"
fix, ce, inf = (float(S[k]["dato"].replace(",", "")) for k in ("SF43718", "SF43936", "SP30578"))
items = [("Tipo de cambio FIX", f"${fix:,.4f}", "pesos por dólar · " + f(S["SF43718"]["fecha"]), "#1565c0"),
         ("CETES 28 días", f"{ce:.2f}%", "subasta del " + f(S["SF43936"]["fecha"]), "#0b6e4f"),
         ("Inflación anual (INPC)", f"{inf:.2f}%", m(S["SP30578"]["fecha"]), "#00838f")]
hoy = dt.datetime.now(ZoneInfo("America/Mexico_City"))
fig = plt.figure(figsize=(6, 7), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 600); ax.set_ylim(0, 700); ax.axis("off")
ax.add_patch(plt.Rectangle((0, 0), 600, 700, color="#f4f8fb"))
ax.add_patch(plt.Rectangle((0, 590), 600, 110, color="#0b6e4f"))
ax.text(300, 655, "Datos del día", color="white", fontsize=28, weight="bold", ha="center", va="center")
ax.text(300, 612, "Finanzas y Tarjetas MX", color="#cfe8dd", fontsize=13, ha="center", va="center")
for i, (t, v, s, c) in enumerate(items):
    y = 430 - i * 150
    ax.add_patch(FancyBboxPatch((40, y), 520, 125, boxstyle="round,pad=0,rounding_size=14", fc="white", ec="#d7e3ec", lw=1.5))
    ax.add_patch(plt.Rectangle((40, y), 10, 125, color=c))
    ax.text(70, y + 98, t, fontsize=14, color="#455a64", va="center")
    ax.text(70, y + 55, v, fontsize=32, weight="bold", color=c, va="center")
    ax.text(70, y + 18, s, fontsize=11, color="#78909c", va="center")
ax.text(300, 55, "Fuente: Banxico (SIE)", fontsize=12, color="#37474f", ha="center")
ax.text(300, 28, "Actualizado: " + f(hoy.strftime("%d/%m/%Y")) + hoy.strftime(", %H:%M") + " hora CDMX", fontsize=11, color="#607d8b", ha="center")
fig.savefig("datos-del-dia.png", dpi=100)
print("FIX", fix, S["SF43718"]["fecha"], "CETES", ce, S["SF43936"]["fecha"], "INF", inf, S["SP30578"]["fecha"])
