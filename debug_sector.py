#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORWARDALPHA - Rapporto giornaliero di copertura dati.

Fotografia onesta dello stato dei prezzi ogni mattina alle 08:00 CEST,
dopo che sono girati tutti e tre gli script:
  - daily_apac_yahoo.py   18:00 CEST del giorno prima
  - daily_eu_yahoo.py     02:30 CEST
  - daily_us_yahoo.py     02:30 CEST

METODO (il punto delicato, per non dare numeri falsi):
Ogni mercato ha un calendario di borsa diverso: festivita' locali, fusi
orari, giorni di chiusura. Non esiste una "data di oggi" valida per tutti.
Quindi per OGNI exchange si determina la seduta piu' recente realmente
presente in latest_prices, e un titolo e' considerato aggiornato se ha
quella data. Questo distingue due situazioni molto diverse:
  - singoli titoli indietro rispetto al loro mercato  -> di solito Yahoo
    non ha ancora pubblicato quel titolo (poco liquido, sospeso, delistato)
  - INTERO mercato fermo da giorni                    -> problema nostro
Il sabato e la domenica l'ultima seduta e' venerdi': non e' un errore e il
rapporto non lo segnala come tale.
"""

import os
import smtplib
import ssl
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
HEADERS = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
REPORT_TO = os.environ.get("REPORT_TO", "") or "andrea@forwardalpha.pro"

# Raggruppamento per come Andrea ragiona sui mercati, non per come sono
# organizzati gli script.
GRUPPI = [
    ("Europa", ["MIL", "XETRA", "PA", "AS", "MC", "BR", "LS", "VI", "HE",
                "IR", "GR", "LSE", "SWX", "OM", "OB", "CPSE"]),
    ("Stati Uniti", ["US"]),
    ("Canada", ["TSX"]),
    ("Giappone", ["TSE"]),
    ("Hong Kong", ["SEHK"]),
    ("Australia", ["ASX"]),
    ("Corea", ["KRX"]),
    ("Singapore", ["SGX"]),
]
TUTTI_EXCHANGE = [ex for _, lista in GRUPPI for ex in lista]

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi",
          "sabato", "domenica"]


def data_estesa(d):
    return "%s %d %s %d" % (GIORNI[d.weekday()], d.day, MESI[d.month - 1], d.year)


def leggi_tutto(tabella, select, exchange, filtri=None):
    """Legge tutte le righe di un exchange, paginando (PostgREST limita a 1000)."""
    righe = []
    offset = 0
    while True:
        params = {"select": select, "exchange": "eq." + exchange,
                  "limit": "1000", "offset": str(offset)}
        if filtri:
            params.update(filtri)
        try:
            r = requests.get(SUPABASE_URL + "/rest/v1/" + tabella,
                             headers=HEADERS, params=params, timeout=60)
            blocco = r.json()
        except Exception:
            break
        if not isinstance(blocco, list) or not blocco:
            break
        righe.extend(blocco)
        if len(blocco) < 1000:
            break
        offset += 1000
    return righe


def raccogli_dati():
    """Costruisce la fotografia, un exchange alla volta."""
    per_exchange = {}
    for ex in TUTTI_EXCHANGE:
        universo = leggi_tutto("stocks", "ticker,company", ex,
                               {"in_universe": "eq.true"})
        prezzi = leggi_tutto("latest_prices", "ticker,price_date", ex)

        nome_per_ticker = {r["ticker"]: (r.get("company") or r["ticker"])
                           for r in universo}
        tickers_universo = set(nome_per_ticker)
        data_per_ticker = {r["ticker"]: r.get("price_date") for r in prezzi
                           if r["ticker"] in tickers_universo}

        assenti = sorted(tickers_universo - set(data_per_ticker))
        date_valide = [d for d in data_per_ticker.values() if d]
        # Riferimento = data PREVALENTE, non la piu' recente in assoluto.
        # Con il massimo bastava un singolo titolo in anticipo (es. un ADR
        # o un titolo con orario di pubblicazione diverso) per far
        # risultare "in ritardo" tutto il resto del mercato che invece era
        # perfettamente corretto: numeri gonfiati e allarmi falsi.
        ultima_seduta = Counter(date_valide).most_common(1)[0][0] if date_valide else None

        aggiornati, in_ritardo = [], []
        for tk, d in data_per_ticker.items():
            # chi ha una data uguale o piu' recente della prevalente e' a posto
            if d and ultima_seduta and d >= ultima_seduta:
                aggiornati.append(tk)
            else:
                in_ritardo.append((tk, nome_per_ticker.get(tk, tk), d))

        per_exchange[ex] = {
            "universo": len(tickers_universo),
            "aggiornati": len(aggiornati),
            "in_ritardo": in_ritardo,
            "assenti": [(tk, nome_per_ticker.get(tk, tk)) for tk in assenti],
            "ultima_seduta": ultima_seduta,
            # data grezza titolo per titolo: serve per la distribuzione esatta
            "date": data_per_ticker,
            "nomi": nome_per_ticker,
        }
    return per_exchange


def distribuzione(per_exchange, exchanges, oggi):
    """Conteggio esatto dei titoli per data di prezzo, con il ritardo in
    giorni di calendario rispetto al giorno in cui gira il rapporto.
    Nessuna interpretazione: date assolute e conteggi verificabili."""
    conta = Counter()
    mai = 0
    for ex in exchanges:
        d = per_exchange[ex]
        mai += len(d["assenti"])
        for data in d["date"].values():
            if data:
                conta[data] += 1
            else:
                mai += 1
    righe = []
    for data, n in sorted(conta.items(), reverse=True):
        try:
            g = (oggi.date() - datetime.strptime(data, "%Y-%m-%d").date()).days
        except Exception:
            g = None
        righe.append({"data": data, "n": n, "giorni": g})
    return righe, mai


def leggi_esecuzioni():
    """Esiti degli script nelle ultime 24 ore."""
    da = (datetime.now(timezone.utc) - timedelta(hours=26)).isoformat()
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/daily_log", headers=HEADERS,
                         params={"select": "market,prices_updated,prices_failed,"
                                           "momentum_updated,rank_updated,"
                                           "duration_seconds,created_at",
                                 "created_at": "gte." + da,
                                 "order": "created_at.desc", "limit": "50"},
                         timeout=60)
        righe = r.json()
        return righe if isinstance(righe, list) else []
    except Exception:
        return []


def leggi_sentinella_quintili():
    """La tabella dei quintili precalcolati e' popolata? Se no, il sito
    ricade sul calcolo lento nel browser (era la causa dei 21 secondi)."""
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/sector_quintile_partials",
                         headers={**HEADERS, "Prefer": "count=exact"},
                         params={"select": "updated_at",
                                 "order": "updated_at.desc", "limit": "1"},
                         timeout=60)
        n = int(r.headers.get("content-range", "0/0").split("/")[-1])
        dati = r.json()
        agg = dati[0]["updated_at"][:10] if isinstance(dati, list) and dati else None
        return n, agg
    except Exception:
        return 0, None


def costruisci_email(per_exchange, esecuzioni, quintili):
    oggi = datetime.now(timezone.utc) + timedelta(hours=2)  # CEST

    tot_universo = sum(d["universo"] for d in per_exchange.values())
    tot_aggiornati = sum(d["aggiornati"] for d in per_exchange.values())
    tot_ritardo = sum(len(d["in_ritardo"]) for d in per_exchange.values())
    tot_assenti = sum(len(d["assenti"]) for d in per_exchange.values())
    perc = (tot_aggiornati / tot_universo * 100) if tot_universo else 0
    dist, mai_scritti = distribuzione(per_exchange, TUTTI_EXCHANGE, oggi)

    # --- segnalazioni: solo cose che meritano davvero attenzione ---
    allarmi = []

    # 1. un mercato intero fermo da troppo tempo = problema nostro
    limite = (oggi - timedelta(days=5)).strftime("%Y-%m-%d")
    for nome, lista in GRUPPI:
        for ex in lista:
            d = per_exchange[ex]
            if d["universo"] == 0:
                continue
            if not d["ultima_seduta"]:
                allarmi.append("%s (%s): nessun prezzo in cache" % (nome, ex))
            elif d["ultima_seduta"] < limite:
                allarmi.append("%s (%s): tutto il mercato fermo al %s"
                               % (nome, ex, d["ultima_seduta"]))

    # 2. script non girato o con molti fallimenti
    visti = set()
    for r in esecuzioni:
        visti.add(r.get("market"))
        falliti = r.get("prices_failed") or 0
        agg = r.get("prices_updated") or 0
        if agg and falliti > agg * 0.02:
            allarmi.append("script %s: %d prezzi falliti su %d"
                           % (r.get("market"), falliti, agg + falliti))
    for atteso in ("EU", "US+CA", "APAC"):
        if atteso not in visti:
            allarmi.append("script %s: nessuna esecuzione nelle ultime 24 ore" % atteso)

    # 3. sentinella quintili
    n_quint, agg_quint = quintili
    if n_quint == 0:
        allarmi.append("tabella quintili vuota: il sito usa il calcolo lento di riserva")

    stato = "ATTENZIONE" if allarmi else "OK"
    recenti = sum(r["n"] for r in dist if r["giorni"] is not None and r["giorni"] <= 1)
    oggetto = "ForwardAlpha %s - %d/%d titoli al giorno prima (%.1f%%)" % (
        stato, recenti, tot_universo,
        recenti / tot_universo * 100 if tot_universo else 0)

    # ---------------- corpo HTML ----------------
    B = []
    B.append("<div style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
             "max-width:640px;color:#111;line-height:1.45'>")
    B.append("<h2 style='margin:0 0 2px'>ForwardAlpha</h2>")
    B.append("<div style='color:#666;font-size:13px;margin-bottom:16px'>%s, ore %s</div>"
             % (data_estesa(oggi), oggi.strftime("%H:%M")))

    colore = "#b00" if allarmi else "#0a7"
    B.append("<div style='border-left:4px solid %s;padding:10px 14px;"
             "background:#f7f7f7;margin-bottom:18px'>" % colore)
    B.append("<div style='font-size:15px;font-weight:700;margin-bottom:8px'>"
             "Universo: %d titoli</div>" % tot_universo)
    B.append("<table style='border-collapse:collapse;font-size:14px;width:100%'>")
    for r in dist:
        g = r["giorni"]
        if g == 0:
            etichetta = "oggi"
        elif g == 1:
            etichetta = "il giorno prima"
        elif g is None:
            etichetta = ""
        else:
            etichetta = "%d giorni fa" % g
        pc = r["n"] / tot_universo * 100 if tot_universo else 0
        grigio = "#666" if (g or 0) >= 3 else "#111"
        B.append("<tr style='color:%s'>"
                 "<td style='padding:2px 10px 2px 0;white-space:nowrap'><b>%s</b>"
                 " <span style='color:#888'>%s</span></td>"
                 "<td style='padding:2px 10px;text-align:right;white-space:nowrap'>"
                 "<b>%d</b> titoli</td>"
                 "<td style='padding:2px 0;text-align:right;color:#888'>%.1f%%</td>"
                 "</tr>" % (grigio, r["data"], etichetta, r["n"], pc))
    if mai_scritti:
        B.append("<tr style='color:#b00'>"
                 "<td style='padding:2px 10px 2px 0'><b>mai scritti</b></td>"
                 "<td style='padding:2px 10px;text-align:right'><b>%d</b> titoli</td>"
                 "<td style='padding:2px 0;text-align:right;color:#888'>%.1f%%</td>"
                 "</tr>" % (mai_scritti, mai_scritti / tot_universo * 100 if tot_universo else 0))
    B.append("</table>")
    B.append("</div>")

    if allarmi:
        B.append("<div style='border:1px solid #b00;background:#fff5f5;"
                 "padding:10px 14px;margin-bottom:18px'>")
        B.append("<b style='color:#b00'>Da guardare</b><ul style='margin:6px 0 0;"
                 "padding-left:18px;font-size:14px'>")
        for a in allarmi:
            B.append("<li>%s</li>" % a)
        B.append("</ul></div>")
    else:
        B.append("<div style='color:#0a7;font-size:14px;margin-bottom:18px'>"
                 "Nessuna anomalia. I titoli in ritardo sono casi isolati in cui "
                 "Yahoo non ha ancora pubblicato la chiusura.</div>")

    # tabella per mercato
    B.append("<h3 style='margin:0 0 6px;font-size:15px'>Per mercato</h3>")
    B.append("<table style='border-collapse:collapse;width:100%;font-size:13px'>")
    B.append("<tr style='background:#f0f0f0;text-align:left'>"
             "<th style='padding:6px'>Mercato</th>"
             "<th style='padding:6px;text-align:right'>Tot.</th>"
             "<th style='padding:6px;text-align:right'>1 g.</th>"
             "<th style='padding:6px;text-align:right'>2 g.</th>"
             "<th style='padding:6px;text-align:right'>+vecchi</th>"
             "<th style='padding:6px;text-align:right'>mai</th>"
             "<th style='padding:6px'>data prevalente</th></tr>")
    for nome, lista in GRUPPI:
        d_mkt, mai_mkt = distribuzione(per_exchange, lista, oggi)
        u = sum(per_exchange[e]["universo"] for e in lista)
        b1 = sum(r["n"] for r in d_mkt if r["giorni"] is not None and r["giorni"] <= 1)
        b2 = sum(r["n"] for r in d_mkt if r["giorni"] == 2)
        b3 = sum(r["n"] for r in d_mkt if r["giorni"] is not None and r["giorni"] >= 3)
        prevalenti = [per_exchange[e]["ultima_seduta"] for e in lista
                      if per_exchange[e]["ultima_seduta"]]
        seduta = Counter(prevalenti).most_common(1)[0][0] if prevalenti else "-"
        col = "#b00" if (b3 + mai_mkt) > u * 0.05 else "#111"
        B.append("<tr style='border-bottom:1px solid #eee;color:%s'>"
                 "<td style='padding:6px'>%s</td>"
                 "<td style='padding:6px;text-align:right'>%d</td>"
                 "<td style='padding:6px;text-align:right'><b>%d</b></td>"
                 "<td style='padding:6px;text-align:right'>%d</td>"
                 "<td style='padding:6px;text-align:right'>%d</td>"
                 "<td style='padding:6px;text-align:right'>%d</td>"
                 "<td style='padding:6px'>%s</td></tr>"
                 % (col, nome, u, b1, b2, b3, mai_mkt, seduta))
    B.append("</table>")

    # esecuzioni
    B.append("<h3 style='margin:18px 0 6px;font-size:15px'>Esecuzione script "
             "<span style='font-weight:400;color:#666;font-size:13px'>"
             "(ultime 24 ore)</span></h3>")
    if esecuzioni:
        B.append("<table style='border-collapse:collapse;width:100%;font-size:13px'>")
        B.append("<tr style='background:#f0f0f0;text-align:left'>"
                 "<th style='padding:6px'>Script</th>"
                 "<th style='padding:6px'>Ora</th>"
                 "<th style='padding:6px;text-align:right'>Prezzi ok</th>"
                 "<th style='padding:6px;text-align:right'>Falliti</th>"
                 "<th style='padding:6px;text-align:right'>Durata</th></tr>")
        for r in esecuzioni[:8]:
            try:
                q = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                ora = (q + timedelta(hours=2)).strftime("%d/%m %H:%M")
            except Exception:
                ora = "-"
            dur = r.get("duration_seconds") or 0
            B.append("<tr style='border-bottom:1px solid #eee'>"
                     "<td style='padding:6px'>%s</td>"
                     "<td style='padding:6px'>%s</td>"
                     "<td style='padding:6px;text-align:right'>%s</td>"
                     "<td style='padding:6px;text-align:right'>%s</td>"
                     "<td style='padding:6px;text-align:right'>%d min</td></tr>"
                     % (r.get("market", "-"), ora, r.get("prices_updated", "-"),
                        r.get("prices_failed", "-"), dur // 60))
        B.append("</table>")
    else:
        B.append("<div style='color:#b00;font-size:14px'>Nessuna esecuzione "
                 "registrata nelle ultime 24 ore.</div>")

    # elenco dei casi che restano indietro da tempo
    cronici = []
    limite_cronico = (oggi - timedelta(days=7)).strftime("%Y-%m-%d")
    for nome, lista in GRUPPI:
        for ex in lista:
            for tk, azienda, d in per_exchange[ex]["in_ritardo"]:
                if d and d < limite_cronico:
                    cronici.append((d, tk, ex, azienda))
    cronici.sort()
    if cronici:
        B.append("<h3 style='margin:18px 0 6px;font-size:15px'>Fermi da oltre "
                 "una settimana <span style='font-weight:400;color:#666;"
                 "font-size:13px'>(%d)</span></h3>" % len(cronici))
        B.append("<div style='font-size:13px;color:#444'>")
        for d, tk, ex, azienda in cronici[:25]:
            B.append("%s.%s &nbsp;<span style='color:#888'>%s</span> &nbsp;→&nbsp; %s<br>"
                     % (tk, ex, azienda[:38], d))
        if len(cronici) > 25:
            B.append("<i>...e altri %d</i>" % (len(cronici) - 25))
        B.append("<div style='color:#888;margin-top:6px'>Di solito titoli "
                 "sospesi o delistati: se confermato, vanno messi "
                 "in_universe=false.</div>")
        B.append("</div>")

    B.append("<div style='margin-top:22px;padding-top:10px;border-top:1px solid #ddd;"
             "font-size:12px;color:#888'>")
    B.append("Quintili precalcolati: %s righe%s<br>"
             % (n_quint, (", aggiornati il " + agg_quint) if agg_quint else ""))
    B.append("Un titolo e' \"aggiornato\" se ha la data dell'ultima seduta "
             "presente per il suo mercato. Ogni borsa ha il proprio calendario, "
             "quindi le date possono differire tra mercati senza che sia un errore.")
    B.append("</div></div>")

    return oggetto, "".join(B)


def invia(oggetto, corpo_html):
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP non configurato: stampo il rapporto senza inviarlo.")
        print(oggetto)
        return False
    msg = EmailMessage()
    msg["Subject"] = oggetto
    msg["From"] = SMTP_USER
    msg["To"] = REPORT_TO
    msg.set_content("Rapporto ForwardAlpha in formato HTML.")
    msg.add_alternative(corpo_html, subtype="html")
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    print("Email inviata a %s" % REPORT_TO)
    return True


def riepilogo_testuale(per_exchange, esecuzioni, quintili):
    """Stessa fotografia in testo, stampata nei log dell'esecuzione."""
    R = []
    tot_u = sum(d["universo"] for d in per_exchange.values())
    tot_a = sum(d["aggiornati"] for d in per_exchange.values())
    tot_r = sum(len(d["in_ritardo"]) for d in per_exchange.values())
    tot_x = sum(len(d["assenti"]) for d in per_exchange.values())
    oggi = datetime.now(timezone.utc) + timedelta(hours=2)
    dist, mai = distribuzione(per_exchange, TUTTI_EXCHANGE, oggi)
    R.append("UNIVERSO: %d titoli" % tot_u)
    R.append("")
    R.append("DISTRIBUZIONE PER DATA")
    for r in dist:
        g = r["giorni"]
        et = "oggi" if g == 0 else ("il giorno prima" if g == 1 else "%s giorni fa" % g)
        R.append("  %s  %-16s %6d titoli  %5.1f%%"
                 % (r["data"], et, r["n"], r["n"] / tot_u * 100 if tot_u else 0))
    if mai:
        R.append("  %-10s %-16s %6d titoli  %5.1f%%"
                 % ("mai scritti", "", mai, mai / tot_u * 100 if tot_u else 0))
    R.append("")
    R.append("%-14s %6s %6s %6s %8s %5s  %s"
             % ("MERCATO", "TOT", "1g", "2g", "+VECCHI", "MAI", "PREVALENTE"))
    for nome, lista in GRUPPI:
        d_mkt, mai_mkt = distribuzione(per_exchange, lista, oggi)
        u = sum(per_exchange[e]["universo"] for e in lista)
        b1 = sum(x["n"] for x in d_mkt if x["giorni"] is not None and x["giorni"] <= 1)
        b2 = sum(x["n"] for x in d_mkt if x["giorni"] == 2)
        b3 = sum(x["n"] for x in d_mkt if x["giorni"] is not None and x["giorni"] >= 3)
        pv = [per_exchange[e]["ultima_seduta"] for e in lista if per_exchange[e]["ultima_seduta"]]
        R.append("%-14s %6d %6d %6d %8d %5d  %s"
                 % (nome, u, b1, b2, b3, mai_mkt,
                    Counter(pv).most_common(1)[0][0] if pv else "-"))
    R.append("")
    R.append("ESECUZIONI ultime 24h: %d" % len(esecuzioni))
    for r in esecuzioni[:6]:
        R.append("  %-6s ok=%s falliti=%s durata=%ss"
                 % (r.get("market"), r.get("prices_updated"),
                    r.get("prices_failed"), r.get("duration_seconds")))
    R.append("")
    R.append("Quintili precalcolati: %d righe (aggiornati %s)" % (quintili[0], quintili[1]))
    return "\n".join(R)


if __name__ == "__main__":
    per_exchange = raccogli_dati()
    esecuzioni = leggi_esecuzioni()
    quintili = leggi_sentinella_quintili()
    oggetto, corpo = costruisci_email(per_exchange, esecuzioni, quintili)
    print("OGGETTO:", oggetto)
    print()
    print(riepilogo_testuale(per_exchange, esecuzioni, quintili))
    print()
    invia(oggetto, corpo)
