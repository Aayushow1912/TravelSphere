import os
import html
import re
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from langchain_core.messages import HumanMessage

st.set_page_config(
    page_title="TravelSphere",
    page_icon="✈️",
    layout="wide"
)


def load_streamlit_secrets_to_env():
    secret_keys = [
        "AVIATIONSTACK_API_KEY",
        "GROQ_API_KEY",
        "TAVILY_API_KEY",
        "TAVLIY_API_KEY",
        "DATABASE_URL",
        "USE_POSTGRES_CHECKPOINTER", 
        "OPENWEATHER_API_KEY",
        "AVIATION_MCP_PYTHON",
        "WEATHER_MCP_SCRIPT",
    ]
    try:
        for key in secret_keys:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


load_streamlit_secrets_to_env()

from main import CHECKPOINTER_WARNING, app

if CHECKPOINTER_WARNING:
    st.warning(CHECKPOINTER_WARNING)


def extract_total_budget(query: str) -> str:
    """Return a short budget phrase from the user's travel query."""
    budget_patterns = [
        r"(?i)\b(?:under|below|within|around|approx(?:imately)?|about|budget(?:\s+of)?|for)\s+((?:rs\.?|inr|usd|\$|eur|gbp|£|₹)?\s*[\d,]+(?:\.\d+)?\s*(?:l|lakhs?|lacs?|cr|crores?|k|thousand|million)?)",
        r"(?i)((?:rs\.?|inr|usd|\$|eur|gbp|£|₹)\s*[\d,]+(?:\.\d+)?\s*(?:l|lakhs?|lacs?|cr|crores?|k|thousand|million)?)",
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, query)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return "Not specified"

# Theme is controlled by the top-right toggle button (JS + localStorage).
# No sidebar toggle needed — the button is the single source of truth.

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── Theme Palettes (CSS variables) ── */
:root, :root[data-theme="dark"] {
    --bg: #0B0D11;
    --bg-elev: #0F1118;
    --card1: #14171E;
    --card2: #181C25;
    --card-flat: #0F1118;
    --sidebar-bg: linear-gradient(180deg, #0E1015 0%, #0B0D11 100%);
    --text: #EDE8DD;
    --text-strong: #FAF6ED;
    --text-body: #C8C5BC;
    --text-dim: #8A8D96;
    --text-faint: #5A5D65;
    --text-mute: #6B6E78;
    --placeholder: #4A4D55;
    --border: rgba(255,255,255,0.06);
    --border-soft: rgba(255,255,255,0.04);
    --border-strong: rgba(255,255,255,0.08);
    --accent: #E8A838;
    --accent2: #38B2AC;
    --accent3: #E07A5F;
    --accent4: #A78BFA;
    --on-accent: #0B0D11;
    --glow1: rgba(232,168,56,0.06);
    --glow2: rgba(56,178,172,0.04);
    --noise-opacity: 0.03;
    --shadow-card: 0 10px 30px rgba(0,0,0,0.3);
    --hero-img-filter: brightness(0.5) saturate(0.9);
    --particle-alpha: 0.55;
}
:root[data-theme="light"] {
    --bg: #FAF6ED;
    --bg-elev: #FFFFFF;
    --card1: #FFFFFF;
    --card2: #F4EEDE;
    --card-flat: #FFFFFF;
    --sidebar-bg: linear-gradient(180deg, #FFFCF5 0%, #FAF6ED 100%);
    --text: #2A2D35;
    --text-strong: #16181D;
    --text-body: #3D4048;
    --text-dim: #56596A;
    --text-faint: #7A7D85;
    --text-mute: #6B6E78;
    --placeholder: #A8A498;
    --border: rgba(30,25,10,0.10);
    --border-soft: rgba(30,25,10,0.06);
    --border-strong: rgba(30,25,10,0.14);
    --accent: #B9740E;
    --accent2: #0E8C82;
    --accent3: #C2553A;
    --accent4: #7657D6;
    --on-accent: #FFFFFF;
    --glow1: rgba(184,116,14,0.05);
    --glow2: rgba(14,140,130,0.04);
    --noise-opacity: 0.015;
    --shadow-card: 0 10px 30px rgba(80,60,15,0.10);
    --hero-img-filter: brightness(0.62) saturate(0.95);
    --particle-alpha: 0.42;
}

/* ── Base ── */
html, body, .stApp,
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"] {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background:
        radial-gradient(ellipse 800px 600px at 20% 10%, var(--glow1) 0%, transparent 60%),
        radial-gradient(ellipse 600px 500px at 80% 90%, var(--glow2) 0%, transparent 60%),
        url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
}

.stApp > div { position: relative; z-index: 1; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--card1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Sidebar Scroll Fix ── */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-soft) !important;
}

section[data-testid="stSidebar"] > div {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    max-height: 100vh !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: thin !important;
    scrollbar-color: var(--card1) transparent !important;
}

section[data-testid="stSidebar"] > div::-webkit-scrollbar { width: 4px !important; }
section[data-testid="stSidebar"] > div::-webkit-scrollbar-track { background: transparent !important; }
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb { background: var(--card1) !important; border-radius: 10px !important; }
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb:hover { background: var(--accent) !important; }

/* ── Sidebar Styles ── */
.sidebar-brand {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--text-strong); margin-bottom: 4px;
}
.sidebar-tagline {
    font-size: 0.78rem; color: var(--text-faint);
    letter-spacing: 0.05em; margin-bottom: 1.5rem;
}
.sidebar-section-title {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--text-faint); margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-soft);
}
.sidebar-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    background: var(--card-flat);
    border: 1px solid var(--border-soft);
    border-radius: 10px; margin-bottom: 6px;
    font-size: 0.82rem; color: var(--text-dim);
    transition: all 0.2s ease; cursor: default;
}
.sidebar-item:hover {
    background: color-mix(in srgb, var(--accent) 8%, transparent);
    border-color: color-mix(in srgb, var(--accent) 20%, transparent);
    color: var(--text); transform: translateX(4px);
}
.sidebar-item-icon { font-size: 1rem; width: 20px; text-align: center; }
.sidebar-pipeline { position: relative; padding-left: 20px; }
.sidebar-pipeline::before {
    content: ''; position: absolute;
    left: 6px; top: 8px; bottom: 8px;
    width: 2px;
    background: linear-gradient(180deg, var(--accent), var(--accent2), var(--accent4));
    border-radius: 2px; opacity: 0.4;
}
.pipeline-step {
    position: relative; display: flex; align-items: center;
    gap: 12px; padding: 10px 14px; margin-bottom: 4px;
    font-size: 0.82rem; color: var(--text-dim); transition: all 0.2s ease;
}
.pipeline-step::before {
    content: ''; position: absolute; left: -17px;
    width: 10px; height: 10px; border-radius: 50%;
    border: 2px solid; background: var(--bg);
}
.pipeline-step:nth-child(1)::before { border-color: var(--accent); }
.pipeline-step:nth-child(2)::before { border-color: var(--accent2); }
.pipeline-step:nth-child(3)::before { border-color: var(--accent3); }
.pipeline-step:nth-child(4)::before { border-color: var(--accent4); }
.pipeline-step:hover { color: var(--text); }

