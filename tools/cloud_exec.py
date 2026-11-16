#!/usr/bin/env python3
"""Run a Luau script inside a real headless Roblox server of a game place, read-only (WE_UNIVERSE / WE_PLACE env; default Type to Defend). Never uploads a build (Open Cloud Luau Execution).

Usage:
  python3 tools/cloud_exec.py script.luau [--version N] [--timeout 300]
  python3 tools/cloud_exec.py --build script.luau     # rojo build + upload a *Saved* version first, run on it

The script's `return` values come back as JSON results; print/warn output comes back as logs.
Game scripts (Main.server) do NOT auto-run in an execution session; require modules explicitly.
Upload with --build never publishes: it creates a Saved version only.
Env: ROBLOX_API_KEY (in the cloud dev container the proxy injects it).
"""
import json, os, subprocess, sys, time, urllib.request

UNIVERSE = int(os.environ.get("WE_UNIVERSE", "10777140395"))
PLACE = int(os.environ.get("WE_PLACE", "109889925586054"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.environ.get("ROBLOX_API_KEY", "injected-by-proxy")
BASE = "https://apis.roblox.com"


def req(method, path, body=None, ctype="application/json"):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data, method=method, headers={"x-api-key": KEY, "Content-Type": ctype})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read() or b"{}")


def main():
    args = sys.argv[1:]
    version = None
    timeout = 300
    build = False
    script = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--version":
            version = int(args[i + 1]); i += 1
        elif a == "--timeout":
            timeout = int(args[i + 1]); i += 1
        elif a == "--build":
            build = True
        else:
            script = a
        i += 1
    if not script:
        print(__doc__); sys.exit(2)
    if build:
        sys.exit("--build is not supported here: the shared repo never uploads over a game place")
    path = f"/cloud/v2/universes/{UNIVERSE}/places/{PLACE}" + (f"/versions/{version}" if version else "") + "/luau-execution-session-tasks"
    task = req("POST", path, {"script": open(script).read(), "timeout": f"{timeout}s"})
    tpath = "/cloud/v2/" + task["path"]
    deadline = time.time() + timeout + 120
    while True:
        t = req("GET", tpath)
        if t.get("state") not in ("QUEUED", "PROCESSING"):
            break
        if time.time() > deadline:
            print("timed out waiting for task", file=sys.stderr); sys.exit(1)
        time.sleep(3)
    try:
        logs = req("GET", tpath + "/logs")
        for page in logs.get("luauExecutionSessionTaskLogs", []):
            for m in page.get("messages", []):
                print("LOG:", m)
    except Exception as e:  # logs are best-effort
        print("(logs unavailable:", e, ")", file=sys.stderr)
    print(json.dumps({"state": t.get("state"), "output": t.get("output"), "error": t.get("error")}, indent=2))
    sys.exit(0 if t.get("state") == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
