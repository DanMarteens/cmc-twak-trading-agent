# Demo video script (~2.5 min)

Goal: show a working end-to-end agent + all three sponsor integrations + honest
results. Record screen + voiceover. Keep it fast.

## 0:00 — Hook (15s)
> "An autonomous trading agent for BNB Hack. It reads CoinMarketCap Agent Hub
> signals, decides on its own, and signs its own swaps on BSC via Trust Wallet
> Agent Kit. The whole game is *most profit without blowing up* — so it's built
> around a hard risk gate."

Show the dashboard (`open dashboard/index.html`) full screen.

## 0:15 — CMC Agent Hub (30s)
Run `python scripts/verify_cmc.py` → show the 12 tools.
Run a live snapshot (or show a log line): BTC RSI / MACD / EMA, Fear & Greed,
BTC dominance.
> "Every decision starts here — CMC Agent Hub. Macro regime from Fear & Greed and
> BTC dominance; per-token momentum on hourly bars."

## 0:45 — Strategy + risk (40s)
Show `agent/decision.py` (RotationDecider) and `agent/risk_gate.py`.
> "Cross-sectional rotation: hold the strongest eligible tokens in an uptrend,
> rotate to cash in a downtrend. Then one risk gate: per-position stop, daily
> pause, and a kill switch at 15% drawdown — well under the 30% DQ. Position size
> scales with how much room we have left to the DQ line."

## 1:25 — Proof: backtest + rule adherence (35s)
Run `python scripts/backtest.py --policy rotation --universe core --period year`.
> "Same code, real prices: minus 14% while the market fell minus 47%, max drawdown
> 14% — never near the DQ line."
Run `python -m agent.reporting` → point at blocked-trade reasons.
> "Every blocked trade is logged with a reason — that's our rule-adherence audit."

## 2:00 — TWAK execution + on-chain identity (25s)
Show a live `twak swap --quote-only` quote, then `twak compete status`
(registered) and the ERC-8004 `agentId`.
> "Execution is real spot swaps via Trust Wallet Agent Kit. The agent is
> registered on-chain for the competition and has an ERC-8004 identity — all three
> sponsors, working together."

## 2:25 — Close (10s)
> "Open source, reproducible decision logs, running 24/7 for the live window.
> CMC × Trust Wallet × BNB."
Show the GitHub repo URL.

---
**B-roll to capture:** dashboard, a tick in `journalctl`/logs, the decisions.jsonl
tail, `twak compete status` JSON, the repo.
