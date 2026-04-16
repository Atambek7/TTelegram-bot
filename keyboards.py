from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import GRADES


def reply_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Learn"), KeyboardButton(text="🎮 Games")],
            [KeyboardButton(text="📊 Comparison"), KeyboardButton(text="👥 Multiplayer")],
            [KeyboardButton(text="📈 Stats"), KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action..."
    )


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Learn", callback_data="menu_learn"),
         InlineKeyboardButton(text="🎮 Games", callback_data="menu_games")],
        [InlineKeyboardButton(text="📊 Comparison", callback_data="menu_comparison"),
         InlineKeyboardButton(text="👥 Multiplayer", callback_data="menu_multiplayer")],
        [InlineKeyboardButton(text="📈 Stats", callback_data="menu_stats")],
    ])


def grade_selection_kb(prefix="learn"):
    rows = []
    for grade in GRADES:
        rows.append([InlineKeyboardButton(
            text=f"Grade {grade}",
            callback_data=f"{prefix}_grade_{grade}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def learn_card_kb(word_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Show Answer", callback_data=f"show_{word_id}")],
        [InlineKeyboardButton(text="⏭ Skip", callback_data=f"skip_{word_id}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu_learn")],
    ])


def learn_answer_kb(word_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😀 Easy", callback_data=f"rate_{word_id}_easy"),
         InlineKeyboardButton(text="😐 Medium", callback_data=f"rate_{word_id}_medium"),
         InlineKeyboardButton(text="😰 Hard", callback_data=f"rate_{word_id}_hard")],
        [InlineKeyboardButton(text="✅ Mark Learned", callback_data=f"learned_{word_id}"),
         InlineKeyboardButton(text="🏆 Mark Mastered", callback_data=f"mastered_{word_id}")],
        [InlineKeyboardButton(text="⏭ Next Word", callback_data="learn_next"),
         InlineKeyboardButton(text="⬅️ Back", callback_data="menu_learn")],
    ])


def games_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Quiz", callback_data="game_quiz"),
         InlineKeyboardButton(text="🔄 Antonyms", callback_data="game_antonyms")],
        [InlineKeyboardButton(text="📊 Comparison", callback_data="game_comparison"),
         InlineKeyboardButton(text="🧩 Context", callback_data="game_context")],
        [InlineKeyboardButton(text="⚡ Speed Round", callback_data="game_speed"),
         InlineKeyboardButton(text="🎲 Mixed", callback_data="game_mixed")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")],
    ])


def answer_options_kb(options, prefix, correct_idx):
    rows = []
    for i, option in enumerate(options):
        rows.append([InlineKeyboardButton(
            text=option,
            callback_data=f"{prefix}_{i}_{correct_idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def speed_answer_kb(options, question_id):
    rows = []
    for i, option in enumerate(options):
        rows.append([InlineKeyboardButton(
            text=option,
            callback_data=f"spd_{i}_{question_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def continue_or_stop_kb(game_type):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Continue", callback_data=f"game_{game_type}"),
         InlineKeyboardButton(text="⬅️ Menu", callback_data="back_to_menu")],
    ])


def repeat_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Start Review", callback_data="repeat_start"),
         InlineKeyboardButton(text="📊 Review Stats", callback_data="repeat_stats")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")],
    ])


def repeat_answer_kb(word_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😀 Knew it", callback_data=f"rr_{word_id}_knew"),
         InlineKeyboardButton(text="😰 Forgot", callback_data=f"rr_{word_id}_forgot")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu_repeat")],
    ])


def multiplayer_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Leaderboard", callback_data="mp_leaderboard"),
         InlineKeyboardButton(text="📊 My Rank", callback_data="mp_my_rank")],
        [InlineKeyboardButton(text="🎲 Group Game", callback_data="mp_group_game"),
         InlineKeyboardButton(text="⚔️ 1v1 Challenge", callback_data="mp_challenge")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")],
    ])


def group_game_kb(session_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Join", callback_data=f"gg_join_{session_id}"),
         InlineKeyboardButton(text="▶️ Start", callback_data=f"gg_start_{session_id}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="gg_cancel")],
    ])


def stats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Progress", callback_data="stats_progress"),
         InlineKeyboardButton(text="🏆 Leaderboard", callback_data="stats_leaderboard")],
        [InlineKeyboardButton(text="📊 Accuracy", callback_data="stats_accuracy"),
         InlineKeyboardButton(text="📚 Words", callback_data="stats_words")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")],
    ])


def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")],
    ])