"""
players.py
Small helpers for working with the players list inside a room dict.
"""


def player_by_id(room: dict, player_id: str):
    for p in room["players"]:
        if p["id"] == player_id:
            return p
    return None


def other_players(room: dict, player_id: str):
    return [p for p in room["players"] if p["id"] != player_id]


def sorted_leaderboard(room: dict):
    return sorted(room["players"], key=lambda p: p.get("score", 0), reverse=True)


def all_connected(room: dict) -> bool:
    return len(room["players"]) == room.get("max_players", 4)
