import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/auth/v1/admin/users",headers=H,params={"per_page":"50"})
print("HTTP:",r.status_code)
try:
    d=r.json()
    users=d.get("users",d) if isinstance(d,dict) else d
    print("utenti registrati:",len(users))
    print()
    for u in users:
        print("  email:",u.get("email"))
        print("    registrato:      ",u.get("created_at"))
        print("    ultimo accesso:  ",u.get("last_sign_in_at"))
        print("    email confermata:",u.get("email_confirmed_at"))
        print()
except Exception as e:
    print("errore:",e, r.text[:300])
