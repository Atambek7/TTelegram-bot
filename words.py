import json
import os
import random

ADJECTIVES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adjectives.json")

_cached_data = None


def load_adjectives():
    global _cached_data
    if _cached_data is not None:
        return _cached_data
    with open(ADJECTIVES_FILE, "r", encoding="utf-8") as f:
        _cached_data = json.load(f)
    return _cached_data


def get_all_words():
    return load_adjectives()["adjectives"]


def get_words_for_grade(grade):
    words = [w for w in get_all_words() if w["grade"] <= grade + 1 and w.get("translation")]
    random.shuffle(words)
    return words


def get_word_by_id(word_id):
    return next((w for w in get_all_words() if w["id"] == word_id), None)


def esc(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text