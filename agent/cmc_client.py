"""
CMC Agent Hub client (F1) — the agent's eyes.

Two implementations behind one interface so the whole pipeline runs today:
  * MockCMCClient    — deterministic synthetic data; no network/key needed.
  * CMCMCPClient     — real CoinMarketCap MCP (JSON-RPC over HTTP).

`get_snapshot(tokens)` returns, per token:
  { price, rsi, macd_state, ema_trend, fear_greed_index, btc_dominance,
    news_sentiment }
matching exactly what signal_engine expects.

NOTE on the real client: the MCP transport (initialize -> tools/call) is wired,
but the 12 tool NAMES and their argument/response shapes must be confirmed
against the live server's tools/list (see _TOOL_NAMES). Confirm in the Builder
Telegram / by calling list_tools() once, then fill the mapping. Everything else
(signal, risk, executor, loop, reporting) is independent of this detail.
"""

from __future__ import annotations

import json
import os
from typing import Protocol


class CMCClient(Protocol):
    def get_snapshot(self, tokens: list[str]) -> dict[str, dict]: ...


# --- Mock (offline / dry-run) --------------------------------------------------
class MockCMCClient:
    """Synthetic but internally-consistent market data for offline testing.

    Uses a seed so a given tick is reproducible. Produces a mild uptrend on BTC
    so the regime is well-defined in demos.
    """

    _BASE_PRICES = {"BNB": 600.0, "CAKE": 2.4, "ETH": 3500.0, "BTC": 65000.0, "USDT": 1.0}

    def __init__(self, seed: int | None = None):
        # None -> time-varying so consecutive runs differ; int -> reproducible.
        self.seed = seed
        self._tick = 0
        self._prices: dict[str, float] = {}   # coherent random walk across ticks

    def get_snapshot(self, tokens: list[str]) -> dict[str, dict]:
        import random
        import time as _time

        base = self.seed if self.seed is not None else int(_time.time())
        rng = random.Random(base + self._tick)
        self._tick += 1
        fg = rng.randint(30, 70)
        btc_dom = round(rng.uniform(50, 58), 2)
        snap: dict[str, dict] = {}
        trends = ["up", "down", "flat"]
        macds = ["bullish_cross", "bullish", "neutral", "bearish", "bearish_cross"]
        for t in tokens:
            # coherent price: small drift + noise on the previous price
            px = self._prices.get(t, self._BASE_PRICES.get(t, 100.0))
            drift = 0.002 if t == "BTC" else rng.uniform(-0.01, 0.01)
            px = max(0.01, px * (1 + drift + rng.uniform(-0.02, 0.02)))
            self._prices[t] = px

            if t == "BTC":
                ema, macd = "up", "bullish"      # define the regime for demos
            else:
                ema, macd = rng.choice(trends), rng.choice(macds)
            snap[t] = {
                "price": round(px, 4),
                "rsi": round(rng.uniform(20, 80), 1),
                "macd_state": macd,
                "ema_trend": ema,
                "fear_greed_index": fg,
                "btc_dominance": btc_dom,
                "news_sentiment": round(rng.uniform(-0.5, 0.5), 2),
            }
        return snap


# --- Real CMC MCP client (tool names + shapes verified against live server) ----
# Tools require a CMC numeric `id` (not symbol). Default map for our universe;
# extend / resolve via search_cryptos for the full 149-token list.
_DEFAULT_IDS = {"BTC": "1", "ETH": "1027", "BNB": "1839", "CAKE": "7186", "USDT": "825"}
_TOOL = {
    "quotes": "get_crypto_quotes_latest",
    "technicals": "get_crypto_technical_analysis",
    "global": "get_global_metrics_latest",
    "news": "get_crypto_latest_news",
}


def _num(x, default: float = 0.0) -> float:
    """Parse CMC's display strings into floats: '+58.18%', '608.13', '2.16 T'."""
    if isinstance(x, (int, float)):
        return float(x)
    if not isinstance(x, str):
        return default
    s = x.strip().replace(",", "").replace("%", "").replace("+", "")
    mult = 1.0
    for suf, m in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if s.upper().endswith(suf):
            mult = m
            s = s[:-1].strip()
            break
    try:
        return float(s) * mult
    except ValueError:
        return default


