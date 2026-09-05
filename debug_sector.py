import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/auth/v1/admin/users",headers=H,params={"per_page":"50"})
d=r.json(); users=d.get("users",d) if isinstance(d,dict) else d
TIENI=["andreameschini19@gmail.com","infocasualinstyle03@gmail.com"]
print("=== UTENTI REGISTRATI (%d) ===" % len(users))
for u in users:
    em=(u.get("email") or "").lower()
    stato="  <-- DA TENERE" if em in [t.lower() for t in TIENI] else "      da rimuovere"
    print("  %-40s registrato %s  ultimo accesso %s %s" % (
        u.get("email"), (u.get("created_at") or "")[:10],
        (u.get("last_sign_in_at") or "mai")[:10], stato))
