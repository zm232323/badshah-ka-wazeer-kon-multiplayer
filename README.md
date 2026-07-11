<div align="center">

# 👑 Badshah Ka Wazeer Kon
### *Digital Multiplayer Edition*

A real-time, 4-player web adaptation of the classic Pakistani childhood
guessing game — built with **Python + Streamlit**, wrapped in a premium
glassmorphism UI with smooth animations, an in-browser audio engine, and
a full admin dashboard.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-7C5CFF?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Hackathon%20Ready-22C55E?style=for-the-badge)

</div>

---

## 📖 Table of Contents

- [🎮 Game Overview](#-game-overview)
- [✨ Features](#-features)
- [🗂️ Project Structure](#️-project-structure)
- [⚙️ How Multiplayer Works](#️-how-multiplayer-works)
- [🚀 Setup & Run](#-setup--run)
- [🛠️ Admin Panel](#️-admin-panel)
- [🧠 Tech Stack](#-tech-stack)
- [📝 Scope Note](#-scope-note)
- [📋 Submission Checklist](#-submission-checklist)
- [👥 Team](#-team)

---

## 🎮 Game Overview

Four players join a shared room from separate devices. Each round, roles
are secretly assigned:

| Role | Icon | Visibility |
|---|:---:|---|
| **Badshah** (King) | 👑 | Revealed immediately |
| **Wazeer** (Minister) | 🧙 | Revealed immediately — must guess the Chor |
| **Sipahi** (Soldier) | 🛡️ | Hidden until the result phase |
| **Chor** (Thief) | 🗡️ | Hidden until the result phase |

The Wazeer must correctly identify the Chor among the two hidden players.
Scoring rewards — or punishes — everyone based on whether the guess was
right.

**Flow:** `Create/Join Room` → `Role Assignment` → `Reveal` → `Guessing` →
`Result` → `Next Round` → `Winner`

---

## ✨ Features

<table>
<tr>
<td valign="top" width="50%">

**🎯 Core Gameplay**
- Unique room codes, hard 4-player cap
- Real-time sync across devices (JSON-backed)
- Secret role assignment, one role per player
- Auto scoring + live scoreboard
- Configurable rounds (default 5)
- Custom, host-editable scoring table
- Countdown timer with auto-resolve on timeout
- Full round history + one-click restart

</td>
<td valign="top" width="50%">

**💎 Premium Extras**
- 🌗 Dark / Light theme — every native widget
  properly re-themed (not just custom cards)
- 🔊 In-browser sound effects + toggleable
  ambient music (Web Audio API, zero asset files,
  never overlaps)
- 🎬 Animated flip cards, round progress dots,
  confetti + victory fanfare
- 🏅 Session-based achievement badges
- 💬 In-room chat
- 🧭 Persistent **Back** button — visible on
  PC and mobile, sidebar or not
- 🛠️ Password-protected **Admin Panel**

</td>
</tr>
</table>

---

## 🗂️ Project Structure
