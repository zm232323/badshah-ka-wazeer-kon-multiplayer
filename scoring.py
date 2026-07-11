"""
scoring.py
Default scoring table (per the assignment) plus support for a custom,
host-configurable point system (bonus feature).
"""

DEFAULT_SCORING = {
    "correct": {"Badshah": 100, "Wazeer": 80, "Sipahi": 50, "Chor": 0},
    "incorrect": {"Badshah": 100, "Wazeer": -20, "Sipahi": 50, "Chor": 120},
}


def calculate_round_scores(roles: dict, guessed_pid: str, actual_chor_pid: str,
                            scoring_config: dict = None):
    """
    roles: {player_id: role_name}
    Returns (points_by_pid: dict, correct: bool)
    """
    cfg = scoring_config or DEFAULT_SCORING
    correct = guessed_pid == actual_chor_pid
    table = cfg["correct"] if correct else cfg["incorrect"]

    points = {}
    for pid, role in roles.items():
        points[pid] = table.get(role, 0)
    return points, correct
