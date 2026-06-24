from agent import decision
from agent.decision import LLMDecider, tradeable_buy_tokens


class Base:
    def decide(self, snapshot, signals, portfolio, risk_limits):
        return [
            {"token": "ETH", "action": "buy", "size_pct": 0.3,
             "confidence": 0.8, "rationale": "deterministic"},
            {"token": "CAKE", "action": "close", "size_pct": 0.0,
             "confidence": 0.7, "rationale": "exit"},
        ]


def test_llm_cannot_invent_trade_and_cannot_veto_exit(monkeypatch, cfg):
    cfg = {**cfg, "llm": {**cfg["llm"], "second_gate": True}}
    monkeypatch.setattr(decision.llm, "complete", lambda *a, **k: (
        '{"decisions":['
        '{"token":"APE","action":"buy","size_pct":1,"confidence":1,"rationale":"invent"},'
        '{"token":"ETH","action":"hold","size_pct":0,"confidence":1,"rationale":"veto"}'
        ']}'
    ))
    out = LLMDecider(cfg, fallback=Base()).decide({}, {},
                                                   {"positions": {}}, {})
    assert out == [{"token": "CAKE", "action": "close", "size_pct": 0.0,
                    "confidence": 0.7, "rationale": "exit"}]


def test_llm_review_can_only_reduce_buy_size(monkeypatch, cfg):
    cfg = {**cfg, "llm": {**cfg["llm"], "second_gate": True}}

    class SizeBase:
        def decide(self, snapshot, signals, portfolio, risk_limits):
            return [
                {"token": "ETH", "action": "buy", "size_pct": 0.4,
                 "confidence": 0.8, "rationale": "deterministic"},
                {"token": "CAKE", "action": "buy", "size_pct": 0.2,
                 "confidence": 0.7, "rationale": "deterministic"},
            ]

    monkeypatch.setattr(decision.llm, "complete", lambda *a, **k: (
        '{"decisions":['
        '{"token":"ETH","action":"buy","size_pct":0.25,"confidence":0.6,"rationale":"late chase risk"},'
        '{"token":"CAKE","action":"buy","size_pct":0.9,"confidence":1,"rationale":"try increase"}'
        ']}'
    ))
    out = LLMDecider(cfg, fallback=SizeBase()).decide({}, {},
                                                       {"positions": {}}, {})
    eth = next(x for x in out if x["token"] == "ETH")
    cake = next(x for x in out if x["token"] == "CAKE")
    assert eth["size_pct"] == 0.25
    assert eth["confidence"] == 0.8
    assert cake["size_pct"] == 0.2
    assert cake["confidence"] == 0.7


def test_llm_cash_preservation_veto_can_be_overridden_for_high_conviction(monkeypatch, cfg):
    cfg = {**cfg, "llm": {**cfg["llm"], "second_gate": True,
                          "cash_veto_override_enabled": True,
                          "cash_veto_override_size_pct": 0.4}}

    class RecoveryBase:
        last_debug = {
            "top_ranked": [{
                "token": "LAB",
                "score": 0.41,
                "cmc_score": 0.88,
                "x402_token_score": 0.28,
                "round_trip_loss_pct": 1.9,
                "token_risk_score": 10,
                "return_6h": 0.01,
            }]
        }

        def decide(self, snapshot, signals, portfolio, risk_limits):
            return [{"token": "LAB", "action": "buy", "size_pct": 0.55,
                     "confidence": 0.75, "rationale": "deterministic"}]

    monkeypatch.setattr(decision.llm, "complete", lambda *a, **k: (
        '{"decisions":[{"token":"LAB","action":"hold","size_pct":0,'
        '"confidence":0,"rationale":"trend_down drawdown preserve cash"}]}'
    ))
    out = LLMDecider(cfg, fallback=RecoveryBase()).decide(
        {}, {}, {"positions": {}}, {"leaderboard_rank": 47,
                                    "leaderboard_drawdown_pct": 17.1})
    assert out == [{"token": "LAB", "action": "buy", "size_pct": 0.4,
                    "confidence": 0.75,
                    "rationale": "deterministic; AI cash-veto overridden by high-conviction recovery guardrail"}]


def test_deny_buy_lifts_only_after_executable_validation(cfg):
    cfg = {**cfg, "twak": {**cfg["twak"],
                           "token_contracts": {"ZETA": "0x1", "CAKE": "0x2"},
                           "deny_buy": ["ZETA"]}}
    assert "ZETA" not in tradeable_buy_tokens(cfg)

    cfg = {**cfg, "universe_runtime": {"ZETA": {
        "round_trip_loss_pct": 1.2,
        "risk_level": "low",
        "history_bars": cfg["universe"]["min_history_bars"],
    }}}
    assert "ZETA" in tradeable_buy_tokens(cfg)

    cfg["universe_runtime"]["ZETA"]["round_trip_loss_pct"] = 9.0
    assert "ZETA" not in tradeable_buy_tokens(cfg)
