# Deploy — 24/7 on a VPS

The agent must run continuously across the live window (22–28 Jun). It is
restart-safe: state is persisted before every send, so a crash/restart never
double-trades; on startup any in-flight order is reconciled, not resent.

## 1. Provision
Any small Linux VPS (1 vCPU / 1 GB is plenty). Then:

```bash
sudo useradd -m -d /opt/cmc-twak-agent agent
sudo -u agent git clone https://github.com/DanMarteens/cmc-twak-trading-agent /opt/cmc-twak-agent
cd /opt/cmc-twak-agent
sudo -u agent python3 -m venv .venv
sudo -u agent .venv/bin/pip install -r requirements.txt
```

Install TWAK for the `agent` user and import the **same agent wallet**
(`portal.trustwallet.com` → install → import wallet via seed). Verify:
`sudo -u agent twak wallet address --chain bsc` → `0x32A8…AB19`.

## 2. Secrets (`/opt/cmc-twak-agent/.env`, chmod 600)
```
CMC_MCP_API_KEY=...
ANTHROPIC_API_KEY=...
TWAK_WALLET_PASSWORD=...      # headless: no OS keychain on a server
```
`TwakExecutor`/`compete`/`erc8004` read the password from `TWAK_WALLET_PASSWORD`
when no keychain is present.

## 3. Config
Set `mode: live` in `config.yaml`. First run seeds cash from the on-chain balance.

## 4. Run under systemd (auto-restart)
```bash
sudo cp deploy/agent.service /etc/systemd/system/cmc-twak-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now cmc-twak-agent
journalctl -u cmc-twak-agent -f          # watch
```

## 5. Pre-flight (before the window opens)
- [ ] `twak compete status` → `registered: true`
- [ ] Wallet funded: BNB (gas) + USDT (in-scope balance at start)
- [ ] One live micro-swap succeeded (`scripts/` / manual `twak swap` ~$2)
- [ ] `journalctl` shows clean ticks: signal → decision → fill/blocked
- [ ] Dashboard renders from live state: `python scripts/build_dashboard.py`

## Monitoring
`logs/agent.out` (ticks/fills), `logs/decisions.jsonl` (full audit), and the
dashboard. The kill switch halts trading if peak-to-now drawdown hits 15%.
