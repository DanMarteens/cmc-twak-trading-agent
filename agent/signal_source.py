"""
Live signal source (the fix for the universe / timeframe / CMC-credit problems).

Per-token technicals (RSI/MACD/EMA) are computed from `twak price --history`
(hourly-scale bars — the right horizon for a 1-week competition) so:
  * every trade token gets a signal (no CMC numeric id needed),
  * signals actually move within the week (vs near-static daily CMC technicals),
  * we don't burn the CMC credit budget on per-token technical calls.

CMC Agent Hub still supplies the macro layer it's unique for — Fear & Greed and
BTC dominance (one cheap call/tick) — so "uses CMC signals" stays true.
"""

from __future__ import annotations

import json
import subprocess

from .cmc_client import CMCMCPClient, MockCMCClient, _dig, _num
from .indicators import signals_from_prices


class TwakCmcSignalClient:
    _BSC_COINID = "20000714"
    _RISK_SCORE = {"low": 10, "medium": 45, "high": 85}

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.contracts = cfg["twak"]["token_contracts"]
        self.chain = cfg["twak"]["chain"]
        self.period = cfg.get("signal", {}).get("history_period", "week")
        self._risk_cache: dict[str, float] = {}    # token -> score (risk is ~static)
        try:
            self._cmc = CMCMCPClient(cfg["cmc"]["mcp_url"], ids=cfg["cmc"].get("token_ids"))
        except Exception:
            self._cmc = None                       # run with neutral macro if no key

    def token_risk_score(self, token: str) -> float:
        """0(safe)..100(risky) from `twak risk`; cached. Unknown -> 100 (block)."""
        addr = self.contracts.get(token)
        if not addr:
            return 0.0                             # benchmark/native, not traded
        if token in self._risk_cache:
            return self._risk_cache[token]
        score = 100.0
        try:
            out = subprocess.run(
                ["twak", "risk", f"c{self._BSC_COINID}_t{addr}", "--json"],
                capture_output=True, text=True, timeout=40)
            r = json.loads(out.stdout[out.stdout.find("{"):])
            if r.get("supportsSwap"):
                lvl = (r.get("securityInfo", {}) or {}).get("riskLevel", "high")
                score = self._RISK_SCORE.get(lvl, 85)
        except Exception:
            pass
        self._risk_cache[token] = score
        return score

    def _history(self, token: str) -> list[float]:
        ref = self.contracts.get(token)            # benchmark (BTC) resolves by symbol
        cmd = ["twak", "price", ref or token, "--history", self.period, "--json"]
        if ref:
            cmd += ["--chain", self.chain]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            data = json.loads(out.stdout[out.stdout.find("{"):])
            return [h["price"] for h in data.get("history", [])]
        except Exception:
            return []

    def _macro_signals(self) -> dict:
        """Fear & Greed + BTC dominance from CMC (cached per snapshot call)."""
        if self._cmc is None:
            return {"fear_greed_index": 50.0, "btc_dominance": 54.0}
        try:
            g = self._cmc.call_tool("get_global_metrics_latest", {}) or {}
            return {
                "fear_greed_index": _num(_dig(g, "sentiment", "fear_greed", "current", "index", default=50)),
                "btc_dominance": _num(_dig(g, "dominance", "btc", "current", default="54%")),
            }
        except Exception:
            return {"fear_greed_index": 50.0, "btc_dominance": 54.0}

    def get_snapshot(self, tokens: list[str]) -> dict[str, dict]:
        macro = self._macro_signals()
        snap: dict[str, dict] = {}
        for t in tokens:
            if t == self.cfg["quote_asset"]:
                continue
            prices = self._history(t)
            if len(prices) < 2:
                continue                           # no data -> skip (off-universe/illiquid)
            snap[t] = {"price": prices[-1], **signals_from_prices(prices),
                       **macro, "news_sentiment": 0.0,
                       "token_risk_score": self.token_risk_score(t)}
        return snap


def build_signal_source(cfg: dict):
    """Live -> TWAK price-history TA + CMC macro; dry-run -> deterministic mock."""
    if cfg.get("mode") == "live":
        return TwakCmcSignalClient(cfg)
    return MockCMCClient()
