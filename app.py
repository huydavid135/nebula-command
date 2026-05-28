from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from alphaforge.data import ASSETS, SourceStatus, load_market
from alphaforge.engine import (
    agent_timeline,
    build_strategy,
    execution_board,
    report_markdown,
    scenario_matrix,
    score_assets,
)

load_dotenv()

st.set_page_config(page_title="AlphaForge AI", page_icon="🧠", layout="wide")

st.markdown(
    """
<style>
:root {
  --bg: #070912;
  --panel: rgba(17, 22, 36, .82);
  --panel2: rgba(20, 26, 45, .62);
  --cyan: #44e4ff;
  --orange: #ff7a18;
  --purple: #9b5cff;
  --green: #00ff9c;
}
.stApp {background: radial-gradient(circle at top left, rgba(68,228,255,.16), transparent 30%), radial-gradient(circle at top right, rgba(255,122,24,.12), transparent 26%), #070912; color: #f7fbff;}
.block-container {padding-top: 1.2rem; max-width: 1600px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #0b0f1d 0%, #11182b 100%); border-right: 1px solid rgba(68,228,255,.18);}
h1, h2, h3 {letter-spacing: .02em;}
.af-hero {padding: 1.2rem 1.4rem; border-radius: 1.4rem; border: 1px solid rgba(68,228,255,.24); background: linear-gradient(135deg, rgba(68,228,255,.12), rgba(155,92,255,.1), rgba(255,122,24,.08)); box-shadow: 0 0 40px rgba(68,228,255,.08);}
.af-title {font-size: 3rem; line-height: 1; font-weight: 900; margin: 0;}
.af-sub {color: #a9b4ce; margin-top: .6rem; font-size: 1rem;}
.af-pill {display: inline-block; padding: .26rem .6rem; margin-right: .35rem; border: 1px solid rgba(68,228,255,.35); border-radius: 999px; color: #dcfbff; background: rgba(68,228,255,.08); font-size: .82rem;}
.af-card {padding: 1rem; border-radius: 1.1rem; border: 1px solid rgba(255,255,255,.09); background: rgba(15, 20, 34, .74); box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 18px 50px rgba(0,0,0,.20);}
.af-card strong {color: #fff;}
.af-number {font-size: 1.9rem; font-weight: 900; color: #44e4ff;}
.af-orange {color: #ff7a18;}
.af-green {color: #00ff9c;}
.af-muted {color: #9ba7bf; font-size: .9rem;}
.stTabs [data-baseweb="tab-list"] {gap: .35rem;}
.stTabs [data-baseweb="tab"] {background: rgba(17,22,36,.74); border-radius: 999px; border: 1px solid rgba(255,255,255,.08); padding: .5rem .8rem;}
.stTabs [aria-selected="true"] {border-color: rgba(68,228,255,.55); color: #44e4ff;}
[data-testid="stMetric"] {background: rgba(15,20,34,.72); border: 1px solid rgba(255,255,255,.08); padding: 1rem; border-radius: 1rem;}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Mission Control")
    assets = st.multiselect("Asset universe", ASSETS, default=["BTC", "ETH", "SOL", "XRP"])
    capital = st.number_input("Strategy capital USD", min_value=500.0, value=float(os.getenv("DEFAULT_CAPITAL", 10000)), step=500.0)
    risk_profile = st.selectbox("Risk profile", ["defensive", "balanced", "aggressive"], index=1)
    require_live = st.toggle("Require live API data", value=False, help="When ON, unavailable live data will not be replaced by local simulation.")
    st.divider()
    thesis = st.text_area(
        "Market thesis",
        value="ETF inflow is improving, BTC remains the core asset, ETH is neutral, and SOL has high volatility but strong upside if liquidity expands.",
        height=150,
    )
    max_slippage = st.slider("Max paper slippage bps", 5, 150, 35, 5)
    st.caption("AlphaForge AI is research and paper execution only. Live trading is disabled.")

market, statuses = load_market(assets or ASSETS[:4], require_live=require_live)
scores = score_assets(market)
plan = build_strategy(thesis, market, capital, risk_profile)
scenario_df = scenario_matrix(plan)
exec_df = execution_board(plan, max_slippage)
score_df = pd.DataFrame([s.__dict__ for s in scores])
status_df = pd.DataFrame([s.__dict__ for s in statuses])

st.markdown(
    """
<div class="af-hero">
  <p class="af-title">🧠 AlphaForge <span class="af-orange">AI</span></p>
  <p class="af-sub">On-chain strategy command center for market thesis, alpha scoring, portfolio battle maps, scenario simulation, and paper execution planning.</p>
  <span class="af-pill">SoSoValue Intelligence</span>
  <span class="af-pill">SoDEX Market Layer</span>
  <span class="af-pill">Paper Execution</span>
  <span class="af-pill">Risk-First Workflow</span>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

k1, k2, k3, k4 = st.columns(4)
ok_sources = int(status_df["ok"].sum()) if not status_df.empty else 0
k1.metric("Regime", plan.regime)
k2.metric("Live source checks", f"{ok_sources}/{len(statuses)}")
k3.metric("Assets scored", len(scores))
k4.metric("Paper capital", f"${capital:,.0f}")

tabs = st.tabs([
    "War Room",
    "Market Radar",
    "Strategy Forge",
    "Battle Map",
    "Scenario Simulator",
    "Execution Board",
    "API Console",
    "Agent Timeline",
    "Export Report",
])

with tabs[0]:
    left, right = st.columns([1.2, .8])
    with left:
        st.subheader("Command Narrative")
        st.markdown(f"<div class='af-card'><strong>Thesis:</strong><br>{plan.thesis}<br><br><strong>Regime:</strong> <span class='af-green'>{plan.regime}</span><br><br>{plan.narrative}</div>", unsafe_allow_html=True)
        st.subheader("Top Alpha Scores")
        if not score_df.empty:
            top = score_df.sort_values("alpha_score", ascending=False).head(6)
            st.plotly_chart(px.bar(top, x="asset", y="alpha_score", color="action", title="Alpha score leaderboard"), use_container_width=True)
    with right:
        st.subheader("Readiness Checklist")
        checks = [
            ("Live data layer connected", ok_sources > 0),
            ("Strategy generated", bool(plan.allocation)),
            ("Risk rules defined", bool(plan.invalidation_rules)),
            ("Execution preview available", not exec_df.empty),
            ("Report export ready", True),
        ]
        for label, passed in checks:
            st.write(("✅" if passed else "⚠️") + " " + label)
        st.subheader("Blocked / Watchlist")
        st.write("**Watchlist:** " + (", ".join(plan.battle_zones.get("watchlist", [])) or "None"))
        st.write("**Blocked:** " + (", ".join(plan.battle_zones.get("blocked", [])) or "None"))

with tabs[1]:
    st.subheader("Market Radar")
    if score_df.empty:
        st.error("No market data available for scoring. Check API Console or disable strict live requirement.")
    else:
        selected = st.selectbox("Select asset", score_df["asset"].tolist())
        row = score_df[score_df["asset"] == selected].iloc[0]
        radar_labels = ["momentum", "flow", "liquidity", "sentiment", "risk_control"]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[row[x] for x in radar_labels], theta=radar_labels, fill="toself", name=selected))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title=f"{selected} radar profile")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(score_df.sort_values("alpha_score", ascending=False), use_container_width=True, hide_index=True)
        st.subheader("Market Series")
        selected_series = st.selectbox("Chart asset", list(market.keys()), key="series_asset")
        df = market[selected_series]
        if not df.empty:
            st.plotly_chart(px.line(df, x="date", y=["price", "sentiment", "net_flow_musd"], title=f"{selected_series} market intelligence series"), use_container_width=True)

