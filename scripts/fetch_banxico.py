#!/usr/bin/env python3
"""CETES 28d (SF43936) e inflación anual INPC (SP30578; respaldo: INPC SP1 con incremento=PorcAnual) del SIE de Banxico.
Uso: BANXICO_TOKEN=... python3 scripts/fetch_banxico.py -> data/banxico.json"""
import os, json, sys, urllib.request, datetime as dt
tok = os.environ.get("BANXICO_TOKEN") or sys.exit("Falta BANXICO_TOKEN")
ini = os.environ.get("DESDE", "2016-01-01"); fin = dt.date.today().isoformat()
def get(sid, q=""):
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{sid}/datos/{ini}/{fin}{q}"
    r = urllib.request.Request(url, headers={"Bmx-Token": tok, "Accept": "application/json"})
    s = json.load(urllib.request.urlopen(r, timeout=60))["bmx"]["series"][0]
    out = []
    for d in s.get("datos", []):
        if d["dato"] in ("N/E", ""): continue
        dd, mm, yy = d["fecha"].split("/"); out.append([f"{yy}-{mm}-{dd}", round(float(d["dato"].replace(",", "")), 2)])
    print(sid, s.get("titulo"), len(out), out[-1] if out else None); return out
cetes = get("SF43936"); inf_id = "SP30578"
try: inf = get("SP30578")
except Exception as e: print("SP30578 error", e); inf = []
if not inf: inf_id = "SP1 (PorcAnual)"; inf = get("SP1", "?incremento=PorcAnual")
if not cetes or not inf: sys.exit("Sin datos")
json.dump({"MUESTRA": False, "actualizado": fin, "fuente": "Banxico SIE API", "serie_inflacion": inf_id,
           "cetes28": cetes, "inflacion": inf}, open("data/banxico.json", "w"), ensure_ascii=False)
