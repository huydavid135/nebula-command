from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import math
import random
from typing import Iterable

import numpy as np
import pandas as pd
import requests

ASSETS = ["BTC", "ETH", "SOL", "XRP", "BNB", "LINK", "ARB", "OP"]

@dataclass
class SourceStatus:
    name: str
    ok: bool
    endpoint: str
    rows: int
    message: str
    last_checked: str


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def synthetic_market(asset: str, days: int = 60) -> pd.DataFrame:
    seed = abs(hash(asset)) % 10_000
    rng = np.random.default_rng(seed)
    dates = [datetime.utcnow().date() - timedelta(days=i) for i in range(days)][::-1]
    base = {"BTC": 70000, "ETH": 3500, "SOL": 160, "XRP": 0.62, "BNB": 600, "LINK": 17, "ARB": 1.2, "OP": 2.1}.get(asset, 100)
    drift = {"BTC": 0.0011, "ETH": 0.0008, "SOL": 0.0014, "XRP": 0.0004}.get(asset, 0.0007)
    vol = {"BTC": 0.025, "ETH": 0.03, "SOL": 0.045, "XRP": 0.035}.get(asset, 0.04)
    returns = rng.normal(drift, vol, days)
    price = base * np.exp(np.cumsum(returns))
    momentum = pd.Series(price).pct_change(7).fillna(0).to_numpy()
    volatility = pd.Series(price).pct_change().rolling(14).std().fillna(vol).to_numpy()
    flow = 35 * np.sin(np.linspace(0, 4.2, days) + seed / 1000) + rng.normal(0, 13, days)
    sentiment = np.clip(50 + momentum * 450 + flow * 0.18 + rng.normal(0, 8, days), 0, 100)
    liquidity = np.clip(70 - volatility * 350 + rng.normal(0, 6, days), 20, 95)
    return pd.DataFrame({
        "date": pd.to_datetime(dates),
        "asset": asset,
        "price": price.round(6),
        "momentum": momentum.round(5),
        "volatility": volatility.round(5),
        "net_flow_musd": flow.round(3),
        "sentiment": sentiment.round(2),
        "liquidity": liquidity.round(2),
    })


def _sodex_symbol(asset: str) -> str:
    return f"{asset.upper()}-USD"


def fetch_sodex(asset: str, timeout: int = 8) -> tuple[pd.DataFrame | None, SourceStatus]:
    base = "https://api.sodex.com"
    endpoint = f"{base}/markets/candles"
    params = {"symbol": _sodex_symbol(asset), "interval": "1d", "limit": 60}
    try:
        r = requests.get(endpoint, params=params, timeout=timeout)
        if not r.ok:
            return None, SourceStatus("SoDEX", False, endpoint, 0, f"HTTP {r.status_code}: {r.text[:120]}", _now())
        data = r.json()
        rows = data.get("data", data if isinstance(data, list) else [])
        if not rows:
            return None, SourceStatus("SoDEX", False, endpoint, 0, "No candle rows returned", _now())
        df = pd.DataFrame(rows)
        # Flexible column normalization for API variants.
        time_col = next((c for c in ["timestamp", "time", "date", "t"] if c in df.columns), None)
        close_col = next((c for c in ["close", "c", "price"] if c in df.columns), None)
        if time_col is None or close_col is None:
            return None, SourceStatus("SoDEX", False, endpoint, len(df), "Unsupported candle schema", _now())
        out = pd.DataFrame({"date": pd.to_datetime(df[time_col], unit="ms", errors="coerce"), "price": pd.to_numeric(df[close_col], errors="coerce")})
        out = out.dropna().sort_values("date").tail(60)
        if out.empty:
            return None, SourceStatus("SoDEX", False, endpoint, 0, "No valid parsed candles", _now())
        out["asset"] = asset
        out["momentum"] = out["price"].pct_change(7).fillna(0)
        out["volatility"] = out["price"].pct_change().rolling(14).std().fillna(0.03)
        out["net_flow_musd"] = 0.0
        out["sentiment"] = np.clip(50 + out["momentum"] * 400 - out["volatility"] * 150, 0, 100)
        out["liquidity"] = np.clip(75 - out["volatility"] * 250, 25, 95)
        return out, SourceStatus("SoDEX", True, endpoint, len(out), "Live market candles loaded", _now())
    except Exception as exc:
        return None, SourceStatus("SoDEX", False, endpoint, 0, str(exc), _now())


