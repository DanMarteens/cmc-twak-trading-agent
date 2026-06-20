# Demo video script (~3 min)

Goal: an honest walkthrough that still feels alive. Tone is a builder who's
genuinely into what they made, talking to you like a person — warm, a bit of
conviction, but no hype and no overselling. The screen carries the proof: real
terminal, real dashboard, real on-chain transactions. Say the tradeoffs out loud;
that's what makes the good parts land. Everything is verifiable (GitHub + bscscan).

Delivery: talk, don't read. A little energy is good — you built this, be into it.
Just don't sell. If a number's on screen, say it plainly. If it's a simulation,
call it a simulation.

## 0:00 — What this is (20s)
Show the dashboard, then the running service (`systemctl status` / a log tail).
> "So this is something I've been building for BNB Hack — a trading agent that runs
> completely on its own. It sits on a little server, checks the market every 15
> minutes, and signs its own swaps on BSC. Let me actually show you it running and
> walk through how it works. No mockups — and the on-chain stuff, you can go verify
> yourself."

## 0:20 — Where the decisions come from (35s)
Run `python scripts/verify_cmc.py` (tool list), then a real snapshot / log line:
RSI, MACD, EMA per token, plus Fear & Greed and BTC dominance.
> "Everything starts with data. The agent pulls from CoinMarketCap's Agent Hub —
> momentum on each coin, so RSI, MACD, moving averages — plus the bigger picture:
> Fear and Greed, Bitcoin dominance, funding rates. All of that gets boiled down
> into a single score per coin. This right here is the raw input, straight from the
> API."

## 0:55 — The strategy, and what it won't do (45s)
Show `agent/decision.py` and `agent/risk_gate.py`. Be straight about the tradeoff.
> "The strategy itself is simple on purpose. Uptrend, it holds the strongest coins.
> Downtrend, it backs off to cash. And here's where I'll be straight with you —
> this is a careful design, not an aggressive one. If the market just rips upward
> all week, a riskier bot will beat it. I built mine not to blow up, because the
> contest disqualifies you around 30% drawdown. It's spot only too — no shorts, no
> leverage — that's what the Trust Wallet kit gives you. And every single trade
> clears a risk gate first: stop-losses, a daily pause, a kill switch."

## 1:40 — Proof, and what the proof is worth (40s)
Run `python scripts/backtest.py --policy rotation --universe core --period year`,
then `python -m agent.reporting` to show blocked-trade reasons.
> "So does it hold up? This is a backtest on a full year of real prices — and to be
> fair, a backtest is a simulation, not a guarantee. But over a stretch where the
> market dropped about 47%, the agent was only down around 12, and it never touched
> the disqualification line. That's exactly what I was going for. And every trade it
> chooses to skip gets logged with the reason — so it's auditable, not a black box."

## 2:20 — The three integrations, with receipts (35s)
Show the dashboard "sponsor stack" card, then a terminal: a `twak swap
--quote-only`, a `twak x402 request` returning a price-paid signal, and bscscan
open on the ERC-8004 metadata transaction with `twak erc8004 get-metadata`.
> "Three integrations, and I really wanted each one to earn its place. CoinMarketCap
> is the eyes. Trust Wallet's kit signs the swaps — and it even pays for premium
> signals itself, about a tenth of a cent each, over x402. Here's one going through.
> And on BNB Chain it's got its own ERC-8004 identity, where it writes its track
> record on-chain. There's the transaction — you can read the numbers right off the
> contract."

## 2:55 — Close (15s)
Show the GitHub repo and the dashboard URL.
> "And that's the agent. It's open source, the full decision log is public, and the
> on-chain records are there if you want to check any of this for yourself. Thanks
> for watching."

---
**Delivery tips:** speak like you're showing a friend something you're proud of —
warm, not flat, but never salesy. Let terminal output sit on screen long enough to
read. The honesty in the strategy and proof sections is the point; deliver it
plainly and let it land.

**B-roll to capture:** dashboard (incl. the sponsor-stack card), `systemctl
status`, a tick in the logs, the decisions.jsonl tail, `twak compete status`, a
`twak x402 request` firing, the bscscan ERC-8004 transaction, the repo.
