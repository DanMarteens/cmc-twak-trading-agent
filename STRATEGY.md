# Strategy Explainer — CMC-TWAK Autonomous Trading Agent

**BNB Hack: AI Trading Agent Edition · Track 1**
Agent wallet (BSC): `0x32A84F2cf8D55a8eC5414D7DC42b0D873A98AB19`
Repo: https://github.com/DanMarteens/cmc-twak-trading-agent

## Thesis
Track 1 ranks by **total return** with a **hard ~30% max-drawdown DQ** ("most profit
without blowing up"). So the agent is built to **maximize return subject to never
touching the DQ line** — the edge is in competition-aware risk engineering and
relative-strength selection, not a secret indicator.

## How it decides
1. **Signals — CMC Agent Hub + hourly technicals.** Macro regime from CMC Agent Hub
   (Fear & Greed, BTC dominance); per-token RSI/MACD/EMA computed on ~3h bars from
   price history (the right horizon for a one-week contest — daily indicators barely
   move in 7 days). A deterministic, judge-reproducible engine turns these into a
   score in [-1, +1] per token and a global regime (trend-up / trend-down / chop).
2. **Decision — cross-sectional rotation.** Rather than waiting for absolute per-token
   setups, the agent ranks the eligible universe by momentum and **holds the top-K
   strongest** in an uptrend, **rotates to cash (USDT)** in a downtrend, and **holds**
   in chop. This guarantees participation (trade cadence), captures upside, and
   preserves capital in risk-off.
3. **Risk gate — every trade passes one chokepoint.** Position-size cap, **tournament
   sizing** (size scales with remaining headroom to the DQ line), concentration cap,
   `twak risk` token screening, trade-rate limits, and a **layered drawdown defense**:
   per-position stop (4%) → daily entry pause → **kill switch** (15% peak-to-now:
   liquidate all + halt). Every blocked trade is logged with a reason.
4. **Execution — Trust Wallet Agent Kit.** Spot swaps on BSC with a slippage cap and a
   quote check before sending; idempotent orders (a crash never double-trades).

## Rules compliance (built in)
- Only the **149 eligible BEP-20 tokens** are tradeable (off-list trades are blocked);
  universe is filter-verified for liquidity + `twak risk`.
- **≥1 trade/day** guaranteed via a maintenance trade; portfolio kept deployed
  (>$1/hour rule honored).
- On-chain registration via `twak compete register`; **ERC-8004 identity** minted via
  `twak erc8004 register`.

## Honest backtest (real prices, same code path)
On a 1-year replay through the live decision/risk code: **−11% while an equal-weight
basket of the same tokens fell −44%**, with **max drawdown 13.5%** (never near the 30%
DQ) over 80+ trades. The story is downside protection + relative strength, not leverage.
*Caveat: coarse historical bars in a down market; the live week is the real test.*

## Stack (all three sponsors)
**CoinMarketCap Agent Hub** (signals) · **Trust Wallet Agent Kit** (self-custody
execution) · **BNB AI Agent SDK / ERC-8004** (on-chain identity).
