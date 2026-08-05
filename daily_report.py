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

import time

import requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
HEADERS = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Namecheap Private Email: host unico mail.privateemail.com, porta 465
# con SSL. Serve la normale password della casella, nessuna password
# applicativa da generare (a differenza di Gmail).
SMTP_HOST = os.environ.get("SMTP_HOST", "mail.privateemail.com")
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
        if offset > 50000:      # salvagente contro cicli infiniti
            break
    return righe


def conta_esatto(tabella, filtri):
    """Conteggio server-side via header Content-Range. Da usare SEMPRE al
    posto di len() su una lettura non paginata: e' il modo in cui, il
    31/7 e il 2/8, un conteggio parziale mi ha fatto credere per errore
    che l'universo USA fosse crollato da 3002 a 2343 titoli."""
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/" + tabella,
                         headers={**HEADERS, "Prefer": "count=exact"},
                         params={**filtri, "select": "ticker", "limit": "1"},
                         timeout=60)
        return int(r.headers.get("content-range", "0/0").split("/")[-1])
    except Exception:
        return None


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


def giorni_di_borsa(data_str, oggi):
    """Distanza in GIORNI DI BORSA, non di calendario. Di domenica l'ultima
    seduta e' venerdi': col calendario risulterebbe "2 giorni fa" e il
    rapporto segnalerebbe 0% aggiornati con tutto perfettamente in ordine.
    Non tiene conto delle festivita' infrasettimanali, ma per un rapporto
    giornaliero l'approssimazione e' irrilevante."""
    d = datetime.strptime(data_str, "%Y-%m-%d").date()
    fine = oggi.date()
    if d >= fine:
        return 0
    n = 0
    cur = d
    while cur < fine:
        cur += timedelta(days=1)
        if cur.weekday() < 5:   # 0-4 = lunedi-venerdi
            n += 1
    return n


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
            g = giorni_di_borsa(data, oggi)
        except Exception:
            g = None
        righe.append({"data": data, "n": n, "giorni": g})
    return righe, mai


def triage_cronici(per_exchange, oggi, giorni_soglia=7):
    """Per i titoli fermi da oltre una settimana chiede a Yahoo se il dato
    esiste. Distingue due situazioni molto diverse:
      - Yahoo NON ha nulla di piu' recente -> titolo delistato/sospeso:
        va tolto dall'universo, nessuna urgenza tecnica
      - Yahoo HA un prezzo piu' recente del nostro -> problema NOSTRO:
        di solito il codice yahoo_ticker e' sbagliato (visto piu' volte:
        REIT canadesi col punto invece del trattino, coreani col prefisso
        "A", tedeschi su Xetra invece che Francoforte, Hong Kong senza lo
        zero iniziale). Sono gli unici casi che richiedono un intervento.
    Interroga solo poche decine di titoli, quindi non pesa sull'esecuzione.
    """
    limite = (oggi - timedelta(days=giorni_soglia)).strftime("%Y-%m-%d")
    candidati = []
    for ex, d in per_exchange.items():
        for tk, data in d["date"].items():
            if data and data < limite:
                candidati.append((data, tk, ex, d["nomi"].get(tk, tk)))
        for tk, azienda in d["assenti"]:
            candidati.append((None, tk, ex, azienda))
    candidati.sort(key=lambda x: (x[0] or ""))

    nostri, delistati, incerti = [], [], []
    if not candidati:
        return nostri, delistati, incerti
    try:
        import yfinance as yf
        import pandas as pd
    except Exception:
        return nostri, delistati, candidati  # senza yfinance non si distingue

    for data, tk, ex, azienda in candidati[:60]:
        yt = None
        try:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=HEADERS,
                             params={"select": "yahoo_ticker", "ticker": "eq." + tk,
                                     "exchange": "eq." + ex}, timeout=30)
            rows = r.json()
            if isinstance(rows, list) and rows:
                yt = rows[0].get("yahoo_ticker")
        except Exception:
            pass
        if not yt:
            incerti.append((data, tk, ex, azienda, "nessun codice Yahoo impostato"))
            continue
        try:
            df = yf.download(yt, period="10d", interval="1d",
                             auto_adjust=True, progress=False)
            if df.empty:
                delistati.append((data, tk, ex, azienda, yt))
                continue
            cl = df["Close"]
            if isinstance(cl, pd.DataFrame):
                cl = cl.iloc[:, 0]
            cl = cl.dropna()
            if len(cl) == 0:
                delistati.append((data, tk, ex, azienda, yt))
                continue
            ultima_yahoo = cl.index[-1].strftime("%Y-%m-%d")
            if data is None or ultima_yahoo > data:
                nostri.append((data, tk, ex, azienda, yt, ultima_yahoo))
            else:
                delistati.append((data, tk, ex, azienda, yt))
        except Exception:
            incerti.append((data, tk, ex, azienda, "errore interrogando Yahoo"))
        time.sleep(0.25)
    return nostri, delistati, incerti


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