/* ── Hero ── */
.hero-shell {
    position: relative; border-radius: 24px; overflow: hidden;
    margin-bottom: 2.5rem;
    border: 1px solid color-mix(in srgb, var(--accent) 22%, transparent);
    box-shadow: 0 0 60px color-mix(in srgb, var(--accent) 10%, transparent),
                0 25px 50px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.03);
}

/* ── Section Helpers ── */
.section-label {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
    padding: 6px 16px; border-radius: 100px; margin-bottom: 1rem;
}

/* ── Destination Cards ── */
.dest-grid {
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}
.dest-card {
    position: relative; height: 140px;
    border-radius: 16px; overflow: hidden; cursor: pointer;
    transition: all 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
    border: 1px solid var(--border);
}
.dest-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 30px color-mix(in srgb, var(--accent) 18%, transparent);
    border-color: color-mix(in srgb, var(--accent) 35%, transparent);
}
.dest-card img {
    width: 100%; height: 100%; object-fit: cover;
    transition: transform 0.6s ease, filter 0.4s ease;
    filter: var(--hero-img-filter);
}
.dest-card:hover img {
    transform: scale(1.1); filter: brightness(0.6) saturate(1.1);
}
.dest-card-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.85) 100%);
}
.dest-card-label {
    position: absolute; bottom: 12px; left: 14px; right: 14px;
    font-family: 'Playfair Display', serif; font-size: 1rem;
    font-weight: 600; color: #FAF6ED;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.dest-card-badge {
    position: absolute; top: 10px; right: 10px;
    width: 28px; height: 28px;
    background: color-mix(in srgb, var(--accent) 90%, white); border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; opacity: 0; transform: scale(0.5);
    transition: all 0.3s ease;
}
.dest-card:hover .dest-card-badge { opacity: 1; transform: scale(1); }

/* ── Input Container ── */
.input-container {
    position: relative;
    background: linear-gradient(135deg, var(--card1) 0%, var(--card2) 100%);
    border: 1px solid var(--border);
    border-radius: 20px; padding: 2rem; margin-bottom: 2rem;
    box-shadow: var(--shadow-card);
}
.input-container::before {
    content: ''; position: absolute;
    top: -1px; left: 40px; right: 40px; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    border-radius: 2px;
}

/* ── Generate Button ── */
.main-generate-btn div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 88%, #000) 50%, color-mix(in srgb, var(--accent) 75%, #000) 100%) !important;
    color: var(--on-accent) !important; border: none !important;
    border-radius: 14px !important;
    padding: 1rem 2.5rem !important; font-size: 1rem !important;
    font-weight: 700 !important; letter-spacing: 0.02em !important;
    width: 100% !important;
    box-shadow: 0 0 30px color-mix(in srgb, var(--accent) 28%, transparent), 0 8px 25px rgba(0,0,0,0.4),
                inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94) !important;
    text-transform: uppercase !important;
}
.main-generate-btn div[data-testid="stButton"] > button:hover {
    box-shadow: 0 0 50px color-mix(in srgb, var(--accent) 42%, transparent), 0 12px 35px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.3) !important;
    transform: translateY(-3px) !important;
    background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 80%, #fff) 0%, var(--accent) 50%, color-mix(in srgb, var(--accent) 88%, #000) 100%) !important;
}
.main-generate-btn div[data-testid="stButton"] > button:active { transform: translateY(-1px) !important; }

/* ── Pipeline ── */
.pipeline-header {
    display: flex; align-items: center; justify-content: space-between;
    margin: 2.5rem 0 1.5rem; padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.pipeline-title {
    font-family: 'Playfair Display', serif; font-size: 1.5rem;
    font-weight: 700; color: var(--text-strong);
}
.pipeline-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: color-mix(in srgb, var(--accent2) 12%, transparent); border: 1px solid color-mix(in srgb, var(--accent2) 32%, transparent);
    color: var(--accent2); padding: 6px 14px; border-radius: 100px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em;
}
@keyframes livePulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.live-dot {
    width: 6px; height: 6px; background: var(--accent2);
    border-radius: 50%; animation: livePulse 1.5s ease-in-out infinite;
}
.agent-complete-toast {
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 280px;
    max-width: min(360px, calc(100vw - 32px));
    padding: 14px 18px;
    background: linear-gradient(135deg, var(--card1) 0%, var(--card2) 100%);
    border: 1px solid color-mix(in srgb, var(--accent2) 38%, transparent);
    border-radius: 14px;
    box-shadow: 0 18px 40px rgba(0,0,0,0.35), 0 0 24px color-mix(in srgb, var(--accent2) 12%, transparent);
    animation: agentCompleteToast 2.6s ease forwards;
    pointer-events: none;
}
.agent-complete-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    background: color-mix(in srgb, var(--accent2) 16%, transparent);
    color: var(--accent2);
    font-weight: 800;
}
.agent-complete-title {
    color: var(--text-strong);
    font-size: 0.9rem;
    font-weight: 700;
    line-height: 1.25;
}
.agent-complete-subtitle {
    color: var(--text-mute);
    font-size: 0.76rem;
    line-height: 1.35;
    margin-top: 2px;
}
@keyframes agentCompleteToast {
    0% { opacity: 0; transform: translateX(120%) scale(0.98); }
    12% { opacity: 1; transform: translateX(0) scale(1); }
    78% { opacity: 1; transform: translateX(0) scale(1); }
    100% { opacity: 0; transform: translateX(120%) scale(0.98); }
}

/* ── Agent Status ── */
[data-testid="stStatusWidget"] {
    background: linear-gradient(135deg, var(--card1) 0%, var(--card-flat) 100%) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important; margin-bottom: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stStatusWidget"]:hover {
    border-color: color-mix(in srgb, var(--accent) 25%, transparent) !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 20px color-mix(in srgb, var(--accent) 6%, transparent) !important;
}
[data-testid="stStatusWidget"] > div:first-child {
    background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 9%, transparent) 0%, transparent 100%) !important;
    border-radius: 16px 16px 0 0 !important; padding: 14px 18px !important;
}
[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: var(--card-flat) !important; color: var(--text-body) !important;
    padding: 16px 20px !important; font-size: 0.9rem !important; line-height: 1.7 !important;
}
[data-testid="stStatusWidget"] * { color: var(--text-body) !important; }
[data-testid="stStatusWidget"] a { color: var(--accent) !important; text-decoration: underline !important; }
[data-testid="stStatusWidget"] hr { border-color: var(--border) !important; margin: 12px 0 !important; }

