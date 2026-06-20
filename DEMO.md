# Demo video script (~3 min)

Goal: an honest engineering walkthrough, not an ad. Tone is a dev showing their
work to other devs — calm, specific, first person. The screen does the talking:
real terminal, real dashboard, real on-chain transactions. State the limitations
out loud; that's what makes the strong parts believable. Everything shown is
verifiable (GitHub + bscscan), and we say so.

Rule for delivery: no superlatives, no "amazing/wild/game-changing", no
exclamation hooks. If a number is on screen, read it as-is. If something is a
simulation, call it a simulation.

## 0:00 — What this is (20s)
Show the dashboard, then the running service (`systemctl status` / a log tail).
> "This is a trading agent I built for BNB Hack. It runs on a small server, reads
> the market every 15 minutes, and signs its own spot swaps on BSC. I want to walk
> through how it actually works and show you it running — not a mockup. Everything
> here is in the repo, and the on-chain parts you can check yourself."

## 0:20 — Where the decisions come from (35s)
Run `python scripts/verify_cmc.py` (tool list), then a real snapshot / log line:
RSI, MACD, EMA per token, plus Fear & Greed and BTC dominance.
> "Every decision starts with data from CoinMarketCap's Agent Hub. Per coin it
> pulls momentum — RSI, MACD, moving averages — and on top of that the market-wide
> stuff: Fear and Greed, Bitcoin dominance, funding rates. Those get combined into
> one score per token. This is the raw input, straight from the API."

## 0:55 — The strategy, and what it won't do (45s)
Show `agent/decision.py` and `agent/risk_gate.py`. Be straight about the tradeoff.
> "The logic is deliberately simple. In an uptrend it rotates into the strongest
> coins; in a downtrend it steps back toward cash. I'll be honest about the
> tradeoff: this is a conservative design. If the week is a straight pump, a more
> aggressive bot will out-return it. I optimized for not blowing up instead,
> because the contest disqualifies you past about 30% drawdown. It's also spot
> only — no shorts, no leverage — because that's what the Trust Wallet kit
> supports. Before any trade, it goes through a risk gate: per-position stops, a
> daily loss pause, and a hard kill switch."

## 1:40 — Proof, and what the proof is worth (40s)
Run `python scripts/backtest.py --policy rotation --universe core --period year`,
then `python -m agent.reporting` to show blocked-trade reasons.
> "Here's a backtest on a year of real prices — and I want to be clear this is a
> simulation, not a promise. Over a stretch where the market fell about 47%, the
> agent was down around 12 and never hit the disqualification line. That's the
> behavior I was after. And every trade it decides not to make is logged with a
> reason, so the decision log is auditable rather than a black box."

## 2:20 — The three integrations, with receipts (35s)
Show the dashboard "sponsor stack" card, then a terminal: a `twak swap
--quote-only`, a `twak x402 request` returning a price-paid signal, and bscscan
open on the ERC-8004 metadata transaction with `twak erc8004 get-metadata`.
> "Three integrations, and each one does real work rather than just being wired in.
> CoinMarketCap is the data layer. Trust Wallet's kit signs the swaps and pays
> about a tenth of a cent per premium signal over x402 — here's the request. And on
> BNB Chain the agent has an ERC-8004 identity that it writes its own track record
> to, on-chain. That's the transaction, and you can read the value straight off the
> contract."

## 2:55 — Close (15s)
Show the GitHub repo and the dashboard URL.
> "That's the agent. It's open source, the decision log is public, and the on-chain
> records are there if you want to verify any of this independently. Thanks for
> taking a look."

---
**Delivery tips:** speak at a normal pace, like you're explaining it to a
colleague. Let the terminal output sit on screen long enough to read. Don't sell
the numbers — just show them. The honesty in the strategy and proof sections is
the point; don't soften it.

**B-roll to capture:** dashboard (incl. the sponsor-stack card), `systemctl
status`, a tick in the logs, the decisions.jsonl tail, `twak compete status`, a
`twak x402 request` firing, the bscscan ERC-8004 transaction, the repo.
