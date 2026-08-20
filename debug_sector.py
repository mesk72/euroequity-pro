#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RICARICO FONDAMENTALI DA TIKR — 18/8/2026

Motivo: 756 titoli europei avevano P/E, P/E prospettico e P/B divergenti da
TIKR, che e' la fonte del progetto. Due difetti distinti:

  1) Valori moltiplicati per 100 su 351 titoli (Oslo 146, Madrid 86,
     Helsinki 58, Copenaghen 49, Bruxelles 10, Amsterdam 2). Esempio:
     Kraft Bank con P/B 107 invece di 1,06, Foamit con P/E 3926 invece di
     39,62. Il Value Score di questi titoli era completamente falsato:
     una societa' economica veniva classificata fra le piu' care.

  2) P/E calcolati internamente dove TIKR dice esplicitamente "non
     significativo" (utili negativi). Syensqo -127, Outokumpu -18,96.
     Un multiplo privo di senso non deve entrare nei percentili.

Cosa fa: riscrive pe_trailing, pe_forward, pb, eps_growth, rev_growth
prendendoli da TIKR con le STESSE formule di weekly_eu.py — nessuna
formula nuova, nessuna trasformazione. I momentum restano quelli di
Yahoo, che sono corretti.
"""

import csv
import io
import os
from datetime import datetime, timedelta

import requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

TODAY_DT = datetime.now()

# Primary Exchange di TIKR -> exchange nostro
MAP_EX = {"BIT": "MIL", "XTRA": "XETRA", "ENXTPA": "PA", "ENXTAM": "AS",
          "BME": "MC", "ENXTBR": "BR", "ENXTLS": "LS", "WBAG": "VI",
          "HLSE": "HE", "ISE": "IR", "ATSE": "GR", "LSE": "LSE",
          "SWX": "SWX", "OM": "OM", "OB": "OB", "CPSE": "CPSE"}


def parse_num(v):
    """Identica a weekly_eu.py: TIKR usa $, MM, virgole, x, %."""
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "NM", "NA", "n/a", "NaN", "—"):
        return None
    s = s.replace("$", "").replace("x", "").replace("%", "")
    for suf in ("USDMM", "EURMM", "MM", "bn"):
        s = s.replace(suf, "")
    s = s.replace(",", "").strip()
    try:
        return float(s)
    except Exception:
        return None


# ── date di chiusura esercizio, per la calendarizzazione ─────
fy_map = {}
try:
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/fiscal_year_end.csv",
                     headers=headers_r, timeout=180)
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8", errors="replace"))):
        t = (row.get("ticker") or row.get("Ticker") or "").strip()
        e = (row.get("exchange") or row.get("Exchange") or "").strip()
        m = row.get("fy_end_month") or row.get("month") or row.get("fiscal_year_end")
        try:
            fy_map[(t, e)] = int(float(str(m).strip()))
        except Exception:
            pass
    print("Date di chiusura esercizio caricate: %d" % len(fy_map))
except Exception as e:
    print("fiscal_year_end non leggibile (%s): uso dicembre come predefinito" % str(e)[:60])


def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)


def calendarize(ticker, exchange, fy2025, fy2026, fy2027, fy2028, today_dt):
    """COPIA ESATTA della funzione di weekly_eu.py — nessuna modifica."""
    if fy2025 is None and fy2026 is None:
        return None, None, True
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm == 2 else 30 if fm in [4, 6, 9, 11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year - 1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        fy_end = datetime(fy_end.year - 1, fm, last_day)
        pub_date = fy_end + timedelta(days=60)
    if fy_end.year >= 2026:
        v0, v1, v2 = fy2026, fy2027, fy2028
    else:
        v0, v1, v2 = fy2025, fy2026, fy2027
    next_pub = datetime(pub_date.year + 1, pub_date.month, pub_date.day)
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next
    ltm = w_curr * v0 + w_next * v1 if v0 is not None and v1 is not None else None
    ntm = w_curr * v1 + w_next * v2 if v1 is not None and v2 is not None else None
    return ltm, ntm, False


def carica_tikr(nome_file, solo_us=False):
    righe = []
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/" + nome_file,
                     headers=headers_r, timeout=300)
    if r.status_code != 200:
        print("  %s: HTTP %s" % (nome_file, r.status_code))
        return righe
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8", errors="replace"))):
        t = (row.get("Ticker") or "").strip()
        px = (row.get("Primary Exchange") or "").strip()
        if not t:
            continue
        ex = "US" if solo_us else MAP_EX.get(px)
        if not ex:
            continue
        righe.append((t, ex, row))
    print("  %s: %d righe utilizzabili" % (nome_file, len(righe)))
    return righe


print("\nLettura file TIKR...")
tutte = carica_tikr("tikr_eu_latest.csv") + carica_tikr("tikr_na_latest.csv", solo_us=True)
print("Totale: %d\n" % len(tutte))

aggiornamenti = []
senza_pe = 0
for ticker, exchange, row in tutte:
    pe = parse_num(row.get("LTM P/E LTM"))
    pef = parse_num(row.get("Mean Fwd P/E NTM"))
    pb = parse_num(row.get("LTM P/BVPS LTM"))
    if pe is None:
        senza_pe += 1

    eps25 = parse_num(row.get("EPS Normalized (FY 2025)"))
    eps26 = parse_num(row.get("Mean EPS Normalized (FY 2026)"))
    eps27 = parse_num(row.get("Mean EPS Normalized (FY 2027)"))
    eps28 = parse_num(row.get("Mean EPS Normalized (FY 2028)"))
    rev25 = parse_num(row.get("Rev (FY 2025)"))
    rev26 = parse_num(row.get("Mean Rev (FY 2026)"))
    rev27 = parse_num(row.get("Mean Rev (FY 2027)"))
    rev28 = parse_num(row.get("Mean Rev (FY 2028)"))

    eps_ltm, eps_ntm, _ = calendarize(ticker, exchange, eps25, eps26, eps27, eps28, TODAY_DT)
    rev_ltm, rev_ntm, _ = calendarize(ticker, exchange, rev25, rev26, rev27, rev28, TODAY_DT)

    eps_growth = (eps_ntm / abs(eps_ltm) - 1) if eps_ntm is not None and eps_ltm else None
    rev_growth = (rev_ntm / abs(rev_ltm) - 1) if rev_ntm is not None and rev_ltm else None

    aggiornamenti.append({
        "ticker": ticker,
        "exchange": exchange,
        "pe_trailing": pe,
        "pe_forward": pef,
        "pb": pb,
        "eps_growth": round(eps_growth, 6) if eps_growth is not None else None,
        "rev_growth": round(rev_growth, 6) if rev_growth is not None else None,
        "mkt_cap": parse_num(row.get("Last Mkt Cap")),
    })

print("Righe da scrivere: %d (di cui %d senza P/E perche' TIKR lo considera non significativo)"
      % (len(aggiornamenti), senza_pe))

ok = 0
for i in range(0, len(aggiornamenti), 200):
    lotto = aggiornamenti[i:i + 200]
    w = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                      headers=headers_up, json=lotto, timeout=120)
    if w.status_code in (200, 201, 204):
        ok += len(lotto)
    else:
        print("  ERRORE HTTP %s: %s" % (w.status_code, w.text[:200]))
print("\nSCRITTI: %d titoli" % ok)

print("\n=== verifica su titoli noti ===")
for tk, ex in [("KRAB", "OB"), ("FOAMIT", "HE"), ("OLE", "MC"),
               ("CARL B", "CPSE"), ("ASML", "AS"), ("ISP", "MIL")]:
    v = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
                     params={"select": "pe_trailing,pe_forward,pb,eps_growth,rev_growth",
                             "ticker": "eq." + tk, "exchange": "eq." + ex},
                     timeout=60).json()
    print("  %-9s %-5s %s" % (tk, ex, v[0] if v else "assente"))