with tabs[2]:
    st.subheader("AI Strategy Generator")
    st.markdown(f"<div class='af-card'><span class='af-muted'>Generated battle plan</span><br><br>{plan.narrative}</div>", unsafe_allow_html=True)
    st.subheader("Invalidation Rules")
    for rule in plan.invalidation_rules:
        st.write("- " + rule)
    st.subheader("Allocation Table")
    st.dataframe(pd.DataFrame(plan.allocation), use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Portfolio Battle Map")
    c1, c2, c3, c4 = st.columns(4)
    zones = [("CORE", plan.battle_zones.get("core", [])), ("SATELLITE", plan.battle_zones.get("satellite", [])), ("WATCHLIST", plan.battle_zones.get("watchlist", [])), ("BLOCKED", plan.battle_zones.get("blocked", []))]
    for col, (name, members) in zip([c1, c2, c3, c4], zones):
        with col:
            st.markdown(f"<div class='af-card'><div class='af-number'>{name}</div><br>{', '.join(members) if members else 'None'}</div>", unsafe_allow_html=True)
    alloc = pd.DataFrame(plan.allocation)
    if not alloc.empty:
        st.plotly_chart(px.pie(alloc, names="asset", values="notional_usd", title="Capital deployment map", hole=.45), use_container_width=True)

with tabs[4]:
    st.subheader("Scenario Simulator")
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(scenario_df, x="scenario", y="portfolio_impact_pct", color="response", title="Scenario impact on portfolio"), use_container_width=True)

with tabs[5]:
    st.subheader("Paper Execution Board")
    st.warning("Live order submission is disabled. This board only previews paper execution planning.")
    st.dataframe(exec_df, use_container_width=True, hide_index=True)
    if not exec_df.empty:
        st.plotly_chart(px.bar(exec_df, x="asset", y="estimated_slippage_bps", color="status", title="Estimated slippage by asset"), use_container_width=True)

with tabs[6]:
    st.subheader("API Live Console")
    st.dataframe(status_df, use_container_width=True, hide_index=True)
    st.caption("SoSoValue and SoDEX are primary connectors. When strict live mode is enabled, missing data will be shown as unavailable instead of being simulated.")

with tabs[7]:
    st.subheader("Agent War Room Timeline")
    for step in agent_timeline(plan):
        st.markdown(f"<div class='af-card'><strong>{step['stage']}</strong><br><span class='af-muted'>{step['message']}</span></div>", unsafe_allow_html=True)
        st.write("")

with tabs[8]:
    st.subheader("Exportable Strategy Report")
    report = report_markdown(plan, scores)
    st.download_button("Download Markdown Report", report, file_name="alphaforge_strategy_report.md", mime="text/markdown")
    st.code(report, language="markdown")