def seduta_reale_di_mercato(per_exchange, exchanges, oggi):
    """Ultima seduta realmente disponibile su Yahoo per questo mercato,
    stabilita con download SINGOLI (affidabili) su qualche titolo di
    riferimento. Serve a distinguere "siamo indietro noi" da "il mercato
    era chiuso per festa": senza questa verifica il rapporto darebbe un
    falso allarme ogni volta che una borsa osserva una festivita' locale."""
    try:
        import yfinance as yf
        import pandas as pd
    except Exception:
        return None
    migliore = None
    for ex in exchanges:
        tickers = list(per_exchange[ex]["date"].keys())[:2]
        for tk in tickers:
            try:
                r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=HEADERS,
                                 params={"select": "yahoo_ticker", "ticker": "eq." + tk,
                                         "exchange": "eq." + ex}, timeout=30)
                rows = r.json()
                yt = rows[0].get("yahoo_ticker") if isinstance(rows, list) and rows else None
                if not yt:
                    continue
                df = yf.download(yt, period="12d", interval="1d",
                                 auto_adjust=True, progress=False)
                if df.empty:
                    continue
                cl = df["Close"]
                if isinstance(cl, pd.DataFrame):
                    cl = cl.iloc[:, 0]
                cl = cl.dropna()
                if len(cl) == 0:
                    continue
                # la barra piu' recente puo' essere del giorno IN CORSO e
                # quindi provvisoria: si scarta se il mercato non ha ancora
                # chiuso da almeno un'ora.
                for i in range(len(cl) - 1, -1, -1):
                    ds = cl.index[i].strftime("%Y-%m-%d")
                    if ds < oggi.strftime("%Y-%m-%d"):
                        if migliore is None or ds > migliore:
                            migliore = ds
                        break
            except Exception:
                pass
            time.sleep(0.3)
        if migliore:
            break
    return migliore


