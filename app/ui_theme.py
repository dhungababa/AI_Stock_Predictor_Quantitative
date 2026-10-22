"""
ui_theme.py — Shared Futuristic Dark Glassmorphism Theme for FinTech Projects
Provides CSS animations, glassmorphism cards, gradient headers, and neon alerts.
"""
import streamlit as st

# ============================================================
# MASTER CSS — Dark Glassmorphism + Animations
# ============================================================
MASTER_CSS = """
<style>
    /* ===== GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ===== ANIMATED PARTICLE BACKGROUND ===== */
    @keyframes float-particle-1 {
        0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
        25% { transform: translate(100px, -50px) scale(1.2); opacity: 0.5; }
        50% { transform: translate(200px, 20px) scale(0.8); opacity: 0.2; }
        75% { transform: translate(50px, 80px) scale(1.1); opacity: 0.4; }
    }
    @keyframes float-particle-2 {
        0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.2; }
        33% { transform: translate(-80px, 60px) scale(1.3); opacity: 0.4; }
        66% { transform: translate(60px, -90px) scale(0.7); opacity: 0.3; }
    }
    @keyframes float-particle-3 {
        0%, 100% { transform: translate(0, 0); opacity: 0.15; }
        50% { transform: translate(-120px, -40px); opacity: 0.35; }
    }
    @keyframes glow-pulse {
        0%, 100% { box-shadow: 0 0 15px rgba(0, 212, 255, 0.15); }
        50% { box-shadow: 0 0 30px rgba(0, 212, 255, 0.3), 0 0 60px rgba(0, 212, 255, 0.1); }
    }
    @keyframes breathing-glow {
        0%, 100% { box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.5); border-top: 1px solid rgba(255,255,255,0.1); }
        50% { box-shadow: 0 4px 30px -2px rgba(0, 212, 255, 0.15); border-top: 1px solid rgba(0, 212, 255, 0.25); }
    }
    @keyframes scan-line {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fade-in-up {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
        70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(0, 208, 132, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 208, 132, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 208, 132, 0); }
    }
    @keyframes neon-border {
        0%, 100% { border-color: rgba(0, 212, 255, 0.3); }
        50% { border-color: rgba(0, 212, 255, 0.7); }
    }
    @keyframes typing-cursor {
        0%, 100% { border-right-color: transparent; }
        50% { border-right-color: #00d4ff; }
    }
    @keyframes slide-in-right {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* ===== GLOBAL APP BACKGROUND ===== */
    [data-testid="stAppViewContainer"], .stApp {
        background: #0a0e27 !important;
        background-image:
            radial-gradient(circle at 15% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 85% 60%, rgba(0, 212, 255, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 50% 90%, rgba(0, 208, 132, 0.04) 0%, transparent 50%) !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stHeader"] {
        background: rgba(10, 14, 39, 0.8) !important;
        backdrop-filter: blur(10px) !important;
    }
    /* Hide default streamlit chrome */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    /* ===== TYPOGRAPHY ===== */
    h1 {
        background: linear-gradient(135deg, #00d4ff, #8b5cf6, #00d084) !important;
        background-size: 200% 200% !important;
        animation: gradient-shift 4s ease infinite !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        font-family: 'Inter', sans-serif !important;
        text-align: center !important;
    }
    h2, h3, h4, h5 {
        font-family: 'Inter', sans-serif !important;
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }
    p, span, label, li {
        color: #cbd5e1 !important;
        font-family: 'Inter', sans-serif !important;
    }
    a { color: #00d4ff !important; }

    /* ===== SIDEBAR DARK GLASS ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1130 0%, #0a0e27 100%) !important;
        border-right: 1px solid rgba(0, 212, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
        color: #00d4ff !important;
        -webkit-text-fill-color: #00d4ff !important;
        background: none !important;
        font-size: 16px !important;
    }

    /* ===== GLASSMORPHISM METRIC CARDS ===== */
    .glass-metric {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-top: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 28px 22px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: breathing-glow 3s ease-in-out infinite, fade-in-up 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    .glass-metric::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.4s;
    }
    .glass-metric:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 40px -4px rgba(0, 212, 255, 0.2);
        border-top: 1px solid rgba(0, 212, 255, 0.4);
    }
    .glass-metric:hover::before { opacity: 1; }
    .glass-metric .metric-value {
        font-size: 34px;
        background: linear-gradient(135deg, #00d4ff, #00d084);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 6px;
    }
    .glass-metric .metric-label {
        font-size: 12px;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }

    /* ===== AI GLASS CONTENT BOX ===== */
    .ai-glass-box {
        padding: 26px;
        background: rgba(15, 23, 42, 0.5);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-left: 4px solid #8b5cf6;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.08);
        transition: all 0.35s ease;
        animation: fade-in-up 0.5s ease-out;
    }
    .ai-glass-box:hover {
        box-shadow: 0 0 35px rgba(139, 92, 246, 0.2);
        border-color: rgba(139, 92, 246, 0.4);
    }

    /* ===== NEON ALERT BOXES ===== */
    .neon-alert-danger {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-left: 4px solid #ef4444;
        color: #fca5a5 !important;
        padding: 18px 22px;
        border-radius: 12px;
        font-weight: 600;
        animation: pulse-red 2s infinite;
        margin-bottom: 16px;
    }
    .neon-alert-success {
        background: rgba(0, 208, 132, 0.06);
        border: 1px solid rgba(0, 208, 132, 0.3);
        border-left: 4px solid #00d084;
        color: #6ee7b7 !important;
        padding: 18px 22px;
        border-radius: 12px;
        font-weight: 600;
        animation: pulse-green 2.5s infinite;
        margin-bottom: 16px;
    }
    .neon-alert-warning {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-left: 4px solid #f59e0b;
        color: #fcd34d !important;
        padding: 18px 22px;
        border-radius: 12px;
        font-weight: 600;
        margin-bottom: 16px;
    }
    .neon-alert-info {
        background: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-left: 4px solid #00d4ff;
        color: #7dd3fc !important;
        padding: 18px 22px;
        border-radius: 12px;
        font-weight: 600;
        margin-bottom: 16px;
    }

    /* ===== TERMINAL BOX ===== */
    .cyber-terminal {
        background: rgba(0, 10, 20, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-left: 4px solid #00d4ff;
        padding: 20px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        color: #4ade80 !important;
        border-radius: 10px;
        white-space: pre-wrap;
        font-size: 13px;
        line-height: 1.7;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.3);
    }
    .cyber-terminal * { color: #4ade80 !important; font-family: 'JetBrains Mono', monospace !important; }

    /* ===== CONTROL PANEL ===== */
    .glass-panel {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    /* ===== BUTTONS ===== */
    .stButton>button {
        width: 100%;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(139, 92, 246, 0.15)) !important;
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        padding: 12px 20px !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        font-size: 13px !important;
    }
    .stButton>button * { color: #e2e8f0 !important; }
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.3), rgba(139, 92, 246, 0.3)) !important;
        border-color: rgba(0, 212, 255, 0.6) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2) !important;
        transform: translateY(-2px) !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px 10px 0 0 !important;
        color: #94a3b8 !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 212, 255, 0.08) !important;
        border-color: rgba(0, 212, 255, 0.3) !important;
        border-bottom-color: transparent !important;
        border-top: 3px solid #00d4ff !important;
        color: #00d4ff !important;
        box-shadow: 0 -4px 15px rgba(0, 212, 255, 0.1) !important;
    }

    /* ===== INPUTS & CHAT INPUT ===== */
    .stTextInput>div>div>input, .stSelectbox>div>div>div,
    .stMultiSelect>div>div>div, .stTextArea>div>div>textarea,
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus,
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(0, 212, 255, 0.6) !important;
        box-shadow: 0 0 12px rgba(0, 212, 255, 0.2) !important;
    }
    /* Fix chat input text color */
    [data-testid="stChatInputTextArea"] {
        background: transparent !important;
        color: #e2e8f0 !important;
    }

    /* ===== CHAT MESSAGES ===== */
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        backdrop-filter: blur(10px) !important;
        animation: fade-in-up 0.4s ease-out !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 2px dashed rgba(0, 212, 255, 0.3) !important;
        border-radius: 14px !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(0, 212, 255, 0.6) !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.15) !important;
        background: rgba(15, 23, 42, 0.8) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: transparent !important;
    }
    [data-testid="stFileUploaderDropzone"] div, 
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small {
        color: #e2e8f0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: rgba(0, 212, 255, 0.1) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
    }

    /* ===== DATAFRAME ===== */
    .stDataFrame { border-radius: 12px; overflow: hidden; }

    /* ===== DIVIDER ===== */
    hr { border-color: rgba(255, 255, 255, 0.06) !important; }

    /* ===== RADIO BUTTONS ===== */
    .stRadio > div { gap: 8px; }
    .stRadio label {
        background: rgba(15, 23, 42, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease !important;
    }
</style>
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def inject_theme():
    """Inject the complete dark glassmorphism theme into the Streamlit app."""
    st.markdown(MASTER_CSS, unsafe_allow_html=True)


def gradient_header(title: str, subtitle: str = ""):
    """Render a gradient-animated title with optional subtitle."""
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f"<p style='text-align: center; color: #64748b !important; font-size: 16px; "
            f"font-weight: 500; letter-spacing: 0.5px; margin-top: -10px;'>{subtitle}</p>",
            unsafe_allow_html=True
        )


def glass_metric(value: str, label: str, icon: str = ""):
    """Render a single glassmorphism metric card with breathing glow."""
    icon_html = f"<div style='font-size: 28px; margin-bottom: 8px;'>{icon}</div>" if icon else ""
    st.markdown(f"""
    <div class="glass-metric">
        {icon_html}
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def glass_metric_row(metrics: list):
    """Render a row of glassmorphism metrics. Each item: (value, label, icon)."""
    cols = st.columns(len(metrics))
    for col, (value, label, icon) in zip(cols, metrics):
        with col:
            glass_metric(value, label, icon)


