# Nebula Command

A mission-control interface for on-chain strategy intelligence.

Nebula Command is intentionally different from a classic trading dashboard. It uses a command-center workflow:

1. Mission Inputs
2. Signal Galaxy
3. Asset Pulse Matrix
4. Strategy War Room
5. Scenario Forge
6. Paper Intent Board
7. Live API Console
8. Mission Report Export

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Main file path:

```text
app.py
```

Secrets format:

```toml
SOSOVALUE_API_KEY = "YOUR_KEY"
SOSOVALUE_BASE_URL = "https://openapi.sosovalue.com/openapi/v1"
SODEX_BASE_URL = "https://api.sodex.com"
SODEX_NETWORK = "mainnet"
SODEX_MARKET = "spot"
SODEX_API_KEY_NAME = "YOUR_KEY_NAME"
SODEX_API_PRIVATE_KEY = "YOUR_PRIVATE_KEY"
```

Live trading is not implemented. The app only generates paper execution plans.
