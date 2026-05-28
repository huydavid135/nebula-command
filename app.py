from __future__ import annotations

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from nebula_command.connectors import ASSETS, build_pulses, pulses_frame
from nebula_command.engine import agent_timeline, export_markdown, generate_mission, scenario_matrix

load_dotenv()

st.set_page_config(page_title="Nebula Command", page_icon="🛰️", layout="wide")

st.markdown(
    """
<style>
:root { --bg:#05070f; --card:#0b1020; --line:#24304f; --cyan:#00e5ff; --violet:#a855f7; --orange:#ff7a18; --green:#20f59b; }
.stApp { background: radial-gradient(circle at top left, #172554 0, #080b16 36%, #02040a 100%); color: #f8fafc; }
.block-container { padding-top: 1rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0b1020, #05070f); border-right: 1px solid #1e2a4a; }
h1, h2, h3 { letter-spacing: -0.03em; }
.nebula-hero { padding: 1.2rem 1.3rem; border: 1px solid rgba(0,229,255,.35); border-radius: 26px; background: linear-gradient(135deg, rgba(0,229,255,.12), rgba(168,85,247,.12), rgba(255,122,24,.08)); box-shadow: 0 0 42px rgba(0,229,255,.14); }
.nebula-title { font-size: 3.2rem; font-weight: 900; line-height: 1; background: linear-gradient(90deg, #fff, #73f3ff, #ffb072); -webkit-background-clip: text; color: transparent; margin-bottom: .25rem; }
.nebula-sub { color: #a9b5d6; font-size: 1rem; }
.command-card { padding: 1rem; border-radius: 22px; background: rgba(11,16,32,.82); border: 1px solid rgba(148,163,184,.20); box-shadow: 0 18px 40px rgba(0,0,0,.25); min-height: 145px; }
.command-card strong { color: #ffffff; }
.pill { display:inline-block; padding:.25rem .55rem; border-radius:999px; border:1px solid rgba(0,229,255,.45); color:#73f3ff; margin-right:.35rem; font-size:.8rem; }
.big-number { font-size: 2.2rem; font-weight: 900; color: #fff; }
.phase { font-weight:800; color:#00e5ff; letter-spacing:.08em; }
.small-muted { color:#94a3b8; font-size:.86rem; }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🛰️ Mission Inputs")
    selected_assets = st.multiselect("Asset universe", ASSETS, default=ASSETS)
    capital = st.number_input("Command capital", min_value=100.0, value=float(os.getenv("DEFAULT_CAPITAL", 10000)), step=500.0)
    risk_mode = st.radio("Risk doctrine", ["Stealth", "Balanced", "Aggressive"], index=1)
    scenario = st.selectbox("Scenario forge", ["ETF inflow surge", "Liquidity drain", "BTC volatility shock", "Alt rotation", "Market calm"])
    st.divider()
    thesis = st.text_area(
        "Mission thesis",
        value="ETF flows strengthen while on-chain liquidity rotates into high quality majors.",
        height=150,
    )
    refresh = st.button("Run Command Scan", type="primary", use_container_width=True)
    st.caption("Live API first. If credentials or endpoints fail, the API console shows the issue instead of hiding it.")

st.markdown(
    """
<div class="nebula-hero">
  <div class="nebula-title">Nebula Command</div>
  <div class="nebula-sub">A mission-control interface for on-chain strategy: scan live sources, decode market pulses, forge scenarios, and export a decision report.</div>
</div>
""",
    unsafe_allow_html=True,
)

assets = selected_assets or ASSETS
pulses, health = build_pulses(assets)
df = pulses_frame(pulses)
plan = generate_mission(thesis, pulses, capital, risk_mode)

st.markdown("### Command Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"<div class='command-card'><span class='small-muted'>Mission Stance</span><div class='big-number'>{plan.stance}</div><span class='pill'>{risk_mode}</span></div>", unsafe_allow_html=True)
with c2:
    top_asset = df.sort_values("command_score", ascending=False).iloc[0]
    st.markdown(f"<div class='command-card'><span class='small-muted'>Top Signal</span><div class='big-number'>{top_asset.asset}</div><span class='pill'>score {top_asset.command_score}</span></div>", unsafe_allow_html=True)
with c3:
    live_count = sum(1 for h in health if h.ok)
    st.markdown(f"<div class='command-card'><span class='small-muted'>Live Source Checks</span><div class='big-number'>{live_count}/{len(health)}</div><span class='pill'>API console</span></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='command-card'><span class='small-muted'>Paper Intents</span><div class='big-number'>{len(plan.orders)}</div><span class='pill'>live trading locked</span></div>", unsafe_allow_html=True)

left, right = st.columns([1.15, 0.85])
with left:
    st.markdown("### Signal Galaxy")
    fig = px.scatter_polar(
        df,
        r="command_score",
        theta="asset",
        size="liquidity",
        color="risk",
        hover_data=["price", "momentum", "flow", "volatility", "source"],
        title="Command score orbit map",
        range_r=[0, 100],
    )
    fig.update_layout(height=470, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### Asset Pulse Matrix")
    matrix = df.set_index("asset")[["momentum", "liquidity", "flow", "volatility", "risk", "command_score"]]
    heat = go.Figure(data=go.Heatmap(z=matrix.values, x=matrix.columns, y=matrix.index, colorscale="Turbo", zmin=0, zmax=100))
    heat.update_layout(height=470, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb", margin=dict(l=30, r=10, t=30, b=30))
    st.plotly_chart(heat, use_container_width=True)

st.markdown("### Strategy War Room")
w1, w2, w3 = st.columns([0.9, 1.05, 1.05])
with w1:
    st.markdown("#### Agent Timeline")
    for item in agent_timeline(plan):
        st.markdown(f"<div class='command-card' style='min-height:76px;margin-bottom:.65rem'><span class='phase'>{item['phase']}</span><br><span class='small-muted'>{item['output']}</span></div>", unsafe_allow_html=True)
with w2:
    st.markdown("#### Portfolio Battle Map")
    zone_rows = []
    for a in plan.priority_assets:
        zone_rows.append({"zone": "Priority", "asset": a, "weight": 40})
    for a in [x for x in assets if x not in plan.priority_assets and x not in plan.blocked_assets]:
        zone_rows.append({"zone": "Watch", "asset": a, "weight": 18})
    for a in plan.blocked_assets:
        zone_rows.append({"zone": "Blocked", "asset": a, "weight": 10})
    zone_df = pd.DataFrame(zone_rows) if zone_rows else pd.DataFrame({"zone": [], "asset": [], "weight": []})
    if not zone_df.empty:
        treemap = px.treemap(zone_df, path=["zone", "asset"], values="weight", title="Core / Watch / Block zones")
        treemap.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb")
        st.plotly_chart(treemap, use_container_width=True)
    else:
        st.info("No map generated.")
with w3:
    st.markdown("#### Scenario Forge")
    shock_df = scenario_matrix(pulses, scenario, capital)
    bar = px.bar(shock_df, x="asset", y="adjusted_score", color="paper_exposure_usd", title=f"{scenario}: adjusted command score", range_y=[0, 100])
    bar.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb")
    st.plotly_chart(bar, use_container_width=True)

st.markdown("### Execution Deck")
e1, e2 = st.columns([1, 1])
with e1:
    st.markdown("#### Paper Intent Board")
    orders_df = pd.DataFrame(plan.orders)
    if orders_df.empty:
        st.warning("No paper intents. Current doctrine recommends observation only.")
    else:
        st.dataframe(orders_df, use_container_width=True, hide_index=True)
    st.caption("This product does not submit live orders. It produces paper execution plans only.")
with e2:
    st.markdown("#### Live API Console")
    health_df = pd.DataFrame([h.__dict__ for h in health])
    st.dataframe(health_df, use_container_width=True, hide_index=True)

st.markdown("### Mission Report")
report = export_markdown(plan)
st.download_button("Download Strategy Report", report, file_name="nebula-command-report.md", mime="text/markdown")
with st.expander("Preview report"):
    st.markdown(report)
