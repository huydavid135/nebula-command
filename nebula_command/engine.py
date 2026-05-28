from __future__ import annotations
from typing import Iterable
import pandas as pd

from .models import AssetPulse, MissionPlan


def generate_mission(thesis: str, pulses: list[AssetPulse], capital: float, risk_mode: str) -> MissionPlan:
    ranked = sorted(pulses, key=lambda p: p.command_score, reverse=True)
    risk_cap = {"Stealth": 0.18, "Balanced": 0.28, "Aggressive": 0.42}.get(risk_mode, 0.28)
    priority = [p.symbol for p in ranked if p.command_score >= 52 and p.risk < 72][:3]
    blocked = [p.symbol for p in ranked if p.risk >= 72 or p.command_score < 38]
    stance = "ACCUMULATE" if ranked and ranked[0].command_score > 62 else "OBSERVE"
    if sum(p.risk for p in pulses) / max(1, len(pulses)) > 68:
        stance = "DEFENSIVE"
    orders = []
    if priority:
        weight_each = risk_cap / len(priority)
        for symbol in priority:
            p = next(x for x in pulses if x.symbol == symbol)
            orders.append({
                "asset": symbol,
                "intent": "paper-buy" if stance != "DEFENSIVE" else "watch",
                "notional_usd": round(capital * weight_each, 2),
                "limit_reference": round(p.price * 0.998, 4),
                "risk_gate": "PASS" if p.risk < 65 else "REVIEW",
            })
    reasoning = [
        f"Mission thesis: {thesis.strip() or 'No thesis provided.'}",
        f"Top command score: {ranked[0].symbol} at {ranked[0].command_score:.1f}/100." if ranked else "No assets selected.",
        f"Risk mode {risk_mode} caps active deployment at {risk_cap:.0%} of capital.",
        "Execution remains paper-only; this command center produces decision plans, not live orders.",
    ]
    return MissionPlan("Nebula Command Mission", stance, priority, blocked, orders, reasoning)


def scenario_matrix(pulses: list[AssetPulse], shock: str, capital: float) -> pd.DataFrame:
    multipliers = {
        "ETF inflow surge": {"flow": 1.25, "momentum": 1.15, "risk": 0.92},
        "Liquidity drain": {"liquidity": 0.72, "risk": 1.28, "momentum": 0.88},
        "BTC volatility shock": {"volatility": 1.35, "risk": 1.22, "momentum": 0.9},
        "Alt rotation": {"flow": 1.05, "momentum": 1.22, "risk": 1.05},
        "Market calm": {"volatility": 0.75, "risk": 0.82, "liquidity": 1.08},
    }.get(shock, {})
    rows = []
    for p in pulses:
        adj_score = p.command_score
        if "momentum" in multipliers:
            adj_score += (p.momentum * multipliers["momentum"] - p.momentum) * 0.25
        if "flow" in multipliers:
            adj_score += (p.flow * multipliers["flow"] - p.flow) * 0.25
        if "risk" in multipliers:
            adj_score -= (p.risk * multipliers["risk"] - p.risk) * 0.2
        if "liquidity" in multipliers:
            adj_score += (p.liquidity * multipliers["liquidity"] - p.liquidity) * 0.16
        adj_score = max(0, min(100, adj_score))
        exposure = capital * max(0, adj_score - 45) / 1000
        rows.append({"asset": p.symbol, "shock": shock, "adjusted_score": round(adj_score, 2), "paper_exposure_usd": round(exposure, 2)})
    return pd.DataFrame(rows)


def agent_timeline(plan: MissionPlan) -> list[dict[str, str]]:
    return [
        {"phase": "SCAN", "output": "Collect API health, price pulse, flow pulse, and risk pressure."},
        {"phase": "DECODE", "output": f"Current stance selected: {plan.stance}."},
        {"phase": "MAP", "output": "Assets are assigned into Priority, Watch, and Block zones."},
        {"phase": "FORGE", "output": f"Generated {len(plan.orders)} paper execution intents."},
        {"phase": "LOCK", "output": "Live trading gate remains locked until manually implemented."},
    ]


def export_markdown(plan: MissionPlan) -> str:
    lines = ["# Nebula Command Strategy Report", "", f"**Stance:** {plan.stance}", "", "## Priority Assets", ", ".join(plan.priority_assets) or "None", "", "## Blocked Assets", ", ".join(plan.blocked_assets) or "None", "", "## Orders"]
    for order in plan.orders:
        lines.append(f"- {order['intent']} {order['asset']} ${order['notional_usd']} near {order['limit_reference']} ({order['risk_gate']})")
    lines += ["", "## Reasoning"] + [f"- {r}" for r in plan.reasoning]
    return "\n".join(lines)
