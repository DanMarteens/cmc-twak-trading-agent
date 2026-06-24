import os

from agent.agent import load_config


def test_non_live_mode_uses_isolated_state_paths(monkeypatch):
    monkeypatch.delenv("AGENT_MODE", raising=False)

    cfg = load_config("config.yaml")

    assert cfg["mode"] == "dry_run"
    assert cfg["paths"]["state_file"] == "state/dry_run_portfolio.json"
    assert cfg["paths"]["decision_log"] == "logs/dry_run_decisions.jsonl"


def test_live_mode_keeps_live_state_paths(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "live")

    cfg = load_config("config.yaml")

    assert cfg["mode"] == "live"
    assert cfg["paths"]["state_file"] == "state/portfolio.json"
    assert cfg["paths"]["decision_log"] == "logs/decisions.jsonl"
