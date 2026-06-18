"""
Build the maximal SAFE tradeable universe from the resolved contracts.

From config/bsc_contracts.json, keep a token only if ALL hold:
  * not a stablecoin (stables are the cash leg, not rotation targets)
  * not ambiguous (multiple same-symbol matches = scam risk)
  * has usable price history (>= MIN_BARS) — else no signal
  * `twak risk` says supportsSwap and riskLevel != high

Output: config/trade_universe.json {symbol: address}. load_config picks it up
via twak.contracts_file. This is how we get breadth (rotation needs it) without
trading illiquid or scam tokens.

    python scripts/build_universe.py
"""

import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BSC_COINID = "20000714"
MIN_BARS = 35
STABLES = {"USDT", "USDC", "DAI", "TUSD", "FDUSD", "USD1", "USDe", "USDD", "FRAX",
           "FRXUSD", "USDF", "USDf", "lisUSD", "EURI", "DUSD", "XUSD"}


def _twak_json(args):
    try:
        out = subprocess.run(["twak", *args, "--json"], capture_output=True, text=True, timeout=60)
        s = out.stdout
        start = min([i for i in (s.find("{"), s.find("[")) if i >= 0], default=-1)
        return json.loads(s[start:]) if start >= 0 else None
    except Exception:
        return None


def has_history(addr):
    d = _twak_json(["price", addr, "--chain", "bsc", "--history", "week"])
    return bool(d) and len(d.get("history", [])) >= MIN_BARS


def is_safe(addr):
    r = _twak_json(["risk", f"c{BSC_COINID}_t{addr}"])
    if not r or "error" in r:
        return False
    lvl = (r.get("securityInfo", {}) or {}).get("riskLevel", "high")
    return r.get("supportsSwap", False) and lvl != "high"


def main():
    with open(os.path.join(ROOT, "config", "bsc_contracts.json")) as f:
        resolved = json.load(f)
    keep, dropped = {}, {}
    cand = [(s, v) for s, v in resolved.items()
            if not v.get("stable") and not v.get("ambiguous") and s not in STABLES]
    for i, (sym, v) in enumerate(cand, 1):
        addr = v["address"]
        if not has_history(addr):
            dropped[sym] = "no_history"
        elif not is_safe(addr):
            dropped[sym] = "risk/no_swap"
        else:
            keep[sym] = addr
        print(f"[{i}/{len(cand)}] {sym:12} {'KEEP' if sym in keep else 'drop:'+dropped.get(sym,'')}")

    out = os.path.join(ROOT, "config", "trade_universe.json")
    with open(out, "w") as f:
        json.dump(keep, f, indent=2)
    print(f"\nKEPT {len(keep)} / {len(cand)} candidates -> {out}")
    print("dropped:", json.dumps(dropped))


if __name__ == "__main__":
    main()
