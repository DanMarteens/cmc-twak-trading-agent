"""
Technical indicators computed from a raw price series (EMA / RSI / MACD).

Shared by the backtester and the live signal source so both compute identical
math. Live, prices come from `twak price --history hour` (hourly bars — the
right horizon for a 1-week competition); in backtest, from historical history.
"""

from __future__ import annotations

from .cmc_client import derive_ema_trend, derive_macd_state


def ema(prices: list[float], n: int) -> list[float]:
    k = 2 / (n + 1)
    out = [prices[0]]
    for p in prices[1:]:
        out.append(p * k + out[-1] * (1 - k))
    return out


def rsi(prices: list[float], n: int = 14) -> list[float]:
    if len(prices) <= n:
        return [50.0] * len(prices)
    gains, losses = [0.0], [0.0]
    for i in range(1, len(prices)):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    out = [50.0] * len(prices)
    avg_g = sum(gains[1:n + 1]) / n
    avg_l = sum(losses[1:n + 1]) / n
    for i in range(n, len(prices)):
        if i > n:
            avg_g = (avg_g * (n - 1) + gains[i]) / n
            avg_l = (avg_l * (n - 1) + losses[i]) / n
        rs = (avg_g / avg_l) if avg_l > 0 else 999
        out[i] = 100 - 100 / (1 + rs)
    return out


def indicators(prices: list[float]):
    """Full per-bar series: (ema7, ema30, macd_line, signal, rsi14)."""
    e7, e30 = ema(prices, 7), ema(prices, 30)
    e12, e26 = ema(prices, 12), ema(prices, 26)
    macd_line = [a - b for a, b in zip(e12, e26)]
    signal = ema(macd_line, 9)
    return e7, e30, macd_line, signal, rsi(prices, 14)


def signals_from_prices(prices: list[float]) -> dict:
    """Latest-bar RSI / MACD state / EMA trend from a price series.

    Returns the same fields the signal engine consumes. Needs >=2 prices;
    returns neutral values otherwise.
    """
    if len(prices) < 2:
        return {"rsi": 50.0, "macd_state": "neutral", "ema_trend": "flat"}
    e7, e30, ml, sig, r = indicators(prices)
    return {
        "rsi": r[-1],
        "macd_state": derive_macd_state(
            {"macdLine": ml[-1], "signalLine": sig[-1], "histogram": ml[-1] - sig[-1]}),
        "ema_trend": derive_ema_trend(
            {"exponential_moving_average_7_day": e7[-1],
             "exponential_moving_average_30_day": e30[-1]}),
    }