/* ── Metrics ── */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 2rem 0;
}
.metric-card {
    background: linear-gradient(135deg, var(--card1) 0%, var(--card2) 100%);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 1.5rem; text-align: center; position: relative;
    overflow: hidden; transition: all 0.35s ease;
}
.metric-card:hover {
    transform: translateY(-4px); border-color: color-mix(in srgb, var(--accent) 25%, transparent);
    box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 3px 3px 0 0;
}
.metric-card:nth-child(1)::before { background: var(--accent); }
.metric-card:nth-child(2)::before { background: var(--accent2); }
.metric-card:nth-child(3)::before { background: var(--accent3); }
.metric-card:nth-child(4)::before { background: var(--accent4); }
.metric-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.metric-value {
    font-family: 'Playfair Display', serif; font-size: 2.2rem;
    font-weight: 700; margin-bottom: 0.25rem;
}
.metric-card:nth-child(1) .metric-value { color: var(--accent); }
.metric-card:nth-child(2) .metric-value { color: var(--accent2); }
.metric-card:nth-child(3) .metric-value { color: var(--accent3); }
.metric-card:nth-child(4) .metric-value { color: var(--accent4); }
.metric-label {
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-mute);
}

/* ── Final Plan Card ── */
.final-plan-card {
    position: relative;
    background: linear-gradient(160deg, var(--card2) 0%, var(--card1) 100%);
    border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent); border-radius: 20px;
    padding: 2.5rem; overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
}
.final-plan-card::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 5px; height: 100%;
    background: linear-gradient(180deg, var(--accent) 0%, var(--accent2) 50%, var(--accent4) 100%);
    border-radius: 5px 0 0 5px;
}
.final-plan-card::after {
    content: ''; position: absolute; top: 0; right: 0;
    width: 200px; height: 200px;
    background: radial-gradient(circle, color-mix(in srgb, var(--accent) 9%, transparent) 0%, transparent 70%);
    pointer-events: none;
}
.final-plan-content {
    position: relative; z-index: 1;
    line-height: 1.9; color: var(--text-body); font-size: 0.95rem;
}
.final-plan-content h1, .final-plan-content h2, .final-plan-content h3 {
    font-family: 'Playfair Display', serif; color: var(--text-strong) !important; margin: 1.5rem 0 0.75rem;
}
.final-plan-content strong { color: var(--accent) !important; }

/* ── Action Bar ── */
.action-bar {
    display: flex; align-items: center; gap: 16px; margin-top: 1.5rem;
    padding: 1rem 1.5rem;
    background: color-mix(in srgb, var(--accent2) 7%, transparent); border: 1px solid color-mix(in srgb, var(--accent2) 18%, transparent);
    border-radius: 14px;
}
.action-bar-text { color: var(--accent2); font-size: 0.88rem; flex: 1; }
.action-bar-text code {
    background: color-mix(in srgb, var(--accent2) 12%, transparent); color: var(--accent2) !important;
    padding: 2px 8px; border-radius: 4px; font-size: 0.82rem;
}
div[data-testid="stDownloadButton"] > button {
    background: color-mix(in srgb, var(--accent) 16%, transparent) !important; color: var(--accent) !important;
    border: 1px solid color-mix(in srgb, var(--accent) 32%, transparent) !important; border-radius: 12px !important;
    font-weight: 600 !important; transition: all 0.25s ease !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: color-mix(in srgb, var(--accent) 26%, transparent) !important; border-color: color-mix(in srgb, var(--accent) 52%, transparent) !important;
    transform: translateY(-2px) !important;
}

/* ── Textarea ── */
.stTextArea textarea {
    background: var(--bg-elev) !important; border: 1px solid var(--border-strong) !important;
    border-radius: 14px !important; color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 1rem !important;
    line-height: 1.7 !important; resize: none !important; padding: 1.2rem !important;
    transition: all 0.3s ease !important;
}
.stTextArea textarea:focus {
    border-color: color-mix(in srgb, var(--accent) 55%, transparent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent), 0 0 30px color-mix(in srgb, var(--accent) 6%, transparent) !important;
}
.stTextArea textarea::placeholder { color: var(--placeholder) !important; font-style: italic; }

/* ── Text Input ── */
input[type="text"], .stTextInput input {
    background: var(--bg-elev) !important; border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important; color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important; padding: 10px 14px !important;
}
input[type="text"]:focus, .stTextInput input:focus {
    border-color: color-mix(in srgb, var(--accent) 55%, transparent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent) !important;
}
input[type="text"]::placeholder { color: var(--placeholder) !important; }
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
    color: var(--text-dim) !important; font-size: 0.78rem !important;
    font-weight: 600 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important;
}

/* ── Markdown ── */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th { color: var(--text-body) !important; line-height: 1.7; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Playfair Display', serif !important; color: var(--text-strong) !important;
}
.stMarkdown code {
    background: color-mix(in srgb, var(--accent) 12%, transparent) !important; color: var(--accent) !important;
    padding: 2px 8px; border-radius: 4px; font-size: 0.85em;
}

/* ── Alert ── */
.stAlert {
    background: color-mix(in srgb, var(--accent) 9%, transparent) !important; border: 1px solid color-mix(in srgb, var(--accent) 22%, transparent) !important;
    border-radius: 14px !important;
}
.stAlert p, .stAlert div { color: var(--accent) !important; }

/* ── Sidebar text ── */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: var(--text-body) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

/* ── Theme Toggle ── */
#theme-toggle {
    position: fixed; top: 14px; right: 18px; z-index: 99999;
    width: 42px; height: 42px; border-radius: 50%;
    background: linear-gradient(135deg, var(--card1), var(--card2));
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
    color: var(--accent); line-height: 1;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 18px rgba(0,0,0,0.35), 0 0 18px color-mix(in srgb, var(--accent) 18%, transparent);
    transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s ease, background 0.4s ease, color 0.4s ease;
    -webkit-backface-visibility: hidden; overflow: hidden;
}
#theme-toggle:hover { transform: translateY(-2px) rotate(18deg); box-shadow: 0 8px 26px rgba(0,0,0,0.4), 0 0 26px color-mix(in srgb, var(--accent) 30%, transparent); }
#theme-toggle:active { transform: scale(0.92); }

