#!/usr/bin/env python3
"""Deterministic non-interactive smoke runner.
Posts a fixed set of questions to the local /ask endpoint and writes
results to web/smoke_results_final.json.
"""
import json
import time
import urllib.request
import urllib.error
import subprocess
import os
from datetime import datetime

DEFAULT_PORT = 8000
OUT = "web/smoke_results_final.json"

def detect_server_port():
    # prefer explicit server.port file if present
    pf = os.path.join("web", "server.port")
    if os.path.exists(pf):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                p = int(f.read().strip())
                return p
        except Exception:
            pass
    return DEFAULT_PORT

def server_url_for_port(port):
    return f"http://127.0.0.1:{port}/ask"

def health_url_for_port(port):
    return f"http://127.0.0.1:{port}/health"

def start_local_server_if_needed(port, timeout=10):
    # if health is already up, do nothing
    import urllib.request
    try:
        with urllib.request.urlopen(health_url_for_port(port), timeout=1) as r:
            if r.status == 200:
                return True
    except Exception:
        pass

    # attempt to start the simple_server.py using the venv python if available
    venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"

    log_path = os.path.join("web", "server.log")
    with open(log_path, "a", encoding="utf-8") as lf:
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd()
            subprocess.Popen([venv_python, "web/simple_server.py"], stdout=lf, stderr=lf, env=env)
        except Exception as e:
            lf.write(f"Failed to start server: {e}\n")

    # wait for the server to become available
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url_for_port(port), timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

TESTS = [
    {"name": "final_trial_prep_summary", "body": {"question": "Summarize the Final Trial Preparation Summary.", "format": "compact"}},
    {"name": "case_overview", "body": {"question": "Give a short overview of the case facts.", "format": "compact"}},
    {"name": "important_dates", "body": {"question": "List important dates mentioned in the corpus.", "format": "compact"}},
]

def run_test(t, server_url):
    payload = json.dumps(t["body"]).encode("utf-8")
    req = urllib.request.Request(server_url, data=payload, headers={"Content-Type": "application/json"})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = r.read().decode("utf-8")
        elapsed = time.time() - start
        try:
            parsed = json.loads(resp)
        except Exception:
            parsed = resp
        return {"name": t["name"], "ok": True, "response": parsed, "time_s": round(elapsed, 3)}
    except Exception as e:
        elapsed = time.time() - start
        return {"name": t["name"], "ok": False, "error": str(e), "time_s": round(elapsed, 3)}


def main():
    results = {"started_at": datetime.utcnow().isoformat() + "Z", "tests": []}

    port = detect_server_port()
    server_url = server_url_for_port(port)

    # try to ensure server is running
    ok = False
    for attempt in range(3):
        print(f"Checking server health on port {port} (attempt {attempt+1})")
        if start_local_server_if_needed(port, timeout=10):
            ok = True
            break
        time.sleep(1)

    if not ok:
        print(f"Server not available on port {port}; proceeding with tests (they may fail)")

    for t in TESTS:
        print("RUNNING:", t["name"])
        r = run_test(t, server_url)
        print(" ->", "OK" if r.get("ok") else "FAILED")
        results["tests"].append(r)

    results["finished_at"] = datetime.utcnow().isoformat() + "Z"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Wrote", OUT)

    # if any failed, collect server.log for diagnosis
    if any(not t.get("ok") for t in results.get("tests", [])):
        try:
            with open(os.path.join("web", "server.log"), "r", encoding="utf-8") as lf:
                logs = lf.read()
        except Exception:
            logs = "(no server.log available)"
        with open(os.path.join("web", "smoke_fail_logs.txt"), "w", encoding="utf-8") as outf:
            outf.write(logs)
        print("Wrote web/smoke_fail_logs.txt (server logs)")


if __name__ == "__main__":
    main()
