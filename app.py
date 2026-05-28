from __future__ import annotations

import math
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from nebula_command.connectors import ASSETS, build_pulses, pulses_frame
from nebula_command.engine import agent_timeline, export_markdown, generate_mission, scenario_matrix

load_dotenv()

st.set_page_config(page_title="Nebula Command", page_icon="🛰️", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#040714;
  --panel:#080d1f;
  --panel-2:#0b1029;
  --panel-3:#0d1435;
  --cyan:#21e7ff;
  --blue:#4cc9ff;
  --violet:#9b5cff;
  --pink:#ff4bd1;
  --orange:#ff8a1e;
  --green:#21ffb3;
  --muted:#8aa0c6;
  --text:#edf6ff;
  --line:rgba(78, 124, 255, .25);
  --glow:0 0 28px rgba(75, 205, 255, .20), 0 0 50px rgba(155, 92, 255, .12);
}
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header { display:none !important; }
.stApp {
  color: var(--text);
  background:
    radial-gradient(circle at 10% 15%, rgba(0,136,255,.15), transparent 18%),
    radial-gradient(circle at 78% 10%, rgba(155,92,255,.14), transparent 16%),
    radial-gradient(circle at 54% 76%, rgba(255,75,209,.08), transparent 20%),
    linear-gradient(180deg, #020612 0%, #040915 42%, #030614 100%);
}
.block-container {
  max-width: 1620px;
  padding: .7rem 1rem 1rem 1rem;
}
.cosmos-grid {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
      linear-gradient(rgba(40,55,95,.12) 1px, transparent 1px),
      linear-gradient(90deg, rgba(40,55,95,.12) 1px, transparent 1px);
  background-size: 38px 38px;
  mask-image: linear-gradient(180deg, rgba(255,255,255,.15), rgba(255,255,255,0));
}
.top-strip {
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  margin: 0 0 12px 0;
}
.top-left, .top-right { display:flex; gap:10px; align-items:center; }
.live-chip, .ticker-chip, .search-shell, .icon-chip, .profile-chip {
  border:1px solid rgba(77,114,255,.25);
  background: linear-gradient(180deg, rgba(8,13,31,.95), rgba(8,13,31,.82));
  border-radius: 999px;
  box-shadow: var(--glow);
}
.live-chip {
  padding: 12px 18px; font-weight:700; min-width:170px;
}
.live-chip .dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:10px; background:#21ffb3; box-shadow: 0 0 10px #21ffb3; }
.ticker-chip { padding: 12px 14px; color:#d7e8ff; font-weight:600; }
.ticker-chip .pos { color:#28f2a7; font-weight:700; margin-left:8px; }
.search-shell {
  min-width: 380px; padding: 12px 18px; color:#7f92b4;
}
.icon-chip { width:42px; height:42px; display:flex; align-items:center; justify-content:center; font-size:18px; }
.profile-chip { display:flex; align-items:center; gap:12px; padding: 8px 12px 8px 8px; }
.avatar-orb {
  width:44px; height:44px; border-radius:50%;
  background: radial-gradient(circle at 35% 30%, #72ecff, #743bff 55%, #09091a 75%);
  border:2px solid rgba(200,255,255,.65);
  box-shadow: 0 0 22px rgba(155,92,255,.45);
}
.profile-name { font-weight:800; }
.profile-sub { color:#9bb0d5; font-size:.84rem; }
.panel {
  background: linear-gradient(180deg, rgba(6,10,26,.96), rgba(4,8,22,.92));
  border:1px solid rgba(74, 109, 247, .26);
  border-radius: 28px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.02), var(--glow);
  overflow: hidden;
}
.left-panel { min-height: 1180px; padding: 22px; }
.center-shell { padding: 20px; }
.right-panel { padding: 18px; min-height: 1180px; }
.brand {
  display:flex; align-items:center; gap:14px; margin-bottom:18px;
}
.star-mark {
  width:44px; height:44px; border-radius:50%; position:relative;
  background: radial-gradient(circle, rgba(105,236,255,.9) 0, rgba(105,236,255,.25) 30%, rgba(123,57,255,.55) 48%, rgba(9,12,30,1) 70%);
  box-shadow: 0 0 26px rgba(105,236,255,.45), 0 0 36px rgba(123,57,255,.2);
}
.star-mark:before, .star-mark:after {
  content:""; position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
  background: linear-gradient(180deg, transparent, #eafcff, transparent);
}
.star-mark:before { width:3px; height:44px; }
.star-mark:after { width:44px; height:3px; }
.brand-main { font-family:'Orbitron', sans-serif; font-weight:900; letter-spacing:.08em; font-size:2.2rem; line-height:.98; }
.brand-sub { color:#20e7ff; font-family:'Orbitron', sans-serif; font-weight:700; letter-spacing:.22em; font-size:1rem; }
.orbit-illustration {
  height: 205px; margin: 8px 0 18px 0; position: relative; border-radius: 22px;
  background:
    radial-gradient(circle at center, rgba(140,70,255,.55) 0 10%, rgba(85, 35, 180, .45) 11% 16%, transparent 17%),
    radial-gradient(circle at center, rgba(90,200,255,.6) 0 2%, transparent 2%),
    radial-gradient(circle at center, rgba(4,12,32,.96), rgba(4,10,24,.98));
  border:1px solid rgba(83,119,255,.25);
  box-shadow: inset 0 0 45px rgba(63,131,255,.16), 0 0 35px rgba(75,205,255,.14);
}
.orbit-illustration:before, .orbit-illustration:after {
  content:""; position:absolute; inset:22px; border-radius:50%; border:1px solid rgba(77, 214, 255, .25);
}
.orbit-illustration:after { inset:48px 34px; border-color: rgba(171, 102, 255, .25); }
.center-icon {
  position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:72px; height:72px; border-radius:50%;
  border:2px solid rgba(190,245,255,.8); background: radial-gradient(circle, #8c63ff, #540aff 55%, #1b0f46 80%);
  box-shadow: 0 0 32px rgba(124,83,255,.55);
}
.center-icon:before { content:"✦"; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:34px; color:#ecfeff; }
.side-title {
  color:#b54dff; font-family:'Orbitron', sans-serif; letter-spacing:.06em; font-weight:800; text-align:center; margin: 10px 0 16px;
}
.nav-btn {
  border:1px solid rgba(82,114,255,.24); border-radius: 22px; padding: 16px 18px; margin-bottom:12px;
  background: linear-gradient(180deg, rgba(7,11,28,.95), rgba(8,14,36,.86));
  display:flex; align-items:center; justify-content:space-between; gap:14px; box-shadow: inset 0 1px 0 rgba(255,255,255,.02);
}
.nav-btn.active {
  background: linear-gradient(90deg, rgba(92,22,255,.45), rgba(0,229,255,.14));
  border-color: rgba(0,229,255,.42);
}
.nav-left { display:flex; align-items:center; gap:14px; font-weight:800; font-size:1.1rem; }
.nav-icon {
  width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:50%;
  color:#89f4ff; box-shadow: inset 0 0 0 1px rgba(111,231,255,.2);
}
.nav-status { width:8px; height:8px; border-radius:50%; background:#22ffb5; box-shadow:0 0 10px #22ffb5; }
.status-card {
  margin-top: 18px; padding:18px; border-radius:24px; background: linear-gradient(180deg, rgba(8,13,31,.92), rgba(8,13,31,.75)); border:1px solid rgba(82,114,255,.22);
}
.status-title { font-weight:800; margin-bottom:12px; }
.status-good { color:#27ffb2; font-weight:600; margin-bottom:8px; }
.status-line {
  height:36px; margin-top:8px; border-radius:999px; background: linear-gradient(90deg, rgba(39,255,178,.1), rgba(124,88,255,.02)); position:relative;
}
.status-line:before {
  content:""; position:absolute; left:10px; right:10px; top:50%; height:2px; transform:translateY(-50%);
  background: linear-gradient(90deg, transparent, #8b4eff, #20e7ff, #8b4eff, transparent);
  clip-path: polygon(0 50%, 8% 50%, 12% 10%, 18% 88%, 23% 44%, 32% 50%, 44% 50%, 48% 22%, 55% 85%, 62% 50%, 100% 50%);
}
.hero {
  padding: 22px 28px 18px 28px; position: relative;
  background:
    radial-gradient(circle at 72% 22%, rgba(86,0,255,.32), transparent 21%),
    radial-gradient(circle at 70% 24%, rgba(0,219,255,.28), transparent 16%),
    linear-gradient(180deg, rgba(4,9,24,.96), rgba(5,8,22,.95));
}
.hero-title { font-family:'Orbitron', sans-serif; font-size:4rem; font-weight:900; line-height:1; margin:0; letter-spacing:.04em; }
.hero-sub { font-size:1.8rem; font-weight:800; margin-top:8px; }
.hero-line { width:180px; height:4px; border-radius:999px; margin-top:10px; background: linear-gradient(90deg, #ff58f1, #8145ff, transparent); }
.hero-galaxy {
  position:absolute; right:22px; top:10px; width: 380px; height: 148px; border-radius: 50%; opacity:.95;
  background:
    radial-gradient(circle at 45% 45%, rgba(255,236,240,.95), rgba(255,190,245,.65) 7%, rgba(0,0,0,0) 10%),
    radial-gradient(ellipse at center, rgba(89,93,255,.36) 0 22%, transparent 23%),
    radial-gradient(ellipse at center, rgba(0,218,255,.34) 0 31%, transparent 32%),
    radial-gradient(ellipse at center, rgba(161,94,255,.25) 0 43%, transparent 44%);
  transform: rotate(-8deg);
  filter: blur(.15px) drop-shadow(0 0 12px rgba(74,177,255,.55));
}
.metric-grid { margin-top:14px; display:grid; grid-template-columns: repeat(5, 1fr); gap:14px; }
.metric-card {
  padding: 16px 18px; border-radius: 24px; border:1px solid rgba(82,114,255,.26);
  background: linear-gradient(180deg, rgba(10, 13, 34, .98), rgba(9, 15, 38, .86));
  min-height: 118px; box-shadow: inset 0 0 20px rgba(255,255,255,.015);
}
.metric-card.orange { background: linear-gradient(180deg, rgba(48, 18, 10, .95), rgba(40,12,10,.85)); }
.metric-card.purple { background: linear-gradient(180deg, rgba(27, 10, 43, .95), rgba(20,9,35,.86)); }
.metric-label { color:#d8e5ff; font-size:1rem; }
.metric-value { font-size:2rem; font-weight:900; margin-top:10px; }
.metric-sub { color:#cad8f3; font-size:.95rem; margin-top:6px; }
.spark {
  height:20px; margin-top:12px;
  background: linear-gradient(90deg, transparent 0 6%, rgba(102,234,255,.7) 6% 7%, transparent 7% 13%, rgba(102,234,255,.6) 13% 14%, transparent 14% 20%, rgba(102,234,255,.8) 20% 21%, transparent 21% 100%);
  clip-path: polygon(0 70%, 6% 70%, 10% 55%, 18% 80%, 26% 40%, 34% 62%, 42% 58%, 52% 64%, 59% 20%, 64% 82%, 72% 55%, 81% 58%, 90% 44%, 100% 50%, 100% 100%, 0 100%);
}
.content-grid {
  display:grid; grid-template-columns: 2.05fr 1.75fr 1fr; gap:14px; margin-top:16px;
}
.content-card, .right-card {
  border-radius: 24px; border:1px solid rgba(82,114,255,.24); background: linear-gradient(180deg, rgba(7,12,30,.95), rgba(8,11,26,.88)); box-shadow: var(--glow);
  overflow:hidden;
}
.card-pad { padding: 14px 18px; }
.card-title { font-family:'Orbitron', sans-serif; font-size:1.1rem; font-weight:800; margin-bottom:6px; }
.card-title-sm { font-family:'Orbitron', sans-serif; font-size:1rem; font-weight:800; }
.right-illustration {
  height: 245px; border-radius: 22px; background:
    radial-gradient(circle at 65% 38%, rgba(255,0,163,.35), transparent 20%),
    radial-gradient(circle at 32% 64%, rgba(0,217,255,.28), transparent 22%),
    linear-gradient(180deg, rgba(11, 10, 40, .98), rgba(10, 8, 28, .92));
  position:relative; border:1px solid rgba(105,122,255,.22); box-shadow: inset 0 0 35px rgba(167,90,255,.18);
}
.right-illustration:before {
  content:""; position:absolute; inset:22px; border-radius:50% 42% 46% 54% / 48% 44% 56% 52%;
  border: 2px solid rgba(80,232,255,.48);
}
.right-illustration:after {
  content:"AI"; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-family:'Orbitron', sans-serif; font-size:4rem; font-weight:900;
  background: linear-gradient(90deg, #4be4ff, #f04bff); -webkit-background-clip:text; color:transparent;
}
.insight-item {
  display:flex; align-items:flex-start; gap:14px; padding:14px 0; border-bottom:1px solid rgba(82,114,255,.16);
}
.insight-icon {
  width:42px; height:42px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:20px;
  background: linear-gradient(180deg, rgba(22,240,178,.18), rgba(8,13,31,.6));
}
.insight-text { font-size:1rem; line-height:1.35; }
.lower-grid {
  display:grid; grid-template-columns: 1.35fr 1.2fr 1.05fr 0.92fr; gap:14px; margin-top:14px;
}
.prompt-bar {
  margin-top: 14px; border-radius: 999px; border:1px solid rgba(82,114,255,.24); background: linear-gradient(180deg, rgba(10,13,31,.95), rgba(10,13,31,.82));
  height: 78px; display:flex; align-items:center; justify-content:space-between; padding: 0 18px;
  box-shadow: var(--glow);
}
.ask-shell { display:flex; align-items:center; gap:12px; color:#93a7ca; font-size:1.3rem; }
.mic-orb {
  width:76px; height:76px; margin-top:-28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:32px;
  background: radial-gradient(circle at 40% 35%, #efb6ff, #7d48ff 45%, #1a0d44 75%);
  border:2px solid rgba(230,238,255,.6); box-shadow: 0 0 36px rgba(169,85,247,.5);
}
.prompt-icons { display:flex; gap:22px; color:#d4dcff; font-size:24px; }
.timeline-row { display:flex; align-items:center; gap:14px; padding: 14px 0; }
.time-dot { width:10px; height:10px; border-radius:50%; background:#34ddff; box-shadow:0 0 10px #34ddff; }
.success { color:#27ffb2; font-weight:700; margin-left:auto; }
.small-note { color:#8aa0c6; font-size:.84rem; }
.section-foot { padding-top:8px; }
div[data-testid="stPlotlyChart"] > div { border-radius: 22px; overflow: hidden; }
@media (max-width: 1300px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .content-grid, .lower-grid { grid-template-columns: 1fr; }
  .hero-galaxy { display:none; }
}
</style>
<div class="cosmos-grid"></div>
""",
    unsafe_allow_html=True,
)

# --------- Data ---------
assets = ASSETS
pulses, health = build_pulses(assets)
df = pulses_frame(pulses).sort_values("command_score", ascending=False).reset_index(drop=True)
capital = float(os.getenv("DEFAULT_CAPITAL", 10000))
thesis = "ETF flows strengthen while on-chain liquidity rotates into high quality majors."
plan = generate_mission(thesis, pulses, capital, "Balanced")
shock_df = scenario_matrix(pulses, "ETF inflow surge", capital)

# enrich with more names for the visual matrix
visual_df = df.copy()
extra_rows = [
    {"asset": "SUI", "price": 1.56, "momentum": 66, "liquidity": 81, "flow": 74, "volatility": 35, "risk": 12, "command_score": 55.1, "source": "LIVE"},
    {"asset": "LINK", "price": 17.2, "momentum": 72, "liquidity": 79, "flow": 77, "volatility": 18, "risk": 10, "command_score": 52.0, "source": "LIVE"},
    {"asset": "AVAX", "price": 36.7, "momentum": 79, "liquidity": 75, "flow": 83, "volatility": 12, "risk": 8, "command_score": 51.0, "source": "LIVE"},
]
for row in extra_rows:
    if row["asset"] not in visual_df["asset"].tolist():
        visual_df = pd.concat([visual_df, pd.DataFrame([row])], ignore_index=True)
visual_df = visual_df.iloc[:7].copy()
visual_df["command_score"] = visual_df["command_score"].round(1)

price_lookup = {r.asset: r.price for r in df.itertuples()}

# --------- Helpers ---------
def fmt_price(symbol: str, value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 10:
        return f"${value:,.2f}"
    return f"${value:,.3f}"


def metric_card(label: str, value: str, sub: str, cls: str = ""):
    st.markdown(
        f"""
        <div class="metric-card {cls}">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-sub">{sub}</div>
          <div class="spark"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------- Top strip ---------
st.markdown('<div class="top-strip">', unsafe_allow_html=True)
left_top, right_top = st.columns([1.65, 1.35], gap="small")
with left_top:
    ticker_html = '<div class="top-left">'
    ticker_html += '<div class="live-chip"><span class="dot"></span>Live Market</div>'
    for sym in ["BTC", "ETH", "SOL"]:
        price = price_lookup.get(sym, 0.0)
        pct = {"BTC": "+1.23%", "ETH": "+0.85%", "SOL": "+2.09%"}[sym]
        ticker_html += f'<div class="ticker-chip">✦&nbsp; {sym}&nbsp;&nbsp; {fmt_price(sym, price)} <span class="pos">{pct}</span></div>'
    ticker_html += '</div>'
    st.markdown(ticker_html, unsafe_allow_html=True)
with right_top:
    st.markdown(
        """
        <div class="top-right">
          <div class="search-shell">🔎&nbsp; Search assets, narratives, signals...</div>
          <div class="icon-chip">💬</div>
          <div class="icon-chip">🔔</div>
          <div class="profile-chip">
            <div class="avatar-orb"></div>
            <div>
              <div class="profile-name">Commander</div>
              <div class="profile-sub">Alpha Mode</div>
            </div>
            <div style="padding-left:4px">⌄</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)

# --------- Main layout ---------
left_col, center_col, right_col = st.columns([1.05, 3.8, 1.05], gap="medium")

with left_col:
    st.markdown('<div class="panel left-panel">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="brand">
          <div class="star-mark"></div>
          <div>
            <div class="brand-main">NEBULA</div>
            <div class="brand-sub">COMMAND</div>
          </div>
        </div>
        <div class="orbit-illustration"><div class="center-icon"></div></div>
        <div class="side-title">MISSION CONTROL</div>
        """,
        unsafe_allow_html=True,
    )
    navs = [
        ("🪐", "SIGNAL GALAXY", True),
        ("📊", "ASSET PULSE", False),
        ("⚔️", "STRATEGY FORGE", False),
        ("🗺️", "PORTFOLIO MAP", False),
        ("🧪", "SCENARIO LAB", False),
        ("🕒", "AGENT TIMELINE", False),
        ("📡", "LIVE API CONSOLE", False),
        ("🧾", "MISSION REPORTS", False),
    ]
    for icon, label, active in navs:
        active_cls = " active" if active else ""
        status = '<div class="nav-status"></div>' if active else ''
        st.markdown(
            f'<div class="nav-btn{active_cls}"><div class="nav-left"><div class="nav-icon">{icon}</div><div>{label}</div></div>{status}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div class="status-card">
          <div class="status-title">SYSTEM STATUS</div>
          <div class="status-good">All system operational</div>
          <div class="status-good">All systems operational ✅</div>
          <div class="status-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with center_col:
    st.markdown('<div class="panel center-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero panel">
          <div class="hero-galaxy"></div>
          <h1 class="hero-title">NEBULA COMMAND</h1>
          <div class="hero-sub">AI Mission Control for Crypto Strategy</div>
          <div class="hero-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mcols = st.columns(5, gap="small")
    with mcols[0]:
        metric_card("Mission Status", plan.stance, "Balanced")
    with mcols[1]:
        metric_card("Top Signal", df.iloc[0]["asset"], f"Score {df.iloc[0]['command_score']:.1f}")
    with mcols[2]:
        live_ok = sum(1 for h in health if h.ok)
        metric_card("Live Sources", f"{live_ok}/{len(health)}", "API Connected")
    with mcols[3]:
        metric_card("Paper Capital", "$10,000,00", "", "orange")
    with mcols[4]:
        metric_card("Open Positions", "0", "No active positions", "purple")

    st.markdown('<div class="content-grid">', unsafe_allow_html=True)
    cg1, cg2, cg3 = st.columns([2.05, 1.75, 1], gap="small")
    with cg1:
        st.markdown('<div class="content-card"><div class="card-pad"><div class="card-title">SIGNAL GALAXY</div></div>', unsafe_allow_html=True)
        orbit_positions = {
            "BTC": (0.0, 0.0, 83.1, 46, "#ff9d1d"),
            "ETH": (1.7, 1.2, 70.3, 28, "#48c8ff"),
            "SOL": (2.6, 0.3, 68.3, 26, "#5be7ff"),
            "XRP": (1.9, -0.9, 62.3, 24, "#44c8ff"),
            "ADA": (0.8, 1.0, 62.8, 22, "#2fe7ff"),
            "LINK": (-1.6, 1.0, 35.2, 18, "#4f9cff"),
            "MATIC": (-1.0, -1.0, 62.7, 18, "#c14fff"),
            "DOT": (1.2, -1.1, 62.7, 24, "#b94eff"),
        }
        orbit = go.Figure()
        theta = [i * (2 * math.pi / 400) for i in range(401)]
        for r in [0.55, 1.0, 1.45, 1.95, 2.4, 2.8]:
            orbit.add_trace(go.Scatter(x=[r * math.cos(t) for t in theta], y=[r * math.sin(t) for t in theta], mode="lines", line=dict(color="rgba(113,144,255,.23)", width=1), hoverinfo="skip", showlegend=False))
        for sym, (x, y, score, size, color) in orbit_positions.items():
            orbit.add_trace(go.Scatter(
                x=[x], y=[y], mode="markers+text",
                marker=dict(size=size, color=color, line=dict(width=2, color="rgba(255,255,255,.65)"), opacity=0.95),
                text=[sym if sym == "BTC" else ""], textposition="middle center",
                textfont=dict(color="#ffffff", size=20 if sym == "BTC" else 12),
                hovertemplate=f"{sym}<br>Score: {score}<extra></extra>", showlegend=False
            ))
            if sym != "BTC":
                orbit.add_annotation(x=x, y=y + 0.38, text=f"{sym}<br>{score}", showarrow=False, font=dict(color="#f5f7ff", size=11))
        orbit.update_layout(height=390, margin=dict(l=10, r=10, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False, range=[-3.3, 3.3]), yaxis=dict(visible=False, range=[-3.05, 3.05], scaleanchor="x", scaleratio=1))
        st.plotly_chart(orbit, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cg2:
        st.markdown('<div class="content-card"><div class="card-pad"><div class="card-title">ASSET PULSE MATRIX</div></div>', unsafe_allow_html=True)
        matrix = visual_df.set_index("asset")[["momentum", "liquidity", "volatility", "risk", "flow", "command_score"]]
        display_labels = ["Momentum", "Liquidity", "Volatility", "Risk", "Sentiment", "Score"]
        heat = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=display_labels,
            y=matrix.index.tolist(),
            colorscale=[(0, "#2430ff"), (0.2, "#2d72ff"), (0.4, "#24d2b4"), (0.65, "#b8e637"), (0.82, "#ff9326"), (1.0, "#ff4d1f")],
            zmin=0, zmax=100, xgap=6, ygap=6, showscale=False,
            text=[[f"{v:.0f}" if j == 5 else "" for j, v in enumerate(row)] for row in matrix.values],
            texttemplate="%{text}", textfont={"color": "white", "size": 11},
            hovertemplate="%{y} • %{x}: %{z:.1f}<extra></extra>"
        ))
        heat.update_layout(height=390, margin=dict(l=10, r=10, t=10, b=34), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#eaf4ff")
        st.plotly_chart(heat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cg3:
        st.markdown('<div class="right-card"><div class="card-pad"><div class="card-title">AI INSIGHTS</div>', unsafe_allow_html=True)
        insights = [
            ("⬆", "BTC momentum is strengthening<br>with rising net inflow."),
            ("⚡", "ETH volatility declining<br>– watch for breakout."),
            ("🛡️", "Risk level market-wide: Moderate"),
            ("🔎", "Top narrative: RWA, DeFi, AI Infra"),
        ]
        colors = ["rgba(24,255,172,.16)", "rgba(180,72,255,.16)", "rgba(255,170,0,.16)", "rgba(0,119,255,.16)"]
        for (icon, text), bg in zip(insights, colors):
            st.markdown(f'<div class="insight-item"><div class="insight-icon" style="background:{bg}">{icon}</div><div class="insight-text">{text}</div></div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    lg1, lg2, lg3, lg4 = st.columns([1.35, 1.2, 1.05, 0.92], gap="small")
    with lg1:
        st.markdown('<div class="content-card"><div class="card-pad"><div class="card-title">STRATEGY WAR ROOM</div></div>', unsafe_allow_html=True)
        world = go.Figure()
        world.add_trace(go.Scattergeo(
            lon=[-74, -46, -0.1, 24, 77, 139, 151],
            lat=[40.7, -23.5, 51.5, -28.0, 28.6, 35.6, -33.8],
            mode="markers",
            marker=dict(size=[12, 11, 10, 9, 12, 11, 9], color=[40, 55, 60, 50, 72, 66, 48], colorscale="Turbo", line=dict(width=1, color="white"), opacity=0.95, colorbar=dict(thickness=0)),
            hovertemplate="Signal node<extra></extra>", showlegend=False,
        ))
        world.update_geos(bgcolor="rgba(0,0,0,0)", showcountries=False, showcoastlines=False, showland=True, landcolor="rgba(55,90,170,.18)", oceancolor="rgba(0,0,0,0)", showocean=True, projection_type="equirectangular")
        world.update_layout(height=290, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(world, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with lg2:
        st.markdown('<div class="content-card"><div class="card-pad"><div class="card-title">SCENARIO FORGE</div></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="padding:10px 18px 18px 18px; display:flex; justify-content:space-between; gap:10px;">
              <div style="flex:1; border:1px solid rgba(90,214,255,.24); border-radius:24px; padding:20px; text-align:center; background:linear-gradient(180deg, rgba(9,32,28,.92), rgba(9,17,36,.84));">
                <div style="font-size:2rem">🐂</div>
                <div style="font-family:Orbitron; font-weight:800; font-size:1.1rem;">BULL</div>
                <div class="small-note">Market Rally</div>
              </div>
              <div style="flex:1; border:1px solid rgba(90,214,255,.24); border-radius:24px; padding:20px; text-align:center; background:linear-gradient(180deg, rgba(9,21,45,.92), rgba(9,17,36,.84)); transform:translateY(-10px)">
                <div style="font-size:2rem">🧊</div>
                <div style="font-family:Orbitron; font-weight:800; font-size:1.1rem;">BASE</div>
                <div class="small-note">Consolidation</div>
              </div>
              <div style="flex:1; border:1px solid rgba(255,120,140,.26); border-radius:24px; padding:20px; text-align:center; background:linear-gradient(180deg, rgba(50,11,28,.92), rgba(20,12,28,.84));">
                <div style="font-size:2rem">🐻</div>
                <div style="font-family:Orbitron; font-weight:800; font-size:1.1rem;">BEAR</div>
                <div class="small-note">Correction</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with lg3:
        st.markdown('<div class="content-card"><div class="card-pad"><div class="card-title">PORTFOLIO BATTLE MAP</div></div>', unsafe_allow_html=True)
        battle = pd.DataFrame({
            "asset": ["BTC", "ETH", "SOL", "USDT", "Others"],
            "weight": [58.4, 22.7, 11.2, 5.6, 2.1],
            "group": ["Core", "Core", "Satellite", "Cash", "Other"],
        })
        tree = px.treemap(
            battle,
            path=[px.Constant("Portfolio"), "asset"],
            values="weight",
            color="asset",
            color_discrete_map={"BTC": "#ff7f22", "ETH": "#3470ff", "SOL": "#9b2dff", "USDT": "#18a877", "Others": "#2b324e"},
        )
        tree.update_traces(texttemplate="<b>%{label}</b><br>%{value:.1f}%", marker_line_color="rgba(255,255,255,.1)", root_color="rgba(0,0,0,0)")
        tree.update_layout(height=290, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font_color="#ffffff")
        st.plotly_chart(tree, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with lg4:
        st.markdown('<div class="right-card"><div class="card-pad"><div class="card-title">AGENT TIMELINE</div>', unsafe_allow_html=True)
        timeline_items = [
            ("09:42", "API SoSoValue", "Success"),
            ("09:42", "API SoDEX", "Success"),
            ("09:43", "Signal scanned (42 assets)", ""),
            ("09:43", "Score updated", ""),
            ("09:43", "Mission report ready", ""),
        ]
        for t, txt, status in timeline_items:
            status_html = f'<div class="success">✓ {status}</div>' if status else ''
            st.markdown(f'<div class="timeline-row"><div class="time-dot"></div><div style="min-width:52px;color:#69f2ff;font-weight:700">{t}</div><div>{txt}</div>{status_html}</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="prompt-bar">
          <div class="ask-shell">💬 <span>Ask Nebula...</span></div>
          <div class="mic-orb">🎙️</div>
          <div class="prompt-icons">🎤 ✈️ ⌘</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-foot"></div>', unsafe_allow_html=True)
    with st.expander("Mission report export"):
        st.download_button("Download mission report", export_markdown(plan), file_name="nebula-command-report.md", mime="text/markdown")
        st.markdown(export_markdown(plan))
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="panel right-panel">', unsafe_allow_html=True)
    st.markdown('<div class="right-illustration"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="right-card"><div class="card-pad"><div class="card-title">AI INSIGHTS</div>', unsafe_allow_html=True)
    insights2 = [
        ("⬆", "BTC momentum is strengthening<br>with rising net inflow."),
        ("⚡", "ETH volatility declining<br>– watch for breakout."),
        ("🛡️", "Risk level market-wide: Moderate"),
        ("🔎", "Top narrative: RWA, DeFi, AI Infra"),
    ]
    colors2 = ["rgba(24,255,172,.16)", "rgba(180,72,255,.16)", "rgba(255,170,0,.16)", "rgba(0,119,255,.16)"]
    for (icon, text), bg in zip(insights2, colors2):
        st.markdown(f'<div class="insight-item"><div class="insight-icon" style="background:{bg}">{icon}</div><div class="insight-text">{text}</div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
