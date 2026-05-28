from __future__ import annotations

import argparse
import json

from .data import ASSETS, load_market
from .engine import build_strategy, execution_board, report_markdown, scenario_matrix, score_assets


def main() -> None:
    parser = argparse.ArgumentParser(description="AlphaForge AI CLI")
    parser.add_argument("--assets", default="BTC,ETH,SOL,XRP")
    parser.add_argument("--thesis", default="ETF inflow improving and liquidity rotating into bluechip crypto")
    parser.add_argument("--capital", type=float, default=10000)
    parser.add_argument("--risk-profile", choices=["defensive", "balanced", "aggressive"], default="balanced")
    parser.add_argument("--strict-live", action="store_true")
    parser.add_argument("--mode", choices=["scores", "strategy", "scenarios", "execution", "report"], default="strategy")
    args = parser.parse_args()

    assets = [x.strip().upper() for x in args.assets.split(",") if x.strip()]
    market, statuses = load_market(assets, require_live=args.strict_live)
    scores = score_assets(market)
    plan = build_strategy(args.thesis, market, args.capital, args.risk_profile)

    if args.mode == "scores":
        print(json.dumps([s.__dict__ for s in scores], indent=2))
    elif args.mode == "scenarios":
        print(scenario_matrix(plan).to_string(index=False))
    elif args.mode == "execution":
        print(execution_board(plan).to_string(index=False))
    elif args.mode == "report":
        print(report_markdown(plan, scores))
    else:
        print(json.dumps(plan.__dict__, indent=2, default=str))

if __name__ == "__main__":
    main()
