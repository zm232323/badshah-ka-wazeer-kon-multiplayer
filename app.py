"""
app.py
Badshah Ka Wazeer Kon - Digital Multiplayer Game
Main Streamlit entry point: routing, session identity, and all UI pages.
"""

import time
import streamlit as st

from utils import (AVATARS, ROLE_EMOJI, ROLE_COLOR, inject_base_css,
                    confetti, play_tone, sync_background_music)
import room as room_db
import game as game_logic
import admin as admin_panel
from players import player_by_id, sorted_leaderboard
from scoring import DEFAULT_SCORING

st.set_page_config(page_title="Badshah Ka Wazeer Kon",
                    page_icon="👑", layout="centered",
                    initial_sidebar_state="expanded")

# ---------------------------------------------------------------- #
# Session / identity bootstrapping
# ---------------------------------------------------------------- #
qp = st.query_params

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "room_code" not in st.session_state:
    st.session_state.room_code = qp.get("room")
if "player_id" not in st.session_state:
    st.session_state.player_id = qp.get("pid")
if "sound_on" not in st.session_state:
    st.session_state.sound_on = True
if "music_on" not in st.session_state:
    st.session_state.music_on = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

inject_base_css(st.session_state.theme)
sync_background_music(st.session_state.music_on)

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False


def sync_query_params():
    if st.session_state.room_code and st.session_state.player_id:
        st.query_params["room"] = st.session_state.room_code
        st.query_params["pid"] = st.session_state.player_id
    else:
        st.query_params.clear()


def leave_room():
    st.session_state.room_code = None
    st.session_state.player_id = None
    st.session_state.pop("confetti_fired", None)
    st.query_params.clear()
    st.rerun()


def exit_admin():
    st.session_state.is_admin = False
    st.rerun()


def render_back_bar(label: str, action):
    """A small, always-visible 'Back' button in the MAIN content area
    (not the sidebar), so it works even on phones where the sidebar is
    collapsed by default. Falls back gracefully on older Streamlit
    versions that don't support st.container(key=...)."""
    try:
        ctx = st.container(key="global_back_bar")
    except TypeError:
        ctx = st.container()
    with ctx:
        if st.button(label, key="global_back_btn"):
            action()


def round_progress(current_room):
    """Small dot-strip round indicator, e.g. filled/empty dots for round 2/5."""
    total = current_room["total_rounds"]
    current = current_room["current_round"]
    dots = "".join(
        f'<span style="color:{ROLE_COLOR["Badshah"]};'
        f'opacity:{"1" if i < current else "0.3"};font-size:1.1rem;margin:0 3px;">●</span>'
        for i in range(total)
    )
    st.markdown(f'<div style="text-align:center;">{dots}</div>', unsafe_allow_html=True)


def compute_badges(current_room):
    """Session-scoped achievement badges derived purely from this room's
    round history — no persistent accounts required."""
    badges = {p["id"]: [] for p in current_room["players"]}
    history = current_room.get("round_history", [])
    if not history:
        return badges

    name_to_id = {p["name"]: p["id"] for p in current_room["players"]}
    best_round_points = {}  # pid -> max single-round points
    for h in history:
        for name, pts in h.get("points", {}).items():
            pid = name_to_id.get(name)
            if pid is None:
                continue
            best_round_points[pid] = max(best_round_points.get(pid, -10 ** 9), pts)

    winner = max(current_room["players"], key=lambda p: p.get("score", 0))
    badges[winner["id"]].append(("🏆", "Champion"))

    if best_round_points:
        mvp_pid = max(best_round_points, key=best_round_points.get)
        badges[mvp_pid].append(("🌟", "MVP Round"))

    return badges


