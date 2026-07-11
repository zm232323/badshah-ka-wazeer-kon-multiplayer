# 👑 Badshah Ka Wazeer Kon — Digital Multiplayer Game

A real-time, 4-player digital adaptation of the classic Pakistani childhood
game *Badshah Ka Wazeer Kon*, built with **Python** and **Streamlit**, with a
premium glassmorphism UI, smooth CSS animations, and confetti celebrations.

---

## 🎮 Game Overview

Four players join a shared room from separate devices. Each round, roles are
secretly assigned:

| Role | Description |
|---|---|
| 👑 Badshah (King) | Revealed immediately |
| 🧙 Wazeer (Minister) | Revealed immediately, must guess the Chor |
| 🛡️ Sipahi (Soldier) | Hidden until the result phase |
| 🗡️ Chor (Thief) | Hidden until the result phase |

The Wazeer must correctly identify the Chor among the two hidden players.
Scoring rewards (or punishes) everyone based on whether the guess was right.

---

## ✨ Features

**Core (assignment requirements)**
- Room creation with unique room codes, 4-player cap
- Real-time multiplayer sync across devices (JSON-backed shared state)
- Secret role assignment, each role appears once per round
- Reveal → Guess → Result → Next Round → Winner flow
- Automatic scoring, live scoreboard, final leaderboard & winner
- Configurable number of rounds (default 5)
- Responsive, professional multi-page UI

**Bonus features included**
- 🎬 Animated role-reveal flip cards + round progress dots
- 🎉 Confetti + winner banner animation
- 🌗 Dark / Light theme — every native widget (inputs, tabs, tables,
  alerts, dropdowns, sidebar) is explicitly re-themed, not just the
  custom cards, so light mode is fully readable
- 🔊 Sound effects **and** a toggleable ambient background loop, both
  generated in-browser with the Web Audio API (no external audio files,
  nothing to preload, and a shared AudioContext so sounds never overlap
  or restart on every auto-refresh)
- 💬 In-room chat
- ⏱️ Countdown timer for the Wazeer's guess (auto-resolves on timeout)
- 🎯 Custom, host-configurable scoring system
- 🧑‍🎤 Player avatar picker
- 🏅 Session-scoped achievement badges (Champion, MVP Round) on the
  final screen
- 📜 Full round history log
- 🔄 One-click restart with the same room/players
- 🛠️ **Admin Panel** (password-protected) — live KPIs, room
  management (force-close / delete / prune inactive rooms), live game
  monitoring, simple analytics charts, and an activity log

---

## 🗂️ Project Structure

```
Badshah-Ka-Wazeer-Kon/
├── app.py              # Streamlit UI, routing, all player-facing pages
├── admin.py             # Password-protected Admin Dashboard
├── game.py               # Core game rules (roles, rounds, guesses)
├── room.py                # Room creation/joining & JSON persistence
├── scoring.py               # Default + custom scoring logic
├── players.py                 # Player list helper functions
├── utils.py                     # CSS theming, avatars, confetti, audio engine, logger
├── .streamlit/config.toml         # Streamlit theme config
├── data/rooms.json                  # Shared multiplayer game state (auto-managed)
├── data/activity_log.json             # Admin activity log (auto-created)
├── requirements.txt
└── README.md
```

---

## ⚙️ How Multiplayer Works

Streamlit runs one session per browser tab, so "multiplayer" here is achieved
through a **shared JSON state file** (`data/rooms.json`):

1. The host creates a room → a unique 5-character room code is generated and
   a new room object is written to `rooms.json`.
2. Other players join using that code from their own devices; they're
   appended to the same room's `players` list.
3. Every player's browser identity (room code + player id) is persisted in
   the URL query parameters, so a page refresh doesn't disconnect them.
4. All connected clients **auto-refresh every 2–3 seconds** (via
   `streamlit-autorefresh`) and re-read the shared room state, so role
   reveals, guesses, and scores stay in sync across every device.
5. A simple file-lock (`rooms.json.lock`) prevents write collisions when two
   players act at the same moment (e.g., joining simultaneously).

Each player only ever *sees* their own secret role and whatever the game
state currently marks as "revealed" — hidden roles are never rendered to
other players' screens until the reveal/result phase.

---

## 🚀 Setup & Run Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Play with friends on the same network
- Find your machine's local IP address (e.g. `192.168.1.10`).
- Streamlit will print a **Network URL** like `http://192.168.1.10:8501` —
  share this with the other 3 players on the same Wi-Fi so they can join
  from their own phones/laptops.
- To play over the internet, deploy to **Streamlit Community Cloud** (free)
  and share the public URL instead.

### 4. Create / Join a room
1. One player clicks **Create Room**, picks a name + avatar, and shares the
   generated **Room Code**.
2. The other three players click **Join Room** and enter that code.
3. Once all 4 are in, the host clicks **Start Game**.

---

## 🧠 Tech Stack

- **Python 3.9+**
- **Streamlit** — UI framework
- **streamlit-autorefresh** — keeps all clients in sync
- **JSON** — lightweight shared game-state storage
- `random` module — role shuffling & tie-breaking
- Custom CSS/JS (via `st.markdown` / `components.html`) — glassmorphism UI,
  card-flip animations, confetti, and generated sound effects
- **pandas** — powers the Admin Panel's tables and charts

---

## 🛠️ Admin Panel

Open the app, expand **🛠️ Admin Panel** in the sidebar, and log in with the
demo password:

```
admin123
```

⚠️ **Change `ADMIN_PASSWORD` at the top of `admin.py` before deploying this
publicly** — the demo password is intentionally simple and is not meant for
production use.

Once unlocked you get:
- **Dashboard** — total players, active/waiting/completed rooms, total rounds played
- **Rooms** — table of every room with status/host/round, plus force-close,
  delete, and "prune inactive rooms (6h+)" actions
- **Monitoring** — inspect any live room's players, current roles, and round history
- **Analytics** — rooms-by-status chart, Wazeer guess accuracy, current top scores
- **Logs** — a running activity feed (room created, round completed, game finished, admin actions)
- **Settings** — a read-only summary explaining that theme/sound are per-browser
  session settings (there's no shared server-side settings store to edit, by design)

---

## 📝 Scope note

The original brief asked for an extremely large wishlist (full XP/leveling,
persistent player profiles, tournament mode, Firebase, etc.). Since this app
intentionally has **no user accounts** — it's per-room, JSON-backed, matching
the assignment's required tech stack — features like XP/levels were
implemented at the level that's actually honest for that architecture:
session-scoped achievement badges instead of a fake persistent XP bar. Adding
real accounts/a database would be a good "Bonus Features" follow-up but is a
different architecture than what's here.

---

## 📋 Submission Checklist

- [x] Fully functional multiplayer game
- [x] Room creation and joining system
- [x] Four-player gameplay
- [x] Random role assignment
- [x] Guessing mechanism
- [x] Automatic score calculation
- [x] Leaderboard
- [x] Responsive, animated user interface
- [x] Clean, modular project structure
- [x] Well-commented source code
- [x] README.md with setup instructions
- [x] requirements.txt

---

## 👥 Team Notes

Replace this section with your team name, members, and any screenshots or a
demo video link before final submission.
"# badshah-ka-wazeer-kon-multiplayer" 
"# badshah-ka-wazeer-kon-multiplayer" 
