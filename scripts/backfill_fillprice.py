"""
One-off: reconstruct fill_price for OLD fill events that predate fill_price logging.

For each traded token, pull `twak price --history` (timestamped bars) and match each
fill event to the nearest bar by time. Approximate (~3h bar granularity, no slippage)
but lets the dashboard show entry/exit prices for historical paper trades. The live
window (go_live.sh clears the log) logs exact fill prices, so this is pre-launch only.

    python scripts/backfill_fillprice.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.agent import load_config

cfg = load_config("config.yaml")
contracts = cfg["twak"]["token_contracts"]
chain = cfg["twak"]["chain"]
LOG = cfg["paths"]["decision_log"]

rows = [json.loads(l) for l in open(LOG)]
toks = {r["token"] for r in rows
        if r.get("kind") == "fill" and not r.get("fill_price") and r.get("token") in contracts}

hist = {}
for t in toks:
    try:
        out = subprocess.run(["twak", "price", contracts[t], "--history", "week",
                              "--chain", chain, "--json"], capture_output=True, text=True, timeout=45)
        d = json.loads(out.stdout[out.stdout.find("{"):])
        hist[t] = [(float(h["date"]), float(h["price"])) for h in d.get("history", [])]
    except Exception:
        hist[t] = []


def nearest(tok, ts_iso):
    h = hist.get(tok) or []
    if not h:
        return None
    e = datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).timestamp()
    return min(h, key=lambda b: abs(b[0] - e))[1]


n = 0
for r in rows:
    if r.get("kind") == "fill" and not r.get("fill_price") and r.get("token") in hist and r.get("ts"):
        px = nearest(r["token"], r["ts"])
        if px:
            r["fill_price"] = round(px, 8)
            n += 1

with open(LOG, "w") as f:
    for r in rows:
        f.write(json.dumps(r, default=str) + "\n")
print(f"backfilled fill_price on {n} historical fills (from {len(hist)} token histories)")
