from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable
import json
import math

import numpy as np
import pandas as pd

@dataclass
class RadarScore:
    asset: str
    momentum: float
    flow: float
    liquidity: float
    sentiment: float
    risk_control: float
    alpha_score: float
    action: str

@dataclass
class StrategyPlan:
    thesis: str
    regime: str
    risk_profile: str
    total_capital: float
    allocation: list[dict]
    battle_zones: dict[str, list[str]]
    invalidation_rules: list[str]
    narrative: str


def _norm(series: pd.Series, inverse: bool = False) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        out = pd.Series([50] * len(s), index=s.index)
    else:
        out = (s - s.min()) / (s.max() - s.min()) * 100
    return 100 - out if inverse else out


def score_assets(market: dict[str, pd.DataFrame]) -> list[RadarScore]:
    latest = []
    for asset, df in market.items():
        if df.empty:
            continue
        tail = df.tail(1).iloc[0]
        latest.append({
            "asset": asset,
            "momentum_raw": float(tail.get("momentum", 0)),
            "flow_raw": float(tail.get("net_flow_musd", 0)),
            "liquidity_raw": float(tail.get("liquidity", 50)),
            "sentiment_raw": float(tail.get("sentiment", 50)),
            "volatility_raw": float(tail.get("volatility", 0.03)),
        })
    if not latest:
        return []
    f = pd.DataFrame(latest)
    f["momentum"] = _norm(f["momentum_raw"])
    f["flow"] = _norm(f["flow_raw"])
    f["liquidity"] = f["liquidity_raw"].clip(0, 100)
    f["sentiment"] = f["sentiment_raw"].clip(0, 100)
    f["risk_control"] = _norm(f["volatility_raw"], inverse=True)
    f["alpha_score"] = (
        f["momentum"] * 0.25 + f["flow"] * 0.24 + f["liquidity"] * 0.18 + f["sentiment"] * 0.2 + f["risk_control"] * 0.13
    )
    def action(score: float) -> str:
        if score >= 68:
            return "ATTACK"
        if score >= 52:
            return "HOLD"
        if score >= 38:
            return "WATCH"
        return "BLOCK"
    f["action"] = f["alpha_score"].apply(action)
    return [RadarScore(**{k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items() if k in RadarScore.__annotations__}) for row in f.to_dict("records")]


def detect_regime(scores: list[RadarScore]) -> str:
    if not scores:
        return "UNKNOWN"
    avg_alpha = np.mean([s.alpha_score for s in scores])
    avg_risk = np.mean([s.risk_control for s in scores])
    avg_flow = np.mean([s.flow for s in scores])
    if avg_alpha >= 65 and avg_flow >= 55:
        return "RISK-ON FLOW EXPANSION"
    if avg_risk <= 35:
        return "HIGH VOLATILITY DEFENSE"
    if avg_flow < 40:
        return "FLOW CONTRACTION"
    return "SELECTIVE ALPHA ROTATION"


def build_strategy(thesis: str, market: dict[str, pd.DataFrame], capital: float, risk_profile: str) -> StrategyPlan:
    scores = score_assets(market)
    regime = detect_regime(scores)
    multipliers = {"defensive": 0.72, "balanced": 1.0, "aggressive": 1.28}
    risk_mult = multipliers.get(risk_profile, 1.0)
    tradable = [s for s in scores if s.action in {"ATTACK", "HOLD"}]
    if not tradable:
        tradable = sorted(scores, key=lambda x: x.alpha_score, reverse=True)[:2]
    total_score = sum(max(s.alpha_score, 1) for s in tradable) or 1
    allocation = []
    for s in sorted(tradable, key=lambda x: x.alpha_score, reverse=True):
        weight = max(s.alpha_score, 1) / total_score
        if risk_profile == "defensive":
            weight = min(weight, 0.38)
        notional = capital * weight * min(risk_mult, 1.0)
        allocation.append({
            "asset": s.asset,
            "zone": "CORE" if s.action == "ATTACK" else "SATELLITE",
            "action": s.action,
            "weight": round(weight, 4),
            "notional_usd": round(notional, 2),
            "alpha_score": s.alpha_score,
            "risk_budget": round(notional * 0.012 * risk_mult, 2),
        })
    battle_zones = {
        "core": [a["asset"] for a in allocation if a["zone"] == "CORE"],
        "satellite": [a["asset"] for a in allocation if a["zone"] == "SATELLITE"],
        "watchlist": [s.asset for s in scores if s.action == "WATCH"],
        "blocked": [s.asset for s in scores if s.action == "BLOCK"],
    }
    invalidation = [
        "Alpha score falls below 45 for the core asset.",
        "Portfolio drawdown exceeds the selected risk budget.",
        "Flow score turns negative while volatility expands.",
        "API source health fails for all primary data connectors.",
    ]
    top = allocation[0]["asset"] if allocation else "no asset"
    narrative = (
        f"The current regime is {regime}. Based on the thesis, AlphaForge prioritizes {top} as the leading exposure "
        f"while keeping lower-score assets in watch or blocked zones. The plan is designed for research and paper execution, "
        f"not automatic live trading."
    )
    return StrategyPlan(thesis, regime, risk_profile, capital, allocation, battle_zones, invalidation, narrative)


