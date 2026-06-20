#!/usr/bin/env bash
# Flip the agent from dry-run/paper to LIVE trading. Fired by cmc-golive.timer at the
# window open (22 Jun 00:05 UTC), or run manually. Reads the seed balance FIRST and
# aborts BEFORE touching state if the wallet isn't funded — never leaves a dead agent.
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; . .env; set +a

USDT="0x55d398326f99059fF775485246999027B3197955"
ADDR=$(.venv/bin/python -c "import yaml;print(yaml.safe_load(open('config.yaml'))['twak']['agent_address'])")

echo "== reading on-chain USDT (address $ADDR) — before touching anything =="
RAW=$(twak balance --address "$ADDR" --token "$USDT" --chain bsc --json 2>/dev/null || true)
SEED=$(printf '%s' "$RAW" | .venv/bin/python -c "import sys,json
s=sys.stdin.read(); i=s.find('{')
try:
    print(round(float(json.loads(s[i:]).get('available') or 0), 2))
except Exception:
    print(0)")
echo "seed cash = \$$SEED"
if ! .venv/bin/python -c "import sys;sys.exit(0 if float('$SEED')>=1 else 1)"; then
  echo "ABORT: USDT balance < \$1 (got \$$SEED). Fund the wallet and re-run. State untouched."
  exit 1
fi

echo "== stopping service + clearing dry-run/paper state =="
systemctl stop cmc-twak-agent || true
rm -f state/portfolio.json logs/decisions.jsonl dashboard/bench_anchor.json

echo "== mode -> live (via .env, survives git pull) =="
grep -q '^AGENT_MODE=' .env && sed -i 's/^AGENT_MODE=.*/AGENT_MODE=live/' .env || echo 'AGENT_MODE=live' >> .env

echo "== seeding live state (one tick) =="
AGENT_MODE=live .venv/bin/python -m agent.agent --once --seed-cash "$SEED" \
  || echo "seed tick errored — service will continue on restart"

echo "== starting 24/7 service =="
systemctl start cmc-twak-agent
sleep 3
systemctl is-active cmc-twak-agent && echo "LIVE. watch: journalctl -u cmc-twak-agent -f"
