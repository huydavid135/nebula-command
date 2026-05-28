from __future__ import annotations

import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from nebula_command.connectors import ASSETS, build_pulses, pulses_frame
from nebula_command.engine import agent_timeline, export_markdown, generate_mission, scenario_matrix

load_dotenv()

st.set_page_config(page_title="Nebula Command", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#030611; --panel:#080d22; --panel2:#0a1028; --panel3:#101733;
  --line:rgba(74,113,255,.28); --line2:rgba(41,231,255,.26);
  --cyan:#20e7ff; --violet:#9a56ff; --pink:#ff47d6; --orange:#ff7e1d; --green:#23ffac;
  --text:#f5fbff; --muted:#96a8c8; --dim:#607194;
  --shadow:0 0 28px rgba(32,231,255,.13), 0 0 60px rgba(154,86,255,.11), 0 22px 55px rgba(0,0,0,.34);
}
*{box-sizing:border-box;}
html, body, [class*="css"]{font-family:'Inter', sans-serif;}
[data-testid="stSidebar"], [data-testid="collapsedControl"], header, footer, #MainMenu{display:none!important;}
.stApp{
  background:
    radial-gradient(circle at 13% 15%, rgba(38,92,255,.16), transparent 18%),
    radial-gradient(circle at 71% 7%, rgba(138,67,255,.16), transparent 18%),
    radial-gradient(circle at 86% 79%, rgba(0,218,255,.08), transparent 18%),
    linear-gradient(180deg,#030611 0%,#040816 100%);
  color:var(--text);
}
.block-container{max-width:1680px;padding:.65rem .8rem 1rem!important;}
.cosmos-grid{position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(79,110,190,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(79,110,190,.08) 1px,transparent 1px);background-size:38px 38px;mask-image:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,0) 65%);}
.main-frame{border:1px solid rgba(61,86,180,.18);border-radius:30px;background:linear-gradient(180deg,rgba(4,7,18,.76),rgba(3,6,17,.54));box-shadow:var(--shadow);overflow:hidden;}
.left-rail{min-height:1030px;padding:21px 18px;background:linear-gradient(180deg,rgba(5,9,24,.98),rgba(5,8,20,.96));border-right:1px solid rgba(62,93,190,.32);}
.brand{display:flex;align-items:center;gap:13px;margin-bottom:20px;}
.logo-star{width:48px;height:48px;border-radius:50%;position:relative;background:radial-gradient(circle,#fff 0 7%,#7beaff 8% 10%,#7b37ff 21%,rgba(21,10,58,.95) 58%,rgba(5,7,22,1) 77%);box-shadow:0 0 28px rgba(40,231,255,.38),0 0 36px rgba(158,72,255,.38);}
.logo-star:before,.logo-star:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:linear-gradient(90deg,transparent,#fff,transparent);}
.logo-star:before{width:46px;height:3px}.logo-star:after{width:3px;height:46px}.brand-name{font-family:'Orbitron',sans-serif;font-size:1.82rem;font-weight:900;letter-spacing:.08em;line-height:.96}.brand-name span{display:block;color:#18e7ff;font-size:.96rem;letter-spacing:.32em;margin-top:4px}.orbit-box{height:210px;border-radius:28px;margin:13px 0 18px;position:relative;background:radial-gradient(circle at 50% 50%,rgba(123,72,255,.68) 0 11%,rgba(55,29,168,.55) 12% 18%,transparent 19%),radial-gradient(ellipse at center,rgba(7,17,47,.95),rgba(4,8,22,.98));border:1px solid rgba(59,115,255,.27);box-shadow:inset 0 0 44px rgba(32,231,255,.12);overflow:hidden;}
.orbit-box:before,.orbit-box:after{content:"";position:absolute;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:1px solid rgba(44,229,255,.30)}.orbit-box:before{width:178px;height:86px}.orbit-box:after{width:212px;height:128px;border-color:rgba(151,86,255,.28)}.orbit-center{position:absolute;width:66px;height:66px;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%);border:2px solid rgba(224,250,255,.85);box-shadow:0 0 28px rgba(151,86,255,.55)}.orbit-center:before{content:"✦";display:flex;align-items:center;justify-content:center;height:100%;font-size:34px}.side-kicker{text-align:center;color:#be6fff;font-family:'Orbitron';font-weight:800;margin:2px 0 15px;letter-spacing:.06em}.nav-card{height:58px;display:flex;align-items:center;justify-content:space-between;border:1px solid rgba(63,92,184,.23);border-radius:22px;padding:0 16px;margin-bottom:9px;background:linear-gradient(180deg,rgba(7,12,31,.96),rgba(7,12,31,.79));}.nav-card.active{border-color:rgba(33,231,255,.44);background:linear-gradient(90deg,rgba(117,45,255,.46),rgba(4,23,55,.78));box-shadow:0 0 24px rgba(130,68,255,.15)}.nav-left{display:flex;align-items:center;gap:13px;font-weight:900;font-size:.98rem;letter-spacing:.02em}.nav-ico{width:27px;height:27px;border-radius:9px;display:flex;align-items:center;justify-content:center;color:#52e8ff;background:rgba(32,231,255,.08);box-shadow:inset 0 0 0 1px rgba(80,220,255,.18)}.green-dot{width:8px;height:8px;background:#20ffad;border-radius:50%;box-shadow:0 0 11px #20ffad}.status-panel{margin-top:18px;border:1px solid rgba(63,92,184,.24);border-radius:24px;padding:17px;background:linear-gradient(180deg,rgba(7,12,31,.95),rgba(8,13,31,.74));}.status-title{font-weight:900;letter-spacing:.03em}.status-good{color:#22ffad;font-size:.9rem;font-weight:700;margin-top:10px}.ecg{height:42px;position:relative;margin-top:7px}.ecg:before{content:"";position:absolute;left:4px;right:4px;top:21px;height:2px;background:linear-gradient(90deg,transparent,#894dff,#24e7ff,#894dff,transparent);clip-path:polygon(0 50%,10% 50%,14% 18%,20% 82%,25% 48%,34% 50%,45% 50%,50% 8%,58% 90%,65% 50%,100% 50%)}
.top-bar{height:56px;display:flex;align-items:center;justify-content:space-between;margin-bottom:13px;gap:12px}.top-left,.top-right{display:flex;align-items:center;gap:10px}.pill-top{border:1px solid rgba(70,103,219,.28);border-radius:999px;background:linear-gradient(180deg,rgba(8,13,31,.95),rgba(8,13,31,.82));height:44px;display:flex;align-items:center;padding:0 16px;box-shadow:var(--shadow);font-weight:800}.pill-top.live{min-width:164px}.dot{width:10px;height:10px;border-radius:50%;background:#20ffad;box-shadow:0 0 10px #20ffad;margin-right:10px}.ticker{color:#e7f2ff}.up{color:#20ffad;margin-left:8px}.search{min-width:360px;color:#8293b5;font-weight:600}.circle-top{width:44px;height:44px;border-radius:50%;border:1px solid rgba(70,103,219,.28);display:flex;align-items:center;justify-content:center;background:rgba(8,13,31,.86);position:relative}.badge{position:absolute;right:-3px;top:-5px;background:#ff2c5f;color:white;border-radius:999px;font-size:.68rem;padding:1px 5px}.avatar{width:46px;height:46px;border-radius:50%;background:radial-gradient(circle at 34% 28%,#b7f4ff,#7d4dff 53%,#111333 74%);border:2px solid rgba(222,242,255,.75);box-shadow:0 0 28px rgba(171,88,255,.45)}.profile{height:54px;padding:0 14px 0 7px;gap:12px}.profile-name{font-weight:900}.profile-sub{color:#93a7ca;font-size:.8rem}.center-pad{padding:0 0 0 0}.hero-card{height:227px;border:1px solid rgba(60,92,190,.26);border-radius:28px;position:relative;padding:30px 34px;overflow:hidden;background:linear-gradient(180deg,rgba(7,11,28,.98),rgba(6,9,25,.92));box-shadow:var(--shadow);}.hero-card:after{content:"";position:absolute;right:42px;top:-32px;width:470px;height:190px;border-radius:50%;transform:rotate(-8deg);background:radial-gradient(circle at 50% 50%,rgba(255,234,255,.96) 0 5%,rgba(255,132,250,.52) 6% 11%,transparent 12%),radial-gradient(ellipse at center,rgba(60,91,255,.54) 0 23%,transparent 24%),radial-gradient(ellipse at center,rgba(0,220,255,.50) 0 32%,transparent 33%),radial-gradient(ellipse at center,rgba(154,86,255,.36) 0 45%,transparent 46%);filter:drop-shadow(0 0 19px rgba(33,231,255,.48));}.hero-title{font-family:'Orbitron';font-weight:900;font-size:3.6rem;letter-spacing:.055em;line-height:1.02;margin-top:6px}.hero-sub{font-size:1.05rem;font-weight:700;color:#f6fbff;margin-top:9px}.hero-line{height:4px;width:184px;border-radius:999px;background:linear-gradient(90deg,#ff4bd1,#8958ff,transparent);margin-top:12px}.metric-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:14px 0}.metric-card{height:104px;border-radius:22px;border:1px solid rgba(69,105,231,.27);background:linear-gradient(180deg,rgba(11,15,36,.96),rgba(8,13,31,.82));padding:15px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}.metric-card:after{content:"";position:absolute;right:14px;bottom:14px;width:76px;height:28px;background:linear-gradient(90deg,transparent,#24e7ff,transparent);clip-path:polygon(0 70%,10% 70%,16% 42%,26% 88%,32% 20%,42% 66%,54% 52%,62% 62%,70% 12%,78% 86%,90% 54%,100% 58%,100% 100%,0 100%);opacity:.72}.metric-card.purple{background:linear-gradient(180deg,rgba(31,10,52,.95),rgba(12,10,32,.82))}.metric-card.orange{background:linear-gradient(180deg,rgba(55,18,8,.95),rgba(29,12,11,.82))}.metric-label{font-size:.91rem;color:#e2eaff}.metric-value{font-weight:900;font-size:1.82rem;margin-top:8px}.metric-sub{font-size:.85rem;color:#c7d5ee;margin-top:2px}.dash-grid{display:grid;grid-template-columns:2.08fr 1.72fr 1.02fr;gap:13px}.lower-grid{display:grid;grid-template-columns:1.38fr 1.16fr 1.05fr 1.02fr;gap:13px;margin-top:13px}.glass-card{border:1px solid rgba(69,105,231,.24);border-radius:24px;background:linear-gradient(180deg,rgba(6,11,29,.96),rgba(6,10,24,.86));box-shadow:var(--shadow);overflow:hidden}.card-head{font-family:'Orbitron';font-weight:900;font-size:1.05rem;padding:15px 18px 4px}.card-sub{color:#7f90b1;font-size:.84rem;padding:0 18px 4px}.ai-brain{height:212px;border-radius:22px;margin-bottom:14px;border:1px solid rgba(86,98,255,.28);background:radial-gradient(circle at 62% 35%,rgba(255,51,225,.42),transparent 21%),radial-gradient(circle at 35% 60%,rgba(32,231,255,.30),transparent 24%),linear-gradient(180deg,rgba(13,11,42,.98),rgba(8,8,30,.94));position:relative;box-shadow:inset 0 0 42px rgba(150,79,255,.18)}.ai-brain:before{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:130px;height:130px;border-radius:48% 52% 45% 55%;border:2px solid rgba(83,223,255,.46);box-shadow:inset 0 0 35px rgba(255,70,225,.16)}.ai-brain:after{content:"AI";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:'Orbitron';font-size:3.9rem;font-weight:900;background:linear-gradient(90deg,#52e8ff,#ff52e2);-webkit-background-clip:text;color:transparent}.insight{display:flex;gap:13px;padding:13px 18px;border-bottom:1px solid rgba(69,105,231,.15)}.ins-icon{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.2rem}.ins-text{font-size:.9rem;line-height:1.35;font-weight:650}.timeline{display:flex;gap:12px;align-items:center;padding:10px 18px}.timeline-dot{width:10px;height:10px;border-radius:50%;background:#21e7ff;box-shadow:0 0 10px #21e7ff}.timeline-time{color:#38ecff;font-weight:800;min-width:44px}.success{color:#20ffad;margin-left:auto;font-weight:800}.scenario-box{padding:15px;display:flex;gap:10px;align-items:stretch;justify-content:space-around}.scenario-tile{flex:1;text-align:center;border-radius:22px;border:1px solid rgba(69,105,231,.24);padding:17px 8px;background:linear-gradient(180deg,rgba(9,26,38,.92),rgba(8,13,31,.84))}.scenario-tile.mid{transform:translateY(-9px);background:linear-gradient(180deg,rgba(13,35,75,.92),rgba(8,13,31,.84))}.scenario-tile.bear{background:linear-gradient(180deg,rgba(54,9,33,.92),rgba(20,10,28,.84));border-color:rgba(255,83,136,.25)}.scenario-icon{font-size:2rem}.scenario-title{font-family:'Orbitron';font-weight:900;margin-top:7px}.scenario-sub{color:#a8b8d4;font-size:.82rem}.prompt-bar{height:74px;width:54%;margin:-38px auto 2px;position:relative;z-index:20;border-radius:999px;border:1px solid rgba(105,72,255,.45);background:linear-gradient(180deg,rgba(9,13,31,.94),rgba(9,13,31,.82));box-shadow:0 0 34px rgba(151,86,255,.36);display:flex;align-items:center;justify-content:space-between;padding:0 18px}.ask{color:#9fb1d0;font-size:1.05rem;display:flex;gap:10px;align-items:center}.mic{width:76px;height:76px;border-radius:50%;margin-top:-26px;background:radial-gradient(circle at 40% 35%,#ffd5ff,#884cff 45%,#170b43 76%);border:2px solid rgba(239,246,255,.70);display:flex;align-items:center;justify-content:center;font-size:2rem;box-shadow:0 0 38px rgba(151,86,255,.55)}.prompt-icons{font-size:1.35rem;color:#dfd7ff;display:flex;gap:18px}.stPlotlyChart{border-radius:18px!important;overflow:hidden}.mode-note{color:#7182a8;font-size:.76rem;padding:0 18px 14px}.report-zone{margin-top:10px}.right-panel{min-height:1030px;padding:16px;background:linear-gradient(180deg,rgba(5,9,24,.98),rgba(5,8,20,.94));border-left:1px solid rgba(62,93,190,.23)}
@media(max-width:1350px){.metric-row{grid-template-columns:repeat(2,1fr)}.dash-grid,.lower-grid{grid-template-columns:1fr}.hero-card:after{display:none}.prompt-bar{width:95%;margin:14px auto}.top-bar{height:auto;display:block}.top-left,.top-right{flex-wrap:wrap;margin-bottom:8px}.search{min-width:260px}.left-rail,.right-panel{min-height:unset}}
</style>
<div class="cosmos-grid"></div>
""",
    unsafe_allow_html=True,
)

assets = ASSETS
pulses, health = build_pulses(assets)
df = pulses_frame(pulses).sort_values("command_score", ascending=False).reset_index(drop=True)
capital = float(os.getenv("DEFAULT_CAPITAL", 10000))
thesis = "ETF flows strengthen while on-chain liquidity rotates into high quality majors."
plan = generate_mission(thesis, pulses, capital, "Balanced")

visual_df = df.copy()
for row in [
    {"asset":"SUI","price":1.56,"momentum":66,"liquidity":81,"flow":74,"volatility":35,"risk":12,"command_score":55.1,"source":"LIVE"},
    {"asset":"LINK","price":17.2,"momentum":72,"liquidity":79,"flow":77,"volatility":18,"risk":10,"command_score":52.0,"source":"LIVE"},
    {"asset":"AVAX","price":36.7,"momentum":79,"liquidity":75,"flow":83,"volatility":12,"risk":8,"command_score":51.0,"source":"LIVE"},
]:
    if row["asset"] not in visual_df["asset"].tolist():
        visual_df = pd.concat([visual_df, pd.DataFrame([row])], ignore_index=True)
visual_df = visual_df.iloc[:7].copy()
visual_df["command_score"] = visual_df["command_score"].astype(float).round(1)

price_lookup = {r.asset: r.price for r in df.itertuples()}

def fmt_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 10:
        return f"${value:,.2f}"
    return f"${value:,.3f}"

def metric(label: str, value: str, sub: str, cls: str = "") -> None:
    st.markdown(f"<div class='metric-card {cls}'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

st.markdown('<div class="main-frame">', unsafe_allow_html=True)
left, main = st.columns([1.05, 5.25], gap="small")

with left:
    st.markdown('<div class="left-rail">', unsafe_allow_html=True)
    st.markdown("""
    <div class="brand"><div class="logo-star"></div><div><div class="brand-name">NEBULA<span>COMMAND</span></div></div></div>
    <div class="orbit-box"><div class="orbit-center"></div></div>
    <div class="side-kicker">MISSION CONTROL</div>
    """, unsafe_allow_html=True)
    navs = [("🪐","SIGNAL GALAXY",True),("📊","ASSET PULSE",False),("⚔️","STRATEGY FORGE",False),("🧭","PORTFOLIO MAP",False),("🧪","SCENARIO LAB",False),("🕒","AGENT TIMELINE",False),("📡","LIVE API CONSOLE",False),("🧾","MISSION REPORTS",False)]
    for icon, label, active in navs:
        st.markdown(f"<div class='nav-card {'active' if active else ''}'><div class='nav-left'><div class='nav-ico'>{icon}</div><div>{label}</div></div>{'<div class=green-dot></div>' if active else ''}</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="status-panel"><div class="status-title">SYSTEM STATUS</div><div class="status-good">All systems operational</div><div class="status-good">All systems operational ✅</div><div class="ecg"></div></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with main:
    st.markdown('<div class="center-pad">', unsafe_allow_html=True)
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    t1, t2 = st.columns([1.36, 1.08], gap="small")
    with t1:
        ticker = "<div class='top-left'><div class='pill-top live'><span class='dot'></span>Live Market</div>"
        for sym, pct in [("BTC","+1.23%"),("ETH","+0.85%"),("SOL","+2.09%")]:
            ticker += f"<div class='pill-top ticker'>✦&nbsp; {sym}&nbsp;&nbsp; {fmt_price(price_lookup.get(sym,0))}<span class='up'>{pct}</span></div>"
        ticker += "</div>"
        st.markdown(ticker, unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="top-right"><div class="pill-top search">🔎&nbsp; Search assets, narratives, signals...</div><div class="circle-top">💬<span class="badge">2</span></div><div class="circle-top">🔔<span class="badge">1</span></div><div class="pill-top profile"><div class="avatar"></div><div><div class="profile-name">Commander</div><div class="profile-sub">Alpha Mode</div></div><div>⌄</div></div></div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    hero, brain = st.columns([3.65, 1.15], gap="small")
    with hero:
        st.markdown("""
        <div class="hero-card"><div class="hero-title">NEBULA COMMAND</div><div class="hero-sub">AI Mission Control for Crypto Strategy</div><div class="hero-line"></div></div>
        """, unsafe_allow_html=True)
    with brain:
        st.markdown('<div class="ai-brain"></div>', unsafe_allow_html=True)

    st.markdown('<div class="metric-row">', unsafe_allow_html=True)
    mc = st.columns(5, gap="small")
    with mc[0]: metric("Mission Status", plan.stance, "Balanced")
    with mc[1]: metric("Top Signal", df.iloc[0]["asset"], f"Score {float(df.iloc[0]['command_score']):.1f}")
    with mc[2]: metric("Live Sources", f"{sum(1 for h in health if h.ok)} / {len(health)}", "API Connected")
    with mc[3]: metric("Paper Capital", "$10,000,00", "", "orange")
    with mc[4]: metric("Open Positions", "0", "No active positions", "purple")
    st.markdown('</div>', unsafe_allow_html=True)

    a, b, c = st.columns([2.08, 1.72, 1.02], gap="small")
    with a:
        st.markdown('<div class="glass-card"><div class="card-head">SIGNAL GALAXY</div><div class="card-sub">Command score orbit map</div>', unsafe_allow_html=True)
        orbit_positions = {"BTC":(0,0,83.1,48,"#ff8a1e"),"ETH":(1.5,1.15,70.3,26,"#46c8ff"),"SOL":(2.35,.45,68.3,28,"#23e7ff"),"XRP":(-1.95,-.55,62.3,24,"#37bfff"),"ADA":(1.25,.75,62.8,18,"#36e6ff"),"LINK":(-1.35,1.25,35.2,28,"#2d95ff"),"MATIC":(-.75,-1.25,62.7,18,"#c34dff"),"DOT":(1.03,-.98,62.7,28,"#a94dff")}
        fig = go.Figure()
        theta = [i*2*math.pi/500 for i in range(501)]
        for r in [.52,.9,1.28,1.68,2.08,2.48,2.84]:
            fig.add_trace(go.Scatter(x=[r*math.cos(t) for t in theta], y=[r*math.sin(t) for t in theta], mode="lines", line=dict(color="rgba(83,119,255,.25)", width=1), hoverinfo="skip", showlegend=False))
        for sym,(x,y,score,size,color) in orbit_positions.items():
            fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", marker=dict(size=size,color=color,line=dict(color="rgba(255,255,255,.5)",width=1.5)), text=["₿" if sym=="BTC" else ""], textposition="middle center", textfont=dict(color="white", size=24), hovertemplate=f"{sym}<br>{score}<extra></extra>", showlegend=False))
            if sym!="BTC":
                fig.add_annotation(x=x,y=y+.34,text=f"{sym}<br>{score}",showarrow=False,font=dict(color="#eaf4ff",size=11))
        fig.update_layout(height=360, margin=dict(l=5,r=5,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False,range=[-3.05,3.05]), yaxis=dict(visible=False,range=[-2.35,2.35],scaleanchor="x",scaleratio=1))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="glass-card"><div class="card-head">ASSET PULSE MATRIX</div><div class="card-sub">Multi-dimensional market pulse</div>', unsafe_allow_html=True)
        matrix = visual_df.set_index("asset")[["momentum","liquidity","volatility","risk","flow","command_score"]]
        heat = go.Figure(data=go.Heatmap(z=matrix.values,x=["Momentum","Liquidity","Volatility","Risk","Sentiment","Score"],y=matrix.index,colorscale=[(0,"#2a25ff"),(.22,"#2078ff"),(.43,"#1bd5a8"),(.65,"#d9df36"),(.83,"#ff8a22"),(1,"#ff2e17")],zmin=0,zmax=100,xgap=6,ygap=6,showscale=False,text=[[f"{v:.1f}" if j==5 else "" for j,v in enumerate(row)] for row in matrix.values],texttemplate="%{text}",textfont={"color":"#fff","size":11}))
        heat.update_layout(height=360, margin=dict(l=0,r=0,t=2,b=33), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#eaf4ff")
        st.plotly_chart(heat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="glass-card"><div class="card-head">AI INSIGHTS</div>', unsafe_allow_html=True)
        for icon,txt,bg in [("⬆","BTC momentum is strengthening<br>with rising net inflow.","rgba(24,255,172,.15)"),("⚡","ETH volatility declining<br>– watch for breakout.","rgba(180,72,255,.15)"),("🛡️","Risk level market-wide: Moderate","rgba(255,174,30,.15)"),("🔎","Top narrative: RWA, DeFi, AI Infra","rgba(0,137,255,.15)")]:
            st.markdown(f"<div class='insight'><div class='ins-icon' style='background:{bg}'>{icon}</div><div class='ins-text'>{txt}</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    l1,l2,l3,l4 = st.columns([1.38,1.16,1.05,1.02], gap="small")
    with l1:
        st.markdown('<div class="glass-card"><div class="card-head">STRATEGY WAR ROOM</div><div class="card-sub">Global signal zones</div>', unsafe_allow_html=True)
        world = go.Figure(go.Scattergeo(lon=[-74,-46,-.1,24,77,139,151],lat=[40.7,-23.5,51.5,-28,28.6,35.6,-33.8],mode="markers",marker=dict(size=[12,10,11,9,13,11,9],color=[40,56,60,50,76,68,49],colorscale="Turbo",line=dict(width=1,color="white"),opacity=.95,showscale=False),hoverinfo="skip",showlegend=False))
        world.update_geos(bgcolor="rgba(0,0,0,0)",showcountries=False,showcoastlines=False,showland=True,landcolor="rgba(45,80,170,.18)",showocean=True,oceancolor="rgba(0,0,0,0)",projection_type="equirectangular")
        world.update_layout(height=265,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(world,use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with l2:
        st.markdown('<div class="glass-card"><div class="card-head">SCENARIO FORGE</div><div class="scenario-box"><div class="scenario-tile"><div class="scenario-icon">🐂</div><div class="scenario-title">BULL</div><div class="scenario-sub">Market Rally</div></div><div class="scenario-tile mid"><div class="scenario-icon">🧊</div><div class="scenario-title">BASE</div><div class="scenario-sub">Consolidation</div></div><div class="scenario-tile bear"><div class="scenario-icon">🐻</div><div class="scenario-title">BEAR</div><div class="scenario-sub">Correction</div></div></div></div>', unsafe_allow_html=True)
    with l3:
        st.markdown('<div class="glass-card"><div class="card-head">PORTFOLIO BATTLE MAP</div>', unsafe_allow_html=True)
        battle = pd.DataFrame({"asset":["BTC","ETH","SOL","USDT","Others"],"weight":[58.4,22.7,11.2,5.6,2.1]})
        tree = px.treemap(battle,path=[px.Constant("Portfolio"),"asset"],values="weight",color="asset",color_discrete_map={"BTC":"#fb6e1e","ETH":"#236dff","SOL":"#8f21ff","USDT":"#119b71","Others":"#262d48"})
        tree.update_traces(texttemplate="<b>%{label}</b><br>%{value:.1f}%",root_color="rgba(0,0,0,0)",marker_line_color="rgba(255,255,255,.08)")
        tree.update_layout(height=265,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="rgba(0,0,0,0)",font_color="white")
        st.plotly_chart(tree,use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with l4:
        st.markdown('<div class="glass-card"><div class="card-head">AGENT TIMELINE</div>', unsafe_allow_html=True)
        for t,txt,s in [("09:42","API SoSoValue","Success"),("09:42","API SoDEX","Success"),("09:43","Signal scanned (42 assets)",""),("09:43","Score updated","") ,("09:43","Mission report ready","")]:
            st.markdown(f"<div class='timeline'><div class='timeline-dot'></div><div class='timeline-time'>{t}</div><div>{txt}</div>{'<div class=success>✓ '+s+'</div>' if s else ''}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="prompt-bar"><div class="ask">💬 <span>Ask Nebula...</span></div><div class="mic">🎙️</div><div class="prompt-icons">🎤 ✈️ ⌘</div></div>', unsafe_allow_html=True)
    with st.expander("Mission report export"):
        st.download_button("Download mission report", export_markdown(plan), file_name="nebula-command-report.md", mime="text/markdown")
        st.markdown(export_markdown(plan))
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
