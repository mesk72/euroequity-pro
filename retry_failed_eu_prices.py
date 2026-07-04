import os, time, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"

TODAY   = datetime.now().strftime("%Y-%m-%d")
FROM_5Y = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EU_EXCHANGES = ["MIL", "LSE", "XETRA", "PA", "OM", "SWX", "AS", "MC", "BR",
                "HE", "CPSE", "OB", "GR", "VI", "IR", "LS"]

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}

LEEWAY_SUFFIX = {
    "MIL":  ".MI",    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":   ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":   ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":   ".IR",    "AT":    ".VI",     "GR":   ".AT",
    "LSE":  ".LSE",   "AIM":   ".AIM",   "SWX":  ".SW",
    "OM":   ".ST",    "NGM":   ".ST",    "OB":   ".OL",
    "CPSE": ".CO",
    "US":   ".US",    "TSX":   ".TO",
    "TSE":  ".TSE",   "ASX":   ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    ticker_clean = ticker.rstrip(".")
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")

print("=" * 60)
print(f"TROVA E RIPARA TITOLI EU SENZA STORICO — {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO EU ────────────────────────────────────
print("\n[1/3] Caricamento universo EU...")
all_stocks = []
for exchange in EU_EXCHANGES:
    offset = 0
    while True:
        try:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker,exchange", "in_universe": "eq.true",
                        "exchange": f"eq.{exchange}", "offset": str(offset), "limit": "1000"},
                timeout=20)
            data = r.json()
        except Exception as e:
            print(f"  WARN lettura universo {exchange}: {e}")
            break
        if not isinstance(data, list) or not data: break
        all_stocks.extend(data)
        offset += 1000
        if len(data) < 1000: break
print(f"  Universo EU: {len(all_stocks)} titoli")

# ── 2. TROVA CHI HA POCHI/NESSUN PREZZO ──────────────────────
print("\n[2/3] Controllo copertura prezzi per ogni titolo...")
SOGLIA_MINIMA_RIGHE = 50  # sotto questa soglia consideriamo il titolo "fallito"
senza_prezzi = []
for i, stock in enumerate(all_stocks):
    ticker = stock["ticker"]; exchange = stock["exchange"]
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod",
            headers={**headers_r, "Prefer": "count=exact"},
            params={"select": "date", "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}",
                    "limit": "1"},
            timeout=15)
        count = int(r.headers.get("content-range", "0/0").split("/")[-1])
    except Exception as e:
        print(f"  WARN controllo {ticker}.{exchange}: {e}")
        count = 0
    if count < SOGLIA_MINIMA_RIGHE:
        senza_prezzi.append((ticker, exchange, count))
    if (i + 1) % 300 == 0:
        print(f"    ... controllati {i+1}/{len(all_stocks)}")
    time.sleep(0.05)

print(f"\n  Titoli con meno di {SOGLIA_MINIMA_RIGHE} righe di prezzo: {len(senza_prezzi)}")
for t, e, c in senza_prezzi[:200]:
    print(f"    {t}.{e}: {c} righe")

# ── 3. RITENTA IL DOWNLOAD CON DIAGNOSTICA COMPLETA ──────────
print(f"\n[3/3] Ritento il download per {len(senza_prezzi)} titoli, con motivo esatto del fallimento...")
esiti = {}  # motivo -> count
ok = 0
for ticker, exchange, old_count in senza_prezzi:
    # Per la Germania, se .XETRA non trova nulla, ritenta con .F (confermato
    # funzionante da verifica manuale su Leeway per i titoli minori/meno liquidi)
    candidati = [leeway_ticker(ticker, exchange)]
    if exchange == "XETRA":
        candidati.append(ticker.rstrip(".") + ".F")

    trovato = False
    for tentativo, lt in enumerate(candidati):
        url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
        try:
            resp = requests.get(url, timeout=20)
        except Exception as e:
            motivo = f"eccezione rete: {type(e).__name__}"
            if tentativo == len(candidati) - 1:
                esiti[motivo] = esiti.get(motivo, 0) + 1
                print(f"    {ticker}.{exchange} (leeway={lt}): {motivo}")
            continue

        if resp.status_code != 200:
            motivo = f"HTTP {resp.status_code}"
            if tentativo == len(candidati) - 1:
                esiti[motivo] = esiti.get(motivo, 0) + 1
                print(f"    {ticker}.{exchange} (leeway={lt}): {motivo} — {resp.text[:120]}")
            continue

        try:
            data_l = resp.json()
        except Exception:
            motivo = "risposta non JSON"
            if tentativo == len(candidati) - 1:
                esiti[motivo] = esiti.get(motivo, 0) + 1
                print(f"    {ticker}.{exchange} (leeway={lt}): {motivo} — {resp.text[:120]}")
            continue

        if not isinstance(data_l, list) or not data_l:
            motivo = "risposta vuota (ticker non trovato su Leeway con questo formato)"
            if tentativo == len(candidati) - 1:
                esiti[motivo] = esiti.get(motivo, 0) + 1
                print(f"    {ticker}.{exchange} (leeway={lt}): {motivo}")
            continue

        rows = []
        for row in data_l:
            adj = row.get("adjusted_close") or row.get("close")
            if adj is None: continue
            rows.append({"ticker": ticker, "exchange": exchange,
                          "date": row["date"], "adj_close": float(adj)})
        if not rows:
            motivo = "righe ricevute ma tutte senza prezzo valido"
            if tentativo == len(candidati) - 1:
                esiti[motivo] = esiti.get(motivo, 0) + 1
                print(f"    {ticker}.{exchange} (leeway={lt}): {motivo}")
            continue

        requests.delete(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up,
            params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})
        for j in range(0, len(rows), 500):
            requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=rows[j:j+500])
        ok += 1
        suffisso_usato = lt.split(".")[-1]
        print(f"    {ticker}.{exchange} (leeway={lt}): OK ({suffisso_usato}), {len(rows)} righe salvate")
        trovato = True
        break
    time.sleep(0.4)

print("\n" + "=" * 60)
print(f"RIPARATI: {ok}/{len(senza_prezzi)}")
print("MOTIVI DI FALLIMENTO RESIDUI:")
for motivo, count in sorted(esiti.items(), key=lambda x: -x[1]):
    print(f"  {motivo}: {count}")
print("=" * 60)
