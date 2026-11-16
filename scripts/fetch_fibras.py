#!/usr/bin/env python3
"""Actualiza data/fibras_precios.json con Yahoo Finance (yfinance).

Precio, variación diaria, rango de 52 semanas, historial ~5 años, capitalización
(si hay títulos en data/fibras.json) y rendimiento bruto a 12 meses
(suma de distribuciones reportadas por Yahoo en 365 días / último precio).

Si un ticker falla, conserva el último valor bueno, marca la fecha del error
y no interrumpe el resto ni el workflow (siempre termina con código 0).
"""
from __future__ import annotations
import json, traceback
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "data" / "fibras.json"
OUT = ROOT / "data" / "fibras_precios.json"
TZ = ZoneInfo("America/Mexico_City")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def weekly_closes(hist):
    """Una observación por semana (último cierre) para la gráfica de 5 años."""
    if hist is None or len(hist) == 0:
        return []
    s = hist["Close"].copy()
    s.index = s.index.tz_localize(None) if getattr(s.index, "tz", None) is not None else s.index
    w = s.resample("W").last().dropna()
    out = []
    for d, v in w.items():
        try:
            out.append([d.date().isoformat(), round(float(v), 4)])
        except Exception:
            continue
    return out


def main():
    hoy = datetime.now(TZ)
    manual = load_json(MANUAL, {"fibras": []})
    prev = load_json(OUT, {"precios": {}})
    precios_prev = prev.get("precios") if isinstance(prev, dict) else {}
    if not isinstance(precios_prev, dict):
        precios_prev = {}

    try:
        import yfinance as yf
    except Exception as e:
        print("No se pudo importar yfinance:", e)
        # Conserva el archivo previo y marca un aviso global
        if isinstance(prev, dict):
            prev["error_global"] = f"{hoy.date().isoformat()}: no se pudo importar yfinance ({e})"
            prev["actualizado"] = prev.get("actualizado") or hoy.date().isoformat()
            OUT.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    out = {
        "actualizado": hoy.date().isoformat(),
        "actualizado_hora": hoy.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "Yahoo Finance (yfinance). Precios no oficiales y pueden ir con retraso.",
        "precios": {},
    }

    for f in manual.get("fibras") or []:
        clave = f.get("clave")
        if not clave:
            continue
        if f.get("estado") == "deslistada":
            out["precios"][clave] = {
                "precio": None,
                "fecha": None,
                "omitido": "deslistada",
            }
            continue
        ticker = f.get("ticker_yahoo")
        anterior = precios_prev.get(clave) if isinstance(precios_prev.get(clave), dict) else {}
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="5y", auto_adjust=False)
            if hist is None or len(hist) == 0:
                raise RuntimeError("Yahoo no devolvió historial")
            hist = hist.dropna(subset=["Close"])
            if len(hist) == 0:
                raise RuntimeError("Historial sin cierres")
            last = hist.iloc[-1]
            fecha = hist.index[-1]
            fecha_s = fecha.date().isoformat()
            precio = round(float(last["Close"]), 4)
            vol = int(last["Volume"]) if "Volume" in last and last["Volume"] == last["Volume"] else 0
            cambio = None
            if len(hist) >= 2:
                prev_c = float(hist["Close"].iloc[-2])
                if prev_c:
                    cambio = round((precio / prev_c - 1) * 100, 2)
            un_anio = hist[hist.index >= (fecha - timedelta(days=370))]
            min_52 = round(float(un_anio["Low"].min() if "Low" in un_anio else un_anio["Close"].min()), 4) if len(un_anio) else None
            max_52 = round(float(un_anio["High"].max() if "High" in un_anio else un_anio["Close"].max()), 4) if len(un_anio) else None
            # Rendimiento bruto 12 meses con dividendos de Yahoo
            yield_12m = None
            try:
                divs = tk.dividends
                if divs is not None and len(divs) and precio:
                    corte = fecha.tz_localize(None) if getattr(fecha, "tzinfo", None) else fecha
                    d = divs.copy()
                    d.index = d.index.tz_localize(None) if getattr(d.index, "tz", None) is not None else d.index
                    suma = float(d[d.index >= (corte - timedelta(days=365))].sum())
                    yield_12m = round(suma / precio * 100, 2)
            except Exception as de:
                print(clave, "dividendos:", de)
            cap = None
            titulos = f.get("titulos")
            if isinstance(titulos, (int, float)) and titulos and precio:
                cap = round(precio * float(titulos), 2)
            # Volumen 0 en las últimas sesiones: el precio puede estar congelado
            cola = hist.tail(10)
            vol_cero = bool("Volume" in cola and (cola["Volume"].fillna(0) == 0).all())
            fila = {
                "ticker": ticker,
                "precio": precio,
                "fecha": fecha_s,
                "cambio_pct": cambio,
                "min_52s": min_52,
                "max_52s": max_52,
                "volumen": vol,
                "yield_12m": yield_12m,
                "capitalizacion": cap,
                "historico": weekly_closes(hist),
                "error": None,
                "obsoleto": False,
            }
            if vol_cero:
                fila["aviso"] = "Yahoo Finance no reporta operaciones recientes (volumen 0); el precio puede estar desactualizado."
            out["precios"][clave] = fila
            print(clave, fecha_s, precio, "yield", yield_12m, "vol0" if vol_cero else "")
        except Exception as e:
            print(clave, "ERROR", type(e).__name__, e)
            traceback.print_exc()
            if anterior and anterior.get("precio") is not None:
                conservado = dict(anterior)
                conservado["error"] = f"{hoy.date().isoformat()}: {e}"
                conservado["obsoleto"] = True
                out["precios"][clave] = conservado
            else:
                out["precios"][clave] = {
                    "precio": None,
                    "fecha": None,
                    "error": f"{hoy.date().isoformat()}: {e}",
                    "obsoleto": True,
                }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
