#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGGIORNAMENTO AUTOMATICO DEI FONDAMENTALI DA TIKR

Cosa deve fare Andrea: caricare i file CSV su Supabase, nella cartella
`tikr-uploads`, con i nomi di sempre. Nient'altro.

    tikr_eu_latest.csv     Europa
    tikr_na_latest.csv     Nord America
    tikr_apac_latest.csv   Asia-Pacifico

Cosa fa questo programma, da solo, entro un'ora dal caricamento:
  1. si accorge che i file sono nuovi (confronta la data di modifica con
     quella dell'ultima elaborazione)
  2. ricalcola pe_trailing, pe_forward, pb, eps_growth, rev_growth, mkt_cap
     con le formule ufficiali del progetto (calendarizzazione dinamica)
  3. scrive i fondamentali aggiornati
  4. CALCOLA quali titoli entrerebbero o uscirebbero dall'universo, ma NON
     li modifica: li elenca nell'email e aspetta il via libera di Andrea
  5. fa ripartire gli script giornalieri, che rigenerano Value Score,
     Growth Score e Best Score sui dati nuovi
  6. manda l'email con il resoconto

REGOLA: l'universo non viene MAI modificato in automatico. Decisione presa
il 20/8/2026 dopo che titoli validi erano usciti senza che nessuno se ne
accorgesse (Norske Skog, in portafoglio reale, sparita per settimane).
"""

import csv
import io
import os
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage

import requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_json = {**headers_r, "Content-Type": "application/json"}
headers_up = {**headers_json, "Prefer": "resolution=merge-duplicates,return=minimal"}

SMTP_HOST = os.environ.get("SMTP_HOST", "mail.privateemail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
REPORT_TO = os.environ.get("REPORT_TO", "") or "andrea@forwardalpha.pro"

FILE_TIKR = {
    "tikr_eu_latest.csv": "Europa",
    "tikr_na_latest.csv": "Nord America",
    "tikr_apac_latest.csv": "Asia-Pacifico",
}

# Primary Exchange di TIKR -> codice mercato nostro
MAP_EX = {
    # Europa
    "BIT": "MIL", "XTRA": "XETRA", "ENXTPA": "PA", "ENXTAM": "AS", "BME": "MC",
    "ENXTBR": "BR", "ENXTLS": "LS", "WBAG": "VI", "HLSE": "HE", "ISE": "IR",
    "ATSE": "GR", "LSE": "LSE", "SWX": "SWX", "OM": "OM", "OB": "OB", "CPSE": "CPSE",
    # Asia-Pacifico
    "TSE": "TSE", "SEHK": "SEHK", "ASX": "ASX",
    "SGX": "SGX", "Catalist": "SGX",
    "KOSE": "KRX", "KOSDAQ": "KRX",
}
# Nord America: TIKR usa NasdaqGS, NYSE, TSX ecc. Si distingue solo USA/Canada.
MAP_NA = {"TSX": "TSX", "TSXV": "TSX"}

# Soglia in milioni di dollari, per i mercati che ne hanno una.
# Gli altri prendono i primi 100 titoli per capitalizzazione.
SOGLIA_300 = ["MIL", "XETRA", "PA", "LSE", "SWX", "OM", "OB", "CPSE"]
PRIMI_100 = ["BR", "HE", "GR"]

PAROLE_FONDI = ["ETF", "ETP", "FUND", "TRUST", "UCITS", "ISHARES", "VANGUARD",
                "XTRACKERS", "LYXOR", "INVESCO", "SPDR", "WISDOMTREE", "VANECK",
                "BLACKROCK", "SICAV", "ICAV", "MSCI", "INDEX", "AMUNDI",
                "KAPITALFORENINGEN", "INVESTERINGSSELSKABET", "SOCIMI"]


def e_fondo(*nomi):
    return any(any(p in (n or "").upper() for p in PAROLE_FONDI) for n in nomi)


def parse_num(v):
    """Formato TIKR: $370.14MM, 12.5x, 3,4 — con simboli e separatori."""
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


def elenca_file():
    """Data di modifica dei file TIKR nella cartella."""
    try:
        r = requests.post(SUPABASE_URL + "/storage/v1/object/list/tikr-uploads",
                          headers=headers_json,
                          json={"prefix": "", "limit": 100, "offset": 0}, timeout=90)
        return {f["name"]: (f.get("updated_at") or "")[:19] for f in r.json()}
    except Exception:
        return {}


def ultima_elaborazione():
    """Quando sono stati elaborati l'ultima volta, letto da script_logs."""
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/script_logs", headers=headers_r,
                         params={"select": "log_text,created_at",
                                 "script_name": "eq.fondamentali_auto",
                                 "order": "created_at.desc", "limit": "20"}, timeout=60)
        for riga in r.json():
            if (riga.get("log_text") or "").startswith("ELABORATI:"):
                return riga["log_text"][len("ELABORATI:"):].strip()
    except Exception:
        pass
    return ""


