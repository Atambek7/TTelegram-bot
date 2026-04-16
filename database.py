import json
import os
from datetime import datetime, timedelta
from config import REPETITION_INTERVALS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_progress():
    _ensure_data_dir()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "leaderboard": []}


def _save_progress(data):
    _ensure_data_dir()
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(user_id):
    data = _load_progress()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "username": "",
            "grade": 5,
            "points": 0,
            "words_learned": [],
            "words_mastered": [],
            "games_played": 0,
            "correct_answers": 0,
            "total_answers": 0,
            "streak": 0,
            "best_streak": 0,
            "spaced_repetition": {},
            "group_points": 0,
            "last_activity": datetime.now().isoformat(),
        }
        _save_progress(data)
    return data["users"][uid]


def update_user(user_id, updates):
    data = _load_progress()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = get_user(user_id)
    data["users"][uid].update(updates)
    data["users"][uid]["last_activity"] = datetime.now().isoformat()
    _save_progress(data)


def add_points(user_id, points):
    user = get_user(user_id)
    user["points"] += points
    update_user(user_id, {"points": user["points"]})
    return user["points"]


def record_answer(user_id, correct: bool):
    user = get_user(user_id)
    user["total_answers"] += 1
    if correct:
        user["correct_answers"] += 1
        user["streak"] += 1
        if user["streak"] > user["best_streak"]:
            user["best_streak"] = user["streak"]
    else:
        user["streak"] = 0
    update_user(user_id, {
        "total_answers": user["total_answers"],
        "correct_answers": user["correct_answers"],
        "streak": user["streak"],
        "best_streak": user["best_streak"],
    })
    return user


def mark_word_learned(user_id, word):
    user = get_user(user_id)
    if word not in user["words_learned"]:
        user["words_learned"].append(word)
        update_user(user_id, {"words_learned": user["words_learned"]})


def mark_word_mastered(user_id, word):
    user = get_user(user_id)
    if word not in user["words_mastered"]:
        user["words_mastered"].append(word)
        update_user(user_id, {"words_mastered": user["words_mastered"]})


def update_spaced_repetition(user_id, word, quality):
    user = get_user(user_id)
    sr = user.get("spaced_repetition", {})
    if word not in sr:
        sr[word] = {"interval_idx": 0, "next_review": datetime.now().isoformat(), "correct_count": 0, "total_count": 0}

    sr[word]["total_count"] += 1
    if quality >= 3:
        sr[word]["correct_count"] += 1
        idx = sr[word]["interval_idx"]
        if idx < len(REPETITION_INTERVALS) - 1:
            idx += 1
        sr[word]["interval_idx"] = idx
        days = REPETITION_INTERVALS[idx]
    else:
        sr[word]["interval_idx"] = 0
        days = REPETITION_INTERVALS[0]

    sr[word]["next_review"] = (datetime.now() + timedelta(days=days)).isoformat()
    update_user(user_id, {"spaced_repetition": sr})


def get_words_due_for_review(user_id):
    user = get_user(user_id)
    sr = user.get("spaced_repetition", {})
    now = datetime.now()
    due = []
    for word, info in sr.items():
        next_review = datetime.fromisoformat(info["next_review"])
        if next_review <= now:
            due.append(word)
    return due


def increment_games_played(user_id):
    user = get_user(user_id)
    user["games_played"] += 1
    update_user(user_id, {"games_played": user["games_played"]})


def update_leaderboard():
    data = _load_progress()
    lb = []
    for uid, user in data["users"].items():
        lb.append({
            "user_id": uid,
            "username": user.get("username", "Unknown"),
            "points": user.get("points", 0),
        })
    lb.sort(key=lambda x: x["points"], reverse=True)
    data["leaderboard"] = lb
    _save_progress(data)


def get_leaderboard(limit=10):
    update_leaderboard()
    data = _load_progress()
    return data["leaderboard"][:limit]


def set_username(user_id, username):
    update_user(user_id, {"username": username})


def set_grade(user_id, grade):
    update_user(user_id, {"grade": grade})