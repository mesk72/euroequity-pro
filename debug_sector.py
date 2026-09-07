import requests
r=requests.get("https://www.forwardalpha.pro/legal",timeout=60,
               headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
h=r.text
print("HTTP:",r.status_code)
print("  Cookie Policy presente:", "Cookie Policy" in h)
print("  clausola beta presente:", "currently in a beta version" in h)
print("  Ownership of Content:   ", "Ownership of Content" in h)
print("  sezione 6 IA:           ", "6. Use of Artificial Intelligence" in h)
print("  rimandi a Section 7:    ", h.count("Section 7"))
