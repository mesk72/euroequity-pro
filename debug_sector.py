import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
TIENI={"andreameschini19@gmail.com","infocasualestyle03@gmail.com"}
r=requests.get(U+"/auth/v1/admin/users",headers=H,params={"per_page":"50"})
d=r.json(); users=d.get("users",d) if isinstance(d,dict) else d
da_togliere=[u for u in users if (u.get("email") or "").lower() not in TIENI]
print("Da rimuovere: %d | da tenere: %d" % (len(da_togliere), len(users)-len(da_togliere)))
print()
for u in da_togliere:
    uid=u["id"]; em=u.get("email")
    # 1) dati collegati: watchlist
    w=requests.get(U+"/rest/v1/watchlist",headers={**H,"Prefer":"count=exact"},
        params={"select":"id","user_id":"eq."+uid,"limit":"1"})
    n=w.headers.get("content-range","0/0").split("/")[-1]
    requests.delete(U+"/rest/v1/watchlist",headers=H,params={"user_id":"eq."+uid})
    # 2) profilo, se esiste
    requests.delete(U+"/rest/v1/profiles",headers=H,params={"id":"eq."+uid})
    # 3) account
    dd=requests.delete(U+"/auth/v1/admin/users/"+uid,headers=H)
    print("  %-38s watchlist %-4s account -> HTTP %s" % (em,n,dd.status_code))
print()
print("=== VERIFICA FINALE ===")
r2=requests.get(U+"/auth/v1/admin/users",headers=H,params={"per_page":"50"})
d2=r2.json(); u2=d2.get("users",d2) if isinstance(d2,dict) else d2
print("utenti rimasti: %d" % len(u2))
for u in u2: print("   %-38s ultimo accesso %s" % (u.get("email"),(u.get("last_sign_in_at") or "mai")[:10]))
print()
rc=requests.get(U+"/rest/v1/watchlist",headers={**H,"Prefer":"count=exact"},params={"select":"id","limit":"1"})
print("righe watchlist rimaste:", rc.headers.get("content-range","?").split("/")[-1])
