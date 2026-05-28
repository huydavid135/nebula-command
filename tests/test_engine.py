from alphaforge.data import synthetic_market
from alphaforge.engine import build_strategy, execution_board, scenario_matrix, score_assets


def test_score_assets_returns_scores():
    market = {a: synthetic_market(a, 30) for a in ["BTC", "ETH", "SOL"]}
    scores = score_assets(market)
    assert len(scores) == 3
    assert all(0 <= s.alpha_score <= 100 for s in scores)


def test_build_strategy_has_allocation():
    market = {a: synthetic_market(a, 30) for a in ["BTC", "ETH", "SOL"]}
    plan = build_strategy("BTC ETF flow bullish", market, 10000, "balanced")
    assert plan.allocation
    assert plan.regime


def test_scenario_and_execution_frames():
    market = {a: synthetic_market(a, 30) for a in ["BTC", "ETH", "SOL"]}
    plan = build_strategy("risk-on rotation", market, 10000, "balanced")
    assert not scenario_matrix(plan).empty
    assert not execution_board(plan).empty
