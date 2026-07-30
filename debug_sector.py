import requests
r = requests.get("https://forwardalpha.pro/?_cb=987654321", timeout=30)
print("HTTP:", r.status_code, "len:", len(r.text))
print("--- primi 2000 caratteri ---")
print(r.text[:2000])
print("--- cerco 'buildId' o '_next' ovunque nel testo ---")
import re
for m in re.finditer(r'.{0,40}_next.{0,40}', r.text):
    print(repr(m.group()))
    if m.start() > 5000: break
