"""
utils.py
Shared helpers: room code generation, avatars, theme-aware CSS (covering
every native Streamlit widget, not just custom divs), animation helpers
(confetti, toasts), a non-overlapping Web Audio sound/music engine, and a
tiny best-effort activity logger used by the Admin Panel.
"""

import json
import os
import random
import string
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components

AVATARS = ["🦁", "🐯", "🐺", "🦊", "🐻", "🦅", "🐉", "🦂",
           "🦉", "🐍", "🦄", "🐲", "🦈", "🐊", "🦇", "🦚"]

ROLE_EMOJI = {
    "Badshah": "👑",
    "Wazeer": "🧙",
    "Sipahi": "🛡️",
    "Chor": "🗡️",
}

ROLE_COLOR = {
    "Badshah": "#E0A800",
    "Wazeer": "#7C5CFF",
    "Sipahi": "#0EA5E9",
    "Chor": "#E11D48",
}

LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "activity_log.json")


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def generate_room_code(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


# ==================================================================== #
# THEME — every colour a component could need, tuned for AA contrast
# in BOTH modes. This is what actually fixes the light-theme bug: the
# project's .streamlit/config.toml pins base="dark" with a fixed white
# textColor, so native widgets (labels, inputs, tabs, alerts, tables)
# stay white-on-white in light mode unless we override every one of
# them explicitly below, by data-testid, with !important.
# ==================================================================== #
THEMES = {
    "dark": dict(
        bg="linear-gradient(135deg,#0f0c29,#302b63,#24243e)",
        card="rgba(255,255,255,0.06)",
        card_solid="#1c1836",
        text="#F5F3FF",
        subtext="#B9B4D6",
        border="rgba(255,255,255,0.14)",
        accent="#FFD700",
        accent2="#7C5CFF",
        input_bg="rgba(255,255,255,0.07)",
        shadow="rgba(0,0,0,0.35)",
        success="#22C55E",
        error="#F43F5E",
        warn="#FBBF24",
        info="#38BDF8",
    ),
    "light": dict(
        bg="linear-gradient(135deg,#F5F3FF,#EDE9FE,#F8FAFC)",
        card="rgba(255,255,255,0.88)",
        card_solid="#FFFFFF",
        text="#1E1B33",
        subtext="#4B4768",
        border="rgba(30,27,51,0.14)",
        accent="#8B5CF6",
        accent2="#0EA5E9",
        input_bg="#FFFFFF",
        shadow="rgba(30,27,51,0.14)",
        success="#15803D",
        error="#BE123C",
        warn="#B45309",
        info="#0369A1",
    ),
}


def inject_base_css(theme: str = "dark"):
    """Injects the full premium look & feel AND forces every native
    Streamlit widget to respect the chosen theme (fixes light-mode
    contrast for text, buttons, inputs, tabs, tables, alerts, etc)."""

    t = THEMES.get(theme, THEMES["dark"])

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Poppins:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}

        .stApp {{ background: {t['bg']}; color: {t['text']}; }}
        #MainMenu, footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
            box-shadow: none !important;
        }}
        /* Keep the mobile sidebar-open arrow visible & theme-coloured —
           it lives inside the header, so fully hiding header (like the
           previous version did) hid this button on phones too. */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{
            visibility: visible !important;
            display: flex !important;
            z-index: 999999 !important;
        }}
        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg {{
            fill: {t['text']} !important;
        }}
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {{
            background: {t['card_solid']} !important;
            border-radius: 8px !important;
        }}

        /* ---------- Force theme on every native widget ---------- */
        .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
        [data-testid="stMarkdownContainer"] * ,
        [data-testid="stWidgetLabel"] * ,
        [data-testid="stCaptionContainer"] * ,
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
        [data-testid="stExpander"] summary,
        [data-testid="stTabs"] button p {{
            color: {t['text']} !important;
        }}
        .stCaption, [data-testid="stCaptionContainer"] {{ color: {t['subtext']} !important; }}

        section[data-testid="stSidebar"] {{
            background: {t['card_solid']} !important;
            border-right: 1px solid {t['border']};
        }}
        section[data-testid="stSidebar"] * {{ color: {t['text']} !important; }}

        /* text / number / textarea inputs */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        .stDateInput input, .stTimeInput input {{
            background: {t['input_bg']} !important;
            color: {t['text']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 10px !important;
        }}
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
            color: {t['subtext']} !important;
            opacity: 0.8;
        }}

        /* selectbox / multiselect */
        [data-baseweb="select"] > div {{
            background: {t['input_bg']} !important;
            border-color: {t['border']} !important;
            color: {t['text']} !important;
        }}
        [data-baseweb="select"] input {{ color: {t['text']} !important; }}
        [data-baseweb="popover"] li, [role="listbox"] li {{
            background: {t['card_solid']} !important;
            color: {t['text']} !important;
        }}

        /* radio / checkbox / toggle */
        .stRadio label, .stCheckbox label, .stToggle label {{ color: {t['text']} !important; }}
        [data-testid="stWidgetLabel"] p {{ color: {t['text']} !important; font-weight: 600; }}

        /* slider */
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"] {{ color: {t['subtext']} !important; }}
        [data-testid="stThumbValue"] {{ color: {t['accent2']} !important; }}

        /* tabs */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap: 6px; border-bottom: 1px solid {t['border']};
        }}
        [data-testid="stTabs"] button {{
            background: transparent !important;
            border-radius: 10px 10px 0 0 !important;
        }}
        [data-testid="stTabs"] button[aria-selected="true"] {{
            background: {t['card']} !important;
            border-bottom: 3px solid {t['accent2']} !important;
        }}

        /* expander */
        [data-testid="stExpander"] {{
            background: {t['card']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 14px !important;
        }}

        /* dataframe / table */
        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            background: {t['card_solid']} !important;
            border-radius: 12px !important;
            border: 1px solid {t['border']} !important;
        }}
        [data-testid="stDataFrame"] * {{ color: {t['text']} !important; }}

        /* alerts (st.success / error / info / warning) */
        [data-testid="stAlert"] {{ border-radius: 12px !important; border: 1px solid transparent !important; }}
        [data-testid="stAlertContentSuccess"] {{ color: {t['success']} !important; }}
        [data-testid="stAlertContentError"] {{ color: {t['error']} !important; }}
        [data-testid="stAlertContentInfo"] {{ color: {t['info']} !important; }}
        [data-testid="stAlertContentWarning"] {{ color: {t['warn']} !important; }}

        /* progress bar */
        [data-testid="stProgress"] > div > div {{ background: {t['accent2']} !important; }}

        /* ---------- Custom components ---------- */
        .bkwk-title {{
            font-family: 'Cinzel', serif;
            font-size: 2.6rem;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(90deg,#E0A800,#DB2777,#7C5CFF,#0EA5E9);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 6s ease infinite;
            margin-bottom: 0;
        }}
        .bkwk-subtitle {{
            text-align: center; color: {t['subtext']} !important;
            font-size: 1.05rem; margin-top: -6px; margin-bottom: 22px; letter-spacing: 0.5px;
        }}
        @keyframes shimmer {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}

        .glass-card {{
            background: {t['card']};
            border: 1px solid {t['border']};
            border-radius: 20px;
            padding: 26px 28px;
            backdrop-filter: blur(14px);
            box-shadow: 0 8px 32px {t['shadow']};
            animation: floatIn 0.5s ease;
            margin-bottom: 18px;
            color: {t['text']};
        }}
        @keyframes floatIn {{ 0%{{opacity:0;transform:translateY(16px)}} 100%{{opacity:1;transform:translateY(0)}} }}

        .room-code-box {{
            font-family: 'Cinzel', serif; letter-spacing: 8px; font-size: 2.2rem; font-weight: 700;
            text-align: center; color: {t['accent']} !important; padding: 14px;
            border: 2px dashed {t['accent']}; border-radius: 14px; margin: 10px 0 18px 0;
            animation: pulseGlow 2.2s ease-in-out infinite;
        }}
        @keyframes pulseGlow {{ 0%,100%{{box-shadow:0 0 6px {t['accent']}55}} 50%{{box-shadow:0 0 22px {t['accent']}aa}} }}

        .player-chip {{
            display: inline-flex; align-items: center; gap: 8px;
            background: {t['card']}; border: 1px solid {t['border']}; border-radius: 999px;
            padding: 8px 16px; margin: 4px 6px 4px 0; font-weight: 600; color: {t['text']} !important;
            animation: floatIn 0.4s ease; transition: transform .15s ease, box-shadow .15s ease;
        }}
        .player-chip:hover {{ transform: translateY(-2px); box-shadow: 0 6px 14px {t['shadow']}; }}
        .player-chip.host {{ border-color: {t['accent']}; }}

        .status-pill {{
            display:inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem;
            font-weight: 700; letter-spacing: .3px; text-transform: uppercase;
        }}
        .status-live {{ background:{t['success']}22; color:{t['success']} !important; }}
        .status-wait {{ background:{t['warn']}22; color:{t['warn']} !important; }}
        .status-done {{ background:{t['subtext']}22; color:{t['subtext']} !important; }}

        .role-card {{ perspective: 1200px; width: 100%; max-width: 320px; height: 220px; margin: 20px auto; }}
        .role-card-inner {{
            position: relative; width: 100%; height: 100%; text-align: center;
            transform-style: preserve-3d; animation: flipReveal 1s cubic-bezier(.4,.2,.2,1);
        }}
        @keyframes flipReveal {{ 0%{{transform:rotateY(180deg) scale(.9)}} 100%{{transform:rotateY(0) scale(1)}} }}
        .role-card-face {{
            position: absolute; inset: 0; border-radius: 20px; display: flex; flex-direction: column;
            align-items: center; justify-content: center; backface-visibility: hidden;
            box-shadow: 0 12px 30px {t['shadow']};
        }}
        .role-emoji {{ font-size: 4rem; margin-bottom: 6px; filter: drop-shadow(0 0 10px rgba(255,255,255,0.35)); }}
        .role-name {{ font-family: 'Cinzel', serif; font-size: 1.6rem; font-weight: 700; }}

        .score-row {{
            display: flex; justify-content: space-between; align-items:center; padding: 10px 16px;
            border-radius: 12px; margin-bottom: 8px; background: {t['card']}; border: 1px solid {t['border']};
            color: {t['text']} !important; animation: floatIn 0.4s ease; transition: transform .12s ease;
        }}
        .score-row:hover {{ transform: translateX(3px); }}

        .winner-banner {{
            text-align: center; font-family: 'Cinzel', serif; font-size: 2.4rem;
            color: {t['accent']} !important; animation: bounceIn 0.9s ease; margin-bottom: 10px;
        }}
        @keyframes bounceIn {{ 0%{{transform:scale(.5);opacity:0}} 60%{{transform:scale(1.08);opacity:1}} 100%{{transform:scale(1)}} }}

        .badge-pill {{
            display:inline-flex; align-items:center; gap:6px; background:linear-gradient(90deg,{t['accent']}33,{t['accent2']}33);
            border:1px solid {t['accent']}; color:{t['text']} !important; border-radius:999px; padding:6px 14px;
            margin:4px 6px 4px 0; font-weight:600; font-size:.85rem; animation: floatIn .5s ease;
        }}

        .skeleton {{
            border-radius: 14px; height: 46px; margin-bottom: 8px;
            background: linear-gradient(90deg, {t['card']} 25%, {t['border']} 50%, {t['card']} 75%);
            background-size: 200% 100%; animation: skeletonMove 1.3s ease-in-out infinite;
        }}
        @keyframes skeletonMove {{ 0%{{background-position:200% 0}} 100%{{background-position:-200% 0}} }}

        .empty-state {{ text-align:center; padding: 30px 10px; color:{t['subtext']} !important; }}
        .empty-state .icon {{ font-size: 2.4rem; margin-bottom: 8px; }}

        .stButton>button, .stDownloadButton>button {{
            border-radius: 12px !important; font-weight: 600 !important; padding: 0.55em 1.4em !important;
            border: none !important; background: linear-gradient(90deg,{t['accent2']},{t['accent']}) !important;
            color: #ffffff !important; transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}
        /* subtle style for the persistent top "Back" bar, so it doesn't
           compete visually with the main gradient action buttons */
        .st-key-global_back_bar .stButton>button {{
            background: {t['card']} !important;
            color: {t['text']} !important;
            border: 1px solid {t['border']} !important;
            box-shadow: none !important;
            padding: 0.35em 1em !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }}
        .st-key-global_back_bar .stButton>button:hover {{
            border-color: {t['accent2']} !important;
            color: {t['accent2']} !important;
            transform: translateX(-2px);
        }}
        .stButton>button:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 8px 20px {t['shadow']}; }}
        .stButton>button:focus-visible {{ outline: 2px solid {t['accent']} !important; outline-offset: 2px; }}
        .stButton>button:disabled {{ opacity: 0.45 !important; transform: none !important; box-shadow:none !important; }}

        .chat-bubble {{
            background: {t['card']}; border: 1px solid {t['border']}; border-radius: 14px;
            padding: 8px 12px; margin-bottom: 6px; font-size: 0.92rem; color:{t['text']} !important;
            animation: floatIn 0.3s ease;
        }}

        .countdown {{ text-align:center; font-size:1.4rem; font-weight:700; color:{t['accent']} !important; }}

        .admin-kpi {{
            background:{t['card']}; border:1px solid {t['border']}; border-radius:16px; padding:18px;
            text-align:center; animation: floatIn .4s ease;
        }}
        .admin-kpi .num {{ font-size:1.9rem; font-weight:700; color:{t['accent2']} !important; }}
        .admin-kpi .lbl {{ font-size:.82rem; color:{t['subtext']} !important; text-transform:uppercase; letter-spacing:.4px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==================================================================== #
# Animations
# ==================================================================== #
def confetti():
    components.html(
        """
        <canvas id="confetti-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;"></canvas>
        <script>
        const canvas = document.getElementById('confetti-canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth; canvas.height = window.innerHeight;
        const colors = ['#E0A800','#DB2777','#7C5CFF','#0EA5E9','#E11D48'];
        let particles = Array.from({length: 140}, () => ({
            x: Math.random()*canvas.width, y: -20 - Math.random()*canvas.height,
            r: 4 + Math.random()*6, c: colors[Math.floor(Math.random()*colors.length)],
            vy: 2 + Math.random()*4, vx: -2 + Math.random()*4, rot: Math.random()*360
        }));
        let frame = 0;
        function draw() {
            ctx.clearRect(0,0,canvas.width,canvas.height);
            particles.forEach(p => {
                p.y += p.vy; p.x += p.vx; p.rot += 6;
                ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot*Math.PI/180);
                ctx.fillStyle = p.c; ctx.fillRect(-p.r/2, -p.r/2, p.r, p.r*0.6); ctx.restore();
            });
            frame++;
            if (frame < 130) requestAnimationFrame(draw); else canvas.remove();
        }
        draw();
        </script>
        """,
        height=0, width=0,
    )


# ==================================================================== #
# AUDIO ENGINE
# One shared AudioContext lives on the browser tab's *parent* window
# (window.parent), so it survives Streamlit re-rendering the small
# component iframe on every rerun/autorefresh. That's what stops sounds
# from overlapping or the music restarting every 2 seconds.
# ==================================================================== #
_TONES = {
    "click":   [(500, 0.05)],
    "join":    [(440, 0.08), (660, 0.10)],
    "flip":    [(300, 0.06), (500, 0.08)],
    "reveal":  [(660, 0.18)],
    "correct": [(523, 0.09), (659, 0.09), (784, 0.16)],
    "wrong":   [(300, 0.12), (220, 0.22)],
    "score":   [(700, 0.07), (900, 0.09)],
    "round":   [(440, 0.08), (554, 0.08), (659, 0.14)],
    "victory": [(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.28)],
    "notify":  [(880, 0.07)],
}


def play_tone(kind: str = "reveal"):
    """Plays a short, non-overlapping generated tone. Safe to call every
    rerun for the *same* event because Streamlit only actually executes
    the script (and this call) once per real event, not per autorefresh
    tick — callers already guard with session_state flags where needed."""
    if not st.session_state.get("sound_on", True):
        return
    steps = _TONES.get(kind, _TONES["click"])
    js_steps = ",".join(f"[{f},{d}]" for f, d in steps)
    components.html(
        f"""
        <script>
        try {{
            const w = window.parent || window;
            if (!w.__bkwk_ctx) {{ w.__bkwk_ctx = new (w.AudioContext || w.webkitAudioContext)(); }}
            const ctx = w.__bkwk_ctx;
            let t = ctx.currentTime;
            const steps = [{js_steps}];
            steps.forEach(([freq, dur]) => {{
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.type = 'sine'; o.frequency.value = freq;
                g.gain.setValueAtTime(0.0001, t);
                g.gain.exponentialRampToValueAtTime(0.16, t + 0.02);
                g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
                o.connect(g); g.connect(ctx.destination);
                o.start(t); o.stop(t + dur + 0.02);
                t += dur * 0.85;
            }});
        }} catch(e) {{}}
        </script>
        """,
        height=0, width=0,
    )


def sync_background_music(music_on: bool, volume: float = 0.06):
    """Starts/stops a soft looping ambient pad exactly once, reusing the
    same parent-window AudioContext so it never doubles up or overlaps."""
    components.html(
        f"""
        <script>
        try {{
            const w = window.parent || window;
            if (!w.__bkwk_ctx) {{ w.__bkwk_ctx = new (w.AudioContext || w.webkitAudioContext)(); }}
            const ctx = w.__bkwk_ctx;
            const shouldPlay = {str(music_on).lower()};
            if (shouldPlay && !w.__bkwk_music) {{
                const notes = [261.6, 329.6, 392.0, 523.3];
                const master = ctx.createGain();
                master.gain.value = {volume};
                master.connect(ctx.destination);
                const oscs = notes.map((f, i) => {{
                    const o = ctx.createOscillator();
                    const g = ctx.createGain();
                    o.type = 'sine'; o.frequency.value = f;
                    g.gain.value = 0.25 / (i + 1);
                    o.connect(g); g.connect(master);
                    o.start();
                    return o;
                }});
                w.__bkwk_music = {{ master, oscs }};
            }} else if (!shouldPlay && w.__bkwk_music) {{
                w.__bkwk_music.master.gain.setTargetAtTime(0, ctx.currentTime, 0.2);
                setTimeout(() => {{
                    try {{ w.__bkwk_music.oscs.forEach(o => o.stop()); }} catch(e) {{}}
                    w.__bkwk_music = null;
                }}, 400);
            }} else if (shouldPlay && w.__bkwk_music) {{
                w.__bkwk_music.master.gain.setTargetAtTime({volume}, ctx.currentTime, 0.2);
            }}
        }} catch(e) {{}}
        </script>
        """,
        height=0, width=0,
    )


# ==================================================================== #
# Lightweight best-effort activity log for the Admin Panel
# ==================================================================== #
def log_event(event_type: str, detail: str = ""):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        entries = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                entries = json.loads(content) if content else []
        entries.append({"ts": time.time(), "type": event_type, "detail": detail})
        entries = entries[-300:]  # keep the log bounded
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except Exception:
        pass  # logging must never break gameplay


def read_log(limit: int = 50):
    try:
        if not os.path.exists(LOG_FILE):
            return []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            entries = json.loads(content) if content else []
        return list(reversed(entries))[:limit]
    except Exception:
        return []
