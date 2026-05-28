from __future__ import annotations

import math
import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from nebula_command.connectors import ASSETS, build_pulses, pulses_frame
from nebula_command.engine import export_markdown, generate_mission, scenario_matrix

load_dotenv()


def sync_streamlit_secrets() -> None:
    """Expose Streamlit Cloud secrets to the connector layer via environment variables."""
    try:
        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ.setdefault(str(key), str(value))
    except Exception:
        pass


sync_streamlit_secrets()

st.set_page_config(page_title="Nebula Command", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#030611;--panel:#080d22;--line:rgba(74,113,255,.28);--cyan:#20e7ff;--violet:#9a56ff;--pink:#ff47d6;--orange:#ff7e1d;--green:#23ffac;--text:#f5fbff;--muted:#96a8c8;--shadow:0 0 28px rgba(32,231,255,.13),0 0 60px rgba(154,86,255,.11),0 22px 55px rgba(0,0,0,.34)}
*{box-sizing:border-box} html, body, [class*="css"]{font-family:'Inter',sans-serif}
[data-testid="stSidebar"],[data-testid="collapsedControl"],header,footer,#MainMenu{display:none!important}
.stApp{background:radial-gradient(circle at 13% 15%,rgba(38,92,255,.16),transparent 18%),radial-gradient(circle at 71% 7%,rgba(138,67,255,.16),transparent 18%),radial-gradient(circle at 86% 79%,rgba(0,218,255,.08),transparent 18%),linear-gradient(180deg,#030611 0%,#040816 100%);color:var(--text)}
.block-container{max-width:1680px;padding:.65rem .8rem 1rem!important}.cosmos-grid{position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,110,190,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(79,110,190,.08) 1px,transparent 1px);background-size:38px 38px;mask-image:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,0) 65%)}
.left-rail{min-height:1030px;padding:21px 18px;background:linear-gradient(180deg,rgba(5,9,24,.98),rgba(5,8,20,.96));border:1px solid rgba(62,93,190,.32);border-radius:0 30px 30px 0;box-shadow:var(--shadow)}
.brand{display:flex;align-items:center;gap:13px;margin-bottom:20px}.logo-star{width:48px;height:48px;border-radius:50%;position:relative;background:radial-gradient(circle,#fff 0 7%,#7beaff 8% 10%,#7b37ff 21%,rgba(21,10,58,.95) 58%,rgba(5,7,22,1) 77%);box-shadow:0 0 28px rgba(40,231,255,.38),0 0 36px rgba(158,72,255,.38)}.logo-star:before,.logo-star:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:linear-gradient(90deg,transparent,#fff,transparent)}.logo-star:before{width:46px;height:3px}.logo-star:after{width:3px;height:46px}.brand-name{font-family:'Orbitron',sans-serif;font-size:1.82rem;font-weight:900;letter-spacing:.08em;line-height:.96}.brand-name span{display:block;color:#18e7ff;font-size:.96rem;letter-spacing:.32em;margin-top:4px}
.orbit-box{height:210px;border-radius:28px;margin:13px 0 18px;position:relative;background:radial-gradient(circle at 50% 50%,rgba(123,72,255,.68) 0 11%,rgba(55,29,168,.55) 12% 18%,transparent 19%),radial-gradient(ellipse at center,rgba(7,17,47,.95),rgba(4,8,22,.98));border:1px solid rgba(59,115,255,.27);box-shadow:inset 0 0 44px rgba(32,231,255,.12);overflow:hidden}.orbit-box:before,.orbit-box:after{content:"";position:absolute;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:1px solid rgba(44,229,255,.30)}.orbit-box:before{width:178px;height:86px}.orbit-box:after{width:212px;height:128px;border-color:rgba(151,86,255,.28)}.orbit-center{position:absolute;width:66px;height:66px;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:2px solid rgba(224,250,255,.85);box-shadow:0 0 28px rgba(151,86,255,.55)}.orbit-center:before{content:"✦";display:flex;align-items:center;justify-content:center;height:100%;font-size:34px}.side-kicker{text-align:center;color:#be6fff;font-family:'Orbitron';font-weight:800;margin:2px 0 15px;letter-spacing:.06em}
.left-rail div[data-testid="stButton"] button{height:58px;width:100%;border:1px solid rgba(63,92,184,.32)!important;border-radius:22px!important;padding:0 16px!important;margin-bottom:2px!important;background:linear-gradient(180deg,rgba(7,12,31,.96),rgba(7,12,31,.79))!important;color:#fff!important;text-align:left!important;font-weight:900!important;font-size:.98rem!important;letter-spacing:.02em!important;box-shadow:none!important}.left-rail div[data-testid="stButton"] button:hover{border-color:rgba(33,231,255,.55)!important;background:linear-gradient(90deg,rgba(117,45,255,.46),rgba(4,23,55,.78))!important}.nav-active{border:1px solid rgba(33,231,255,.44);border-radius:22px;padding:8px 12px;background:linear-gradient(90deg,rgba(117,45,255,.46),rgba(4,23,55,.78));margin-bottom:6px;box-shadow:0 0 24px rgba(130,68,255,.15);font-weight:900}.status-panel{margin-top:18px;border:1px solid rgba(63,92,184,.24);border-radius:24px;padding:17px;background:linear-gradient(180deg,rgba(7,12,31,.95),rgba(8,13,31,.74))}.status-title{font-weight:900;letter-spacing:.03em}.status-good{color:#22ffad;font-size:.9rem;font-weight:700;margin-top:10px}.status-bad{color:#ff6b7a;font-size:.9rem;font-weight:700;margin-top:10px}.ecg{height:42px;position:relative;margin-top:7px}.ecg:before{content:"";position:absolute;left:4px;right:4px;top:21px;height:2px;background:linear-gradient(90deg,transparent,#894dff,#24e7ff,#894dff,transparent);clip-path:polygon(0 50%,10% 50%,14% 18%,20% 82%,25% 48%,34% 50%,45% 50%,50% 8%,58% 90%,65% 50%,100% 50%)}
.top-bar{margin-bottom:13px}.pill-top{border:1px solid rgba(70,103,219,.28);border-radius:999px;background:linear-gradient(180deg,rgba(8,13,31,.95),rgba(8,13,31,.82));height:44px;display:flex;align-items:center;padding:0 16px;box-shadow:var(--shadow);font-weight:800}.dot{width:10px;height:10px;border-radius:50%;background:#20ffad;box-shadow:0 0 10px #20ffad;margin-right:10px}.up{color:#20ffad;margin-left:8px}.avatar{width:46px;height:46px;border-radius:50%;background:radial-gradient(circle at 34% 28%,#b7f4ff,#7d4dff 53%,#111333 74%);border:2px solid rgba(222,242,255,.75);box-shadow:0 0 28px rgba(171,88,255,.45)}.profile-label{font-weight:900}.profile-sub{color:#93a7ca;font-size:.8rem}.top-control div[data-testid="stTextInput"] input{border-radius:999px!important;background:rgba(8,13,31,.86)!important;border:1px solid rgba(70,103,219,.28)!important;color:#eaf4ff!important;height:44px!important}.top-control div[data-testid="stButton"] button{height:44px;width:44px;border-radius:50%!important;padding:0!important;border:1px solid rgba(70,103,219,.28)!important;background:rgba(8,13,31,.86)!important;color:#fff!important}.top-control div[data-testid="stSelectbox"] > div > div{border-radius:999px!important;background:rgba(8,13,31,.86)!important;border:1px solid rgba(70,103,219,.28)!important;min-height:44px!important;color:#fff!important}
.hero-card{height:227px;border:1px solid rgba(60,92,190,.26);border-radius:28px;position:relative;padding:30px 34px;overflow:hidden;background:linear-gradient(180deg,rgba(7,11,28,.98),rgba(6,9,25,.92));box-shadow:var(--shadow)}.hero-card:after{content:"";position:absolute;right:42px;top:-32px;width:470px;height:190px;border-radius:50%;transform:rotate(-8deg);background:radial-gradient(circle at 50% 50%,rgba(255,234,255,.96) 0 5%,rgba(255,132,250,.52) 6% 11%,transparent 12%),radial-gradient(ellipse at center,rgba(60,91,255,.54) 0 23%,transparent 24%),radial-gradient(ellipse at center,rgba(0,220,255,.50) 0 32%,transparent 33%),radial-gradient(ellipse at center,rgba(154,86,255,.36) 0 45%,transparent 46%);filter:drop-shadow(0 0 19px rgba(33,231,255,.48))}.hero-title{font-family:'Orbitron';font-weight:900;font-size:3.6rem;letter-spacing:.055em;line-height:1.02;margin-top:6px}.hero-sub{font-size:1.05rem;font-weight:700;color:#f6fbff;margin-top:9px}.hero-line{height:4px;width:184px;border-radius:999px;background:linear-gradient(90deg,#ff4bd1,#8958ff,transparent);margin-top:12px}.ai-brain{height:227px;border-radius:28px;border:1px solid rgba(86,98,255,.28);background:radial-gradient(circle at 62% 35%,rgba(255,51,225,.42),transparent 21%),radial-gradient(circle at 35% 60%,rgba(32,231,255,.30),transparent 24%),linear-gradient(180deg,rgba(13,11,42,.98),rgba(8,8,30,.94));position:relative;box-shadow:inset 0 0 42px rgba(150,79,255,.18)}.ai-brain:before{content:"AI";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:'Orbitron';font-size:4rem;font-weight:900;background:linear-gradient(90deg,#6ff5ff,#ff63df);-webkit-background-clip:text;color:transparent}.ai-brain:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:130px;height:130px;border-radius:50%;border:1px solid rgba(50,220,255,.38)}
.metric-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:14px 0}.metric-card{height:104px;border-radius:22px;border:1px solid rgba(69,105,231,.27);background:linear-gradient(180deg,rgba(11,15,36,.96),rgba(8,13,31,.82));padding:15px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}.metric-card:after{content:"";position:absolute;right:14px;bottom:14px;width:76px;height:28px;background:linear-gradient(90deg,transparent,#24e7ff,transparent);clip-path:polygon(0 70%,10% 70%,16% 42%,26% 88%,32% 20%,42% 66%,54% 52%,62% 62%,70% 12%,78% 86%,90% 54%,100% 58%,100% 100%,0 100%);opacity:.72}.metric-card.purple{background:linear-gradient(180deg,rgba(31,10,52,.95),rgba(12,10,32,.82))}.metric-card.orange{background:linear-gradient(180deg,rgba(55,18,8,.95),rgba(29,12,11,.82))}.metric-label{font-size:.91rem;color:#e2eaff}.metric-value{font-weight:900;font-size:1.82rem;margin-top:8px}.metric-sub{font-size:.85rem;color:#c7d5ee;margin-top:2px}.glass-card{border:1px solid rgba(69,105,231,.24);border-radius:24px;background:linear-gradient(180deg,rgba(6,11,29,.96),rgba(6,10,24,.86));box-shadow:var(--shadow);overflow:hidden}.card-head{font-family:'Orbitron';font-weight:900;font-size:1.05rem;padding:15px 18px 4px}.card-sub{color:#7f90b1;font-size:.84rem;padding:0 18px 4px}.insight{display:flex;gap:14px;padding:16px;border-bottom:1px solid rgba(69,105,231,.16)}.ins-icon{width:40px;height:40px;border-radius:13px;display:flex;align-items:center;justify-content:center}.ins-text{font-weight:800;line-height:1.38;font-size:.91rem}.timeline{display:flex;align-items:center;gap:10px;padding:12px 16px}.timeline-dot{width:10px;height:10px;background:#20e7ff;border-radius:50%;box-shadow:0 0 10px #20e7ff}.timeline-time{color:#28f6ff;font-weight:800;min-width:47px}.success{margin-left:auto;color:#22ffad;font-weight:800}.prompt-control div[data-testid="stTextInput"] input{border-radius:999px!important;background:rgba(10,12,31,.96)!important;border:1px solid rgba(130,75,255,.35)!important;height:60px!important;color:#fff!important;font-size:1.05rem!important}.prompt-control div[data-testid="stButton"] button{height:60px;border-radius:999px!important;border:1px solid rgba(130,75,255,.35)!important;background:linear-gradient(90deg,rgba(85,40,200,.55),rgba(8,13,31,.86))!important;color:#fff!important;font-weight:900!important}.api-warning{padding:18px;border:1px solid rgba(255,107,122,.35);border-radius:20px;background:rgba(255,107,122,.08);color:#ffd6dc;font-weight:700;margin:16px 0}.small-note{color:#93a7ca;font-size:.84rem}div[data-testid="stPlotlyChart"]>div{border-radius:20px;overflow:hidden}@media(max-width:1300px){.metric-row{grid-template-columns:repeat(2,1fr)}.hero-card:after{display:none}}
</style>
<div class="cosmos-grid"></div>
""",
    unsafe_allow_html=True,
)

# ---------- state ----------
MENU = [
    ("SIGNAL GALAXY", "🪐"),
    ("ASSET PULSE", "📊"),
    ("STRATEGY FORGE", "⚔️"),
    ("PORTFOLIO MAP", "🧭"),
    ("SCENARIO LAB", "🧪"),
    ("AGENT TIMELINE", "🕒"),
    ("LIVE API CONSOLE", "📡"),
    ("MISSION REPORTS", "🧾"),
]
if "section" not in st.session_state:
    st.session_state.section = "SIGNAL GALAXY"
if "right_panel" not in st.session_state:
    st.session_state.right_panel = "AI INSIGHTS"
if "ask_log" not in st.session_state:
    st.session_state.ask_log = []

# ---------- data ----------
assets = ASSETS
pulses, health = build_pulses(assets)
df = pulses_frame(pulses)
capital = float(os.getenv("DEFAULT_CAPITAL", 10000))
base_thesis = "ETF flows strengthen while on-chain liquidity rotates into high quality majors."
has_live = not df.empty
if has_live:
    df = df.sort_values("command_score", ascending=False).reset_index(drop=True)
    plan = generate_mission(base_thesis, pulses, capital, "Balanced")
else:
    plan = None


def fmt_price(v: float | None) -> str:
    if v is None:
        return "N/A"
    if v >= 1000:
        return f"${v:,.0f}"
    if v >= 10:
        return f"${v:,.2f}"
    return f"${v:,.4f}"


def metric(label: str, value: str, sub: str, cls: str = "") -> None:
    st.markdown(
        f"<div class='metric-card {cls}'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def orbit_chart(data: pd.DataFrame):
    fig = go.Figure()
    theta = [i * 2 * math.pi / 500 for i in range(501)]
    for r in [.52, .9, 1.28, 1.68, 2.08, 2.48, 2.84]:
        fig.add_trace(go.Scatter(x=[r * math.cos(t) for t in theta], y=[r * math.sin(t) for t in theta], mode="lines", line=dict(color="rgba(83,119,255,.25)", width=1), hoverinfo="skip", showlegend=False))
    palette = ["#ff8a1e", "#46c8ff", "#23e7ff", "#37bfff", "#2d95ff", "#c34dff", "#a94dff", "#34ffaa", "#ffcc33", "#ff5ca8"]
    n = len(data)
    for idx, row in enumerate(data.itertuples()):
        angle = idx * 2 * math.pi / max(1, n)
        radius = 0.65 + (100 - float(row.command_score)) / 100 * 2.05
        if idx == 0:
            radius = 0.0
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        size = 22 + max(0, float(row.command_score)) * .28
        sym = str(row.asset)
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", marker=dict(size=size, color=palette[idx % len(palette)], line=dict(color="rgba(255,255,255,.5)", width=1.5)), text=[sym if idx == 0 else ""], textposition="middle center", textfont=dict(color="white", size=18 if idx == 0 else 10), hovertemplate=f"{sym}<br>Price: {fmt_price(float(row.price))}<br>Score: {float(row.command_score):.1f}<br>Source: {row.source}<extra></extra>", showlegend=False))
        if idx != 0:
            fig.add_annotation(x=x, y=y + .34, text=f"{sym}<br>{float(row.command_score):.1f}", showarrow=False, font=dict(color="#eaf4ff", size=11))
    fig.update_layout(height=430, margin=dict(l=5, r=5, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False, range=[-3.05, 3.05]), yaxis=dict(visible=False, range=[-2.35, 2.35], scaleanchor="x", scaleratio=1))
    return fig


def heatmap_chart(data: pd.DataFrame):
    matrix = data.set_index("asset")[["momentum", "liquidity", "volatility", "risk", "flow", "command_score"]]
    heat = go.Figure(data=go.Heatmap(z=matrix.values, x=["Momentum", "Liquidity", "Volatility", "Risk", "Flow", "Score"], y=matrix.index, colorscale=[(0, "#2a25ff"), (.22, "#2078ff"), (.43, "#1bd5a8"), (.65, "#d9df36"), (.83, "#ff8a22"), (1, "#ff2e17")], zmin=0, zmax=100, xgap=6, ygap=6, showscale=False, text=[[f"{v:.1f}" if j == 5 else "" for j, v in enumerate(row)] for row in matrix.values], texttemplate="%{text}", textfont={"color": "#fff", "size": 11}))
    heat.update_layout(height=430, margin=dict(l=0, r=0, t=2, b=33), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#eaf4ff")
    return heat


left, main = st.columns([1.05, 4.65], gap="large")

with left:
    live_count = sum(1 for h in health if h.ok)
    status_line = "All data sources operational" if live_count == len(health) else ("Partial live data" if live_count else "API connection required")
    status_class = "status-good" if live_count else "status-bad"
    st.markdown('<div class="left-rail">', unsafe_allow_html=True)
    st.markdown("""
    <div class="brand"><div class="logo-star"></div><div><div class="brand-name">NEBULA<span>COMMAND</span></div></div></div>
    <div class="orbit-box"><div class="orbit-center"></div></div><div class="side-kicker">MISSION CONTROL</div>
    """, unsafe_allow_html=True)
    for label, icon in MENU:
        if st.session_state.section == label:
            st.markdown(f"<div class='nav-active'>{icon}&nbsp;&nbsp; {label} &nbsp; <span style='float:right;color:#23ffac'>●</span></div>", unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.section = label
                st.rerun()
    st.markdown(f"<div class='status-panel'><div class='status-title'>SYSTEM STATUS</div><div class='{status_class}'>{status_line}</div><div class='small-note'>{live_count}/{len(health)} source checks passed</div><div class='ecg'></div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with main:
    top = df.iloc[0] if has_live else None
    st.markdown('<div class="top-control">', unsafe_allow_html=True)
    t1, t2, t3, t4, t5, t6, t7 = st.columns([1.05, 1.12, 1.12, 1.12, 2.55, .34, .34], gap="small")
    with t1:
        st.markdown('<div class="pill-top"><span class="dot"></span>Live Market</div>', unsafe_allow_html=True)
    for col, idx in [(t2, 0), (t3, 1), (t4, 2)]:
        with col:
            if has_live and idx < len(df):
                r = df.iloc[idx]
                st.markdown(f"<div class='pill-top ticker'>✦&nbsp; {r['asset']}&nbsp;&nbsp; {fmt_price(float(r['price']))}<span class='up'>score {float(r['command_score']):.1f}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='pill-top ticker'>No data</div>", unsafe_allow_html=True)
    with t5:
        search = st.text_input("Search assets, narratives, signals", placeholder="🔎  Search assets, narratives, signals...", label_visibility="collapsed", key="search_query")
    with t6:
        if st.button("💬", key="chat_btn", help="Open mission chat"):
            st.session_state.right_panel = "CHAT"
    with t7:
        if st.button("🔔", key="alert_btn", help="Open alerts"):
            st.session_state.right_panel = "ALERTS"
    p1, p2 = st.columns([.7, 1.1], gap="small")
    with p1:
        st.markdown('<div class="avatar"></div>', unsafe_allow_html=True)
    with p2:
        mode = st.selectbox("Commander mode", ["Alpha Mode", "Risk Mode", "Research Mode", "Execution Preview"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    hero, brain = st.columns([3.65, 1.15], gap="small")
    with hero:
        st.markdown("<div class='hero-card'><div class='hero-title'>NEBULA COMMAND</div><div class='hero-sub'>AI Mission Control for Crypto Strategy</div><div class='hero-line'></div></div>", unsafe_allow_html=True)
    with brain:
        st.markdown('<div class="ai-brain"></div>', unsafe_allow_html=True)

    if not has_live:
        st.markdown("<div class='api-warning'>No live market data could be loaded. Check SoDEX, SoSoValue, Binance, or CoinGecko connectivity in the API console below. The UI will not show fake prices or fake scores.</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([h.__dict__ for h in health]), use_container_width=True, hide_index=True)
        st.stop()

    if search:
        mask = df["asset"].str.contains(search.strip(), case=False, na=False) | df["source"].str.contains(search.strip(), case=False, na=False)
        view_df = df[mask].copy()
        if view_df.empty:
            st.warning(f"No live asset matched: {search}")
            view_df = df.copy()
    else:
        view_df = df.copy()

    plan = generate_mission(base_thesis, pulses, capital, "Balanced")
    live_count = sum(1 for h in health if h.ok)
    top = view_df.iloc[0]
    st.markdown('<div class="metric-row">', unsafe_allow_html=True)
    mc = st.columns(5, gap="small")
    with mc[0]:
        metric("Mission Status", plan.stance, mode)
    with mc[1]:
        metric("Top Signal", str(top["asset"]), f"Score {float(top['command_score']):.1f}")
    with mc[2]:
        metric("Live Sources", f"{live_count} / {len(health)}", "Primary + fallback checks")
    with mc[3]:
        metric("Paper Capital", f"${capital:,.0f}", "paper only", "orange")
    with mc[4]:
        metric("Open Positions", "0", "No live execution", "purple")
    st.markdown('</div>', unsafe_allow_html=True)

    section = st.session_state.section

    if section == "SIGNAL GALAXY":
        a, b, c = st.columns([2.08, 1.72, 1.02], gap="small")
        with a:
            st.markdown('<div class="glass-card"><div class="card-head">SIGNAL GALAXY</div><div class="card-sub">Live command score orbit map</div>', unsafe_allow_html=True)
            st.plotly_chart(orbit_chart(view_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="glass-card"><div class="card-head">ASSET PULSE MATRIX</div><div class="card-sub">Live multi-dimensional market pulse</div>', unsafe_allow_html=True)
            st.plotly_chart(heatmap_chart(view_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c:
            st.markdown('<div class="glass-card"><div class="card-head">AI INSIGHTS</div>', unsafe_allow_html=True)
            insights = [("⬆", f"{top['asset']} has highest live score: {float(top['command_score']):.1f}.", "rgba(24,255,172,.15)"), ("📡", f"Sources passed {live_count}/{len(health)} checks.", "rgba(0,137,255,.15)"), ("🛡️", f"Average risk index: {view_df['risk'].mean():.1f}/100.", "rgba(255,174,30,.15)"), ("🔎", f"Best source: {top['source']}.", "rgba(180,72,255,.15)")]
            for icon, txt, bg in insights:
                st.markdown(f"<div class='insight'><div class='ins-icon' style='background:{bg}'>{icon}</div><div class='ins-text'>{txt}</div></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif section == "ASSET PULSE":
        st.markdown('<div class="glass-card"><div class="card-head">ASSET PULSE MATRIX</div><div class="card-sub">Sortable live asset intelligence table</div>', unsafe_allow_html=True)
        st.plotly_chart(heatmap_chart(view_df), use_container_width=True)
        st.dataframe(view_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    elif section == "STRATEGY FORGE":
        st.markdown('<div class="glass-card"><div class="card-head">STRATEGY FORGE</div><div class="card-sub">Build a live-data mission plan</div></div>', unsafe_allow_html=True)
        thesis = st.text_area("Mission thesis", value=base_thesis, height=130)
        risk_mode = st.segmented_control("Risk doctrine", ["Stealth", "Balanced", "Aggressive"], default="Balanced")
        cap = st.number_input("Paper capital USD", min_value=100.0, value=capital, step=500.0)
        forged = generate_mission(thesis, pulses, cap, risk_mode)
        st.markdown(f"### Mission stance: `{forged.stance}`")
        for line in forged.reasoning:
            st.write("- " + line)
        st.dataframe(pd.DataFrame(forged.orders), use_container_width=True, hide_index=True)

    elif section == "PORTFOLIO MAP":
        st.markdown('<div class="glass-card"><div class="card-head">PORTFOLIO BATTLE MAP</div><div class="card-sub">Paper allocation derived from live risk gates</div>', unsafe_allow_html=True)
        if plan.orders:
            battle = pd.DataFrame(plan.orders).rename(columns={"notional_usd": "weight"})
            battle["weight"] = battle["weight"].astype(float)
            tree = px.treemap(battle, path=[px.Constant("Paper Portfolio"), "asset"], values="weight", color="risk_gate", color_discrete_map={"PASS": "#23ffac", "REVIEW": "#ff8a1e"})
            tree.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", root_color="rgba(0,0,0,0)", marker_line_color="rgba(255,255,255,.08)")
            tree.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(tree, use_container_width=True)
        else:
            st.info("No paper intent generated from live risk gates.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif section == "SCENARIO LAB":
        scenario = st.selectbox("Scenario", ["ETF inflow surge", "Liquidity drain", "BTC volatility shock", "Alt rotation", "Market calm"])
        shock_df = scenario_matrix(pulses, scenario, capital)
        fig2 = px.bar(shock_df, x="asset", y="adjusted_score", color="paper_exposure_usd", range_y=[0, 100], color_continuous_scale="Turbo")
        fig2.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(shock_df, use_container_width=True, hide_index=True)

    elif section == "AGENT TIMELINE":
        st.markdown('<div class="glass-card"><div class="card-head">AGENT TIMELINE</div>', unsafe_allow_html=True)
        timeline = [(datetime.now(timezone.utc).strftime("%H:%M"), "Live sources scanned", f"{live_count}/{len(health)}"), (datetime.now(timezone.utc).strftime("%H:%M"), "Fallback data checked", "Done"), (datetime.now(timezone.utc).strftime("%H:%M"), f"Signals scanned ({len(view_df)} assets)", ""), (datetime.now(timezone.utc).strftime("%H:%M"), "Score updated", ""), (datetime.now(timezone.utc).strftime("%H:%M"), "Mission report ready", "")]
        for t, txt, s in timeline:
            st.markdown(f"<div class='timeline'><div class='timeline-dot'></div><div class='timeline-time'>{t}</div><div>{txt}</div>{'<div class=success>✓ '+s+'</div>' if s else ''}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    elif section == "LIVE API CONSOLE":
        st.markdown('<div class="glass-card"><div class="card-head">LIVE API CONSOLE</div><div class="card-sub">Source health: SoDEX / SoSoValue / Binance / CoinGecko</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([h.__dict__ for h in health]), use_container_width=True, hide_index=True)
        st.caption("Data priority: SoDEX/SoSoValue first, then Binance public market data, then CoinGecko public market data. No fake price fallback is used.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif section == "MISSION REPORTS":
        report = export_markdown(plan)
        st.download_button("Download mission report", report, file_name="nebula-command-report.md", mime="text/markdown")
        st.markdown(report)

    # right/top action panels
    if st.session_state.right_panel == "CHAT":
        with st.expander("Mission Chat", expanded=True):
            st.write("Ask Nebula is connected below. Use it to query the current live signal set.")
            for item in st.session_state.ask_log[-5:]:
                st.write("- " + item)
    elif st.session_state.right_panel == "ALERTS":
        with st.expander("Alerts", expanded=True):
            st.write(f"- {live_count}/{len(health)} source checks are passing.")
            st.write(f"- Current top signal: {top['asset']} score {float(top['command_score']):.1f}.")
            st.write("- Live trading remains locked; paper execution only.")

    st.markdown('<div class="prompt-control">', unsafe_allow_html=True)
    q1, q2, q3, q4, q5 = st.columns([3.4, .55, .55, .55, .55], gap="small")
    with q1:
        ask = st.text_input("Ask Nebula", placeholder="💬  Ask Nebula about live signals, risk, sources, or portfolio map...", label_visibility="collapsed", key="ask_nebula")
    with q2:
        if st.button("🎙️", key="mic_btn", help="Voice placeholder"):
            st.toast("Voice input placeholder: type your mission question for now.")
    with q3:
        if st.button("✈️", key="send_btn", help="Send mission question"):
            if ask.strip():
                answer = f"Nebula readout: {top['asset']} leads with score {float(top['command_score']):.1f}; average risk is {view_df['risk'].mean():.1f}."
                st.session_state.ask_log.append(f"Q: {ask} — A: {answer}")
                st.session_state.right_panel = "CHAT"
                st.rerun()
            else:
                st.toast("Type a mission question first.")
    with q4:
        if st.button("⌘", key="shortcut_btn", help="Open command shortcuts"):
            st.session_state.right_panel = "CHAT"
            st.toast("Shortcuts: Signal, Risk, API, Report, Scenario.")
    with q5:
        if st.button("📄", key="quick_report", help="Open reports"):
            st.session_state.section = "MISSION REPORTS"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
