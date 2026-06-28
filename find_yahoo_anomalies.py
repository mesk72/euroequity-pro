import os, requests
import yfinance as yf

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type": "application/json", "Prefer": "return=minimal"}

# Ticker anomali da verificare su Yahoo Finance
# BR: privati — quasi certamente non quotati su Yahoo
# SEHK: zero-pad 4 cifre + .HK
# TSE: numero + .T
# LSE: ticker senza punto finale + .L

CANDIDATES = {
    # BR — privati, probabilmente non quotati
    "001062148": ["BE0974282148.BR"],  # prova con ISIN
    "002278082": ["BE0003593044.BR"],
    "009915016": ["BE0974293251.BR"],
    "017250539": ["BE0974276082.BR"],
    "094124352": ["BE0003764785.BR"],
    "094124453": ["FR0000021842.BR"],
    "094426466": ["BE0974264930.BR"],
    "626591203": ["BE0974268972.BR"],
    # SEHK
    "901":  ["0901.HK"],
    "2066": ["2066.HK"],
    "2627": ["2627.HK"],
    # TSE
    "8303": ["8303.T"],
    "581A": ["581A.T", "581A.TYO"],
    # LSE
    "UU.":  ["UU.L"],
}

EXCHANGES = {
    "001062148": "BR", "002278082": "BR", "009915016": "BR", "017250539": "BR",
    "094124352": "BR", "094124453": "BR", "094426466": "BR", "626591203": "BR",
    "901": "SEHK", "2066": "SEHK", "2627": "SEHK",
    "8303": "TSE", "581A": "TSE",
    "UU.": "LSE",
}

print(f"Ricerca ticker Yahoo per titoli anomali...")
print(f"{'Ticker':<15} {'Exchange':<8} {'Yahoo Ticker':<15} {'Ultimo Prezzo':<15} {'Data'}")
print("-" * 65)

found = []
for ticker, yahoo_candidates in CANDIDATES.items():
    exchange = EXCHANGES[ticker]
    best_yt = None
    best_price = None
    best_date = None

    for yt in yahoo_candidates:
        try:
            data = yf.download(yt, period="5d", interval="1d",
                               auto_adjust=True, progress=False)
            if not data.empty:
                last_row = data.iloc[-1]
                price = float(last_row["Close"])
                date = data.index[-1].strftime("%Y-%m-%d")
                if price > 0:
                    best_yt = yt
                    best_price = price
                    best_date = date
                    break
        except:
            pass

    if best_yt:
        print(f"{ticker:<15} {exchange:<8} {best_yt:<15} {best_price:<15.2f} {best_date}")
        found.append((ticker, exchange, best_yt))
    else:
        print(f"{ticker:<15} {exchange:<8} {'NOT FOUND':<15} -")

print(f"\nTrovati: {len(found)} / {len(CANDIDATES)}")

# Aggiorna yahoo_ticker nel DB per quelli trovati
if found:
    print("\nAggiornamento DB...")
    for ticker, exchange, yt in found:
        r = requests.patch(
            SUPABASE_URL + "/rest/v1/stocks",
            headers=headers_up,
            params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
            json={"yahoo_ticker": yt}
        )
        print(f"  {exchange} {ticker} → {yt}: HTTP {r.status_code}")