def annota(testo):
    try:
        requests.post(SUPABASE_URL + "/rest/v1/script_logs", headers=headers_json,
                      json=[{"script_name": "fondamentali_auto", "log_text": testo}],
                      timeout=30)
    except Exception:
        pass


# ── calendarizzazione: copia esatta di weekly_eu.py ──────────
fy_map = {}
try:
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/fiscal_year_end.csv",
                     headers=headers_r, timeout=200)
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8", errors="replace"))):
        t = (row.get("ticker") or "").strip()
        e = (row.get("exchange") or "").strip()
        try:
            fy_map[(t, e)] = int(float(str(row.get("fiscal_month")).strip()))
        except Exception:
            pass
except Exception:
    pass


def calendarize(ticker, exchange, v2025, v2026, v2027, v2028, oggi):
    if v2025 is None and v2026 is None:
        return None, None
    fm = fy_map.get((ticker, exchange), 12)
    last_day = 28 if fm == 2 else 30 if fm in (4, 6, 9, 11) else 31
    fy_end = datetime(oggi.year, fm, last_day)
    if fy_end > oggi:
        fy_end = datetime(oggi.year - 1, fm, last_day)
    pub = fy_end + timedelta(days=60)
    if pub > oggi:
        fy_end = datetime(fy_end.year - 1, fm, last_day)
        pub = fy_end + timedelta(days=60)
    if fy_end.year >= 2026:
        a, b, c = v2026, v2027, v2028
    else:
        a, b, c = v2025, v2026, v2027
    nxt = datetime(pub.year + 1, pub.month, pub.day)
    w_next = (oggi - pub).days / (nxt - pub).days
    w_curr = 1 - w_next
    ltm = w_curr * a + w_next * b if a is not None and b is not None else None
    ntm = w_curr * b + w_next * c if b is not None and c is not None else None
    return ltm, ntm


def leggi_file(nome):
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/" + nome,
                     headers=headers_r, timeout=400)
    if r.status_code != 200:
        return []
    out = []
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8", errors="replace"))):
        t = (row.get("Ticker") or "").strip()
        px = (row.get("Primary Exchange") or "").strip()
        if not t:
            continue
        if nome == "tikr_na_latest.csv":
            ex = MAP_NA.get(px, "US")
        else:
            ex = MAP_EX.get(px)
        if not ex:
            continue
        out.append((t, ex, row))
    return out