def derive_macd_state(macd: dict) -> str:
    """histogram = macdLine - signalLine. Sign -> bullish/bearish, ~0 -> neutral."""
    hist = _num(macd.get("histogram"))
    line = _num(macd.get("macdLine"))
    sig = _num(macd.get("signalLine"))
    eps = 1e-6
    if hist > eps and line >= sig:
        return "bullish"
    if hist < -eps and line <= sig:
        return "bearish"
    return "neutral"


def derive_ema_trend(ma: dict, eps: float = 0.001) -> str:
    """Short vs medium EMA: ema7 > ema30 -> up, < -> down, within eps -> flat."""
    fast = _num(ma.get("exponential_moving_average_7_day"))
    slow = _num(ma.get("exponential_moving_average_30_day"))
    if slow <= 0:
        return "flat"
    if fast > slow * (1 + eps):
        return "up"
    if fast < slow * (1 - eps):
        return "down"
    return "flat"


class CMCMCPClient:
    def __init__(self, mcp_url: str, api_key: str | None = None, timeout: float = 30.0,
                 ids: dict | None = None):
        import httpx

        self.url = mcp_url
        self.ids = ids or _DEFAULT_IDS
        self.api_key = api_key or os.environ.get("CMC_MCP_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("CMC_MCP_API_KEY not set")
        self._client = httpx.Client(timeout=timeout, headers={
            "X-CMC-MCP-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        self._id = 0
        self._handshake()

    def _post(self, payload: dict):
        resp = self._client.post(self.url, json=payload)
        resp.raise_for_status()
        if "text/event-stream" in resp.headers.get("content-type", ""):
            for line in resp.text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
            return {}
        return resp.json()

    def _handshake(self) -> None:
        self._id += 1
        init = self._post({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "bnb-hack-agent", "version": "0.1"}}})
        sid = None
        # session id may come back as a header on the raw response; re-issue safely
        if isinstance(init, dict):
            sid = init.get("result", {}).get("sessionId")
        if sid:
            self._client.headers["Mcp-Session-Id"] = sid
        self._client.post(self.url, json={"jsonrpc": "2.0",
                          "method": "notifications/initialized", "params": {}})

    def list_tools(self) -> list[dict]:
        self._id += 1
        return self._post({"jsonrpc": "2.0", "id": self._id,
                           "method": "tools/list", "params": {}}).get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict):
        self._id += 1
        res = self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                          "params": {"name": name, "arguments": arguments}}).get("result", {})
        if "error" in res:
            raise RuntimeError(f"MCP tool {name}: {res['error']}")
        content = res.get("content", res)
        if isinstance(content, list):              # MCP wraps text content in a list
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except (ValueError, KeyError):
                        return item.get("text")
        return content

    def _id_of(self, token: str) -> str | None:
        return self.ids.get(token)

    def get_snapshot(self, tokens: list[str]) -> dict[str, dict]:
        g = self.call_tool(_TOOL["global"], {}) or {}
        fg = _num(_dig(g, "sentiment", "fear_greed", "current", "index", default=50))
        btc_dom = _num(_dig(g, "dominance", "btc", "current", default="54%"))

        snap: dict[str, dict] = {}
        for t in tokens:
            cid = self._id_of(t)
            if not cid:
                continue                            # not in id map -> skip (off-universe)
            quotes = self.call_tool(_TOOL["quotes"], {"id": cid})
            quote = quotes[0] if isinstance(quotes, list) and quotes else (quotes or {})
            tech = self.call_tool(_TOOL["technicals"], {"id": cid}) or {}
            snap[t] = {
                "price": _num(_dig(quote, "price", default=0.0)),
                "rsi": _num(_dig(tech, "rsi", "rsi14", default=50.0)),
                "macd_state": derive_macd_state(tech.get("macd", {})),
                "ema_trend": derive_ema_trend(tech.get("moving_averages", {})),
                "fear_greed_index": fg,
                "btc_dominance": btc_dom,
                "news_sentiment": 0.0,              # TODO: LLM-score get_crypto_latest_news
            }
        return snap


def _dig(obj, *keys, default=None):
    """Safely walk nested dicts; returns default if any key is missing."""
    cur = obj
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def build_cmc_client(cfg: dict) -> CMCClient:
    if cfg.get("mode") == "live":
        ids = cfg.get("cmc", {}).get("token_ids")
        return CMCMCPClient(cfg["cmc"]["mcp_url"], ids=ids)
    return MockCMCClient()