def costruisci_email(per_exchange, esecuzioni, quintili, triage):
    oggi = datetime.now(timezone.utc) + timedelta(hours=2)  # CEST

    tot_universo = sum(d["universo"] for d in per_exchange.values())
    tot_aggiornati = sum(d["aggiornati"] for d in per_exchange.values())
    tot_ritardo = sum(len(d["in_ritardo"]) for d in per_exchange.values())
    tot_assenti = sum(len(d["assenti"]) for d in per_exchange.values())
    perc = (tot_aggiornati / tot_universo * 100) if tot_universo else 0
    dist, mai_scritti = distribuzione(per_exchange, TUTTI_EXCHANGE, oggi)
    nostri, delistati, incerti = triage

    # --- segnalazioni: solo cose che meritano davvero attenzione ---
    allarmi = []

    # 1. MERCATO INDIETRO RISPETTO A CIO' CHE YAHOO HA GIA'
    # FIX 6/8/2026: la prima versione confrontava i mercati FRA LORO, ma
    # i loro script girano a orari diversi (Europa alle 21, USA alle 3:23)
    # e a meta' notte l'Europa ha legittimamente una seduta in piu' degli
    # Stati Uniti: avrebbe allarmato ogni notte senza motivo.
    # Ora ogni mercato si confronta con SE STESSO: si chiede a Yahoo qual
    # e' la sua ultima seduta chiusa e si allarma solo se noi non ce
    # l'abbiamo. Indipendente da fusi orari, orari degli script e
    # festivita' locali (se la borsa era chiusa, Yahoo non ha nulla di
    # piu' recente e non scatta nessun allarme).
    for nome, lista in GRUPPI:
        titoli_gruppo = sum(per_exchange[e]["universo"] for e in lista)
        if not titoli_gruppo:
            continue
        date_gruppo = [per_exchange[e]["ultima_seduta"] for e in lista
                       if per_exchange[e]["universo"] and per_exchange[e]["ultima_seduta"]]
        if not date_gruppo:
            allarmi.append("%s: nessun prezzo disponibile (%d titoli)" % (nome, titoli_gruppo))
            continue
        seduta_nostra = max(date_gruppo)
        reale = seduta_reale_di_mercato(per_exchange, lista, oggi)
        if reale and reale > seduta_nostra:
            allarmi.append(
                "%s: siamo fermi alla seduta del %s, Yahoo ha gia' quella del %s "
                "(%d titoli)" % (nome, seduta_nostra, reale, titoli_gruppo))

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

    # 3. titoli con codice Yahoo sbagliato: unico caso che richiede intervento
    if nostri:
        allarmi.append("%d titoli con dato disponibile su Yahoo ma non nostro "
                       "(probabile codice errato): %s"
                       % (len(nostri), ", ".join("%s.%s" % (x[1], x[2]) for x in nostri[:5])
                          + (" e altri" if len(nostri) > 5 else "")))

    # 4. sentinella quintili
    n_quint, agg_quint = quintili
    if n_quint == 0:
        allarmi.append("tabella quintili vuota: il sito usa il calcolo lento di riserva")

    stato = "ATTENZIONE" if allarmi else "OK"
    recenti = sum(r["n"] for r in dist if r["giorni"] is not None and r["giorni"] <= 1)
    oggetto = "ForwardAlpha %s - %d/%d titoli aggiornati (%.1f%%)" % (
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
            etichetta = "ultima seduta"
        elif g == 1:
            etichetta = "una seduta indietro"
        elif g is None:
            etichetta = ""
        else:
            etichetta = "%d sedute indietro" % g
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

    # ── Titoli fermi da tempo, divisi per CAUSA ───────────────
    # La distinzione e' la parte utile: i delistati non richiedono nulla
    # di tecnico, i "problema nostro" sono azioni concrete da fare.

    if nostri:
        B.append("<div style='border:2px solid #b00;background:#fff5f5;"
                 "padding:12px 14px;margin-top:20px'>")
        B.append("<b style='color:#b00;font-size:15px'>DA SISTEMARE: %d titoli "
                 "per cui Yahoo ha il dato e noi no</b>" % len(nostri))
        B.append("<div style='font-size:13px;color:#444;margin:6px 0 8px'>"
                 "Quasi sempre e' il codice Yahoo sbagliato in "
                 "<code>stocks.yahoo_ticker</code>.</div>")
        B.append("<table style='border-collapse:collapse;width:100%;font-size:13px'>")
        B.append("<tr style='background:#ffe8e8;text-align:left'>"
                 "<th style='padding:5px'>Titolo</th>"
                 "<th style='padding:5px'>Societa'</th>"
                 "<th style='padding:5px'>Codice usato</th>"
                 "<th style='padding:5px'>Nostro</th>"
                 "<th style='padding:5px'>Yahoo ha</th></tr>")
        for data, tk, ex, azienda, yt, uy in nostri:
            B.append("<tr style='border-bottom:1px solid #f0d0d0'>"
                     "<td style='padding:5px'><b>%s.%s</b></td>"
                     "<td style='padding:5px'>%s</td>"
                     "<td style='padding:5px'><code>%s</code></td>"
                     "<td style='padding:5px'>%s</td>"
                     "<td style='padding:5px;color:#b00'><b>%s</b></td></tr>"
                     % (tk, ex, azienda[:30], yt, data or "mai scritto", uy))
        B.append("</table></div>")

    if delistati:
        B.append("<h3 style='margin:20px 0 6px;font-size:15px'>Fermi ma non e' "
                 "colpa nostra <span style='font-weight:400;color:#666;"
                 "font-size:13px'>(%d)</span></h3>" % len(delistati))
        B.append("<div style='font-size:13px;color:#444'>"
                 "Yahoo non ha nulla di piu' recente: societa' delistate, "
                 "acquisite o sospese. Nessun intervento tecnico, "
                 "eventualmente da togliere dall'universo.<br><br>")
        for data, tk, ex, azienda, yt in delistati[:20]:
            g = ""
            if data:
                try:
                    g = " (%d gg)" % (oggi.date() - datetime.strptime(data, "%Y-%m-%d").date()).days
                except Exception:
                    pass
            B.append("%s.%s <span style='color:#888'>%s</span> &nbsp;fermo al %s%s<br>"
                     % (tk, ex, azienda[:32], data or "mai scritto", g))
        if len(delistati) > 20:
            B.append("<i>...e altri %d</i>" % (len(delistati) - 20))
        B.append("</div>")

    if incerti:
        B.append("<div style='font-size:13px;color:#888;margin-top:12px'>"
                 "Non verificati (%d): " % len(incerti))
        B.append(", ".join("%s.%s" % (x[1], x[2]) for x in incerti[:15]))
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


def traccia(esito, dettaglio=""):
    """Registra l'esito dell'invio in script_logs: i log di GitHub Actions
    non sono sempre leggibili dall'esterno, cosi' l'esito resta comunque
    verificabile con una query."""
    try:
        requests.post(SUPABASE_URL + "/rest/v1/script_logs",
                      headers={**HEADERS, "Content-Type": "application/json"},
                      json=[{"script_name": "daily_report",
                             "log_text": "INVIO EMAIL: %s %s" % (esito, dettaglio)}],
                      timeout=30)
    except Exception:
        pass


def invia(oggetto, corpo_html):
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP non configurato: stampo il rapporto senza inviarlo.")
        traccia("NON CONFIGURATO", "SMTP_USER o SMTP_PASS mancanti")
        print(oggetto)
        return False
    msg = EmailMessage()
    msg["Subject"] = oggetto
    msg["From"] = SMTP_USER
    msg["To"] = REPORT_TO
    msg.set_content("Rapporto ForwardAlpha in formato HTML.")
    msg.add_alternative(corpo_html, subtype="html")
    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        print("ERRORE INVIO: %s" % e)
        traccia("ERRORE", "%s: %s" % (type(e).__name__, str(e)[:200]))
        return False
    print("Email inviata a %s" % REPORT_TO)
    traccia("OK", "-> %s" % REPORT_TO)
    return True


def riepilogo_testuale(per_exchange, esecuzioni, quintili, triage):
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
        et = "ultima seduta" if g == 0 else ("1 seduta indietro" if g == 1 else "%s sedute indietro" % g)
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
    nostri_t, delist_t, _ = triage
    R.append("")
    if nostri_t:
        R.append("DA SISTEMARE (Yahoo ha il dato, noi no): %d" % len(nostri_t))
        for data, tk, ex, az, yt, uy in nostri_t:
            R.append("  %-9s %-5s codice=%-12s nostro=%-10s yahoo=%s"
                     % (tk, ex, yt, data or "mai", uy))
    else:
        R.append("DA SISTEMARE: nessuno")
    R.append("Delistati/sospesi (nessun intervento): %d" % len(delist_t))
    R.append("")
    R.append("Quintili precalcolati: %d righe (aggiornati %s)" % (quintili[0], quintili[1]))
    return "\n".join(R)


if __name__ == "__main__":
    per_exchange = raccogli_dati()
    # Controllo di coerenza: il totale letto deve combaciare col conteggio
    # fatto dal database. Se non combacia, una lettura e' stata troncata e
    # TUTTI i numeri del rapporto sarebbero sbagliati.
    letto = sum(d["universo"] for d in per_exchange.values())
    atteso = sum(conta_esatto("stocks", {"exchange": "eq." + ex,
                                         "in_universe": "eq.true"}) or 0
                 for ex in TUTTI_EXCHANGE)
    if letto != atteso:
        print("ATTENZIONE: letti %d titoli ma il database ne conta %d. "
              "Una lettura e' stata troncata, i numeri sotto non sono "
              "affidabili." % (letto, atteso))
    esecuzioni = leggi_esecuzioni()
    quintili = leggi_sentinella_quintili()
    # calcolato UNA volta sola: interroga Yahoo, non va ripetuto
    triage = triage_cronici(per_exchange, datetime.now(timezone.utc) + timedelta(hours=2))
    oggetto, corpo = costruisci_email(per_exchange, esecuzioni, quintili, triage)
    print("OGGETTO:", oggetto)
    print()
    print(riepilogo_testuale(per_exchange, esecuzioni, quintili, triage))
    print()
    invia(oggetto, corpo)
