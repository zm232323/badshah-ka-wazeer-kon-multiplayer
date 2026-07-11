"""
room.py
Handles room creation, joining, and persistence.
Rooms are stored in data/rooms.json so every connected browser (device)
reads/writes the same shared game state — this is what makes the game
"multiplayer" inside Streamlit's per-session model.
"""

import json
import os
import time
from utils import new_id, generate_room_code, log_event

ROOMS_FILE = os.path.join(os.path.dirname(__file__), "data", "rooms.json")
LOCK_FILE = ROOMS_FILE + ".lock"
MAX_PLAYERS = 4


def _acquire_lock(timeout=5.0):
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            return True
        except FileExistsError:
            if time.time() - start > timeout:
                # stale lock safety valve
                try:
                    os.remove(LOCK_FILE)
                except OSError:
                    pass
                return True
            time.sleep(0.05)


def _release_lock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def load_rooms() -> dict:
    if not os.path.exists(ROOMS_FILE):
        return {}
    try:
        with open(ROOMS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_rooms(rooms: dict):
    with open(ROOMS_FILE, "w", encoding="utf-8") as f:
        json.dump(rooms, f, indent=2)


def get_room(room_code: str):
    rooms = load_rooms()
    return rooms.get(room_code)


def update_room(room_code: str, room_data: dict):
    _acquire_lock()
    try:
        rooms = load_rooms()
        rooms[room_code] = room_data
        save_rooms(rooms)
    finally:
        _release_lock()


def create_room(host_name: str, avatar: str, total_rounds: int = 5,
                 scoring_config: dict = None) -> tuple:
    from scoring import DEFAULT_SCORING

    _acquire_lock()
    try:
        rooms = load_rooms()
        code = generate_room_code()
        while code in rooms:
            code = generate_room_code()

        player_id = new_id()
        room = {
            "room_code": code,
            "host_id": player_id,
            "players": [
                {"id": player_id, "name": host_name, "avatar": avatar,
                 "score": 0, "connected": True}
            ],
            "max_players": MAX_PLAYERS,
            "total_rounds": total_rounds,
            "current_round": 0,
            "status": "waiting",          # waiting -> reveal -> guessing -> result -> finished
            "roles": {},
            "revealed_roles": [],
            "chor_candidates": [],
            "wazeer_guess": None,
            "actual_chor": None,
            "guess_correct": None,
            "round_history": [],
            "chat": [],
            "scoring_config": scoring_config or DEFAULT_SCORING,
            "guess_deadline": None,
            "created_at": time.time(),
        }
        rooms[code] = room
        save_rooms(rooms)
        log_event("room_created", f"{code} by {host_name}")
        return code, player_id
    finally:
        _release_lock()


def join_room(room_code: str, name: str, avatar: str):
    _acquire_lock()
    try:
        rooms = load_rooms()
        room = rooms.get(room_code)
        if room is None:
            return None, "Room not found. Please check the room code."
        if room["status"] != "waiting":
            return None, "This game has already started."
        if len(room["players"]) >= MAX_PLAYERS:
            return None, "Room is full (4/4 players)."

        player_id = new_id()
        room["players"].append(
            {"id": player_id, "name": name, "avatar": avatar,
             "score": 0, "connected": True}
        )
        rooms[room_code] = room
        save_rooms(rooms)
        return player_id, None
    finally:
        _release_lock()


def get_player(room: dict, player_id: str):
    for p in room["players"]:
        if p["id"] == player_id:
            return p
    return None


# ---------------------------------------------------------------- #
# Admin-only helpers (read/manage every room). Purely additive —
# does not change any existing gameplay function above.
# ---------------------------------------------------------------- #
def list_all_rooms() -> dict:
    return load_rooms()


def admin_delete_room(room_code: str):
    _acquire_lock()
    try:
        rooms = load_rooms()
        existed = rooms.pop(room_code, None) is not None
        save_rooms(rooms)
        if existed:
            log_event("room_deleted", f"{room_code} (admin)")
        return existed
    finally:
        _release_lock()


def admin_force_close_room(room_code: str):
    _acquire_lock()
    try:
        rooms = load_rooms()
        room = rooms.get(room_code)
        if room is None:
            return False
        room["status"] = "finished"
        rooms[room_code] = room
        save_rooms(rooms)
        log_event("room_force_closed", f"{room_code} (admin)")
        return True
    finally:
        _release_lock()


def admin_delete_inactive_rooms(max_age_seconds: int = 6 * 3600):
    """Removes waiting/finished rooms older than max_age_seconds. Returns
    the list of deleted room codes."""
    _acquire_lock()
    try:
        rooms = load_rooms()
        now = time.time()
        stale = [
            code for code, r in rooms.items()
            if now - r.get("created_at", now) > max_age_seconds
            and r.get("status") in ("waiting", "finished")
        ]
        for code in stale:
            rooms.pop(code, None)
        save_rooms(rooms)
        if stale:
            log_event("rooms_pruned", f"{len(stale)} inactive room(s) removed")
        return stale
    finally:
        _release_lock()
