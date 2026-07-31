import yfinance as yf, pandas as pd, time
titoli = [
 ("MBH3","Maschinenfabrik Berthold Hermle"),
 ("SPB","Sedlmayr Grund und Immobilien"),
 ("EUK3","EUROKAI"),
 ("BFV","Berliner Effektengesellschaft"),
 ("PHH2","Paul Hartmann"),
 ("HG1","HOMAG Group"),
 ("WBAH","Wild Bunch"),
 ("SIM0","SIMONA"),
 ("LEC","Lechwerke"),
 ("T2G","Tradegate"),
 ("MNV6","Mainova"),
 ("SSH","Suedwestdeutsche Salzwerke"),
 ("NLM","FRoSTA"),
]
# .DE = Xetra (quella che usiamo ora), poi le altre piazze tedesche
suffissi = [(".DE","Xetra"),(".F","Francoforte"),(".MU","Monaco"),
            (".SG","Stoccarda"),(".BE","Berlino"),(".HM","Amburgo"),(".DU","Dusseldorf")]

for tk, nome in titoli:
    trovato = []
    for suf, piazza in suffissi:
        try:
            df = yf.download(tk+suf, period="8d", interval="1d",
                             auto_adjust=True, progress=False)
            if df.empty: continue
            cl = df["Close"]
            if isinstance(cl, pd.DataFrame): cl = cl.iloc[:,0]
            cl = cl.dropna()
            if len(cl)==0: continue
            trovato.append("%s%s (%s) ultima %s = %.2f" %
                (tk, suf, piazza, cl.index[-1].strftime("%d/%m"), float(cl.iloc[-1])))
        except Exception:
            pass
        time.sleep(0.3)
    print("\n%-6s %s" % (tk, nome))
    if trovato:
        for t in trovato: print("    TROVATO: " + t)
    else:
        print("    nessuna piazza tedesca ha dati -> probabile delisting reale")