# ---------------------------------------------------------------- #
# Sidebar - theme, sound, room controls, admin access
# ---------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    theme_choice = st.radio("Theme", ["dark", "light"],
                             index=0 if st.session_state.theme == "dark" else 1,
                             horizontal=True)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.session_state.sound_on = st.toggle("🔊 Sound effects", value=st.session_state.sound_on)
    music_choice = st.toggle("🎵 Background music", value=st.session_state.music_on)
    if music_choice != st.session_state.music_on:
        st.session_state.music_on = music_choice
        st.rerun()

    if st.session_state.room_code:
        st.markdown("---")
        st.markdown(f"**Room:** `{st.session_state.room_code}`")
        if st.button("🚪 Leave Room"):
            leave_room()

    st.markdown("---")
    with st.expander("🛠️ Admin Panel"):
        if st.session_state.is_admin:
            st.success("Admin mode active")
            if st.button("Go to Admin Dashboard →", use_container_width=True):
                st.session_state.room_code = None
                st.rerun()
            if st.button("Log out of Admin", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
        else:
            pw = st.text_input("Admin password", type="password", key="sidebar_admin_pw")
            if st.button("Unlock", use_container_width=True):
                if pw == admin_panel.ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.session_state.room_code = None
                    st.rerun()
                else:
                    st.error("Incorrect password.")

    st.markdown("---")
    st.caption("Badshah Ka Wazeer Kon 👑\nBuilt with Python + Streamlit")


# ---------------------------------------------------------------- #
# Header
# ---------------------------------------------------------------- #
if not st.session_state.is_admin:
    st.markdown('<div class="bkwk-title">👑 Badshah Ka Wazeer Kon</div>', unsafe_allow_html=True)
    st.markdown('<div class="bkwk-subtitle">The classic Pakistani guessing game — reimagined online</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- #
# HOME PAGE — create or join a room
# ---------------------------------------------------------------- #
def render_home():
    tab_create, tab_join = st.tabs(["🏗️ Create Room", "🔑 Join Room"])

    with tab_create:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        name = st.text_input("Your name", key="create_name", max_chars=18)
        avatar = st.selectbox("Choose an avatar", AVATARS, key="create_avatar")
        rounds = st.slider("Number of rounds", min_value=1, max_value=10, value=5)

        with st.expander("🎯 Custom scoring (optional)"):
            st.caption("Leave defaults for the standard fair scoring system.")
            c1, c2 = st.columns(2)
            correct_cfg = {}
            incorrect_cfg = {}
            for role in ["Badshah", "Wazeer", "Sipahi", "Chor"]:
                with c1:
                    correct_cfg[role] = st.number_input(
                        f"{role} (correct guess)",
                        value=DEFAULT_SCORING["correct"][role], key=f"c_{role}")
                with c2:
                    incorrect_cfg[role] = st.number_input(
                        f"{role} (wrong guess)",
                        value=DEFAULT_SCORING["incorrect"][role], key=f"i_{role}")
            custom_scoring = {"correct": correct_cfg, "incorrect": incorrect_cfg}

        if st.button("🚀 Create Room", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                code, pid = room_db.create_room(name.strip(), avatar, rounds, custom_scoring)
                st.session_state.room_code = code
                st.session_state.player_id = pid
                sync_query_params()
                if st.session_state.sound_on:
                    play_tone("join")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_join:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        jname = st.text_input("Your name", key="join_name", max_chars=18)
        javatar = st.selectbox("Choose an avatar", AVATARS, key="join_avatar")
        jcode = st.text_input("Room Code", key="join_code", max_chars=6).upper().strip()

        if st.button("🔗 Join Room", use_container_width=True):
            if not jname.strip():
                st.error("Please enter your name.")
            elif not jcode:
                st.error("Please enter a room code.")
            else:
                pid, err = room_db.join_room(jcode, jname.strip(), javatar)
                if err:
                    st.error(err)
                else:
                    st.session_state.room_code = jcode
                    st.session_state.player_id = pid
                    sync_query_params()
                    if st.session_state.sound_on:
                        play_tone("join")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- #
# WAITING ROOM
# ---------------------------------------------------------------- #
def render_waiting_room(current_room, me):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="room-code-box">{current_room["room_code"]}</div>',
                unsafe_allow_html=True)
    st.caption("Share this Room Code with up to 3 friends so they can join.")

    st.markdown("#### 👥 Connected Players")
    chips = ""
    for p in current_room["players"]:
        host_tag = " 👑 (Host)" if p["id"] == current_room["host_id"] else ""
        host_cls = " host" if p["id"] == current_room["host_id"] else ""
        chips += f'<span class="player-chip{host_cls}">{p["avatar"]} {p["name"]}{host_tag}</span>'
    for _ in range(current_room["max_players"] - len(current_room["players"])):
        chips += '<span class="player-chip" style="opacity:0.4;">➕ Waiting...</span>'
    st.markdown(chips, unsafe_allow_html=True)

    st.progress(len(current_room["players"]) / current_room["max_players"])
    st.markdown(
        f"**{len(current_room['players'])}/{current_room['max_players']}** players joined · "
        f"**{current_room['total_rounds']}** rounds planned"
    )

    is_host = me["id"] == current_room["host_id"]
    room_full = len(current_room["players"]) == current_room["max_players"]

    if is_host:
        if st.button("▶️ Start Game", disabled=not room_full, use_container_width=True):
            current_room = game_logic.start_new_round(current_room)
            room_db.update_room(current_room["room_code"], current_room)
            st.toast("Game started! Roles have been assigned. 🎲")
            st.rerun()
        if not room_full:
            st.info("Waiting for all 4 players before the host can start.")
    else:
        st.markdown(
            '<div class="status-pill status-wait">Waiting for host to start</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    render_chat(current_room, me)


# ---------------------------------------------------------------- #
# CHAT (bonus feature)
# ---------------------------------------------------------------- #
def render_chat(current_room, me):
    with st.expander("💬 Room Chat"):
        chat = current_room.get("chat", [])
        if not chat:
            st.markdown(
                '<div class="empty-state"><div class="icon">💬</div>No messages yet — say hi!</div>',
                unsafe_allow_html=True)
        for msg in chat[-12:]:
            st.markdown(
                f'<div class="chat-bubble"><b>{msg["avatar"]} {msg["name"]}:</b> {msg["text"]}</div>',
                unsafe_allow_html=True)
        chat_col1, chat_col2 = st.columns([4, 1])
        with chat_col1:
            text = st.text_input("Type a message", key="chat_input", label_visibility="collapsed")
        with chat_col2:
            send = st.button("Send", key="chat_send")
        if send and text.strip():
            current_room.setdefault("chat", []).append(
                {"name": me["name"], "avatar": me["avatar"], "text": text.strip()[:200]})
            room_db.update_room(current_room["room_code"], current_room)
            st.rerun()


# ---------------------------------------------------------------- #
# ROLE / REVEAL SCREEN
# ---------------------------------------------------------------- #
def render_reveal_phase(current_room, me):
    my_role = current_room["roles"].get(me["id"])
    emoji = ROLE_EMOJI.get(my_role, "❓")
    color = ROLE_COLOR.get(my_role, "#888")

    st.markdown(f"### Round {current_room['current_round']} / {current_room['total_rounds']}")
    round_progress(current_room)

    st.markdown(
        f"""
        <div class="role-card">
            <div class="role-card-inner">
                <div class="role-card-face" style="background:linear-gradient(160deg,{color}33,{color}11); border:2px solid {color};">
                    <div class="role-emoji">{emoji}</div>
                    <div class="role-name" style="color:{color};">{my_role}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("This is your secret role. Only you can see it (unless it gets revealed below).")

    reveal_key = f"reveal_sound_{current_room['room_code']}_{current_room['current_round']}"
    if st.session_state.get(reveal_key) != me["id"]:
        play_tone("flip")
        st.session_state[reveal_key] = me["id"]

    revealed = current_room["revealed_roles"]
    st.markdown("#### 🔎 Publicly Revealed Roles")
    reveal_line = ""
    for pid, role in current_room["roles"].items():
        p = player_by_id(current_room, pid)
        if role in revealed:
            reveal_line += (f'<span class="player-chip" style="border-color:{ROLE_COLOR[role]};">'
                             f'{ROLE_EMOJI[role]} {p["name"]} — {role}</span>')
        else:
            reveal_line += f'<span class="player-chip" style="opacity:0.55;">❔ {p["name"]} — Hidden</span>'
    st.markdown(reveal_line, unsafe_allow_html=True)

    is_wazeer = my_role == "Wazeer"
    is_host = me["id"] == current_room["host_id"]

    st.markdown("---")
    if is_wazeer:
        st.success("You are the **Wazeer**! Study the remaining two players carefully.")
    else:
        st.info("The Wazeer is now deciding who among the remaining players is the Chor.")

    if is_host:
        if st.button("➡️ Proceed to Guessing Phase", use_container_width=True):
            current_room = game_logic.advance_to_guessing(current_room)
            room_db.update_room(current_room["room_code"], current_room)
            st.rerun()


# ---------------------------------------------------------------- #
# GUESSING PHASE
# ---------------------------------------------------------------- #
def render_guessing_phase(current_room, me):
    my_role = current_room["roles"].get(me["id"])
    candidates = current_room["chor_candidates"]

    st.markdown(f"### Round {current_room['current_round']} — 🕵️ Guessing Phase")
    round_progress(current_room)

    deadline = current_room.get("guess_deadline")
    if deadline:
        remaining = max(0, int(deadline - time.time()))
        urgent = ' style="color:#E11D48;"' if remaining <= 5 else ""
        st.markdown(f'<div class="countdown"{urgent}>⏳ {remaining}s remaining</div>', unsafe_allow_html=True)
        if remaining == 0 and current_room["wazeer_guess"] is None:
            current_room = game_logic.auto_resolve_timeout(current_room)
            room_db.update_room(current_room["room_code"], current_room)
            st.rerun()

    cand_players = [player_by_id(current_room, pid) for pid in candidates]

    if my_role == "Wazeer":
        st.write("Who do you think is the **Chor**? Choose carefully — points are at stake!")
        choice_labels = [f'{p["avatar"]} {p["name"]}' for p in cand_players]
        choice = st.radio("Suspected Chor:", choice_labels, key="guess_radio")
        if st.button("✅ Submit Guess", use_container_width=True):
            picked = cand_players[choice_labels.index(choice)]
            current_room = game_logic.process_guess(current_room, picked["id"])
            room_db.update_room(current_room["room_code"], current_room)
            st.rerun()
    else:
        st.info("Only the **Wazeer** can make the guess. Please wait...")
        chips = "".join(f'<span class="player-chip">{p["avatar"]} {p["name"]}</span>' for p in cand_players)
        st.markdown("Candidates: " + chips, unsafe_allow_html=True)


# ---------------------------------------------------------------- #
# RESULT PHASE
# ---------------------------------------------------------------- #
def render_result_phase(current_room, me):
    st.markdown(f"### Round {current_room['current_round']} — 📜 Result")
    round_progress(current_room)

    result_key = f"result_sound_{current_room['room_code']}_{current_room['current_round']}"
    already_played = st.session_state.get(result_key)

    correct = current_room["guess_correct"]
    if correct:
        st.success("🎉 The Wazeer guessed **correctly**!")
        if not already_played:
            play_tone("correct")
    else:
        st.error("❌ The Wazeer guessed **incorrectly**.")
        if not already_played:
            play_tone("wrong")
    st.session_state[result_key] = True

    st.markdown("#### 🎭 All Roles Revealed")
    for pid, role in current_room["roles"].items():
        p = player_by_id(current_room, pid)
        st.markdown(
            f'<div class="score-row"><span>{ROLE_EMOJI[role]} <b>{p["name"]}</b> — {role}</span>'
            f'<span style="color:{ROLE_COLOR[role]};">{"🎯 Guessed" if pid == current_room["wazeer_guess"] else ""}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("#### 🏆 Scoreboard")
    for p in sorted_leaderboard(current_room):
        st.markdown(
            f'<div class="score-row"><span>{p["avatar"]} {p["name"]}</span>'
            f'<span><b>{p["score"]}</b> pts</span></div>',
            unsafe_allow_html=True,
        )

    is_host = me["id"] == current_room["host_id"]
    if is_host:
        if game_logic.is_final_round(current_room):
            if st.button("🏁 Show Final Results", use_container_width=True):
                current_room = game_logic.finish_game(current_room)
                room_db.update_room(current_room["room_code"], current_room)
                st.rerun()
        else:
            if st.button("➡️ Next Round", use_container_width=True):
                current_room = game_logic.start_new_round(current_room)
                room_db.update_room(current_room["room_code"], current_room)
                play_tone("round")
                st.rerun()
    else:
        st.info("Waiting for the host to continue...")


# ---------------------------------------------------------------- #
# FINAL LEADERBOARD
# ---------------------------------------------------------------- #
def render_final_screen(current_room, me):
    winner = game_logic.get_winner(current_room)
    st.markdown(f'<div class="winner-banner">🏆 {winner["avatar"]} {winner["name"]} Wins!</div>',
                unsafe_allow_html=True)

    if "confetti_fired" not in st.session_state:
        confetti()
        play_tone("victory")
        st.session_state.confetti_fired = True

    badges = compute_badges(current_room)
    if badges.get(me["id"]):
        badge_html = "".join(f'<span class="badge-pill">{icon} {label}</span>' for icon, label in badges[me["id"]])
        st.markdown(f"**Your badges:** {badge_html}", unsafe_allow_html=True)

    st.markdown("#### 📊 Final Leaderboard")
    for i, p in enumerate(sorted_leaderboard(current_room), start=1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        p_badges = "".join(f' <span class="badge-pill">{icon}</span>' for icon, _ in badges.get(p["id"], []))
        st.markdown(
            f'<div class="score-row"><span>{medal} {p["avatar"]} <b>{p["name"]}</b>{p_badges}</span>'
            f'<span><b>{p["score"]}</b> pts</span></div>',
            unsafe_allow_html=True,
        )

    with st.expander("📜 Round History"):
        if not current_room["round_history"]:
            st.markdown('<div class="empty-state">No rounds played.</div>', unsafe_allow_html=True)
        for r in current_room["round_history"]:
            st.markdown(f"**Round {r['round']}** — "
                        f"{'✅ Correct' if r['correct'] else '❌ Incorrect'} "
                        f"(guessed *{r['guessed']}*, actual Chor was *{r['actual_chor']}*)")

    is_host = me["id"] == current_room["host_id"]
    if is_host:
        if st.button("🔄 Restart Game (new roles, same room)", use_container_width=True):
            for p in current_room["players"]:
                p["score"] = 0
            current_room["round_history"] = []
            current_room["current_round"] = 0
            current_room = game_logic.start_new_round(current_room)
            room_db.update_room(current_room["room_code"], current_room)
            st.session_state.pop("confetti_fired", None)
            st.rerun()

    if st.button("🏠 Back to Home"):
        leave_room()


# ---------------------------------------------------------------- #
# ROUTER
# ---------------------------------------------------------------- #
def main():
    if st.session_state.is_admin:
        render_back_bar("⬅️ Exit Admin Panel", exit_admin)
        admin_panel.render_admin_panel()
        return

    if not st.session_state.room_code or not st.session_state.player_id:
        render_home()
        return

    current_room = room_db.get_room(st.session_state.room_code)
    if current_room is None:
        st.error("This room no longer exists.")
        if st.button("⬅️ Back to Home"):
            leave_room()
        return

    me = player_by_id(current_room, st.session_state.player_id)
    if me is None:
        st.error("You are not part of this room anymore.")
        if st.button("⬅️ Back to Home"):
            leave_room()
        return

    render_back_bar("⬅️ Leave Room", leave_room)

    # keep every connected device in sync
    if HAS_AUTOREFRESH and current_room["status"] != "waiting":
        st_autorefresh(interval=2000, key="game_sync")
    elif HAS_AUTOREFRESH:
        st_autorefresh(interval=3000, key="lobby_sync")

    status = current_room["status"]
    if status == "waiting":
        render_waiting_room(current_room, me)
    elif status == "reveal":
        render_reveal_phase(current_room, me)
    elif status == "guessing":
        render_guessing_phase(current_room, me)
    elif status == "result":
        render_result_phase(current_room, me)
    elif status == "finished":
        render_final_screen(current_room, me)


if __name__ == "__main__":
    main()
