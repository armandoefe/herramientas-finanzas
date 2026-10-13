#!/usr/bin/env python3
"""Rendimiento acumulado 10 años (base 100), mensual, en MXN. Fuentes: Yahoo Finance (yfinance) y Banxico SIE.
Udibono: aproximación por acarreo = variación UDI (SP68257) + tasa real de subasta Udibono 10a (SF43924) devengada mensual; no incluye cambios de precio."""
import os, json, datetime as dt, urllib.request
import pandas as pd, yfinance as yf
fin = pd.Timestamp.today().normalize(); ini = fin - pd.DateOffset(years=10)
def yh(t, adj):
    s = yf.Ticker(t).history(start=ini - pd.DateOffset(days=40), end=fin + pd.DateOffset(days=1), auto_adjust=adj)["Close"]
    s.index = s.index.tz_localize(None); return s.resample("ME").last().ffill()
def bmx(sid):
    u = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{sid}/datos/{(ini-pd.DateOffset(days=40)).date()}/{fin.date()}"
    r = urllib.request.Request(u, headers={"Bmx-Token": os.environ["BANXICO_TOKEN"], "Accept": "application/json"})
    d = json.load(urllib.request.urlopen(r, timeout=60))["bmx"]["series"][0]["datos"]
    s = pd.Series({pd.to_datetime(x["fecha"], dayfirst=True): float(x["dato"].replace(",", "")) for x in d if x["dato"] not in ("N/E", "")})
    return s.resample("ME").last().ffill()
fx = yh("MXN=X", False)
spx, mxx, gold = yh("^GSPC", False), yh("^MXX", False), yh("GC=F", False)
fib = None
for t in ["FIBRATC14.MX", "FIBRATC.MX"]:
    try:
        h = yf.Ticker(t).history(period="max", auto_adjust=False)
        if len(h): fib_t = t; break
    except Exception as e: print(t, e)
h.index = h.index.tz_localize(None)
div = h["Dividends"][h["Dividends"] > 0]
print("FIBRATC", fib_t, "inicio", h.index[0].date(), "filas", len(h), "distribuciones", len(div), div.tail(8).to_dict())
fib_inicio = h.index[0]
fib = h["Adj Close"].resample("ME").last().ffill()
cl = h["Close"].resample("ME").last().ffill()
print("Adj/Close ratio inicio", float(fib[fib.index>=ini].iloc[0]/cl[cl.index>=ini].iloc[0]))
if fib_inicio > ini: ini = fib_inicio
udi, yr = bmx("SP68257"), bmx("SF43924").ffill()
idx = spx.index[spx.index >= ini]
ultimo = min(fin, yf.Ticker("^GSPC").history(period="10d").index[-1].tz_localize(None).normalize())
def base(s): s = s.reindex(idx).ffill(); return (s / s.iloc[0] * 100)
fibr = fib
u = udi.reindex(idx).ffill(); y = yr.reindex(idx).ffill()
udib = ((u / u.shift(1)).fillna(1) * (1 + y.shift(1).fillna(y.iloc[0]) / 100 / 12)).cumprod() * 100
S = {"S&P 500 (MXN)": base(spx * fx), "S&P/BMV IPC": base(mxx), "FIBRATC (ETF FIBRAs)": base(fibr),
     "Oro (MXN)": base(gold * fx), "Udibono 10a (aprox.)": base(udib),
     "S&P 500 (USD)": base(spx), "Oro (USD)": base(gold)}
yrs = (ultimo - idx[0]).days / 365.25
out = {"fibratc": {"ticker": fib_t, "inicio": str(fib_inicio.date()), "distribuciones": len(div)}, "actualizado": str(fin.date()), "inicio": str(idx[0].date()), "fin": str(ultimo.date()), "fechas": [str(d.date()) for d in idx],
       "series": {k: [round(float(x), 2) for x in v] for k, v in S.items()},
       "resumen": {k: {"acumulado": round(float(v.iloc[-1] - 100), 1), "anual": round(float((v.iloc[-1] / 100) ** (1 / yrs) - 1) * 100, 1)} for k, v in S.items()}}
json.dump(out, open("data/comparativo.json", "w"), ensure_ascii=False)
print(json.dumps(out["resumen"], ensure_ascii=False, indent=1), out["inicio"], out["fin"])