def elabora():
    oggi = datetime.now()
    print("Lettura file TIKR...")
    tutte = []
    conteggi = {}
    for nome, area in FILE_TIKR.items():
        righe = leggi_file(nome)
        conteggi[area] = len(righe)
        tutte += righe
        print("  %-24s %5d righe" % (nome, len(righe)))
    if not tutte:
        return None

    aggiornamenti = []
    for ticker, exchange, row in tutte:
        eps = [parse_num(row.get("EPS Normalized (FY %d)" % y)) if y == 2025
               else parse_num(row.get("Mean EPS Normalized (FY %d)" % y))
               for y in (2025, 2026, 2027, 2028)]
        rev = [parse_num(row.get("Rev (FY %d)" % y)) if y == 2025
               else parse_num(row.get("Mean Rev (FY %d)" % y))
               for y in (2025, 2026, 2027, 2028)]
        eps_ltm, eps_ntm = calendarize(ticker, exchange, *eps, oggi)
        rev_ltm, rev_ntm = calendarize(ticker, exchange, *rev, oggi)
        aggiornamenti.append({
            "ticker": ticker,
            "exchange": exchange,
            "pe_trailing": parse_num(row.get("LTM P/E LTM")),
            "pe_forward": parse_num(row.get("Mean Fwd P/E NTM")),
            "pb": parse_num(row.get("LTM P/BVPS LTM")),
            "eps_growth": round(eps_ntm / abs(eps_ltm) - 1, 6)
                          if eps_ntm is not None and eps_ltm else None,
            "rev_growth": round(rev_ntm / abs(rev_ltm) - 1, 6)
                          if rev_ntm is not None and rev_ltm else None,
            "mkt_cap": parse_num(row.get("Last Mkt Cap")),
        })

    print("Scrittura fondamentali: %d titoli" % len(aggiornamenti))
    scritti = 0
    for i in range(0, len(aggiornamenti), 200):
        lotto = aggiornamenti[i:i + 200]
        w = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                          headers=headers_up, json=lotto, timeout=180)
        if w.status_code in (200, 201, 204):
            scritti += len(lotto)
    print("  scritti: %d" % scritti)

    # ── cosa cambierebbe nell'universo (solo proposta) ────────
    print("Calcolo variazioni proposte per l'universo...")
    mc = {(x["ticker"], x["exchange"]): x["mkt_cap"] for x in aggiornamenti}
    nomi = {(t, ex): (row.get("Company Name") or "") for t, ex, row in tutte}

    st = []
    off = 0
    while True:
        b = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                         params={"select": "ticker,exchange,company,in_universe",
                                 "limit": "1000", "offset": str(off)}, timeout=120).json()
        if not isinstance(b, list) or not b:
            break
        st += b
        off += 1000
        if len(b) < 1000:
            break

    entrano, escono = [], []
    for x in st:
        k = (x["ticker"], x["exchange"])
        v = mc.get(k)
        if v is None or x["exchange"] not in SOGLIA_300:
            continue
        if e_fondo(nomi.get(k), x.get("company")):
            continue
        dentro = bool(x.get("in_universe"))
        if v >= 300 and not dentro:
            entrano.append((x["ticker"], x["exchange"], nomi.get(k) or x.get("company") or "", v))
        elif v < 300 and dentro:
            escono.append((x["ticker"], x["exchange"], nomi.get(k) or x.get("company") or "", v))

    return {
        "conteggi": conteggi,
        "scritti": scritti,
        "totale": len(aggiornamenti),
        "entrano": sorted(entrano, key=lambda z: -z[3]),
        "escono": sorted(escono, key=lambda z: z[3]),
        "senza_pe": sum(1 for a in aggiornamenti if a["pe_trailing"] is None),
    }


def rigenera_punteggi():
    """Fa ripartire gli script giornalieri, che ricalcolano i rank."""
    esiti = []
    for nome, url in [
        ("Europa", "https://forwardalpha.pro/api/cron/trigger-daily-eu"),
        ("USA e Canada", "https://forwardalpha.pro/api/cron/trigger-daily-eu-us"),
        ("Asia-Pacifico", "https://forwardalpha.pro/api/cron/trigger-daily-apac"),
    ]:
        try:
            r = requests.get(url, timeout=120)
            esiti.append((nome, r.status_code == 200))
        except Exception:
            esiti.append((nome, False))
    return esiti


