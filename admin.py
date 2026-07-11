"""
admin.py
Standalone Admin Panel: live stats, room/user management, game
monitoring, simple analytics, and an activity log. Read-only with
respect to game logic — it only inspects room.py's shared JSON store
and calls the additive admin_* helpers in room.py.
"""

import time
from collections import Counter

import pandas as pd
import streamlit as st

import room as room_db
from players import sorted_leaderboard
from utils import read_log

ADMIN_PASSWORD = "admin123"  # demo-only — change before deploying publicly


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    return f"{seconds / 3600:.1f}h ago"


def render_admin_login():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Admin Login")
    st.caption("Demo password is `admin123` — change ADMIN_PASSWORD in admin.py before real deployment.")
    pw = st.text_input("Password", type="password", key="admin_pw")
    if st.button("🔓 Unlock Admin Panel", use_container_width=True):
        if pw == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_admin_panel():
    rooms = room_db.list_all_rooms()

    top = st.columns([6, 1])
    with top[0]:
        st.markdown("## 🛠️ Admin Dashboard")
    with top[1]:
        if st.button("🔒 Log out"):
            st.session_state.is_admin = False
            st.rerun()

    tabs = st.tabs(["📊 Dashboard", "🚪 Rooms", "🎮 Monitoring",
                     "📈 Analytics", "📜 Logs", "⚙️ Settings"])

    # ---------------- Dashboard ---------------- #
    with tabs[0]:
        total_rooms = len(rooms)
        total_players = sum(len(r["players"]) for r in rooms.values())
        active = sum(1 for r in rooms.values() if r["status"] in ("reveal", "guessing", "result"))
        waiting = sum(1 for r in rooms.values() if r["status"] == "waiting")
        finished = sum(1 for r in rooms.values() if r["status"] == "finished")
        total_rounds = sum(len(r.get("round_history", [])) for r in rooms.values())

        kpis = [
            ("👥 Total Players", total_players),
            ("🚪 Active Rooms", total_rooms),
            ("🎮 Running Games", active),
            ("⏳ Waiting Rooms", waiting),
            ("✅ Completed Games", finished),
            ("🔁 Total Rounds Played", total_rounds),
        ]
        cols = st.columns(3)
        for i, (label, value) in enumerate(kpis):
            with cols[i % 3]:
                st.markdown(
                    f'<div class="admin-kpi"><div class="num">{value}</div>'
                    f'<div class="lbl">{label}</div></div>',
                    unsafe_allow_html=True,
                )
                st.write("")

        if not rooms:
            st.markdown(
                '<div class="empty-state"><div class="icon">🌙</div>'
                'No rooms yet. Once players create rooms, live stats appear here.</div>',
                unsafe_allow_html=True,
            )

    # ---------------- Rooms ---------------- #
    with tabs[1]:
        st.markdown("#### 🚪 Room Management")
        if not rooms:
            st.markdown('<div class="empty-state"><div class="icon">📭</div>No rooms to manage.</div>',
                        unsafe_allow_html=True)
        else:
            now = time.time()
            rows = []
            for code, r in rooms.items():
                host = next((p["name"] for p in r["players"] if p["id"] == r["host_id"]), "?")
                rows.append({
                    "Code": code,
                    "Status": r["status"],
                    "Players": f'{len(r["players"])}/{r["max_players"]}',
                    "Host": host,
                    "Round": f'{r["current_round"]}/{r["total_rounds"]}',
                    "Created": _fmt_age(now - r.get("created_at", now)),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.markdown("##### Actions")
            code_choice = st.selectbox("Select a room", list(rooms.keys()), key="admin_room_pick")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🛑 Force Close", use_container_width=True):
                    room_db.admin_force_close_room(code_choice)
                    st.toast(f"Room {code_choice} force-closed.")
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete Room", use_container_width=True):
                    room_db.admin_delete_room(code_choice)
                    st.toast(f"Room {code_choice} deleted.")
                    st.rerun()
            with c3:
                if st.button("🧹 Prune Inactive (6h+)", use_container_width=True):
                    removed = room_db.admin_delete_inactive_rooms()
                    st.toast(f"Removed {len(removed)} inactive room(s).")
                    st.rerun()

    # ---------------- Monitoring ---------------- #
    with tabs[2]:
        st.markdown("#### 🎮 Live Game Monitoring")
        if not rooms:
            st.markdown('<div class="empty-state"><div class="icon">🎲</div>No live games right now.</div>',
                        unsafe_allow_html=True)
        else:
            code_choice = st.selectbox("Room to inspect", list(rooms.keys()), key="admin_monitor_pick")
            r = rooms[code_choice]
            st.markdown(f'<span class="status-pill status-{"live" if r["status"] in ("reveal","guessing","result") else ("wait" if r["status"]=="waiting" else "done")}">{r["status"]}</span>',
                        unsafe_allow_html=True)
            st.write("")
            st.markdown("**Players & current roles**")
            for p in r["players"]:
                role = r["roles"].get(p["id"], "—")
                st.markdown(
                    f'<div class="score-row"><span>{p["avatar"]} {p["name"]}</span>'
                    f'<span>{role} · <b>{p.get("score",0)}</b> pts</span></div>',
                    unsafe_allow_html=True,
                )
            if r.get("round_history"):
                st.markdown("**Round history**")
                st.dataframe(pd.DataFrame(r["round_history"])[["round", "guessed", "actual_chor", "correct"]],
                             use_container_width=True, hide_index=True)

    # ---------------- Analytics ---------------- #
    with tabs[3]:
        st.markdown("#### 📈 Analytics")
        if not rooms:
            st.markdown('<div class="empty-state"><div class="icon">📉</div>Nothing to chart yet.</div>',
                        unsafe_allow_html=True)
        else:
            status_counts = Counter(r["status"] for r in rooms.values())
            st.markdown("**Rooms by status**")
            st.bar_chart(pd.DataFrame.from_dict(status_counts, orient="index", columns=["rooms"]))

            correct_total = sum(
                1 for r in rooms.values() for h in r.get("round_history", []) if h["correct"]
            )
            wrong_total = sum(
                1 for r in rooms.values() for h in r.get("round_history", []) if not h["correct"]
            )
            st.markdown("**Wazeer guess accuracy (all rooms)**")
            st.bar_chart(pd.DataFrame(
                {"rounds": [correct_total, wrong_total]}, index=["Correct guess", "Wrong guess"]
            ))

            all_players = [p for r in rooms.values() for p in r["players"]]
            if all_players:
                st.markdown("**Top scores currently on the board**")
                top_df = pd.DataFrame(
                    sorted(all_players, key=lambda p: p.get("score", 0), reverse=True)[:10]
                )[["name", "avatar", "score"]]
                st.dataframe(top_df, use_container_width=True, hide_index=True)

    # ---------------- Logs ---------------- #
    with tabs[4]:
        st.markdown("#### 📜 Activity Log")
        entries = read_log(100)
        if not entries:
            st.markdown('<div class="empty-state"><div class="icon">🗒️</div>No activity logged yet.</div>',
                        unsafe_allow_html=True)
        else:
            now = time.time()
            for e in entries:
                st.markdown(
                    f'<div class="chat-bubble"><b>{e["type"]}</b> — {e.get("detail","")} '
                    f'<span style="opacity:0.6;">({_fmt_age(now - e["ts"])})</span></div>',
                    unsafe_allow_html=True,
                )

    # ---------------- Settings ---------------- #
    with tabs[5]:
        st.markdown("#### ⚙️ Settings Overview")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write(f"**Theme:** {st.session_state.get('theme', 'dark')}")
        st.write(f"**Sound effects:** {'On' if st.session_state.get('sound_on', True) else 'Off'}")
        st.write(f"**Music:** {'On' if st.session_state.get('music_on', False) else 'Off'}")
        st.caption("Per-visitor preferences are stored in each player's own browser session "
                   "(Streamlit session state), matching how the rest of the app works — there is "
                   "no shared server-side settings store to edit here.")
        st.markdown('</div>', unsafe_allow_html=True)
