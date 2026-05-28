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
*{box-sizing:border-box} html,body,[class*="css"]{font-family:'Inter',sans-serif}[data-testid="stSidebar"],[data-testid="collapsedControl"],header,footer,#MainMenu{display:none!important}
.stApp{background:radial-gradient(circle at 13% 15%,rgba(38,92,255,.16),transparent 18%),radial-gradient(circle at 71% 7%,rgba(138,67,255,.16),transparent 18%),radial-gradient(circle at 86% 79%,rgba(0,218,255,.08),transparent 18%),linear-gradient(180deg,#030611 0%,#040816 100%);color:var(--text)}
.block-container{max-width:1680px;padding:.65rem .8rem 1rem!important}.cosmos-grid{position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,110,190,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(79,110,190,.08) 1px,transparent 1px);background-size:38px 38px;mask-image:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,0) 65%)}
.left-rail{min-height:1030px;padding:21px 18px;background:linear-gradient(180deg,rgba(5,9,24,.98),rgba(5,8,20,.96));border:1px solid rgba(62,93,190,.32);border-radius:0 30px 30px 0;box-shadow:var(--shadow)}
.brand{display:flex;align-items:center;gap:13px;margin-bottom:20px}.logo-star{width:48px;height:48px;border-radius:50%;position:relative;background:radial-gradient(circle,#fff 0 7%,#7beaff 8% 10%,#7b37ff 21%,rgba(21,10,58,.95) 58%,rgba(5,7,22,1) 77%);box-shadow:0 0 28px rgba(40,231,255,.38),0 0 36px rgba(158,72,255,.38)}.logo-star:before,.logo-star:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:linear-gradient(90deg,transparent,#fff,transparent)}.logo-star:before{width:46px;height:3px}.logo-star:after{width:3px;height:46px}.brand-name{font-family:'Orbitron',sans-serif;font-size:1.82rem;font-weight:900;letter-spacing:.08em;line-height:.96}.brand-name span{display:block;color:#18e7ff;font-size:.96rem;letter-spacing:.32em;margin-top:4px}
.orbit-box{height:210px;border-radius:28px;margin:13px 0 18px;position:relative;background:radial-gradient(circle at 50% 50%,rgba(123,72,255,.68) 0 11%,rgba(55,29,168,.55) 12% 18%,transparent 19%),radial-gradient(ellipse at center,rgba(7,17,47,.95),rgba(4,8,22,.98));border:1px solid rgba(59,115,255,.27);box-shadow:inset 0 0 44px rgba(32,231,255,.12);overflow:hidden}.orbit-box:before,.orbit-box:after{content:"";position:absolute;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:1px solid rgba(44,229,255,.30)}.orbit-box:before{width:178px;height:86px}.orbit-box:after{width:212px;height:128px;border-color:rgba(151,86,255,.28)}.orbit-center{position:absolute;width:66px;height:66px;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:2px solid rgba(224,250,255,.85);box-shadow:0 0 28px rgba(151,86,255,.55)}.orbit-center:before{content:"✦";display:flex;align-items:center;justify-content:center;height:100%;font-size:34px}.side-kicker{text-align:center;color:#be6fff;font-family:'Orbitron';font-weight:800;margin:2px 0 15px;letter-spacing:.06em}
.nav-current{border:1px solid rgba(33,231,255,.44);background:linear-gradient(90deg,rgba(117,45,255,.46),rgba(4,23,55,.78));box-shadow:0 0 24px rgba(130,68,255,.15);border-radius:22px;padding:14px 16px;margin-bottom:9px;font-weight:900}.nav-dot{float:right;width:8px;height:8px;margin-top:7px;background:#20ffad;border-radius:50%;box-shadow:0 0 11px #20ffad}
.stButton>button{width:100%;height:58px;text-align:left!important;border:1px solid rgba(63,92,184,.25)!important;border-radius:22px!important;padding:0 16px!important;margin-bottom:5px!important;background:linear-gradient(180deg,rgba(7,12,31,.96),rgba(7,12,31,.79))!important;color:#f5fbff!important;font-weight:900!important;letter-spacing:.02em!important;box-shadow:none!important}.stButton>button:hover{border-color:rgba(33,231,255,.55)!important;background:linear-gradient(90deg,rgba(117,45,255,.38),rgba(4,23,55,.78))!important;color:#fff!important}
.status-panel{margin-top:18px;border:1px solid rgba(63,92,184,.24);border-radius:24px;padding:17px;background:linear-gradient(180deg,rgba(7,12,31,.95),rgba(8,13,31,.74))}.status-title{font-weight:900;letter-spacing:.03em}.status-good{color:#22ffad;font-size:.9rem;font-weight:700;margin-top:10px}.status-bad{color:#ff6b7a;font-size:.9rem;font-weight:700;margin-top:10px}.ecg{height:42px;position:relative;margin-top:7px}.ecg:before{content:"";position:absolute;left:4px;right:4px;top:21px;height:2px;background:linear-gradient(90deg,transparent,#894dff,#24e7ff,#894dff,transparent);clip-path:polygon(0 50%,10% 50%,14% 18%,20% 82%,25% 48%,34% 50%,45% 50%,50% 8%,58% 90%,65% 50%,100% 50%)}
.top-bar{height:56px;display:flex;align-items:center;justify-content:space-between;margin-bottom:13px;gap:12px}.top-left,.top-right{display:flex;align-items:center;gap:10px}.pill-top{border:1px solid rgba(70,103,219,.28);border-radius:999px;background:linear-gradient(180deg,rgba(8,13,31,.95),rgba(8,13,31,.82));height:44px;display:flex;align-items:center;padding:0 16px;box-shadow:var(--shadow);font-weight:800}.pill-top.live{min-width:164px}.dot{width:10px;height:10px;border-radius:50%;background:#20ffad;box-shadow:0 0 10px #20ffad;margin-right:10px}.ticker{color:#e7f2ff}.up{color:#20ffad;margin-left:8px}.search{min-width:360px;color:#8293b5;font-weight:600}.circle-top{width:44px;height:44px;border-radius:50%;border:1px solid rgba(70,103,219,.28);display:flex;align-items:center;justify-content:center;background:rgba(8,13,31,.86);position:relative}.badge{position:absolute;right:-3px;top:-5px;background:#ff2c5f;color:white;border-radius:999px;font-size:.68rem;padding:1px 5px}.avatar{width:46px;height:46px;border-radius:50%;background:radial-gradient(circle at 34% 28%,#b7f4ff,#7d4dff 53%,#111333 74%);border:2px solid rgba(222,242,255,.75);box-shadow:0 0 28px rgba(171,88,255,.45)}.profile{height:54px;padding:0 14px 0 7px;gap:12px}.profile-name{font-weight:900}.profile-sub{color:#93a7ca;font-size:.8rem}
.hero-card{height:227px;border:1px solid rgba(60,92,190,.26);border-radius:28px;position:relative;padding:30px 34px;overflow:hidden;background:linear-gradient(180deg,rgba(7,11,28,.98),rgba(6,9,25,.92));box-shadow:var(--shadow)}.hero-card:after{content:"";position:absolute;right:42px;top:-32px;width:470px;height:190px;border-radius:50%;transform:rotate(-8deg);background:radial-gradient(circle at 50% 50%,rgba(255,234,255,.96) 0 5%,rgba(255,132,250,.52) 6% 11%,transparent 12%),radial-gradient(ellipse at center,rgba(60,91,255,.54) 0 23%,transparent 24%),radial-gradient(ellipse at center,rgba(0,220,255,.50) 0 32%,transparent 33%),radial-gradient(ellipse at center,rgba(154,86,255,.36) 0 45%,transparent 46%);filter:drop-shadow(0 0 19px rgba(33,231,255,.48))}.hero-title{font-family:'Orbitron';font-weight:900;font-size:3.6rem;letter-spacing:.055em;line-height:1.02;margin-top:6px}.hero-sub{font-size:1.05rem;font-weight:700;color:#f6fbff;margin-top:9px}.hero-line{height:4px;width:184px;border-radius:999px;background:linear-gradient(90deg,#ff4bd1,#8958ff,transparent);margin-top:12px}.ai-brain{height:227px;border-radius:28px;border:1px solid rgba(86,98,255,.28);background:radial-gradient(circle at 62% 35%,rgba(255,51,225,.42),transparent 21%),radial-gradient(circle at 35% 60%,rgba(32,231,255,.30),transparent 24%),linear-gradient(180deg,rgba(13,11,42,.98),rgba(8,8,30,.94));position:relative;box-shadow:inset 0 0 42px rgba(150,79,255,.18)}.ai-brain:before{content:"AI";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:'Orbitron';font-size:4rem;font-weight:900;background:linear-gradient(90deg,#6ff5ff,#ff63df);-webkit-background-clip:text;color:transparent}.ai-brain:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:130px;height:130px;border-radius:50%;border:1px solid rgba(50,220,255,.38)}
.metric-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:14px 0}.metric-card{height:104px;border-radius:22px;border:1px solid rgba(69,105,231,.27);background:linear-gradient(180deg,rgba(11,15,36,.96),rgba(8,13,31,.82));padding:15px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}.metric-card:after{content:"";position:absolute;right:14px;bottom:14px;width:76px;height:28px;background:linear-gradient(90deg,transparent,#24e7ff,transparent);clip-path:polygon(0 70%,10% 70%,16% 42%,26% 88%,32% 20%,42% 66%,54% 52%,62% 62%,70% 12%,78% 86%,90% 54%,100% 58%,100% 100%,0 100%);opacity:.72}.metric-card.purple{background:linear-gradient(180deg,rgba(31,10,52,.95),rgba(12,10,32,.82))}.metric-card.orange{background:linear-gradient(180deg,rgba(55,18,8,.95),rgba(29,12,11,.82))}.metric-label{font-size:.91rem;color:#e2eaff}.metric-value{font-weight:900;font-size:1.82rem;margin-top:8px}.metric-sub{font-size:.85rem;color:#c7d5ee;margin-top:2px}
.glass-card{border:1px solid rgba(69,105,231,.24);border-radius:24px;background:linear-gradient(180deg,rgba(6,11,29,.96),rgba(6,10,24,.86));box-shadow:var(--shadow);overflow:hidden;padding-bottom:10px;margin-bottom:14px}.card-head{font-family:'Orbitron';font-weight:900;font-size:1.05rem;padding:15px 18px 4px}.card-sub{color:#7f90b1;font-size:.84rem;padding:0 18px 4px}.insight{display:flex;gap:13px;align-items:flex-start;border-bottom:1px solid rgba(69,105,231,.15);padding:13px 16px}.ins-icon{width:41px;height:41px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:19px}.ins-text{font-weight:800;line-height:1.35}.timeline{display:flex;align-items:center;gap:12px;padding:11px 14px}.timeline-dot{width:10px;height:10px;border-radius:50%;background:#21e7ff;box-shadow:0 0 10px #21e7ff}.timeline-time{color:#34e8ff;font-weight:800;min-width:52px}.success{margin-left:auto;color:#21ffad;font-weight:800}.prompt-bar{height:74px;border-radius:999px;border:1px solid rgba(91,113,255,.28);background:linear-gradient(180deg,rgba(8,13,31,.96),rgba(8,13,31,.78));display:flex;align-items:center;justify-content:space-between;padding:0 22px;margin-top:13px;box-shadow:var(--shadow)}.ask{font-size:1.2rem;color:#98a9ca;display:flex;gap:12px}.mic{width:78px;height:78px;border-radius:50%;margin-top:-30px;background:radial-gradient(circle,#f4d9ff,#8d52ff 45%,#190d45 76%);display:flex;align-items:center;justify-content:center;font-size:32px;border:2px solid rgba(231,241,255,.65);box-shadow:0 0 34px rgba(152,84,255,.52)}.prompt-icons{font-size:22px;color:#dae3ff;letter-spacing:.35rem}.api-warning{border:1px solid rgba(255,120,120,.35);background:rgba(70,10,20,.45);border-radius:22px;padding:18px;margin:16px 0;color:#ffb8c3;font-weight:800}.page-title{font-family:'Orbitron';font-size:1.9rem;font-weight:900;margin:10px 0 14px}.page-panel{border:1px solid rgba(69,105,231,.24);border-radius:24px;background:linear-gradient(180deg,rgba(6,11,29,.96),rgba(6,10,24,.86));box-shadow:var(--shadow);padding:18px;margin-bottom:14px}
div[data-testid="stPlotlyChart"]>div{border-radius:22px;overflow:hidden}.stDataFrame{border-radius:18px;overflow:hidden}@media(max-width:1300px){.metric-row{grid-template-columns:repeat(2,1fr)}.hero-card:after{display:none}}
</style><div class="cosmos-grid"></div>
""",
    unsafe_allow_html=True,
)

PAGES = [
    ("🪐", "SIGNAL GALAXY"),
    ("📊", "ASSET PULSE"),
    ("⚔️", "STRATEGY FORGE"),
    ("🧭", "PORTFOLIO MAP"),
    ("🧪", "SCENARIO LAB"),
    ("🕒", "AGENT TIMELINE"),
    ("📡", "LIVE API CONSOLE"),
    ("🧾", "MISSION REPORTS"),
]
if "page" not in st.session_state:
    st.session_state.page = "SIGNAL GALAXY"

assets = ASSETS
pulses, health = build_pulses(assets)
df = pulses_frame(pulses)
if not df.empty:
    df = df.sort_values("command_score", ascending=False).reset_index(drop=True)
capital = float(os.getenv("DEFAULT_CAPITAL", 10000))
thesis_default = "ETF flows strengthen while on-chain liquidity rotates into high quality majors."
plan = generate_mission(thesis_default, pulses, capital, "Balanced") if pulses else None
has_live = not df.empty


def fmt_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 10:
        return f"${value:,.2f}"
    return f"${value:,.4f}"


def metric(label: str, value: str, sub: str, cls: str = "") -> None:
    st.markdown(f"<div class='metric-card {cls}'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)


def render_topbar() -> None:
    tickers = []
    if has_live:
        for sym in ["BTC", "ETH", "SOL"]:
            row = df[df["asset"] == sym]
            if not row.empty:
                r = row.iloc[0]
                tickers.append(f"<div class='pill-top ticker'>✦&nbsp; {sym}<br>{fmt_price(float(r['price']))} <span class='up'>{float(r['momentum'])-50:+.2f}%</span></div>")
    if not tickers:
        tickers = ["<div class='pill-top ticker'>No live market data</div>"]
    st.markdown(
        "<div class='top-bar'><div class='top-left'><div class='pill-top live'><span class='dot'></span>Live Market</div>"
        + "".join(tickers)
        + "</div><div class='top-right'><div class='pill-top search'>🔎&nbsp; Search assets, narratives, signals...</div><div class='circle-top'>💬<span class='badge'>2</span></div><div class='circle-top'>🔔<span class='badge'>1</span></div><div class='pill-top profile'><div class='avatar'></div><div><div class='profile-name'>Commander</div><div class='profile-sub'>Alpha Mode</div></div><div>⌄</div></div></div></div>",
        unsafe_allow_html=True,
    )


def render_shell_header() -> None:
    hero, brain = st.columns([3.65, 1.15], gap="small")
    with hero:
        st.markdown("<div class='hero-card'><div class='hero-title'>NEBULA COMMAND</div><div class='hero-sub'>AI Mission Control for Crypto Strategy</div><div class='hero-line'></div></div>", unsafe_allow_html=True)
    with brain:
        st.markdown('<div class="ai-brain"></div>', unsafe_allow_html=True)


def render_metrics() -> None:
    live_count = sum(1 for h in health if h.ok)
    if has_live:
        top = df.iloc[0]
        vals = [
            ("Mission Status", plan.stance if plan else "N/A", "Live data loaded", ""),
            ("Top Signal", str(top["asset"]), f"Score {float(top['command_score']):.1f}", ""),
            ("Live Sources", f"{live_count} / {len(health)}", "Primary + fallback checks", ""),
            ("Paper Capital", f"${capital:,.0f}", "paper only", "orange"),
            ("Open Positions", "0", "No live execution", "purple"),
        ]
    else:
        vals = [("Mission Status", "OFFLINE", "No live data", ""), ("Top Signal", "N/A", "API unavailable", ""), ("Live Sources", f"0 / {len(health)}", "Check console", ""), ("Paper Capital", f"${capital:,.0f}", "paper only", "orange"), ("Open Positions", "0", "No live execution", "purple")]
    cols = st.columns(5, gap="small")
    for col, (label, value, sub, cls) in zip(cols, vals):
        with col:
            metric(label, value, sub, cls)


def signal_galaxy_chart(height: int = 360) -> go.Figure:
    fig = go.Figure()
    theta = [i * 2 * math.pi / 500 for i in range(501)]
    for r in [.52, .9, 1.28, 1.68, 2.08, 2.48, 2.84]:
        fig.add_trace(go.Scatter(x=[r * math.cos(t) for t in theta], y=[r * math.sin(t) for t in theta], mode="lines", line=dict(color="rgba(83,119,255,.25)", width=1), hoverinfo="skip", showlegend=False))
    palette = ["#ff8a1e", "#46c8ff", "#23e7ff", "#37bfff", "#2d95ff", "#c34dff", "#a94dff", "#34ffaa", "#ffcc33", "#ff5ca8"]
    n = len(df)
    for idx, row in enumerate(df.itertuples()):
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
    fig.update_layout(height=height, margin=dict(l=5, r=5, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False, range=[-3.05, 3.05]), yaxis=dict(visible=False, range=[-2.35, 2.35], scaleanchor="x", scaleratio=1))
    return fig


def pulse_heatmap(height: int = 360) -> go.Figure:
    matrix = df.set_index("asset")[["momentum", "liquidity", "volatility", "risk", "flow", "command_score"]]
    heat = go.Figure(data=go.Heatmap(z=matrix.values, x=["Momentum", "Liquidity", "Volatility", "Risk", "Flow", "Score"], y=matrix.index, colorscale=[(0, "#2a25ff"), (.22, "#2078ff"), (.43, "#1bd5a8"), (.65, "#d9df36"), (.83, "#ff8a22"), (1, "#ff2e17")], zmin=0, zmax=100, xgap=6, ygap=6, showscale=False, text=[[f"{v:.1f}" if j == 5 else "" for j, v in enumerate(row)] for row in matrix.values], texttemplate="%{text}", textfont={"color": "#fff", "size": 11}))
    heat.update_layout(height=height, margin=dict(l=0, r=0, t=2, b=33), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#eaf4ff")
    return heat


def render_offline_warning() -> None:
    if not has_live:
        st.markdown("<div class='api-warning'>No live market data could be loaded. Check SoDEX, SoSoValue, Binance, or CoinGecko connectivity in the API console. The UI will not show fake prices or fake scores.</div>", unsafe_allow_html=True)


def render_overview() -> None:
    render_shell_header()
    render_offline_warning()
    if not has_live:
        return
    render_metrics()
    a, b, c = st.columns([2.08, 1.72, 1.02], gap="small")
    with a:
        st.markdown('<div class="glass-card"><div class="card-head">SIGNAL GALAXY</div><div class="card-sub">Live command score orbit map</div>', unsafe_allow_html=True)
        st.plotly_chart(signal_galaxy_chart(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="glass-card"><div class="card-head">ASSET PULSE MATRIX</div><div class="card-sub">Live multi-dimensional market pulse</div>', unsafe_allow_html=True)
        st.plotly_chart(pulse_heatmap(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c:
        render_insights()
    render_lower_modules()
    st.markdown('<div class="prompt-bar"><div class="ask">💬 <span>Ask Nebula...</span></div><div class="mic">🎙️</div><div class="prompt-icons">🎤 ✈️ ⌘</div></div>', unsafe_allow_html=True)


def render_insights() -> None:
    st.markdown('<div class="glass-card"><div class="card-head">AI INSIGHTS</div>', unsafe_allow_html=True)
    if not has_live:
        st.markdown('<div class="insight"><div class="ins-icon">📡</div><div class="ins-text">No live market data. Open API Console.</div></div>', unsafe_allow_html=True)
    else:
        top = df.iloc[0]
        live_count = sum(1 for h in health if h.ok)
        insights = [
            ("⬆", f"{top['asset']} has the highest live command score: {float(top['command_score']):.1f}.", "rgba(24,255,172,.15)"),
            ("📡", f"Primary/fallback sources passed {live_count}/{len(health)} checks.", "rgba(0,137,255,.15)"),
            ("🛡️", f"Average risk index: {df['risk'].mean():.1f}/100.", "rgba(255,174,30,.15)"),
            ("🔎", f"Best live source: {top['source']} for {top['asset']}.", "rgba(180,72,255,.15)"),
        ]
        for icon, txt, bg in insights:
            st.markdown(f"<div class='insight'><div class='ins-icon' style='background:{bg}'>{icon}</div><div class='ins-text'>{txt}</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_lower_modules() -> None:
    l1, l2, l3, l4 = st.columns([1.38, 1.16, 1.05, 1.02], gap="small")
    with l1:
        st.markdown('<div class="glass-card"><div class="card-head">STRATEGY WAR ROOM</div><div class="card-sub">Global signal zones from live asset scores</div>', unsafe_allow_html=True)
        world = go.Figure(go.Scattergeo(lon=[-74, -46, -.1, 24, 77, 139, 151][:len(df)], lat=[40.7, -23.5, 51.5, -28, 28.6, 35.6, -33.8][:len(df)], text=df.head(7)["asset"], mode="markers+text", marker=dict(size=(df.head(7)["command_score"] / 4 + 8), color=df.head(7)["command_score"], colorscale="Turbo", line=dict(width=1, color="white"), opacity=.95, showscale=False), hovertemplate="%{text}<extra></extra>", showlegend=False))
        world.update_geos(bgcolor="rgba(0,0,0,0)", showcountries=False, showcoastlines=False, showland=True, landcolor="rgba(45,80,170,.18)", showocean=True, oceancolor="rgba(0,0,0,0)", projection_type="equirectangular")
        world.update_layout(height=265, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(world, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with l2:
        render_scenario_chart(compact=True)
    with l3:
        render_portfolio_map(compact=True)
    with l4:
        render_agent_timeline(compact=True)


def render_scenario_chart(compact: bool = False) -> None:
    st.markdown('<div class="glass-card"><div class="card-head">SCENARIO FORGE</div>', unsafe_allow_html=True)
    if has_live:
        scenario = "ETF inflow surge" if compact else st.selectbox("Scenario", ["ETF inflow surge", "Liquidity drain", "BTC volatility shock", "Alt rotation", "Market calm"])
        shock_df = scenario_matrix(pulses, scenario, capital)
        fig2 = px.bar(shock_df, x="asset", y="adjusted_score", color="paper_exposure_usd", range_y=[0, 100], color_continuous_scale="Turbo")
        fig2.update_layout(height=265 if compact else 520, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", coloraxis_showscale=not compact)
        st.plotly_chart(fig2, use_container_width=True)
        if not compact:
            st.dataframe(shock_df, use_container_width=True, hide_index=True)
    else:
        st.info("No live scenario data available.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_portfolio_map(compact: bool = False) -> None:
    st.markdown('<div class="glass-card"><div class="card-head">PORTFOLIO BATTLE MAP</div>', unsafe_allow_html=True)
    if plan and plan.orders:
        battle = pd.DataFrame(plan.orders).rename(columns={"notional_usd": "weight"})
        battle["weight"] = battle["weight"].astype(float)
        tree = px.treemap(battle, path=[px.Constant("Paper Portfolio"), "asset"], values="weight", color="risk_gate", color_discrete_map={"PASS": "#23ffac", "REVIEW": "#ff8a1e"})
        tree.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", root_color="rgba(0,0,0,0)", marker_line_color="rgba(255,255,255,.08)")
        tree.update_layout(height=265 if compact else 560, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(tree, use_container_width=True)
        if not compact:
            st.dataframe(battle, use_container_width=True, hide_index=True)
    else:
        st.info("No paper intent generated from live risk gates.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_agent_timeline(compact: bool = False) -> None:
    st.markdown('<div class="glass-card"><div class="card-head">AGENT TIMELINE</div>', unsafe_allow_html=True)
    live_count = sum(1 for h in health if h.ok)
    timeline = [
        (datetime.now(timezone.utc).strftime("%H:%M"), "Live sources scanned", f"{live_count}/{len(health)}"),
        (datetime.now(timezone.utc).strftime("%H:%M"), "Fallback data checked", "Done"),
        (datetime.now(timezone.utc).strftime("%H:%M"), f"Signals scanned ({len(df)} assets)", ""),
        (datetime.now(timezone.utc).strftime("%H:%M"), "Score updated", ""),
        (datetime.now(timezone.utc).strftime("%H:%M"), "Mission report ready", ""),
    ]
    for t, txt, s in timeline:
        st.markdown(f"<div class='timeline'><div class='timeline-dot'></div><div class='timeline-time'>{t}</div><div>{txt}</div>{'<div class=success>✓ '+s+'</div>' if s else ''}</div>", unsafe_allow_html=True)
    if not compact:
        st.dataframe(pd.DataFrame(timeline, columns=["time", "event", "status"]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_selected_page() -> None:
    page = st.session_state.page
    render_shell_header()
    render_offline_warning()
    if page == "SIGNAL GALAXY":
        if has_live:
            render_metrics()
            st.markdown('<div class="page-title">SIGNAL GALAXY</div>', unsafe_allow_html=True)
            st.plotly_chart(signal_galaxy_chart(620), use_container_width=True)
    elif page == "ASSET PULSE":
        st.markdown('<div class="page-title">ASSET PULSE MATRIX</div>', unsafe_allow_html=True)
        if has_live:
            st.plotly_chart(pulse_heatmap(560), use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
    elif page == "STRATEGY FORGE":
        st.markdown('<div class="page-title">STRATEGY FORGE</div>', unsafe_allow_html=True)
        thesis = st.text_area("Mission thesis", value=thesis_default, height=120)
        risk_mode = st.segmented_control("Risk doctrine", ["Stealth", "Balanced", "Aggressive"], default="Balanced")
        new_plan = generate_mission(thesis, pulses, capital, risk_mode) if pulses else None
        if new_plan:
            st.markdown(f"<div class='page-panel'><b>Mission stance:</b> {new_plan.stance}<br><b>Priority assets:</b> {', '.join(new_plan.priority_assets) or 'None'}<br><b>Blocked assets:</b> {', '.join(new_plan.blocked_assets) or 'None'}</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(new_plan.orders), use_container_width=True, hide_index=True)
            for r in new_plan.reasoning:
                st.write("- " + r)
    elif page == "PORTFOLIO MAP":
        st.markdown('<div class="page-title">PORTFOLIO MAP</div>', unsafe_allow_html=True)
        render_portfolio_map(compact=False)
    elif page == "SCENARIO LAB":
        st.markdown('<div class="page-title">SCENARIO LAB</div>', unsafe_allow_html=True)
        render_scenario_chart(compact=False)
    elif page == "AGENT TIMELINE":
        st.markdown('<div class="page-title">AGENT TIMELINE</div>', unsafe_allow_html=True)
        render_agent_timeline(compact=False)
    elif page == "LIVE API CONSOLE":
        st.markdown('<div class="page-title">LIVE API CONSOLE</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([h.__dict__ for h in health]), use_container_width=True, hide_index=True)
        st.caption("Data priority: SoDEX/SoSoValue first, then Binance public market data, then CoinGecko public market data. No fake price fallback is used.")
    elif page == "MISSION REPORTS":
        st.markdown('<div class="page-title">MISSION REPORTS</div>', unsafe_allow_html=True)
        report = export_markdown(plan) if plan else "No live data available."
        st.download_button("Download mission report", report, file_name="nebula-command-report.md", mime="text/markdown")
        st.markdown(report)


def set_page(label: str) -> None:
    st.session_state.page = label


st.markdown('<div class="cosmos-grid"></div>', unsafe_allow_html=True)
left_col, main_col = st.columns([1.05, 4.7], gap="medium")
with left_col:
    st.markdown('<div class="left-rail">', unsafe_allow_html=True)
    st.markdown('<div class="brand"><div class="logo-star"></div><div class="brand-name">NEBULA<span>COMMAND</span></div></div><div class="orbit-box"><div class="orbit-center"></div></div><div class="side-kicker">MISSION CONTROL</div>', unsafe_allow_html=True)
    for icon, label in PAGES:
        if st.session_state.page == label:
            st.markdown(f"<div class='nav-current'>{icon}&nbsp;&nbsp; {label}<span class='nav-dot'></span></div>", unsafe_allow_html=True)
        else:
            st.button(f"{icon}  {label}", key=f"nav_{label}", on_click=set_page, args=(label,))
    good = sum(1 for h in health if h.ok) > 0
    st.markdown(f"<div class='status-panel'><div class='status-title'>SYSTEM STATUS</div><div class='{'status-good' if good else 'status-bad'}'>{'Live data online' if good else 'API attention required'}</div><div class='{'status-good' if has_live else 'status-bad'}'>{'Market pulse active ✅' if has_live else 'No live market data'}</div><div class='ecg'></div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with main_col:
    render_topbar()
    render_selected_page()
