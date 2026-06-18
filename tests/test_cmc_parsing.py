"""Tests for the CMC response parsing/derivation (pure, offline)."""

from agent.cmc_client import _num, derive_ema_trend, derive_macd_state


def test_num_parses_cmc_display_strings():
    assert _num("+58.18%") == 58.18
    assert _num("608.13") == 608.13
    assert abs(_num("2.16 T") - 2.16e12) < 1.0    # multiplier; float-tolerant
    assert abs(_num("87.83 B") - 87.83e9) < 1.0
    assert _num("1,234.5") == 1234.5
    assert _num(19) == 19.0
    assert _num(None, default=50) == 50
    assert _num("garbage", default=42) == 42


def test_derive_macd_state():
    assert derive_macd_state({"macdLine": "-10.92", "signalLine": "-11.43",
                              "histogram": "0.50603"}) == "bullish"
    assert derive_macd_state({"macdLine": "-11.4", "signalLine": "-10.9",
                              "histogram": "-0.5"}) == "bearish"
    assert derive_macd_state({"macdLine": "0", "signalLine": "0",
                              "histogram": "0"}) == "neutral"


def test_derive_ema_trend():
    up = {"exponential_moving_average_7_day": "610",
          "exponential_moving_average_30_day": "600"}
    down = {"exponential_moving_average_7_day": "590",
            "exponential_moving_average_30_day": "600"}
    flat = {"exponential_moving_average_7_day": "600.1",
            "exponential_moving_average_30_day": "600.0"}
    assert derive_ema_trend(up) == "up"
    assert derive_ema_trend(down) == "down"
    assert derive_ema_trend(flat) == "flat"
