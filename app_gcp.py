# ============================================================
# FORWARDALPHA — Cloud Run Flask Wrapper
# Espone routes HTTP per Cloud Scheduler
# Routes:
#   POST /daily-eu       → daily_eu.py
#   POST /daily-apac     → daily_apac.py
#   POST /daily-us       → daily_us.py
#   POST /weekly-eu      → weekly_eu.py
#   POST /weekly-apac    → weekly_apac.py
#   POST /weekly-us      → weekly_us.py
#   POST /fetch-news     → fetch_news_cache.py
#   POST /fix-rank       → fix_combined_rank.py
#   GET  /health         → healthcheck
# ============================================================

import os
import subprocess
import sys
from flask import Flask, jsonify, request

app = Flask(__name__)

# Secret per autenticare Cloud Scheduler
CLOUD_SECRET = os.environ.get("CLOUD_SCHEDULER_SECRET", "")

def check_auth():
    """Verifica header Authorization da Cloud Scheduler"""
    auth = request.headers.get("Authorization", "")
    if CLOUD_SECRET and auth != f"Bearer {CLOUD_SECRET}":
        return False
    return True

def run_script(script_name):
    """Esegue uno script Python e restituisce output"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.exists(script_path):
        return jsonify({"error": f"Script {script_name} not found"}), 404
    
    print(f"[Cloud Run] Starting {script_name}...", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,  # Mostra output in Cloud Run logs
            timeout=3600,          # 60 minuti max
            env=os.environ.copy()
        )
        status = "success" if result.returncode == 0 else "error"
        print(f"[Cloud Run] {script_name} completed with status: {status}", flush=True)
        return jsonify({"status": status, "script": script_name, "returncode": result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({"status": "timeout", "script": script_name}), 504
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "forwardalpha-runner"})

@app.route("/daily-eu", methods=["POST"])
def daily_eu():
    return run_script("daily_eu.py")

@app.route("/daily-apac", methods=["POST"])
def daily_apac():
    return run_script("daily_apac.py")

@app.route("/daily-us", methods=["POST"])
def daily_us():
    return run_script("daily_us.py")

@app.route("/weekly-eu", methods=["POST"])
def weekly_eu():
    return run_script("weekly_eu.py")

@app.route("/weekly-apac", methods=["POST"])
def weekly_apac():
    return run_script("weekly_apac.py")

@app.route("/weekly-us", methods=["POST"])
def weekly_us():
    return run_script("weekly_us.py")

@app.route("/fetch-news", methods=["POST"])
def fetch_news():
    return run_script("fetch_news_cache.py")

@app.route("/fix-rank", methods=["POST"])
def fix_rank():
    return run_script("fix_combined_rank.py")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
