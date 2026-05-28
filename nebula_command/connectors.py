from __future__ import annotations

import math
import os
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv

from .models import AssetPulse, SourceHealth

load_dotenv()

ASSETS = ["BTC", "ETH", "SOL", "XRP", "BNB", "LINK", "AVAX", "ADA", "MATIC", "DOT"]

SODEX_SYMBOL_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "XRP": "XRP-USD",
    "BNB": "BNB-USD",
    "LINK": "LINK-USD",
    "AVAX": "AVAX-USD",
    "ADA": "ADA-USD",
    "MATIC": "MATIC-USD",
    "DOT": "DOT-USD",
}

BINANCE_SYMBOL_MAP = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "BNB": "BNBUSDT",
    "LINK": "LINKUSDT",
    "AVAX": "AVAXUSDT",
    "ADA": "ADAUSDT",
    "MATIC": "MATICUSDT",
    "DOT": "DOTUSDT",
}

COINGECKO_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "BNB": "binancecoin",
    "LINK": "chainlink",
    "AVAX": "avalanche-2",
    "ADA": "cardano",
    "MATIC": "matic-network",
    "DOT": "polkadot",
}


def _bounded(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 0.0
    return float(max(lo, min(hi, v)))


def _request_json(url: str, headers: dict | None = None, params: dict | None = None, timeout: int = 12):
    r = requests.get(url, headers=headers or {}, params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _first_float(data: dict, keys: list[str]) -> float | None:
    for key in keys:
        if key in data and data[key] not in [None, ""]:
            try:
                return float(data[key])
            except Exception:
                pass
    return None


def _score_from_pct(pct: float | None) -> float:
    if pct is None:
        return 50.0
    return _bounded(50 + pct * 3.0)


def _liquidity_from_volume(volume_usd: float | None) -> float:
    if not volume_usd or volume_usd <= 0:
        return 45.0
    # Log-scale: around $1M => low, $1B+ => high.
    return _bounded((math.log10(volume_usd) - 5.5) * 18 + 45)


def _volatility_from_range(high: float | None, low: float | None, last: float | None, pct: float | None) -> float:
    if high and low and last and last > 0:
        return _bounded(abs(high - low) / last * 100 * 4)
    if pct is not None:
        return _bounded(abs(pct) * 7)
    return 35.0


def fetch_sodex(asset: str) -> tuple[dict, SourceHealth]:
    base = os.getenv("SODEX_BASE_URL", "https://api.sodex.com")
    symbol = SODEX_SYMBOL_MAP.get(asset, f"{asset}-USD")
    endpoint = f"{base.rstrip('/')}/markets/tickers"
    try:
        payload = _request_json(endpoint, params={"market": symbol})
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if isinstance(data, list):
            # Prefer exact market if returned, otherwise first row.
            exact = None
            for row in data:
                if isinstance(row, dict) and str(row.get("market") or row.get("symbol") or "").upper() in {symbol.upper(), symbol.replace("-", "").upper()}:
                    exact = row
                    break
            data = exact or (data[0] if data else {})
        if not isinstance(data, dict):
            raise ValueError("Unexpected SoDEX response shape")
        price = _first_float(data, ["price", "last", "lastPrice", "markPrice", "indexPrice", "close"])
        if price is None:
            raise ValueError("SoDEX ticker response did not include a price")
        pct = _first_float(data, ["priceChangePercent", "changePercent", "percentChange", "change24hPercent"])
        high = _first_float(data, ["highPrice", "high24h", "high"])
        low = _first_float(data, ["lowPrice", "low24h", "low"])
        volume = _first_float(data, ["quoteVolume", "volumeUsd", "volumeUSD", "volume24hUsd", "quote_volume"])
        return {
            "provider": "SoDEX",
            "price": price,
            "pct_24h": pct,
            "volume_usd": volume,
            "high": high,
            "low": low,
        }, SourceHealth("SoDEX", True, f"Live market data loaded for {symbol}", endpoint)
    except Exception as exc:
        return {}, SourceHealth("SoDEX", False, str(exc)[:180], endpoint)


def fetch_sosovalue(asset: str) -> tuple[dict, SourceHealth]:
    key = os.getenv("SOSOVALUE_API_KEY", "")
    base = os.getenv("SOSOVALUE_BASE_URL", "https://openapi.sosovalue.com/openapi/v1")
    endpoint = f"{base.rstrip('/')}/etfs/summary-history"
    if not key:
        return {}, SourceHealth("SoSoValue", False, "Missing SOSOVALUE_API_KEY", endpoint)
    try:
        headers = {"x-soso-api-key": key}
        payload = _request_json(endpoint, headers=headers, params={"limit": 30})
        data = payload.get("data", []) if isinstance(payload, dict) else []
        text = str(data).lower()
        # Use only information from the live payload. This is a normalized flow index, not a price.
        positives = text.count("inflow") + text.count("positive")
        negatives = text.count("outflow") + text.count("negative")
        flow_score = _bounded(50 + positives * 1.6 - negatives * 1.6)
        return {"provider": "SoSoValue", "flow": flow_score}, SourceHealth("SoSoValue", True, "Live ETF flow endpoint reachable", endpoint)
    except Exception as exc:
        return {}, SourceHealth("SoSoValue", False, str(exc)[:180], endpoint)


def fetch_binance(asset: str) -> tuple[dict, SourceHealth]:
    symbol = BINANCE_SYMBOL_MAP.get(asset)
    endpoint = "https://api.binance.com/api/v3/ticker/24hr"
    if not symbol:
        return {}, SourceHealth("Binance", False, f"No Binance symbol mapping for {asset}", endpoint)
    try:
        data = _request_json(endpoint, params={"symbol": symbol})
        if not isinstance(data, dict):
            raise ValueError("Unexpected Binance response shape")
        price = _first_float(data, ["lastPrice", "weightedAvgPrice", "prevClosePrice"])
        if price is None:
            raise ValueError("Binance ticker response did not include lastPrice")
        pct = _first_float(data, ["priceChangePercent"])
        volume = _first_float(data, ["quoteVolume"])
        high = _first_float(data, ["highPrice"])
        low = _first_float(data, ["lowPrice"])
        return {
            "provider": "Binance",
            "price": price,
            "pct_24h": pct,
            "volume_usd": volume,
            "high": high,
            "low": low,
        }, SourceHealth("Binance", True, f"Live 24h ticker loaded for {symbol}", endpoint)
    except Exception as exc:
        return {}, SourceHealth("Binance", False, str(exc)[:180], endpoint)


def fetch_coingecko(asset: str) -> tuple[dict, SourceHealth]:
    coin_id = COINGECKO_ID_MAP.get(asset)
    endpoint = "https://api.coingecko.com/api/v3/simple/price"
    if not coin_id:
        return {}, SourceHealth("CoinGecko", False, f"No CoinGecko id mapping for {asset}", endpoint)
    try:
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        }
        key = os.getenv("COINGECKO_API_KEY", "")
        headers = {"x-cg-demo-api-key": key} if key else {}
        data = _request_json(endpoint, headers=headers, params=params)
        row = data.get(coin_id, {}) if isinstance(data, dict) else {}
        price = _first_float(row, ["usd"])
        if price is None:
            raise ValueError("CoinGecko response did not include usd price")
        pct = _first_float(row, ["usd_24h_change"])
        volume = _first_float(row, ["usd_24h_vol"])
        return {
            "provider": "CoinGecko",
            "price": price,
            "pct_24h": pct,
            "volume_usd": volume,
            "high": None,
            "low": None,
        }, SourceHealth("CoinGecko", True, f"Live simple price loaded for {coin_id}", endpoint)
    except Exception as exc:
        return {}, SourceHealth("CoinGecko", False, str(exc)[:180], endpoint)


def _market_data_with_fallback(asset: str) -> tuple[dict, list[SourceHealth]]:
    health: list[SourceHealth] = []
    for fetcher in [fetch_sodex, fetch_binance, fetch_coingecko]:
        data, h = fetcher(asset)
        health.append(h)
        if data.get("price") is not None:
            return data, health
    return {}, health


def build_pulses(assets: Iterable[str]) -> tuple[list[AssetPulse], list[SourceHealth]]:
    pulses: list[AssetPulse] = []
    health: list[SourceHealth] = []
    for asset in assets:
        market, market_health = _market_data_with_fallback(asset)
        soso, h_soso = fetch_sosovalue(asset)
        health.extend(market_health)
        health.append(h_soso)
        if not market.get("price"):
            # No fake default. Skip asset if no live/free source returned a price.
            continue
        price = float(market["price"])
        pct = market.get("pct_24h")
        volume = market.get("volume_usd")
        high = market.get("high")
        low = market.get("low")
        momentum = _score_from_pct(pct)
        liquidity = _liquidity_from_volume(volume)
        flow = float(soso.get("flow", 50.0))  # neutral only if SoSoValue flow is unavailable
        volatility = _volatility_from_range(high, low, price, pct)
        risk = _bounded(volatility * 0.62 + (100 - liquidity) * 0.28 + max(0, 50 - momentum) * 0.22)
        flow_note = " + SoSoValue" if h_soso.ok else ""
        provider = market.get("provider", "Live")
        pulses.append(AssetPulse(asset, price, momentum, liquidity, flow, volatility, risk, f"{provider}{flow_note}"))
    return pulses, health


def pulses_frame(pulses: list[AssetPulse]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset": p.symbol,
            "price": round(p.price, 8),
            "momentum": round(p.momentum, 2),
            "liquidity": round(p.liquidity, 2),
            "flow": round(p.flow, 2),
            "volatility": round(p.volatility, 2),
            "risk": round(p.risk, 2),
            "command_score": round(p.command_score, 2),
            "source": p.source,
        }
        for p in pulses
    ])
