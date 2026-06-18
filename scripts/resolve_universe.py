"""
Resolve BSC contract addresses for the eligible tokens via `twak search`
(authoritative — we never guess contracts for real-money trades).

For each eligible symbol: search on BSC, take the FIRST result whose symbol
matches exactly (case-insensitive) with a sane price (drops dust/scam clones).
Flags ambiguous symbols (>1 exact match) for manual review. Stablecoins are
recorded but tagged (they're the cash leg, not rotation targets).

    python scripts/resolve_universe.py            # full list
    python scripts/resolve_universe.py DOGE LINK  # specific symbols

Output: config/bsc_contracts.json  -> {symbol: {address, decimals, priceUsd, ambiguous}}
Review the result before trusting it live; the risk gate also runs `twak risk`.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STABLES = {"USDT", "USDC", "DAI", "TUSD", "FDUSD", "USD1", "USDe", "USDD", "FRAX",
           "FRXUSD", "USDF", "USDf", "lisUSD", "EURI", "DUSD", "XUSD", "USDf"}
MIN_PRICE = 1e-4          # below this = dust/clone, skip
SKIP = {"BTC", "BNB"}     # not eligible anyway; signal/regime only


def load_symbols():
    if len(sys.argv) > 1:
        return sys.argv[1:]
    out = []
    with open(os.path.join(ROOT, "config", "eligible_tokens.txt"), encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                out.append(s)
    return out


def search_bsc(sym):
    try:
        out = subprocess.run(["twak", "search", sym, "--networks", "bsc",
                              "--limit", "8", "--json"],
                             capture_output=True, text=True, timeout=60)
        return json.loads(out.stdout[out.stdout.find("["):])
    except Exception:
        return []


def resolve(sym):
    results = search_bsc(sym)
    exact = [r for r in results
             if r.get("chain") == "bsc"
             and (r.get("symbol", "").upper() == sym.upper())
             and (r.get("priceUsd") or 0) > MIN_PRICE]
    if not exact:
        return None
    best = exact[0]
    return {"address": best["address"], "decimals": best.get("decimals", 18),
            "priceUsd": best.get("priceUsd"), "ambiguous": len(exact) > 1}


def main():
    symbols = [s for s in load_symbols() if s not in SKIP]
    resolved, missing, ambiguous = {}, [], []
    for i, sym in enumerate(symbols, 1):
        r = resolve(sym)
        tag = ""
        if r:
            resolved[sym] = {**r, "stable": sym in STABLES}
            if r["ambiguous"]:
                ambiguous.append(sym)
                tag = "  ⚠ ambiguous"
            print(f"[{i}/{len(symbols)}] {sym:12} {r['address']}{tag}")
        else:
            missing.append(sym)
            print(f"[{i}/{len(symbols)}] {sym:12} — not resolved")

    path = os.path.join(ROOT, "config", "bsc_contracts.json")
    with open(path, "w") as f:
        json.dump(resolved, f, indent=2)

    non_stable = [s for s in resolved if not resolved[s]["stable"]]
    print(f"\nresolved {len(resolved)}/{len(symbols)}  "
          f"(tradeable non-stable: {len(non_stable)}, ambiguous: {len(ambiguous)})")
    print(f"missing: {', '.join(missing) if missing else 'none'}")
    print(f"ambiguous (review): {', '.join(ambiguous) if ambiguous else 'none'}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
