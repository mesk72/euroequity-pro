import sys, os, base64, json, requests

files = sys.argv[1:]
token = os.environ["GH_TOKEN"]
repo = os.environ["GH_REPO"]
headers = {"Authorization": f"token {token}"}

for fname in files:
    if not os.path.exists(fname):
        continue
    with open(fname, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    r = requests.get(f"https://api.github.com/repos/{repo}/contents/{fname}", headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"output: {fname}", "content": content_b64}
    if sha:
        payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{repo}/contents/{fname}", headers=headers, json=payload)
    print(f"{fname}: HTTP {rp.status_code}")