def fetch_sosovalue(asset: str, timeout: int = 8) -> tuple[pd.DataFrame | None, SourceStatus]:
    key = os.getenv("SOSOVALUE_API_KEY", "").strip().strip('"')
    base = os.getenv("SOSOVALUE_BASE_URL", "https://openapi.sosovalue.com/openapi/v1").rstrip("/")
    endpoint = f"{base}/etfs/summary-history"
    if not key:
        return None, SourceStatus("SoSoValue", False, endpoint, 0, "SOSOVALUE_API_KEY is missing", _now())
    try:
        headers = {"x-soso-api-key": key}
        params = {"symbol": asset.upper(), "limit": 60}
        r = requests.get(endpoint, headers=headers, params=params, timeout=timeout)
        if not r.ok:
            return None, SourceStatus("SoSoValue", False, endpoint, 0, f"HTTP {r.status_code}: {r.text[:120]}", _now())
        data = r.json()
        rows = data.get("data", data.get("rows", data if isinstance(data, list) else [])) if isinstance(data, dict) else data
        if not rows:
            return None, SourceStatus("SoSoValue", False, endpoint, 0, "No ETF flow rows returned", _now())
        df = pd.DataFrame(rows)
        date_col = next((c for c in ["date", "time", "timestamp", "day"] if c in df.columns), None)
        flow_col = next((c for c in ["netInflow", "net_flow", "netFlow", "net_flow_musd", "totalNetInflow"] if c in df.columns), None)
        if date_col is None or flow_col is None:
            return None, SourceStatus("SoSoValue", False, endpoint, len(df), "Unsupported ETF flow schema", _now())
        out = pd.DataFrame({
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "net_flow_musd": pd.to_numeric(df[flow_col], errors="coerce").fillna(0),
        }).dropna().sort_values("date").tail(60)
        out["asset"] = asset
        out["price"] = np.nan
        out["momentum"] = 0.0
        out["volatility"] = 0.03
        out["sentiment"] = np.clip(50 + out["net_flow_musd"].rank(pct=True) * 50 - 25, 0, 100)
        out["liquidity"] = 70
        return out, SourceStatus("SoSoValue", True, endpoint, len(out), "ETF flow loaded", _now())
    except Exception as exc:
        return None, SourceStatus("SoSoValue", False, endpoint, 0, str(exc), _now())


def load_market(assets: Iterable[str], require_live: bool = False) -> tuple[dict[str, pd.DataFrame], list[SourceStatus]]:
    all_data: dict[str, pd.DataFrame] = {}
    statuses: list[SourceStatus] = []
    for asset in assets:
        sodex_df, sodex_status = fetch_sodex(asset)
        soso_df, soso_status = fetch_sosovalue(asset)
        statuses.extend([sodex_status, soso_status])
        if sodex_df is not None:
            df = sodex_df.copy()
            if soso_df is not None and not soso_df.empty:
                flow = soso_df[["date", "net_flow_musd", "sentiment"]].copy()
                df = pd.merge_asof(df.sort_values("date"), flow.sort_values("date"), on="date", direction="nearest", suffixes=("", "_soso"))
                if "net_flow_musd_soso" in df.columns:
                    df["net_flow_musd"] = df["net_flow_musd_soso"].fillna(df["net_flow_musd"])
                if "sentiment_soso" in df.columns:
                    df["sentiment"] = (df["sentiment"] * 0.5 + df["sentiment_soso"].fillna(df["sentiment"]) * 0.5)
                df = df[["date", "asset", "price", "momentum", "volatility", "net_flow_musd", "sentiment", "liquidity"]]
            all_data[asset] = df.tail(60)
        elif require_live:
            all_data[asset] = pd.DataFrame(columns=["date", "asset", "price", "momentum", "volatility", "net_flow_musd", "sentiment", "liquidity"])
        else:
            all_data[asset] = synthetic_market(asset)
            statuses.append(SourceStatus("Local simulation", True, "internal", len(all_data[asset]), "Used because live source is unavailable", _now()))
    return all_data, statuses
