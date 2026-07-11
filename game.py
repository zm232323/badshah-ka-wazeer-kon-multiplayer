"""
game.py
Core game rules: role assignment, reveal phase, guessing phase,
result computation, and round/game progression.
"""

import random
import time
from scoring import calculate_round_scores
from utils import log_event

ROLES = ["Badshah", "Wazeer", "Sipahi", "Chor"]
GUESS_TIME_LIMIT = 30  # seconds, used by the optional countdown timer


def start_new_round(room: dict):
    player_ids = [p["id"] for p in room["players"]]
    shuffled_roles = ROLES[:]
    random.shuffle(shuffled_roles)
    roles = dict(zip(player_ids, shuffled_roles))

    room["roles"] = roles
    room["revealed_roles"] = ["Badshah", "Wazeer"]
    room["wazeer_guess"] = None
    room["guess_correct"] = None
    room["current_round"] += 1

    actual_chor = next(pid for pid, r in roles.items() if r == "Chor")
    room["actual_chor"] = actual_chor

    remaining = [pid for pid, r in roles.items() if r in ("Sipahi", "Chor")]
    random.shuffle(remaining)
    room["chor_candidates"] = remaining

    room["status"] = "reveal"
    room["guess_deadline"] = None
    return room


def advance_to_guessing(room: dict):
    room["status"] = "guessing"
    room["guess_deadline"] = time.time() + GUESS_TIME_LIMIT
    return room


def process_guess(room: dict, guessed_pid: str):
    roles = room["roles"]
    points, correct = calculate_round_scores(
        roles, guessed_pid, room["actual_chor"], room.get("scoring_config")
    )

    for p in room["players"]:
        p["score"] = p.get("score", 0) + points.get(p["id"], 0)

    room["wazeer_guess"] = guessed_pid
    room["guess_correct"] = correct
    room["revealed_roles"] = ROLES[:]  # reveal everyone
    room["status"] = "result"

    id_to_name = {p["id"]: p["name"] for p in room["players"]}
    room["round_history"].append({
        "round": room["current_round"],
        "roles": {id_to_name.get(pid, pid): role for pid, role in roles.items()},
        "guessed": id_to_name.get(guessed_pid, guessed_pid),
        "actual_chor": id_to_name.get(room["actual_chor"], room["actual_chor"]),
        "correct": correct,
        "points": {id_to_name.get(pid, pid): pts for pid, pts in points.items()},
    })
    log_event("round_completed",
              f"room={room['room_code']} round={room['current_round']} correct={correct}")
    return room


def auto_resolve_timeout(room: dict):
    """If the guess timer runs out, a random candidate is auto-guessed."""
    if room["wazeer_guess"] is None and room["chor_candidates"]:
        guess = random.choice(room["chor_candidates"])
        return process_guess(room, guess)
    return room


def is_final_round(room: dict) -> bool:
    return room["current_round"] >= room["total_rounds"]


def finish_game(room: dict):
    room["status"] = "finished"
    log_event("game_finished", f"room={room['room_code']} rounds={room['current_round']}")
    return room


def get_winner(room: dict):
    if not room["players"]:
        return None
    return max(room["players"], key=lambda p: p.get("score", 0))
