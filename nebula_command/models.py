from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class AssetPulse:
    symbol: str
    price: float
    momentum: float
    liquidity: float
    flow: float
    volatility: float
    risk: float
    source: str

    @property
    def command_score(self) -> float:
        raw = self.momentum * 0.28 + self.liquidity * 0.18 + self.flow * 0.26 - self.volatility * 0.14 - self.risk * 0.14
        return max(0.0, min(100.0, raw))

@dataclass
class SourceHealth:
    source: str
    ok: bool
    message: str
    endpoint: str

@dataclass
class MissionPlan:
    title: str
    stance: str
    priority_assets: List[str]
    blocked_assets: List[str]
    orders: List[Dict[str, str | float]]
    reasoning: List[str]
