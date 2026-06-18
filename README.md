# CMC × TWAK Autonomous Trading Agent — BNB HACK Track 1

Autonomous BSC trading agent: reads **CoinMarketCap Agent Hub** signals → ranks the
eligible universe by cross-sectional momentum → enforces a hard **risk gate** →
executes **spot swaps via Trust Wallet Agent Kit** on BSC → mints an **ERC-8004**
on-chain identity (BNB AI Agent SDK).

Built for *BNB HACK: AI Trading Agent Edition*. Live trading **22–28 Jun**, judged on
a held-out window by **total return** with a hard ~30% max-drawdown DQ —
*"most profit without blowing up."*

Agent wallet (BSC): `0x32A84F2cf8D55a8eC5414D7DC42b0D873A98AB19`

## Why this design wins

The score is **total return** with a **hard ~30% drawdown DQ**, a **≥1 trade/day**
minimum, **simulated tx costs**, and a **keep-capital-deployed** rule. The edge is in
competition-aware risk engineering + relative-strength selection, not a secret signal:

| Criterion | What the agent does |
|---|---|
| **Returns** | **Cross-sectional rotation** — holds the top-K strongest eligible tokens by momentum in uptrends, rotates to cash in downtrends. Signals are **hourly** (right horizon for a 1-week contest), driven by CMC Agent Hub. |
| **Drawdown** | **Layered defense**: per-position stop (4%) → daily entry pause (resets next day) → **kill switch at 15% peak-to-now** (liquidate all + halt). Buffer well under the ~30% DQ. |
| **Risk-adjusted** | **Tournament sizing**: position size scales with the remaining headroom to the DQ line — assertive while healthy, automatically de-risks near the edge. |
| **Rule adherence** | One `risk_gate` enforces every limit; **every blocked trade is logged with a reason**. Min 1 trade/day guaranteed; eligible-token + keep-deployed rules built in. |

### Backtest (real prices, same code path as live)

Replaying 1 year of real prices through the live decision/risk code over 40 liquid
eligible tokens: **−14% while an equal-weight basket of the same tokens fell −47%**,
**max drawdown 14%** (never near the 30% DQ), 95 trades. Downside protection + relative
strength, not leverage. *Caveat: coarse historical bars in a down market — the live
week is the real test.* See the dashboard: `python scripts/build_dashboard.py`.

## Architecture

```
CMC Agent Hub ─F&G / BTC dominance──┐
twak price --history ─hourly TA─────┴► signal_engine ─score[-1..1]+regime─► rotation
                                                                              │ decisions
   state / decision log ◄── executor (TWAK spot swap) ◄──pass── risk_gate ◄───┘
                                                          │ fail → blocked + logged
twak erc8004 register ──► on-chain agent identity   ·   twak compete register ──► entry
```

| File | Role |
|---|---|
| `agent/signal_source.py` | Live signals: hourly RSI/MACD/EMA from TWAK price history + CMC macro |
| `agent/indicators.py` | EMA / RSI / MACD (shared by live + backtest) |
| `agent/signal_engine.py` | Deterministic score `[-1,1]` + regime (judge-reproducible) |
| `agent/decision.py` | `RotationDecider` (default) + threshold + Claude deciders |
| `agent/risk_gate.py` | All risk checks + tournament sizing + layered drawdown defense |
| `agent/executor.py` | TWAK spot swap (USD-in / token-out), slippage cap, idempotency |
| `agent/state.py` | Persistent positions, idempotent orders, drawdown tracking |
| `agent/agent.py` | Main loop: reconcile → de-risk → signal → decide → gate → execute → log |
| `agent/reporting.py` | PnL, max drawdown, Sharpe-like, trade/block summary |
| `scripts/` | `verify_cmc`, `resolve_universe`, `build_universe`, `backtest`, `build_dashboard`, `register` |

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q                              # 35 tests

# offline demo (no keys)
.venv/bin/python scripts/demo.py --ticks 60 --cash 200 && .venv/bin/python -m agent.reporting

# backtest on real prices + build the dashboard
.venv/bin/python scripts/backtest.py --policy rotation --universe core --period year
.venv/bin/python scripts/build_dashboard.py && open dashboard/index.html
```

## Going live (trading window)

1. `cp .env.example .env`; set `CMC_MCP_API_KEY` (+ `ANTHROPIC_API_KEY` to enable the LLM layer).
2. Install TWAK (`portal.trustwallet.com`), create the **agent wallet**, fund **minimal** BNB (gas) + USDT (capital) on BSC.
3. `bash scripts/register.sh` → `twak compete register` + `twak erc8004 register` (needs gas).
4. Set `mode: live` in `config.yaml`, then run under `systemd` for 24/7 uptime — see [DEPLOY.md](DEPLOY.md).

> ⚠️ Real funds on mainnet. Every limit lives in `config.yaml`; keep capital minimal.

## Rule-adherence evidence
`logs/decisions.jsonl` records the full chain per tick: `tick → signal → decision →
blocked|fill (tx_hash)`. `python -m agent.reporting` summarizes blocked trades by reason.

## Sponsor stack (all three)
- [x] **CoinMarketCap Agent Hub** — signals drive every decision (live MCP verified, `scripts/verify_cmc.py`)
- [x] **Trust Wallet Agent Kit** — self-custody spot execution + on-chain competition registration
- [x] **BNB AI Agent SDK / ERC-8004** — on-chain agent identity (`scripts/register.sh`)
