import random
import string
import time
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import multiplayer_menu_kb, group_game_kb, main_menu_kb, answer_options_kb
import database as db
import words as wlib
from config import POINTS_CORRECT

router = Router()

active_group_sessions = {}
active_challenges = {}


def generate_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def E(text):
    return wlib.esc(text)


class GroupStates(StatesGroup):
    waiting_players = State()
    in_game = State()


class ChallengeStates(StatesGroup):
    answering = State()


@router.callback_query(F.data == "mp_leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    leaderboard = db.get_leaderboard(10)
    if not leaderboard:
        await callback.message.edit_text(
            "🏆 <b>Leaderboard</b>\n\nNo players yet! Be the first!",
            reply_markup=multiplayer_menu_kb(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "🏆 <b>Leaderboard — Top 10</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, entry in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"{i + 1}."
        username = E(entry.get("username", "Unknown"))
        points = entry.get("points", 0)
        text += f"{medal} <b>{username}</b> — {points} pts\n"

    await callback.message.edit_text(text, reply_markup=multiplayer_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "mp_my_rank")
async def my_rank(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    leaderboard = db.get_leaderboard(0)
    uid = str(callback.from_user.id)

    rank = next((i + 1 for i, e in enumerate(leaderboard) if e["user_id"] == uid), len(leaderboard))

    text = (
        f"📊 <b>Your Stats</b>\n\n"
        f"🏅 Rank: <b>#{rank}</b>\n"
        f"🏆 Points: <b>{user.get('points', 0)}</b>\n"
        f"📚 Words Learned: <b>{len(user.get('words_learned', []))}</b>\n"
        f"✅ Correct Answers: <b>{user.get('correct_answers', 0)}</b>\n"
        f"📝 Total Answers: <b>{user.get('total_answers', 0)}</b>\n"
        f"🔥 Best Streak: <b>{user.get('best_streak', 0)}</b>\n"
        f"🎮 Games Played: <b>{user.get('games_played', 0)}</b>"
    )
    await callback.message.edit_text(text, reply_markup=multiplayer_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "mp_group_game")
async def create_group_game(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    code = generate_code()
    all_words = wlib.get_all_words()
    random.shuffle(all_words)
    questions = all_words[:10]

    active_group_sessions[code] = {
        "creator_id": callback.from_user.id,
        "creator_name": callback.from_user.username or callback.from_user.first_name,
        "players": {str(callback.from_user.id): {
            "name": callback.from_user.username or callback.from_user.first_name,
            "score": 0,
        }},
        "status": "waiting",
        "current_question": 0,
        "questions": questions,
        "all_words": all_words,
        "message_ids": {str(callback.from_user.id): callback.message.message_id},
    }

    await state.set_state(GroupStates.waiting_players)
    await state.update_data(session_code=code)

    text = (
        f"🎲 <b>Group Game Created!</b>\n\n"
        f"🆔 Code: <b>{code}</b>\n\n"
        f"Share this code with friends!\n"
        f"They can join using: /join {code}\n\n"
        f"Players: 1"
    )
    await callback.message.edit_text(text, reply_markup=group_game_kb(code), parse_mode="HTML")
    await callback.answer()


@router.message(F.text.startswith("/join"))
async def join_group_game(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Usage: /join <code>\nExample: /join ABC123")
        return

    code = parts[1].upper()
    if code not in active_group_sessions:
        await message.answer("❌ Game session not found. Check the code and try again.")
        return

    session = active_group_sessions[code]
    if session["status"] != "waiting":
        await message.answer("❌ This game has already started!")
        return

    uid = str(message.from_user.id)
    if uid in session["players"]:
        await message.answer("You're already in this game!")
        return

    session["players"][uid] = {
        "name": message.from_user.username or message.from_user.first_name,
        "score": 0,
    }

    player_list = "\n".join(f"• {p['name']}" for p in session["players"].values())
    await message.answer(
        f"✅ <b>Joined game {code}!</b>\n\nPlayers:\n{player_list}\n\n"
        f"Wait for the creator to start the game!",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("gg_join_"))
async def join_group_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Use the command: /join <code> to join a group game!")


@router.callback_query(F.data.startswith("gg_start_"))
async def start_group_game(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_")[-1]
    if code not in active_group_sessions:
        await callback.answer("Session not found.")
        return

    session = active_group_sessions[code]
    if callback.from_user.id != session["creator_id"]:
        await callback.answer("Only the creator can start the game!")
        return

    session["status"] = "active"
    session["current_question"] = 0

    await state.set_state(GroupStates.in_game)
    await state.update_data(session_code=code)

    question_word = session["questions"][0]
    all_words = session["all_words"]
    options = _unique_options(
        [question_word["translation"]] + [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        question_word["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(question_word["translation"])

    kb = answer_options_kb(options, "gpgr", correct_idx)

    text = (
        f"🎲 <b>Group Game</b> — Question 1/{len(session['questions'])}\n\n"
        f"What does <b>{question_word['emoji']} {E(question_word['word'])}</b> mean?"
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gg_cancel")
async def cancel_group_game(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data.get("session_code", "")
    if code in active_group_sessions:
        del active_group_sessions[code]
    await callback.message.edit_text("❌ Group game cancelled.", reply_markup=multiplayer_menu_kb(), parse_mode="HTML")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("gpgr_"))
async def group_game_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data.get("session_code", "")
    if code not in active_group_sessions:
        await callback.answer("Session expired.")
        await state.clear()
        return

    session = active_group_sessions[code]
    parts = callback.data.split("_")
    selected_idx = int(parts[1])
    correct_idx = int(parts[2])
    q_idx = session["current_question"]

    uid = str(callback.from_user.id)
    is_correct = selected_idx == correct_idx
    if is_correct and uid in session["players"]:
        session["players"][uid]["score"] += POINTS_CORRECT

    db.record_answer(callback.from_user.id, is_correct)

    emoji = "✅" if is_correct else "❌"
    correct_text = session["questions"][q_idx]["translation"] if q_idx < len(session.get("questions", [])) else ""

    session["current_question"] = q_idx + 1
    await state.update_data(session_code=code)

    await callback.answer(f"{emoji} {'Correct!' if is_correct else f'Wrong! Answer: {correct_text}'}")

    if q_idx + 1 >= len(session.get("questions", [])):
        results = "🏆 <b>Game Over! Results:</b>\n\n"
        sorted_players = sorted(session["players"].items(), key=lambda x: x[1]["score"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid_p, player) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else f"{i + 1}."
            results += f"{medal} <b>{E(player['name'])}</b> — {player['score']} pts\n"
        await callback.message.edit_text(results, reply_markup=main_menu_kb(), parse_mode="HTML")
        del active_group_sessions[code]
        await state.clear()
        return

    question_word = session["questions"][q_idx + 1]
    all_words = session["all_words"]
    options = _unique_options(
        [question_word["translation"]],
        [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        question_word["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(question_word["translation"])

    kb = answer_options_kb(options, "gpgr", correct_idx)
    text = (
        f"🎲 <b>Group Game</b> — Question {q_idx + 2}/{len(session['questions'])}\n\n"
        f"What does <b>{question_word['emoji']} {E(question_word['word'])}</b> mean?"
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


def _unique_options(base, extras, correct, min_count=4):
    options = list(base) + list(extras[:6])
    seen = set()
    unique = []
    for opt in options:
        if opt not in seen:
            unique.append(opt)
            seen.add(opt)
    while len(unique) < min_count:
        unique.append(correct)
    return unique[:max(min_count, len(unique))]


@router.callback_query(F.data == "mp_challenge")
async def start_challenge(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    code = generate_code()
    all_words = wlib.get_all_words()
    random.shuffle(all_words)
    questions = all_words[:10]

    active_challenges[code] = {
        "creator_id": callback.from_user.id,
        "creator_name": callback.from_user.username or callback.from_user.first_name,
        "creator_score": 0,
        "creator_current_q": 0,
        "opponent_id": None,
        "opponent_name": "",
        "opponent_score": 0,
        "opponent_current_q": 0,
        "status": "waiting",
        "questions": questions,
        "all_words": all_words,
    }

    await state.set_state(ChallengeStates.answering)
    await state.update_data(challenge_code=code, is_creator=True)

    q = questions[0]
    options = _unique_options(
        [q["translation"]],
        [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        q["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(q["translation"])

    kb = answer_options_kb(options, "ch1v", correct_idx)

    text = (
        f"⚔️ <b>1v1 Challenge Created!</b>\n\n"
        f"🆔 Code: <b>{code}</b>\n\n"
        f"Your first question:\n\n"
        f"What does <b>{q['emoji']} {E(q['word'])}</b> mean?"
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

    other_text = (
        f"📤 Share this code with a friend!\n"
        f"They accept with: /accept {code}\n\n"
        f"You've started playing already. Good luck!"
    )
    await callback.message.answer(other_text, parse_mode="HTML")


@router.message(F.text.startswith("/accept"))
async def accept_challenge(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Usage: /accept <code>\nExample: /accept ABC123")
        return

    code = parts[1].upper()
    if code not in active_challenges:
        await message.answer("❌ Challenge not found. Check the code and try again.")
        return

    challenge = active_challenges[code]
    if challenge["status"] == "finished":
        await message.answer("❌ This challenge is already finished.")
        return

    if challenge["opponent_id"] is not None and challenge["opponent_id"] != message.from_user.id:
        await message.answer("❌ This challenge already has an opponent.")
        return

    challenge["opponent_id"] = message.from_user.id
    challenge["opponent_name"] = message.from_user.username or message.from_user.first_name
    challenge["status"] = "active"

    questions = challenge["questions"]
    all_words = challenge["all_words"]

    q = questions[0]
    options = _unique_options(
        [q["translation"]],
        [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        q["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(q["translation"])

    kb = answer_options_kb(options, "ch1v", correct_idx)

    await state.set_state(ChallengeStates.answering)
    await state.update_data(challenge_code=code, is_creator=False)

    await message.answer(
        f"⚔️ <b>Challenge Accepted!</b>\n\n"
        f"You vs <b>{E(challenge['creator_name'])}</b>\n\n"
        f"Let's go! Question 1/10:\n\n"
        f"What does <b>{q['emoji']} {E(q['word'])}</b> mean?",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ch1v_"))
async def challenge_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data.get("challenge_code", "")

    if code not in active_challenges:
        await callback.answer("Challenge expired.")
        await state.clear()
        try:
            await callback.message.edit_text("⏰ Challenge expired. Back to menu.", reply_markup=main_menu_kb(), parse_mode="HTML")
        except Exception:
            pass
        return

    challenge = active_challenges[code]
    is_creator = data.get("is_creator", True)

    parts = callback.data.split("_")
    selected_idx = int(parts[1])
    correct_idx = int(parts[2])

    is_correct = selected_idx == correct_idx

    if is_creator:
        challenge["creator_current_q"] = challenge.get("creator_current_q", 0) + 1
        if is_correct:
            challenge["creator_score"] += POINTS_CORRECT
    else:
        challenge["opponent_current_q"] = challenge.get("opponent_current_q", 0) + 1
        if is_correct:
            challenge["opponent_score"] += POINTS_CORRECT

    db.record_answer(callback.from_user.id, is_correct)

    current_q_idx = challenge["creator_current_q"] if is_creator else challenge["opponent_current_q"]

    questions = challenge["questions"]
    all_words = challenge["all_words"]

    if current_q_idx >= len(questions):
        c_score = challenge["creator_score"]
        o_score = challenge["opponent_score"]
        c_name = E(challenge["creator_name"])
        o_name = E(challenge["opponent_name"] or "Waiting...")

        if challenge["creator_current_q"] >= len(questions) and challenge["opponent_current_q"] >= len(questions):
            if o_score > c_score:
                winner = f"🎉 <b>{o_name} wins!</b>"
            elif c_score > o_score:
                winner = f"🎉 <b>{c_name} wins!</b>"
            else:
                winner = "🤝 <b>It's a tie!</b>"
            challenge["status"] = "finished"
            del active_challenges[code]
            await state.clear()
        else:
            if o_score > c_score:
                winner = f"Currently <b>{o_name}</b> is leading!"
            elif c_score > o_score:
                winner = f"Currently <b>{c_name}</b> is leading!"
            else:
                winner = "Currently tied!"

        emoji = "✅" if is_correct else "❌"
        await callback.message.edit_text(
            f"⚔️ <b>Challenge — You're done!</b>\n\n"
            f"{emoji} You scored <b>{c_score if is_creator else o_score}</b> points!\n\n"
            f"⚔️ <b>{E(challenge['creator_name'])}</b>: {challenge['creator_score']} pts\n"
            f"⚔️ <b>{E(challenge.get('opponent_name', 'Waiting...'))}</b>: {challenge['opponent_score']} pts\n\n"
            f"{winner}",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await callback.answer("✅ Correct!" if is_correct else "❌ Wrong!")
        return

    q = questions[current_q_idx]
    options = _unique_options(
        [q["translation"]],
        [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        q["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(q["translation"])

    kb = answer_options_kb(options, "ch1v", correct_idx)
    emoji = "✅" if is_correct else "❌"

    await callback.message.edit_text(
        f"⚔️ {emoji} Question {current_q_idx + 1}/10\n\n"
        f"What does <b>{q['emoji']} {E(q['word'])}</b> mean?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer("✅ Correct!" if is_correct else "❌ Wrong!")