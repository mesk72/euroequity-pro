import os, requests
import yfinance as yf

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type": "application/json", "Prefer": "return=minimal"}

# Cerca per nome — BR privati potrebbero non essere su Yahoo
# SEHK, TSE, LSE invece sì
CANDIDATES = {
    # BR — cerca per nome su .BR (Euronext Brussels)
    "001062148": ("SNCB SA",                          "BR",   ["SNCB.BR"]),
    "002278082": ("vdk bank nv",                      "BR",   ["VDK.BR"]),
    "009915016": ("Total Petrochemicals Refining",    "BR",   ["TPRF.BR","TPC.BR"]),
    "017250539": ("BNP Paribas Fortis",               "BR",   ["BNPP.BR","BNP.BR"]),
    "094124352": ("Aliaxis SA",                       "BR",   ["ALIAXIS.BR","ALX.BR"]),
    "094124453": ("Etex NV",                          "BR",   ["ETEX.BR","ETX.BR"]),
    "094426466": ("Sibelco NV",                       "BR",   ["SIBELCO.BR","SBC.BR"]),
    "626591203": ("Infrabel SA",                      "BR",   ["INFRABEL.BR"]),
    # SEHK — cerca con zero-padding .HK
    "901":       ("Shenzhen SDMC Technology",         "SEHK", ["0901.HK","901.HK"]),
    "2066":      ("Shengjing Bank",                   "SEHK", ["2066.HK"]),
    "2627":      ("Ab&B Bio-Tech",                    "SEHK", ["2627.HK"]),
    # TSE
    "8303":      ("SBI Shinsei Bank",                 "TSE",  ["8303.T"]),
    "581A":      ("GO Inc",                           "TSE",  ["581A.T","9275.T"]),
    # LSE
    "UU.":       ("United Utilities Group",           "LSE",  ["UU.L"]),
}

print(f"{'Ticker':<15} {'Exchange':<8} {'Company':<35} {'Yahoo':<12} {'Prezzo':<10} {'Data'}")
print("-" * 85)

found = []
for ticker, (company, exchange, candidates) in CANDIDATES.items():
    best_yt = None
    best_price = None
    best_date = None

    for yt in candidates:
        try:
            data = yf.download(yt, period="5d", interval="1d",
                               auto_adjust=True, progress=False)
            if not data.empty and len(data) > 0:
                price = float(data["Close"].iloc[-1])
                date = data.index[-1].strftime("%Y-%m-%d")
                if price > 0:
                    best_yt = yt
                    best_price = price
                    best_date = date
                    break
        except:
            pass

    if best_yt:
        print(f"{ticker:<15} {exchange:<8} {company[:33]:<35} {best_yt:<12} {best_price:<10.2f} {best_date}")
        found.append((ticker, exchange, best_yt))
    else:
        print(f"{ticker:<15} {exchange:<8} {company[:33]:<35} {'NOT FOUND':<12} — privato o delisted")

print(f"\nTrovati: {len(found)} / {len(CANDIDATES)}")

if found:
    print("\nAggiornamento yahoo_ticker nel DB...")
    for ticker, exchange, yt in found:
        r = requests.patch(
            SUPABASE_URL + "/rest/v1/stocks",
            headers=headers_up,
            params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
            json={"yahoo_ticker": yt}
        )
        print(f"  {exchange} {ticker} → {yt}: HTTP {r.status_code}")