def ai_box(content: str, border_color: str = "#8b5cf6"):
    """Render an AI-styled glassmorphism content box."""
    st.markdown(f"""
    <div class="ai-glass-box" style="border-left-color: {border_color};">
        {content}
    </div>
    """, unsafe_allow_html=True)


def cyber_terminal(content: str, title: str = "SYSTEM OUTPUT"):
    """Render a cyberpunk-style terminal output box."""
    st.markdown(f"""
    <div class="cyber-terminal">
<span style="color: #00d4ff !important; font-weight: 700;">▶ {title}</span>
────────────────────────────────────────
{content}
    </div>
    """, unsafe_allow_html=True)


def neon_alert(message: str, alert_type: str = "info"):
    """Render a neon-glow alert box. Types: danger, success, warning, info."""
    icons = {"danger": "", "success": "", "warning": "", "info": "ℹ"}
    icon = icons.get(alert_type, "ℹ")
    st.markdown(f"""
    <div class="neon-alert-{alert_type}">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def glass_panel(title: str):
    """Render a glass panel header card."""
    st.markdown(f"""
    <div class="glass-panel">
        <h4 style="color: #00d4ff !important; margin: 0; font-weight: 700;
            letter-spacing: 1px; text-transform: uppercase; font-size: 14px;">
            [ {title} ]
        </h4>
    </div>
    """, unsafe_allow_html=True)


def section_divider():
    """Render a subtle neon divider."""
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent,
        rgba(0, 212, 255, 0.3), rgba(139, 92, 246, 0.3), transparent);
        margin: 30px 0;"></div>
    """, unsafe_allow_html=True)


# ============================================================
# PLOTLY DARK THEME
# ============================================================
PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor='rgba(10, 14, 39, 0.0)',
    plot_bgcolor='rgba(10, 14, 39, 0.3)',
    font=dict(family='Inter', color='#94a3b8'),
    xaxis=dict(
        gridcolor='rgba(255,255,255,0.04)',
        zerolinecolor='rgba(255,255,255,0.06)',
        tickfont=dict(color='#64748b')
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.04)',
        zerolinecolor='rgba(255,255,255,0.06)',
        tickfont=dict(color='#64748b')
    ),
    legend=dict(font=dict(color='#94a3b8')),
    hoverlabel=dict(
        bgcolor='rgba(15, 23, 42, 0.9)',
        bordercolor='rgba(0, 212, 255, 0.3)',
        font=dict(color='#e2e8f0', family='Inter')
    ),
    margin=dict(l=40, r=40, t=40, b=40),
)

def apply_plotly_dark(fig):
    """Apply the dark neon theme to any Plotly figure."""
    fig.update_layout(**PLOTLY_DARK_LAYOUT)
    return fig