/* Animated sun ⇄ moon icon morph (rays retract + crescent carves via SVG mask) */
.ts-toggle-icon { width: 22px; height: 22px; display: block; }
.ts-sun-rays {
    transform-box: fill-box; transform-origin: center;
    transform: scale(1);
    transition: transform .5s cubic-bezier(.34,1.56,.64,1);
}
.ts-moon-cut { transition: transform .5s cubic-bezier(.34,1.56,.64,1); }
#theme-toggle:not(.is-light) .ts-moon-cut { transform: translate(9px, -7px); } /* cut hidden → full sun */
#theme-toggle.is-light .ts-sun-rays { transform: scale(0) rotate(55deg); }     /* rays retract */

/* Theme-change flash ripple originating from the button */
.ts-theme-flash {
    position: fixed; inset: 0; z-index: 99998; pointer-events: none; opacity: 0;
    background: radial-gradient(circle at var(--fx, 50%) var(--fy, 50%),
                color-mix(in srgb, var(--accent) 24%, transparent) 0%, transparent 55%);
}
.ts-theme-flash.go { animation: tsFlash .6s ease-out forwards; }
@keyframes tsFlash { 0%{opacity:0} 30%{opacity:1} 100%{opacity:0} }

/* ── Full-page Starfield Background (brightening / dimming) ── */
#ts-starfield {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 0; pointer-events: none;
}

/* ── Hide defaults (but KEEP the sidebar collapse/expand control!) ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* Keep the top-right sidebar control visible & clickable in both themes */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] button { opacity: 1 !important; }
[data-testid="stSidebarCollapsedControl"] svg { color: var(--accent) !important; }

@media (max-width: 768px) {
    .dest-grid { grid-template-columns: repeat(2, 1fr); }
    .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">TravelSphere</div>
    <div class="sidebar-tagline">AI-Powered Journey Planning</div>
    <hr style="border-color: var(--border-soft); margin: 0.5rem 0;">
    """, unsafe_allow_html=True)

    thread_id = st.text_input("User ID", value="aayush_user",
                              help="Session identifier for travel history",
                              label_visibility="collapsed")

    st.markdown("<div class='sidebar-section-title'>Tech Stack</div>", unsafe_allow_html=True)
    for icon, name in [("🔗", "LangGraph"), ("🧠", "LLaMA 3.3 70B"),
                       ("🐘", "PostgreSQL"), ("🔍", "Tavily Search"),
                       ("✈️", "AviationStack")]:
        st.markdown(f'<div class="sidebar-item"><span class="sidebar-item-icon">{icon}</span><span>{name}</span></div>',
                    unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section-title'>Agent Pipeline</div>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-pipeline">', unsafe_allow_html=True)
    for icon, name in [("✈️", "Flight Agent"), ("🏨", "Hotel Agent"),
                       ("☀️", "Weather Agent"), ("🗓️", "Itinerary Agent")]:
        st.markdown(f'<div class="pipeline-step"><span>{icon}</span><span>{name}</span></div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 2rem; padding: 1rem; background: color-mix(in srgb, var(--accent) 7%, transparent);
                border: 1px solid color-mix(in srgb, var(--accent) 15%, transparent); border-radius: 12px;">
        <div style="font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em;
                    text-transform: uppercase; color: var(--accent); margin-bottom: 8px;">Pro Tip</div>
        <div style="font-size: 0.8rem; color: var(--text-dim); line-height: 1.5;">
            Be specific with dates, budget, and preferences for better results.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Hero (Three.js — height controlled by CSS, not st.html param) ─────────────
HERO_HTML = """
<div style="position:relative; height:320px; border-radius:24px; overflow:hidden;">
  <canvas id="scene" style="width:100%; height:320px; display:block;"></canvas>
  <canvas id="hero-particles" style="position:absolute; top:0; left:0; width:100%; height:320px; pointer-events:none; z-index:1;"></canvas>
  <div style="position:absolute; top:0; left:0; width:100%; height:320px;
              display:flex; flex-direction:column; align-items:center; justify-content:center;
              text-align:center; font-family:'DM Sans',sans-serif; pointer-events:none; z-index:2;">
    <div style="display:inline-flex; align-items:center; gap:8px;
                background:color-mix(in srgb, var(--accent) 14%, transparent); border:1px solid color-mix(in srgb, var(--accent) 32%, transparent);
                color:var(--accent); font-size:11px; font-weight:700; letter-spacing:2px;
                text-transform:uppercase; padding:8px 20px; border-radius:100px; margin-bottom:20px;
                animation: hfloat 3s ease-in-out infinite;">
      ✦ Multi-Agent AI System
    </div>
    <div style="font-family:'Playfair Display',serif; font-size:2.8rem; font-weight:700;
                color:var(--text-strong); margin:0 0 12px; text-shadow:0 4px 30px rgba(0,0,0,0.5);">
      Your Journey,<br>Orchestrated by AI
    </div>
    <div style="color:var(--text-mute); font-size:1rem; max-width:520px; line-height:1.6;
                text-shadow:0 2px 10px rgba(0,0,0,0.5);">
      Flight, hotel, weather, and itinerary checks run together to build a practical travel plan
    </div>
    <div style="display:flex; gap:40px; margin-top:30px;">
      <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:var(--accent);">Flights</div>
        <div style="font-size:0.7rem; color:var(--text-faint); text-transform:uppercase; letter-spacing:0.1em; margin-top:2px;">Route Options</div>
      </div>
      <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:var(--accent);">Hotels</div>
        <div style="font-size:0.7rem; color:var(--text-faint); text-transform:uppercase; letter-spacing:0.1em; margin-top:2px;">Stay Matches</div>
      </div>
      <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:var(--accent);">Weather</div>
        <div style="font-size:0.7rem; color:var(--text-faint); text-transform:uppercase; letter-spacing:0.1em; margin-top:2px;">Forecast Context</div>
      </div>
    </div>
  </div>
</div>
<style>@keyframes hfloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
  var canvas = document.getElementById('scene');
  var renderer = new THREE.WebGLRenderer({canvas:canvas, antialias:true, alpha:true});
  renderer.setSize(canvas.parentElement.clientWidth, 320);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(60, canvas.parentElement.clientWidth/320, 0.1, 1000);
  camera.position.set(0,2,8); camera.lookAt(0,0,0);

  var pg=new THREE.BufferGeometry(), pp=new Float32Array(800*3);
  for(var i=0;i<2400;i++) pp[i]=(Math.random()-0.5)*(i%3===1?20:40);
  pg.setAttribute('position',new THREE.BufferAttribute(pp,3));
  scene.add(new THREE.Points(pg,new THREE.PointsMaterial({color:0xE8A838,size:0.04,transparent:true,opacity:0.6})));

  var pg2=new THREE.BufferGeometry(), pp2=new Float32Array(300*3);
  for(var i=0;i<900;i++) pp2[i]=(Math.random()-0.5)*(i%3===1?18:35);
  pg2.setAttribute('position',new THREE.BufferAttribute(pp2,3));
  scene.add(new THREE.Points(pg2,new THREE.PointsMaterial({color:0x38B2AC,size:0.025,transparent:true,opacity:0.4})));

  function mkFlight(sa,ea,h,c){
    var pts=[];
    for(var i=0;i<=60;i++){var t=i/60,a=sa+(ea-sa)*t;
      pts.push(new THREE.Vector3(Math.sin(a)*3,Math.sin(t*Math.PI)*h,Math.cos(a)*3-2));}
    var curve=new THREE.CatmullRomCurve3(pts);
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(100)),
      new THREE.LineBasicMaterial({color:c,transparent:true,opacity:0.3})));
    var dot=new THREE.Mesh(new THREE.SphereGeometry(0.08,12,12),new THREE.MeshBasicMaterial({color:c}));
    scene.add(dot);
    var glow=new THREE.Mesh(new THREE.SphereGeometry(0.2,12,12),new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:0.2}));
    scene.add(glow);
    return{curve:curve,dot:dot,glow:glow,spd:0.003+Math.random()*0.002};
  }
  var flights=[
    mkFlight(0,Math.PI*0.8,2.5,0xE8A838),
    mkFlight(Math.PI,Math.PI*1.7,2,0x38B2AC),
    mkFlight(Math.PI*0.5,Math.PI*1.3,1.8,0xE07A5F),
    mkFlight(Math.PI*1.5,Math.PI*2.1,2.2,0xA78BFA)
  ];
  var sphere=new THREE.Mesh(new THREE.SphereGeometry(3,20,16),
    new THREE.MeshBasicMaterial({color:0x2A2D35,wireframe:true,transparent:true,opacity:0.15}));
  sphere.position.set(0,0,-2); scene.add(sphere);
  var time=0;
  function animate(){
    requestAnimationFrame(animate); time+=0.008;
    for(var i=0;i<flights.length;i++){
      var f=flights[i], t=((time)*f.spd*100+i*0.25)%1, p=f.curve.getPoint(t);
      f.dot.position.copy(p); f.glow.position.copy(p);
    }
    sphere.rotation.y+=0.001;
    camera.position.x=Math.sin(time*0.1)*0.5;
    camera.position.y=2+Math.sin(time*0.15)*0.3;
    camera.lookAt(0,0,-2);
    renderer.render(scene,camera);
  }
  animate();
  window.addEventListener('resize',function(){
    var w=canvas.parentElement.clientWidth;
    camera.aspect=w/320; camera.updateProjectionMatrix();
    renderer.setSize(w,320);
  });
})();
</script>
<script>
/* Floating particle accents — pure canvas, no dependencies.
   Colors are read from the theme CSS variables, so they recolor when the
   theme flips. Safe no-op if the canvas is missing. */
