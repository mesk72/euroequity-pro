#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORWARDALPHA - Sorvegliante delle esecuzioni giornaliere.

Perche' esiste: il 6/8/2026 l'esecuzione serale europea e' stata ANNULLATA
dopo 15 minuti (due cron partivano a 7 minuti di distanza e il blocco di
concorrenza faceva si' che il secondo uccidesse il primo). Nessuno se n'e'
accorto: il sito e' rimasto indietro di un giorno finche' non l'ha notato
Andrea guardando le pagine. Non esisteva alcun controllo sull'ESITO degli
script, solo sui dati che producevano.

Cosa fa, ogni due ore:
  1. per ciascuno dei tre script guarda l'ultima esecuzione
  2. se e' fallita o annullata, e dopo di essa non ce n'e' una riuscita,
     la rilancia
  3. se un mercato non ha avuto NESSUNA esecuzione riuscita nelle ultime
     20 ore, la rilancia comunque (copre il caso in cui il cron non sia
     proprio partito)

Non fa nulla se e' gia' tutto a posto, quindi puo' girare spesso senza
costi apprezzabili.
"""

import os
import time
from datetime import datetime, timedelta, timezone

import requests

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
API = "https://api.github.com/repos/" + REPO

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
HEADERS_DB = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

WORKFLOW = {
    "daily_eu_yahoo.yml": "Europa",
    "daily_us_yahoo.yml": "Stati Uniti e Canada",
    "daily_apac_yahoo.yml": "Asia Pacifico",
}

ORE_MASSIME_SENZA_SUCCESSO = 20


def gh(percorso, **kw):
    h = {"Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json"}
    return requests.get(API + percorso, headers=h, timeout=60, **kw)


# Il rilancio passa dagli endpoint del sito, non dall'API di GitHub: il
# token automatico delle Azioni non puo' far partire altri workflow, mentre
# quegli endpoint hanno gia' il loro token e sono gli stessi che usa il cron
# di Vercel tutti i giorni.
ENDPOINT = {
    "daily_eu_yahoo.yml": "https://forwardalpha.pro/api/cron/trigger-daily-eu",
    "daily_us_yahoo.yml": "https://forwardalpha.pro/api/cron/trigger-daily-eu-us",
    "daily_apac_yahoo.yml": "https://forwardalpha.pro/api/cron/trigger-daily-apac",
}


def rilancia(wf):
    url = ENDPOINT.get(wf)
    if not url:
        return False
    try:
        r = requests.get(url, timeout=90)
        return r.status_code == 200
    except Exception:
        return False


def annota(testo):
    """Lascia traccia nel database, cosi' l'intervento e' visibile anche
    nel rapporto del mattino e non solo nei log di GitHub."""
    try:
        requests.post(SUPABASE_URL + "/rest/v1/script_logs",
                      headers={**HEADERS_DB, "Content-Type": "application/json"},
                      json=[{"script_name": "sorvegliante", "log_text": testo}],
                      timeout=30)
    except Exception:
        pass


def controlla(wf, nome):
    r = gh("/actions/workflows/%s/runs?per_page=10" % wf)
    if r.status_code != 200:
        print("  %s: impossibile leggere le esecuzioni (HTTP %s)" % (nome, r.status_code))
        return
    runs = r.json().get("workflow_runs", [])
    if not runs:
        print("  %s: nessuna esecuzione trovata" % nome)
        return

    adesso = datetime.now(timezone.utc)
    ultimo_successo = None
    for run in runs:
        if run.get("conclusion") == "success":
            ultimo_successo = datetime.fromisoformat(
                run["created_at"].replace("Z", "+00:00"))
            break

    ultima = runs[0]
    esito = ultima.get("conclusion")
    stato = ultima.get("status")

    # 1) e' in corso: non si tocca
    if stato != "completed":
        print("  %s: esecuzione in corso, non intervengo" % nome)
        return

    # 2) l'ultima e' fallita o annullata
    if esito in ("failure", "cancelled", "timed_out"):
        msg = "%s: ultima esecuzione %s (%s) -> RILANCIO" % (
            nome, esito, ultima["created_at"][:19])
        print("  " + msg)
        if rilancia(wf):
            annota(msg + " - rilancio inviato")
        else:
            annota(msg + " - RILANCIO FALLITO")
        return

    # 3) troppo tempo senza successi
    if ultimo_successo is None or (adesso - ultimo_successo) > timedelta(hours=ORE_MASSIME_SENZA_SUCCESSO):
        quando = ultimo_successo.strftime("%d/%m %H:%M") if ultimo_successo else "mai"
        msg = "%s: nessuna esecuzione riuscita da %s -> RILANCIO" % (nome, quando)
        print("  " + msg)
        if rilancia(wf):
            annota(msg + " - rilancio inviato")
        else:
            annota(msg + " - RILANCIO FALLITO")
        return

    print("  %s: ultima esecuzione riuscita il %s, tutto regolare"
          % (nome, ultimo_successo.strftime("%d/%m %H:%M")))


if __name__ == "__main__":
    print("Sorvegliante esecuzioni - %s UTC"
          % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    if not TOKEN:
        print("ERRORE: manca il token GitHub")
        raise SystemExit(1)
    for wf, nome in WORKFLOW.items():
        controlla(wf, nome)
        time.sleep(1)
    print("fine")