def scenario_matrix(plan: StrategyPlan) -> pd.DataFrame:
    scenarios = [
        ("ETF inflow spike", 0.075, 0.78),
        ("BTC risk-off shock", -0.11, 0.9),
        ("Liquidity expansion", 0.045, 0.52),
        ("Alt rotation", 0.061, 0.67),
        ("Volatility squeeze", -0.038, 0.73),
        ("Flow reversal", -0.069, 0.81),
    ]
    rows = []
    exposure = sum(a["weight"] for a in plan.allocation) or 1
    for name, impact, stress in scenarios:
        adjusted = impact * exposure
        rows.append({
            "scenario": name,
            "portfolio_impact_pct": round(adjusted * 100, 2),
            "stress_level": round(stress * 100, 1),
            "response": "reduce risk" if adjusted < -0.05 else "hold plan" if adjusted < 0.04 else "scale winners",
        })
    return pd.DataFrame(rows)


def execution_board(plan: StrategyPlan, max_slippage_bps: int = 35) -> pd.DataFrame:
    rows = []
    for a in plan.allocation:
        est_slippage = min(max_slippage_bps, 6 + int((100 - a["alpha_score"]) / 4))
        rows.append({
            "asset": a["asset"],
            "paper_order": "LIMIT-IOC",
            "side": "BUY" if a["action"] in {"ATTACK", "HOLD"} else "NONE",
            "notional_usd": a["notional_usd"],
            "max_slippage_bps": max_slippage_bps,
            "estimated_slippage_bps": est_slippage,
            "status": "READY" if est_slippage <= max_slippage_bps else "BLOCKED",
        })
    return pd.DataFrame(rows)


def agent_timeline(plan: StrategyPlan) -> list[dict[str, str]]:
    return [
        {"stage": "OBSERVE", "message": "Pull market, flow, liquidity, and sentiment inputs from connected sources."},
        {"stage": "RANK", "message": f"Score assets under the {plan.regime} regime."},
        {"stage": "BUILD", "message": "Convert thesis into core, satellite, watchlist, and blocked zones."},
        {"stage": "RISK CHECK", "message": "Apply position limits, risk budgets, and invalidation rules."},
        {"stage": "PREVIEW", "message": "Generate paper execution plan with slippage and status checks."},
        {"stage": "REPORT", "message": "Produce a decision-ready strategy brief for review."},
    ]


def report_markdown(plan: StrategyPlan, scores: list[RadarScore]) -> str:
    alloc = "\n".join([f"- {a['asset']}: {a['weight']:.1%}, ${a['notional_usd']:,.0f}, {a['zone']}" for a in plan.allocation])
    blocked = ", ".join(plan.battle_zones.get("blocked", [])) or "None"
    return f"""# AlphaForge AI Strategy Report

## Thesis
{plan.thesis}

## Market Regime
{plan.regime}

## Allocation
{alloc}

## Blocked Assets
{blocked}

## Invalidation Rules
""" + "\n".join([f"- {x}" for x in plan.invalidation_rules]) + f"""

## Narrative
{plan.narrative}
"""