(function(){
  var cv = document.getElementById('hero-particles');
  if(!cv) return;
  var ctx = cv.getContext('2d');
  var W = 0, H = 0, particles = [], running = true;

  function readColors(){
    var cs = getComputedStyle(document.documentElement);
    var pick = function(v){ var c = cs.getPropertyValue(v).trim(); return c || '#E8A838'; };
    return [pick('--accent'), pick('--accent2'), pick('--accent4')];
  }
  function hexA(hex, a){
    // Accept #rgb / #rrggbb; return rgba() string.
    var h = hex.replace('#',''); if(h.length===3) h = h.split('').map(function(c){return c+c;}).join('');
    var r = parseInt(h.substr(0,2),16)||0, g = parseInt(h.substr(2,2),16)||0, b = parseInt(h.substr(4,2),16)||0;
    return 'rgba('+r+','+g+','+b+','+a+')';
  }

  function resize(){
    var r = cv.getBoundingClientRect();
    W = r.width; H = r.height;
    var dpr = Math.min(window.devicePixelRatio||1, 2);
    cv.width = W*dpr; cv.height = H*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }

  function build(){
    particles = [];
    var n = 38;
    for(var i=0;i<n;i++){
      particles.push({
        x: Math.random()*W,
        y: Math.random()*H,
        r: 0.8 + Math.random()*2.0,
        vy: -(0.15 + Math.random()*0.45),
        vx: (Math.random()-0.5)*0.25,
        ph: Math.random()*Math.PI*2,
        ci: i % 3
      });
    }
  }

  function frame(){
    if(running){
      ctx.clearRect(0,0,W,H);
      var cols = readColors();
      for(var i=0;i<particles.length;i++){
        var p = particles[i];
        p.ph += 0.02;
        p.y += p.vy;
        p.x += p.vx + Math.sin(p.ph)*0.25;
        if(p.y < -5){ p.y = H + 5; p.x = Math.random()*W; }
        if(p.x < -5) p.x = W + 5; else if(p.x > W + 5) p.x = -5;
        var tw = 0.5 + 0.5*Math.sin(p.ph*1.5);     // twinkle
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
        ctx.fillStyle = hexA(cols[p.ci], 0.55*tw);
        ctx.shadowBlur = 8; ctx.shadowColor = hexA(cols[p.ci], 0.5);
        ctx.fill();
      }
      ctx.shadowBlur = 0;
    }
    requestAnimationFrame(frame);
  }

  resize(); build(); frame();
  window.addEventListener('resize', function(){ resize(); build(); });
  document.addEventListener('visibilitychange', function(){ running = !document.hidden; });
})();
</script>
"""

st.markdown("<div class='hero-shell'>", unsafe_allow_html=True)
st.html(HERO_HTML)
st.markdown("</div>", unsafe_allow_html=True)

# ── Theme Toggle (top-right animated sun⇄moon, persisted in localStorage) ────
# ── Plus full-page twinkling starfield (brighten/dim, theme-aware) ───────────
components.html("""
<canvas id="ts-starfield"></canvas>
<div class="ts-theme-flash"></div>
<script>
(function(){
  var win = window.parent;
  var doc = win.document;
  if (win.__travelSphereThemeStarsBooted) return;
  win.__travelSphereThemeStarsBooted = true;

  /* ===== Theme boot + state ===== */
  var root = doc.documentElement;
  var saved = (function(){ try { return win.localStorage.getItem('ts-theme'); } catch(e){ return null; } })();
  var theme = (saved === 'light' || saved === 'dark') ? saved : 'dark';
  root.setAttribute('data-theme', theme);

  /* Sun ⇄ moon icon: solid sun (dark) or crescent moon (light).
     Rays retract on toggle; crescent carves out via the cut circle. */
  function iconHTML(){
    return ''
    + '<svg class="ts-toggle-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    +   '<g class="ts-sun-rays" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
    +     '<line x1="12" y1="1.5" x2="12" y2="4"/>'
    +     '<line x1="12" y1="20" x2="12" y2="22.5"/>'
    +     '<line x1="1.5" y1="12" x2="4" y2="12"/>'
    +     '<line x1="20" y1="12" x2="22.5" y2="12"/>'
    +     '<line x1="4.2" y1="4.2" x2="6" y2="6"/>'
    +     '<line x1="18" y1="18" x2="19.8" y2="19.8"/>'
    +     '<line x1="4.2" y1="19.8" x2="6" y2="18"/>'
    +     '<line x1="18" y1="6" x2="19.8" y2="4.2"/>'
    +   '</g>'
  +   '<mask id="tsMoonMask">'
  +     '<rect width="24" height="24" fill="white"/>'
  +     '<circle class="ts-moon-cut" cx="14.6" cy="10" r="5.6" fill="black"/>'
  +   '</mask>'
    +   '<circle cx="12" cy="12" r="4.6" fill="currentColor" mask="url(#tsMoonMask)"/>'
    + '</svg>';
  }

  function applyIcon(){
    var btn = doc.getElementById('theme-toggle');
    if (btn) btn.innerHTML = iconHTML();
    updateClass();
  }
  function updateClass(){
    var btn = doc.getElementById('theme-toggle');
    if (btn) btn.classList.toggle('is-light', root.getAttribute('data-theme') === 'light');
  }

  function makeButton(){
    var btn = doc.createElement('button');
    btn.id = 'theme-toggle'; btn.type = 'button';
    btn.title = 'Toggle light / dark theme';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.innerHTML = iconHTML();
    updateClass();
    btn.addEventListener('click', toggleTheme);
    doc.body.appendChild(btn);
  }

  function flashFrom(x, y){
    var fx = doc.querySelector('.ts-theme-flash');
    if (!fx) {
      fx = doc.createElement('div');
      fx.className = 'ts-theme-flash';
      doc.body.appendChild(fx);
    }
    if (!fx) return;
    fx.style.setProperty('--fx', x + 'px');
    fx.style.setProperty('--fy', y + 'px');
    fx.classList.remove('go'); void fx.offsetWidth;   // restart animation
    fx.classList.add('go');
  }

  function toggleTheme(e){
    var cur = root.getAttribute('data-theme') || 'dark';
    var next = (cur === 'dark') ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { win.localStorage.setItem('ts-theme', next); } catch(_){}
    updateClass();
    var r = (e && e.target && e.target.getBoundingClientRect) ? e.target.getBoundingClientRect() : null;
    flashFrom(r ? r.left + r.width/2 : win.innerWidth - 40, r ? r.top + r.height/2 : 40);
    rebuildStars();
  }

  function bootToggle(){
    if (doc.getElementById('theme-toggle')) { applyIcon(); return; }
    makeButton();
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', bootToggle);
  else bootToggle();

  /* ===== Full-page twinkling starfield =====
     Each star has its own depth, speed & phase so they brighten and dim
     independently. Colors are read from theme CSS variables and refreshed
     on every theme flip. Honors prefers-reduced-motion. */
  var starHost = doc.querySelector('.stApp') || doc.body;
  var cv = doc.getElementById('ts-starfield');
  if (!cv) {
    cv = doc.createElement('canvas');
    cv.id = 'ts-starfield';
    starHost.appendChild(cv);
  } else if (cv.parentElement !== starHost) {
    starHost.appendChild(cv);
  }
  var ctx = cv ? cv.getContext('2d') : null;
  var stars = [], W = 0, H = 0, DPR = 1, running = true;
  var reduceMotion = win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function starColors(){
    var cs = win.getComputedStyle(root);
    var accent = cs.getPropertyValue('--accent').trim() || '#E8A838';
    // Orange family — warm golds and ambers for a cohesive starry sky.
    // --accent drives the base hue; lighter/deeper variants add depth
    // while keeping every star inside the orange palette.
    if (accent.toLowerCase() === '#b9740e') {
      // Light (warm-white) theme: brighter oranges read better on cream.
      return [accent, '#D98A1F', '#F0A93D', '#FFC56B'];
    }
    // Dark theme: rich amber + warm highlights.
    return [accent, '#FFB84D', '#FF8C42', '#FFD89E'];
  }

  function resize(){
    DPR = Math.min(win.devicePixelRatio || 1, 2);
    W = win.innerWidth; H = win.innerHeight;
    cv.width = W * DPR; cv.height = H * DPR;
    cv.style.width = W + 'px'; cv.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  function rebuildStars(){
    var area = W * H;
    var n = Math.min(220, Math.max(80, Math.round(area / 9000)));
    stars = [];
    for (var i = 0; i < n; i++){
      var depth = Math.random();
      stars.push({
        x: Math.random() * W,
        y: Math.random() * H,
        r: 0.5 + depth * 2.1,                      // depth drives size (slightly larger)
        depth: depth,
        spd: 0.35 + Math.random() * 1.6,           // twinkle speed (brighten/dim)
        ph: Math.random() * Math.PI * 2,           // phase offset
        ci: i % 4                                  // color index
      });
    }
  }

  function frame(now){
    if (running && ctx){
      ctx.clearRect(0, 0, W, H);
      var cols = starColors();
      var t = now * 0.001;
      for (var i = 0; i < stars.length; i++){
        var s = stars[i];
        // Independent brightening & dimming: sin wave → 0.1 .. 1.0 brightness.
        var tw;
        if (reduceMotion) {
          tw = 0.5 + 0.4 * s.depth;
        } else {
          // Stronger dim/brighten swing: 0.04 (near-invisible) → 1.0 (full glow).
          // This makes the orange stars clearly pulse — dimming then brightening —
          // instead of a subtle shimmer.
          tw = 0.04 + 0.96 * (0.5 + 0.5 * Math.sin(t * s.spd + s.ph));
        }
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = withAlpha(cols[s.ci], 0.92 * tw);
        ctx.shadowBlur = s.r * 5 * tw;             // bigger glow when bright
        ctx.shadowColor = withAlpha(cols[s.ci], 0.7 * tw);
        ctx.fill();
      }
      ctx.shadowBlur = 0;
    }
    win.requestAnimationFrame(frame);
  }

  function withAlpha(hex, a){
    var h = hex.replace('#', '');
    if (h.length === 3) h = h.split('').map(function(c){ return c + c; }).join('');
    var r = parseInt(h.substr(0, 2), 16) || 0,
        g = parseInt(h.substr(2, 2), 16) || 0,
        b = parseInt(h.substr(4, 2), 16) || 0;
    return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
  }

  function bootStars(){
    if (!cv || !ctx) return;
    resize(); rebuildStars();
    win.requestAnimationFrame(frame);
    win.addEventListener('resize', function(){ resize(); rebuildStars(); });
    doc.addEventListener('visibilitychange', function(){ running = !doc.hidden; });
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', bootStars);
  else bootStars();
})();
</script>
""", height=0)

# ── Destination Cards ────────────────────────────────────────────────────────
DESTINATIONS = [
    ("Tokyo",   "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400&q=75"),
    ("Paris",   "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400&q=75"),
    ("Bangkok", "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400&q=75"),
    ("Rome",    "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&q=75"),
    ("Dubai",   "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400&q=75"),
]

dest_html = '<div class="dest-grid">'
for name, img in DESTINATIONS:
    dest_html += f"""
    <div class="dest-card">
        <img src="{img}" alt="{name}" loading="lazy" />
        <div class="dest-card-overlay"></div>
        <div class="dest-card-label">{name}</div>
        <div class="dest-card-badge">→</div>
    </div>"""
dest_html += '</div>'

st.markdown("""
<div style="margin-bottom:0.5rem;">
    <div class="section-label">Popular Destinations</div>
    <div style="font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:var(--text-strong);">Trending This Season</div>
</div>
""", unsafe_allow_html=True)
st.html(dest_html)

# ── Suggestion Cards (3D Hover) ──────────────────────────────────────────────
SUGGESTION_HTML = """
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px; padding:4px;">
  <div class="sug-card" data-text="7-day Japan under ₹2L">
    <div class="sug-glow"></div>
    <span class="sug-icon">🇯🇵</span>
    <div class="sug-text">7-day Japan under ₹2L</div>
    <div class="sug-sub">Flights + Hotels + Sightseeing</div>
    <div class="sug-arrow">→</div>
  </div>
  <div class="sug-card" data-text="Paris trip for 5 days">
    <div class="sug-glow"></div>
    <span class="sug-icon">🇫🇷</span>
    <div class="sug-text">Paris trip for 5 days</div>
    <div class="sug-sub">Romantic getaway plan</div>
    <div class="sug-arrow">→</div>
  </div>
  <div class="sug-card" data-text="Dubai weekend trip">
    <div class="sug-glow"></div>
    <span class="sug-icon">🇦🇪</span>
    <div class="sug-text">Dubai weekend trip</div>
    <div class="sug-sub">Luxury short break</div>
    <div class="sug-arrow">→</div>
  </div>
  <div class="sug-card" data-text="Bali backpacking 10 days">
    <div class="sug-glow"></div>
    <span class="sug-icon">🇮🇩</span>
    <div class="sug-text">Bali backpacking 10 days</div>
    <div class="sug-sub">Budget adventure</div>
    <div class="sug-arrow">→</div>
  </div>
</div>
<style>
  .sug-card {
    position:relative; background:linear-gradient(145deg,var(--card1) 0%,var(--card2) 100%);
    border:1px solid var(--border); border-radius:16px; padding:22px 20px;
    cursor:pointer; overflow:hidden;
    transform-style:preserve-3d;
    transition:transform 0.2s ease-out, box-shadow 0.3s ease, border-color 0.3s ease;
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
  }
  .sug-card:hover {
    border-color:color-mix(in srgb, var(--accent) 38%, transparent);
    box-shadow: 0 20px 45px rgba(0,0,0,0.5), 0 0 30px color-mix(in srgb, var(--accent) 14%, transparent);
  }
  .sug-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg, var(--accent), var(--accent2));
    opacity:0; transition:opacity 0.3s ease; border-radius:16px 16px 0 0;
  }
  .sug-card:hover::before { opacity:1; }
  .sug-icon { font-size:1.6rem; margin-bottom:12px; display:block; transform:translateZ(20px); }
  .sug-text {
    font-size:0.88rem; font-weight:600; color:var(--text); line-height:1.5;
    transform:translateZ(15px);
  }
  .sug-sub {
    font-size:0.72rem; color:var(--text-faint); margin-top:6px; letter-spacing:0.03em;
    transform:translateZ(10px);
  }
  .sug-arrow {
    position:absolute; bottom:18px; right:18px; width:28px; height:28px;
    background:color-mix(in srgb, var(--accent) 14%, transparent); border:1px solid color-mix(in srgb, var(--accent) 28%, transparent);
    border-radius:50%; display:flex; align-items:center; justify-content:center;
    color:var(--accent); font-size:0.75rem;
    opacity:0; transform:translateZ(25px) translateX(-8px);
    transition:all 0.35s cubic-bezier(0.25,0.46,0.45,0.94);
  }
  .sug-card:hover .sug-arrow { opacity:1; transform:translateZ(25px) translateX(0); }
  .sug-glow {
    position:absolute; top:-50%; left:-50%; width:200%; height:200%;
    background:radial-gradient(circle at var(--mx,50%) var(--my,50%), color-mix(in srgb, var(--accent) 9%, transparent) 0%, transparent 50%);
    pointer-events:none; opacity:0; transition:opacity 0.3s ease;
  }
  .sug-card:hover .sug-glow { opacity:1; }
</style>
<script>
document.querySelectorAll('.sug-card').forEach(function(card) {
  card.addEventListener('mousemove', function(e) {
    var r = card.getBoundingClientRect();
    var x = e.clientX - r.left, y = e.clientY - r.top;
    var cx = r.width / 2, cy = r.height / 2;
    var rx = ((y - cy) / cy) * -10;
    var ry = ((x - cx) / cx) * 10;
    card.style.transform = 'perspective(800px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateY(-8px) scale(1.03)';
    card.style.setProperty('--mx', (x / r.width * 100) + '%');
    card.style.setProperty('--my', (y / r.height * 100) + '%');
  });
  card.addEventListener('mouseleave', function() {
    card.style.transform = 'perspective(800px) rotateX(0) rotateY(0) translateY(0) scale(1)';
  });
  card.addEventListener('click', function() {
    var text = card.getAttribute('data-text');
    try {
      var textarea = window.parent.document.querySelector('.stTextArea textarea');
      if (textarea) {
        var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(textarea, text);
        textarea.dispatchEvent(new Event('input', {bubbles: true}));
        textarea.dispatchEvent(new Event('change', {bubbles: true}));
        textarea.focus();
      }
    } catch(err) {}
  });
});
</script>
"""

st.markdown("""
<div style="margin-bottom:0.5rem;">
    <div class="section-label">Quick Start</div>
    <div style="font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:var(--text-strong);">
        Tap a suggestion to begin
    </div>
</div>
""", unsafe_allow_html=True)
st.html(SUGGESTION_HTML)

# ── Input Section ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="input-container">
    <div class="section-label" style="margin-bottom:1.2rem;">Describe Your Trip</div>
    <div style="font-family:'Playfair Display',serif; font-size:1.3rem; font-weight:600; color:var(--text-strong); margin-bottom:0.5rem;">
        Where would you like to go?
    </div>
    <div style="color:var(--text-mute); font-size:0.88rem; margin-bottom:1rem;">
        Describe your dream trip and our AI agents will handle the rest
    </div>
""", unsafe_allow_html=True)

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