def manda_email(dati, esiti):
    n_ent, n_esc = len(dati["entrano"]), len(dati["escono"])
    oggetto = "ForwardAlpha — fondamentali aggiornati: %d titoli" % dati["scritti"]
    if n_ent or n_esc:
        oggetto += " (%d entrano, %d escono: serve conferma)" % (n_ent, n_esc)

    B = ["<div style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:680px;color:#111'>"]
    B.append("<h2 style='margin:0 0 4px'>Fondamentali aggiornati</h2>")
    B.append("<div style='color:#666;font-size:13px;margin-bottom:16px'>%s</div>"
             % datetime.now().strftime("%d/%m/%Y %H:%M"))

    B.append("<div style='background:#f5f5f5;border-left:4px solid #0a7;padding:10px 14px;margin-bottom:18px'>")
    B.append("<div style='font-size:20px;font-weight:700'>%d titoli aggiornati</div>" % dati["scritti"])
    B.append("<div style='font-size:13px;color:#444;margin-top:4px'>")
    B.append(" &nbsp;·&nbsp; ".join("%s %d" % (a, n) for a, n in dati["conteggi"].items()))
    B.append("</div></div>")

    if dati["entrano"] or dati["escono"]:
        B.append("<div style='border:2px solid #c60;background:#fffaf3;padding:12px 14px;margin-bottom:18px'>")
        B.append("<b style='color:#c60'>Serve una tua conferma: l'universo NON e' stato modificato</b>")
        B.append("<div style='font-size:13px;color:#444;margin:6px 0 10px'>"
                 "Queste variazioni derivano dalla soglia di 300 milioni di dollari. "
                 "Rispondi a questa email indicando cosa applicare.</div>")
        if dati["entrano"]:
            B.append("<b style='font-size:14px'>Entrerebbero (%d)</b>" % len(dati["entrano"]))
            B.append("<table style='border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 12px'>")
            for t, ex, nome, v in dati["entrano"][:40]:
                B.append("<tr style='border-bottom:1px solid #eee'>"
                         "<td style='padding:4px'><b>%s.%s</b></td>"
                         "<td style='padding:4px'>%s</td>"
                         "<td style='padding:4px;text-align:right'>%.0f MM</td></tr>"
                         % (t, ex, nome[:38], v))
            B.append("</table>")
            if len(dati["entrano"]) > 40:
                B.append("<i>...e altri %d</i>" % (len(dati["entrano"]) - 40))
        if dati["escono"]:
            B.append("<b style='font-size:14px'>Uscirebbero (%d)</b>" % len(dati["escono"]))
            B.append("<table style='border-collapse:collapse;width:100%;font-size:13px;margin:6px 0'>")
            for t, ex, nome, v in dati["escono"][:40]:
                B.append("<tr style='border-bottom:1px solid #eee'>"
                         "<td style='padding:4px'><b>%s.%s</b></td>"
                         "<td style='padding:4px'>%s</td>"
                         "<td style='padding:4px;text-align:right'>%.0f MM</td></tr>"
                         % (t, ex, nome[:38], v))
            B.append("</table>")
            if len(dati["escono"]) > 40:
                B.append("<i>...e altri %d</i>" % (len(dati["escono"]) - 40))
        B.append("</div>")
    else:
        B.append("<div style='color:#0a7;font-size:14px;margin-bottom:18px'>"
                 "Nessuna variazione da approvare per l'universo.</div>")

    B.append("<h3 style='font-size:15px;margin:0 0 6px'>Ricalcolo dei punteggi</h3>")
    B.append("<div style='font-size:13px'>")
    for nome, ok in esiti:
        B.append("%s: %s<br>" % (nome, "avviato" if ok else "<b style='color:#b00'>NON avviato</b>"))
    B.append("</div>")
    B.append("<div style='font-size:12px;color:#888;margin-top:8px'>"
             "Value Score, Growth Score e Best Score si rigenerano entro un'ora.</div>")

    B.append("<div style='margin-top:20px;padding-top:10px;border-top:1px solid #ddd;font-size:12px;color:#888'>")
    B.append("%d titoli senza P/E perche' TIKR lo considera non significativo (utili negativi): "
             "e' il comportamento corretto, quel multiplo non entra nei percentili.<br>" % dati["senza_pe"])
    B.append("Fonte dei dati: TIKR. Prezzi e rendimenti: Yahoo Finance.")
    B.append("</div></div>")

    corpo = "".join(B)
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP non configurato, stampo soltanto:", oggetto)
        return
    msg = EmailMessage()
    msg["Subject"] = oggetto
    msg["From"] = SMTP_USER
    msg["To"] = REPORT_TO
    msg.set_content("Resoconto aggiornamento fondamentali (versione HTML).")
    msg.add_alternative(corpo, subtype="html")
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context()) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print("Email inviata a", REPORT_TO)
        annota("EMAIL: inviata a " + REPORT_TO)
    except Exception as e:
        print("ERRORE invio:", e)
        annota("EMAIL: ERRORE %s" % str(e)[:150])


if __name__ == "__main__":
    print("Controllo file TIKR — %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    presenti = elenca_file()
    firma = "|".join("%s=%s" % (n, presenti.get(n, "")) for n in sorted(FILE_TIKR))
    print("  firma attuale:  ", firma)
    precedente = ultima_elaborazione()
    print("  ultima elaborata:", precedente or "(mai)")

    forzato = os.environ.get("FORZA", "") == "1"
    if firma == precedente and not forzato:
        print("\nNessun file nuovo. Non c'e' nulla da fare.")
        raise SystemExit(0)

    print("\nFile nuovi rilevati: procedo.\n" if not forzato else "\nEsecuzione forzata.\n")
    dati = elabora()
    if not dati:
        print("Nessun dato leggibile dai file.")
        annota("ERRORE: file non leggibili")
        raise SystemExit(1)

    esiti = rigenera_punteggi()
    manda_email(dati, esiti)
    annota("ELABORATI:" + firma)
    print("\nFatto.")
