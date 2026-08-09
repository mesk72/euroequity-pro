import requests
for u in ["https://forwardalpha.pro/robots.txt","https://forwardalpha.pro/sitemap.xml"]:
    try:
        r=requests.get(u,timeout=30)
        print("---",u,"HTTP",r.status_code,"---")
        print(r.text[:600])
    except Exception as e: print(u,"errore",e)
