# AlphaForge AI

A futuristic on-chain strategy command center for crypto research, thesis generation, risk analysis, scenario simulation, and paper execution planning.

AlphaForge AI is designed as a different product direction from Nexus Alpha: instead of a classic signal dashboard, it behaves like a strategy war room. Users enter a market thesis, review live API health, inspect market radar scores, generate strategy plans, simulate scenarios, and export a decision report.

## Features

- AI-style strategy generator
- Market radar scoring
- Portfolio battle map
- Scenario simulator
- Agent war room timeline
- API live console
- Paper execution board
- Exportable strategy report
- English UI with futuristic dark design

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Environment variables

```toml
SOSOVALUE_API_KEY="your_key"
SOSOVALUE_BASE_URL="https://openapi.sosovalue.com/openapi/v1"
SODEX_NETWORK="mainnet"
SODEX_MARKET="spot"
SODEX_API_KEY_NAME="your_key_name"
SODEX_API_PRIVATE_KEY="your_private_key"
DEFAULT_CAPITAL="10000"
```

Live execution is disabled. AlphaForge AI is built for research, planning, simulation, and paper execution preview.