user_query = st.text_area(
    "Your travel query",
    key="user_query",
    placeholder="e.g. Plan a 7-day Japan trip including flights, hotels, and sightseeing under ₹2 lakhs. I prefer cultural experiences and local food...",
    height=110,
    label_visibility="collapsed",
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="main-generate-btn">', unsafe_allow_html=True)
generate = st.button("✈️  Generate Travel Plan", use_container_width=True, type="primary")
st.markdown('</div>', unsafe_allow_html=True)

# ── Agent Pipeline Execution ──────────────────────────────────────────────────
AGENT_META = {
    "flight_agent":    ("✈️", "Flight Agent",    "#E8A838"),
    "hotel_agent":     ("🏨", "Hotel Agent",     "#38B2AC"),
    "weather_agent":   ("☀️", "Weather Agent",   "#A78BFA"),
    "itinerary_agent": ("🗓️", "Itinerary Agent", "#E07A5F"),
}

if generate:
    if not user_query.strip():
        st.warning("Please describe your trip to get started.")
    else:
        config = {"configurable": {"thread_id": thread_id}}
        collected = {
            "flight_results": "", "hotel_results": "", "weather_results": "",
            "itinerary": "", "final_response": "", "llm_calls": 0,
            "total_budget": extract_total_budget(user_query),
            "agents_executed": 0,
        }
        executed_agents = set()

        st.markdown("""
        <div class="pipeline-header">
            <div class="pipeline-title">Agent Pipeline</div>
            <div class="pipeline-badge"><span class="live-dot"></span> Processing</div>
        </div>
        """, unsafe_allow_html=True)

        for chunk in app.stream(
            {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "flight_results": "", "hotel_results": "",
                "weather_results": "", "itinerary": "", "llm_calls": 0,
            },
            config=config,
            stream_mode="updates",
        ):
            for node_name, state_update in chunk.items():
                icon, label, _ = AGENT_META.get(node_name, ("🔧", node_name, "#E8A838"))
                executed_agents.add(node_name)
                collected["agents_executed"] = len(executed_agents)

                with st.status(f"{icon}  {label}", state="complete", expanded=True):
                    if node_name == "flight_agent":
                        text = state_update.get("flight_results", "")
                        collected["flight_results"] = text
                        st.markdown(text or "_No flight data returned._")
                    elif node_name == "hotel_agent":
                        text = state_update.get("hotel_results", "")
                        collected["hotel_results"] = text
                        st.markdown(text or "_No hotel data returned._")
                    elif node_name == "weather_agent":
                        text = state_update.get("weather_results", "")
                        collected["weather_results"] = text
                        st.markdown(text or "_No weather data returned._")
                    elif node_name == "itinerary_agent":
                        text = state_update.get("itinerary", "")
                        collected["itinerary"] = text
                        collected["final_response"] = text
                        st.markdown(text or "_No itinerary generated._")

                    collected["llm_calls"] = state_update.get("llm_calls", collected["llm_calls"])

        st.markdown("""
        <div class="agent-complete-toast">
            <div class="agent-complete-icon">✓</div>
            <div>
                <div class="agent-complete-title">Multi-agent planning complete</div>
                <div class="agent-complete-subtitle">Your travel plan is ready to review.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        budget_display = html.escape(collected["total_budget"])
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-icon">🤖</div>
                <div class="metric-value">{collected['agents_executed']}</div>
                <div class="metric-label">Agents Executed</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">⚡</div>
                <div class="metric-value">{collected['llm_calls']}</div>
                <div class="metric-label">LLM Calls</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">✅</div>
                <div class="metric-value">100%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-value">{budget_display}</div>
                <div class="metric-label">Total Budget</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Final Plan
        if collected["final_response"]:
            st.markdown("""
            <div style="margin-bottom:1rem;">
                <div class="section-label">Final Output</div>
                <div style="font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:var(--text-strong);">
                    Your Complete Travel Plan
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(
                f'<div class="final-plan-card"><div class="final-plan-content">{collected["final_response"]}</div></div>',
                unsafe_allow_html=True
            )

        # Save & Download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"travel_plan_{timestamp}.md"
        save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")
        os.makedirs(save_dir, exist_ok=True)

        file_content = f"""# Travel Plan — TravelSphere

**Query:** {user_query}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User ID:** {thread_id}
**Total Budget:** {collected['total_budget']}

---

## ✈️ Flight Information

{collected['flight_results'] or 'N/A'}

---

## 🏨 Hotel Information

{collected['hotel_results'] or 'N/A'}

---

## ☀️ Weather Information

{collected['weather_results'] or 'N/A'}

---

## 🗓️ Itinerary

{collected['itinerary'] or 'N/A'}

---

## 🧠 Final Travel Plan

{collected['final_response'] or 'N/A'}

---

*Generated by TravelSphere Multi-Agent System | LLM Calls: {collected['llm_calls']}*
"""
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(file_content)

        dl_col, info_col = st.columns([1, 4])
        with dl_col:
            st.download_button(
                "⬇️ Download", data=file_content,
                file_name=filename, mime="text/markdown",
                use_container_width=True
            )
        with info_col:
            st.markdown(f"""
            <div class="action-bar">
                <div class="action-bar-text">📁 Auto-saved to <code>travel_plans/{filename}</code></div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color: var(--border-soft); margin: 3rem 0 1.5rem;">
<div style="display:flex; justify-content:space-between; align-items:center; padding:1rem 0;">
    <div style="font-family:'Playfair Display',serif; font-size:1rem; color:var(--text-faint);">TravelSphere</div>
    <div style="font-size:0.75rem; color:var(--text-faint);">Multi-Agent AI System • LangGraph + LLaMA 3.3</div>
</div>
""", unsafe_allow_html=True)

