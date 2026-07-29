import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"created_at,log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"10"})
logs = r.json()
for log in logs:
    print(f"\n===== {log['created_at']} =====")
    txt = log["log_text"]
    # Mostra solo le righe con parole chiave utili (errori, ASX, riepilogo)
    for line in txt.split("\n"):
        if any(k in line for k in ["ASX", "error", "Error", "ERROR", "fail", "ok=", "Prezzi", "Traceback", "Exception", "chunk", "rate", "429", "timeout"]):
            print(line)
