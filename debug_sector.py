from datetime import datetime, timedelta
TODAY = datetime.now().strftime("%Y-%m-%d")
END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
print(f"TODAY calcolato ORA sul runner GitHub: {TODAY}")
print(f"END_FOR_DOWNLOAD: {END_FOR_DOWNLOAD}")
print(f"Test confronto: '2026-07-21' >= TODAY -> {'2026-07-21' >= TODAY}")
