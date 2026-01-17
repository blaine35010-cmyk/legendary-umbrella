import time
import json
import urllib.request

time.sleep(2)
data = json.dumps({"question": "Summarize the Final Trial Preparation Summary.", "format": "compact"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8000/ask", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print(r.read().decode("utf-8"))
except Exception as e:
    print("SMOKE TEST ERROR:", e)
    raise
