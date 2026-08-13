import requests, re
print("=== I link nel sito puntano alla versione inglese? ===")
for tk in ["SBUX-US","MAR-US","AAPL-US"]:
    r=requests.get("https://forwardalpha.pro/stock/"+tk,timeout=60)
    h=r.text
    ana=re.findall(r'https://finance\.yahoo\.com/quote/[^"\\]*?/analysis[^"\\]*', h)
    print("  %-9s %s" % (tk, ana[0] if ana else "link non trovato nell'HTML iniziale"))
print()
print("=== Yahoo risponde in inglese con hl=en-US? ===")
for u in ["https://finance.yahoo.com/quote/SBUX/analysis/?p=SBUX&hl=en-US&guccounter=1",
          "https://finance.yahoo.com/quote/MAR/analysis/?p=MAR&hl=en-US&guccounter=1"]:
    try:
        r=requests.get(u,timeout=45,headers={"User-Agent":"Mozilla/5.0"})
        h=r.text
        eng=sum(1 for k in ["Earnings Estimate","Revenue Estimate","Growth Estimates","Analyst Price Targets"] if k in h)
        ita=sum(1 for k in ["Stima utili","Stima ricavi","Stime di crescita","Obiettivi di prezzo"] if k in h)
        print("  %s -> HTTP %s | segnali inglese: %d | italiano: %d" % (u.split('/quote/')[1][:22], r.status_code, eng, ita))
    except Exception as e:
        print("  errore:", str(e)[:60])
