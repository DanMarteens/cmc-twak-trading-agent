from agent.indicators import ema, rsi, signals_from_prices


def test_ema_tracks_trend():
    up = list(range(1, 60))
    e = ema(up, 7)
    assert e[-1] < up[-1] and e[-1] > e[0]      # lags but rises


def test_rsi_high_on_uptrend_low_on_downtrend():
    up = [float(i) for i in range(1, 60)]
    down = [float(i) for i in range(60, 1, -1)]
    assert rsi(up, 14)[-1] > 70
    assert rsi(down, 14)[-1] < 30


def test_signals_from_prices_uptrend():
    up = [100 * (1.01 ** i) for i in range(40)]   # steady climb
    s = signals_from_prices(up)
    assert s["ema_trend"] == "up"
    assert s["rsi"] > 60
    assert set(s) == {"rsi", "macd_state", "ema_trend"}


def test_signals_from_prices_short_series_neutral():
    s = signals_from_prices([100.0])
    assert s == {"rsi": 50.0, "macd_state": "neutral", "ema_trend": "flat"}
