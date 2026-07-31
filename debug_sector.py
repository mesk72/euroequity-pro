from datetime import datetime, timedelta

def fai(ora_limite):
    def seduta_conclusa(date_str):
        try: d = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception: return False
        return datetime.utcnow() >= d.replace(hour=ora_limite, minute=0, second=0)
    return seduta_conclusa

adesso = datetime.utcnow()
print("Adesso (UTC):", adesso.strftime("%Y-%m-%d %H:%M"))
oggi = adesso.strftime("%Y-%m-%d")
ieri = (adesso - timedelta(days=1)).strftime("%Y-%m-%d")
laltroieri = (adesso - timedelta(days=2)).strftime("%Y-%m-%d")

for nome, limite in [("APAC", 10), ("Europa", 17), ("USA", 22)]:
    f = fai(limite)
    print("\n%s (limite %02d:00 UTC)" % (nome, limite))
    for et, d in [("oggi        ", oggi), ("ieri        ", ieri), ("l'altroieri ", laltroieri)]:
        print("   %s %s -> %s" % (et, d, "ACCETTATA" if f(d) else "SCARTATA (seduta non chiusa)"))
