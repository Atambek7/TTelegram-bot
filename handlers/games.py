import asyncio
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    answer_options_kb, games_menu_kb, continue_or_stop_kb,
    speed_answer_kb, main_menu_kb, grade_selection_kb
)
import database as db
import words as wlib
from config import QUESTIONS_PER_ROUND, SPEED_ROUND_TIME, POINTS_CORRECT, POINTS_STREAK_BONUS, POINTS_SPEED_BONUS

router = Router()


class GameStates(StatesGroup):
    quiz = State()
    antonyms = State()
    comparison = State()
    context = State()
    speed = State()
    mixed = State()


def E(text):
    return wlib.esc(text)


def _unique_options(options, correct_answer, min_count=4):
    seen = set()
    unique = []
    for opt in options:
        if opt not in seen:
            unique.append(opt)
            seen.add(opt)
    while len(unique) < min_count:
        unique.append(correct_answer)
    return unique[:max(min_count, len(unique))]


def generate_quiz_question(words, all_words):
    word = random.choice(words)
    options = _unique_options(
        [word["translation"]] + [w["translation"] for w in random.sample(all_words, min(3, len(all_words)))],
        word["translation"]
    )
    random.shuffle(options)
    correct_idx = options.index(word["translation"])
    return {
        "type": "quiz",
        "word": word,
        "question": f"🎯 What does <b>{E(word['emoji'])} {E(word['word'])}</b> mean?",
        "options": options,
        "correct_idx": correct_idx,
        "correct_text": word["translation"],
    }


def generate_antonym_question(words, all_words):
    eligible = [w for w in words if w.get("antonym")]
    if not eligible:
        return None
    word = random.choice(eligible)
    antonym = word["antonym"]
    all_antonyms = list(set(w["antonym"] for w in all_words if w.get("antonym") and w["antonym"] != antonym))
    random.shuffle(all_antonyms)
    options = _unique_options([antonym] + all_antonyms[:6], antonym)
    random.shuffle(options)
    correct_idx = options.index(antonym)
    return {
        "type": "antonyms",
        "word": word,
        "question": f"🔄 What is the <b>antonym</b> of <b>{E(word['emoji'])} {E(word['word'])}</b> ({E(word['translation'])})?",
        "options": options,
        "correct_idx": correct_idx,
        "correct_text": antonym,
    }


def generate_comparison_question(words, all_words):
    eligible = [w for w in words if w.get("degrees") and w["degrees"].get("comparative")]
    if not eligible:
        return None
    word = random.choice(eligible)
    deg = word["degrees"]
    patterns = [
        {
            "question": f"📊 Fill in the blank:\n<b>{E(word['word'])} → {E(deg['comparative'])} → ___?</b>",
            "answer": deg["superlative"],
            "template": "superlative",
        },
        {
            "question": f"📊 What is the <b>comparative</b> form of <b>{E(word['emoji'])} {E(word['word'])}</b>?",
            "answer": deg["comparative"],
            "template": "comparative",
        },
    ]
    pattern = random.choice(patterns)
    other_degrees = list(set(
        w["degrees"][pattern["template"]]
        for w in all_words
        if w.get("degrees") and w["degrees"].get("comparative") and w["degrees"].get(pattern["template"]) and w["degrees"][pattern["template"]] != pattern["answer"]
    ))
    random.shuffle(other_degrees)
    options = _unique_options([pattern["answer"]] + other_degrees[:6], pattern["answer"])
    random.shuffle(options)
    correct_idx = options.index(pattern["answer"])
    return {
        "type": "comparison",
        "word": word,
        "question": pattern["question"],
        "options": options,
        "correct_idx": correct_idx,
        "correct_text": pattern["answer"],
    }


def generate_context_question(words, all_words):
    word = random.choice(words)
    blanked = word.get("sentence_blank", "")
    if not blanked or "___" not in blanked:
        example = word.get("example", "")
        if word["word"] in example:
            blanked = example.replace(word["word"], "___", 1)
        else:
            blanked = f"The weather is very ___ today."

    options = _unique_options(
        [word["word"]] + [w["word"] for w in random.sample(all_words, min(3, len(all_words)))],
        word["word"]
    )
    random.shuffle(options)
    correct_idx = options.index(word["word"])
    return {
        "type": "context",
        "word": word,
        "question": f"🧩 Choose the correct adjective:\n\n<i>{E(blanked)}</i>",
        "options": options,
        "correct_idx": correct_idx,
        "correct_text": word["word"],
    }


async def start_game(callback: CallbackQuery, state: FSMContext, game_type: str, grade: int = None):
    await state.clear()
    if grade is None:
        user = db.get_user(callback.from_user.id)
        grade = user.get("grade", 5)

    words = wlib.get_words_for_grade(grade)
    all_words = wlib.get_all_words()

    if len(words) < 4:
        words = wlib.get_all_words()[:50]
        random.shuffle(words)

    state_mapping = {
        "quiz": GameStates.quiz,
        "antonyms": GameStates.antonyms,
        "comparison": GameStates.comparison,
        "context": GameStates.context,
        "speed": GameStates.speed,
        "mixed": GameStates.mixed,
    }

    await state.set_state(state_mapping[game_type])
    await state.update_data(
        grade=grade,
        score=0,
        question_num=0,
        total_questions=QUESTIONS_PER_ROUND,
        words=words,
        all_words=all_words,
        answers=[],
    )
    db.increment_games_played(callback.from_user.id)
    await send_question(callback, state, game_type)


async def send_question(callback: CallbackQuery, state: FSMContext, game_type: str):
    data = await state.get_data()
    words = data.get("words", [])
    all_words = data.get("all_words", [])
    question_num = data.get("question_num", 0)
    total = data.get("total_questions", QUESTIONS_PER_ROUND)

    if not words:
        await callback.message.edit_text("No words available. Try a different grade.", reply_markup=main_menu_kb(), parse_mode="HTML")
        await state.clear()
        return

    generators = {
        "quiz": lambda: generate_quiz_question(words, all_words),
        "antonyms": lambda: generate_antonym_question(words, all_words),
        "comparison": lambda: generate_comparison_question(words, all_words),
        "context": lambda: generate_context_question(words, all_words),
        "mixed": lambda: random.choice([
            lambda: generate_quiz_question(words, all_words),
            lambda: generate_antonym_question(words, all_words),
            lambda: generate_comparison_question(words, all_words),
            lambda: generate_context_question(words, all_words),
        ])(),
    }

    question = None
    attempts = 0
    while question is None and attempts < 10:
        question = generators.get(game_type, generators["quiz"])()
        attempts += 1

    if question is None:
        question = generate_quiz_question(words, all_words)

    score = data.get("score", 0)
    streak = db.get_user(callback.from_user.id).get("streak", 0)

    prefix_map = {"quiz": "quiz", "antonyms": "anto", "comparison": "comp", "context": "ctxt", "mixed": "mxgd"}
    prefix = prefix_map.get(game_type, "quiz")
    kb = answer_options_kb(question["options"], prefix, question["correct_idx"])

    await state.update_data(current_question=question, game_type=game_type)

    streak_text = f" 🔥{streak}" if streak >= 3 else ""
    header = f"Question {question_num + 1}/{total} | Score: {score}{streak_text}\n\n"

    try:
        await callback.message.edit_text(
            header + question["question"],
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            header + question["question"],
            reply_markup=kb,
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("quiz_grade_"))
async def quiz_grade(callback: CallbackQuery, state: FSMContext):
    grade = int(callback.data.split("_")[-1])
    await start_game(callback, state, "quiz", grade)
    await callback.answer()


@router.callback_query(F.data.startswith("comp_grade_"))
async def comparison_grade(callback: CallbackQuery, state: FSMContext):
    grade = int(callback.data.split("_")[-1])
    await start_game(callback, state, "comparison", grade)
    await callback.answer()


@router.callback_query(F.data == "game_quiz")
async def game_quiz(callback: CallbackQuery, state: FSMContext):
    await start_game(callback, state, "quiz")


@router.callback_query(F.data == "game_antonyms")
async def game_antonyms(callback: CallbackQuery, state: FSMContext):
    await start_game(callback, state, "antonyms")


@router.callback_query(F.data == "game_comparison")
async def game_comparison(callback: CallbackQuery, state: FSMContext):
    await start_game(callback, state, "comparison")


@router.callback_query(F.data == "game_context")
async def game_context(callback: CallbackQuery, state: FSMContext):
    await start_game(callback, state, "context")


@router.callback_query(F.data == "game_mixed")
async def game_mixed(callback: CallbackQuery, state: FSMContext):
    await start_game(callback, state, "mixed")


@router.callback_query(F.data == "game_speed")
async def game_speed(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = db.get_user(callback.from_user.id)
    grade = user.get("grade", 5)
    words = wlib.get_words_for_grade(grade)
    all_words = wlib.get_all_words()

    if len(words) < 4:
        words = wlib.get_all_words()[:50]
        random.shuffle(words)

    await state.set_state(GameStates.speed)
    import time
    await state.update_data(
        grade=grade,
        score=0,
        question_num=0,
        words=words,
        all_words=all_words,
        start_time=time.time(),
        answers=[],
    )
    db.increment_games_played(callback.from_user.id)

    question = generate_quiz_question(words, all_words)
    await state.update_data(current_question=question)
    kb = speed_answer_kb(question["options"], question["correct_idx"])
    await callback.message.edit_text(
        f"⚡ <b>Speed Round!</b> (60 seconds)\n\n"
        f"Question 1 | Score: 0\n\n{question['question']}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


async def handle_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question = data.get("current_question")
    if not question:
        await callback.answer("Game session expired. Start a new game from the menu.")
        try:
            await callback.message.edit_text("⏰ <b>Session expired.</b> Start a new game!", reply_markup=main_menu_kb(), parse_mode="HTML")
        except Exception:
            pass
        await state.clear()
        return

    parts = callback.data.split("_")
    selected_idx = int(parts[1])
    correct_idx = int(parts[2])
    game_type = data.get("game_type", "quiz")

    is_correct = selected_idx == correct_idx
    user = db.record_answer(callback.from_user.id, is_correct)

    points = 0
    if is_correct:
        points = POINTS_CORRECT
        if user.get("streak", 0) >= 3:
            points += POINTS_STREAK_BONUS
        db.add_points(callback.from_user.id, points)

    score = data.get("score", 0) + points
    question_num = data.get("question_num", 0) + 1
    total = data.get("total_questions", QUESTIONS_PER_ROUND)
    await state.update_data(score=score, question_num=question_num)

    if is_correct:
        result_text = f"✅ <b>Correct!</b> +{points} points\n"
    else:
        correct_option = question["options"][correct_idx]
        result_text = f"❌ <b>Wrong!</b> The correct answer was: <b>{E(correct_option)}</b>\n"

    streak = user.get("streak", 0)
    if streak >= 5:
        result_text += f"🔥 Streak: {streak}!\n"

    if question_num >= total:
        final_text = (
            f"🎉 <b>Game Over!</b>\n\n"
            f"📊 Score: <b>{score}</b> / {total * POINTS_CORRECT}\n"
            f"✅ Correct: {user.get('correct_answers', 0)}\n"
            f"📝 Total: {user.get('total_answers', 0)}\n\n"
            f"{result_text}"
        )
        await callback.message.edit_text(final_text, reply_markup=continue_or_stop_kb(game_type), parse_mode="HTML")
        await state.clear()
    else:
        await state.update_data(score=score)
        result_text += f"\n⏳ Next question..."
        try:
            await callback.message.edit_text(result_text, parse_mode="HTML")
        except Exception:
            await callback.message.answer(result_text, parse_mode="HTML")
        await asyncio.sleep(1)
        await send_question(callback, state, game_type)


@router.callback_query(F.data.startswith("quiz_"))
async def quiz_answer(callback: CallbackQuery, state: FSMContext):
    await handle_answer(callback, state)


@router.callback_query(F.data.startswith("anto_"))
async def antonyms_answer(callback: CallbackQuery, state: FSMContext):
    await handle_answer(callback, state)


@router.callback_query(F.data.startswith("comp_"))
async def comparison_answer(callback: CallbackQuery, state: FSMContext):
    await handle_answer(callback, state)


@router.callback_query(F.data.startswith("ctxt_"))
async def context_answer(callback: CallbackQuery, state: FSMContext):
    await handle_answer(callback, state)


@router.callback_query(F.data.startswith("mxgd_"))
async def mixed_answer(callback: CallbackQuery, state: FSMContext):
    await handle_answer(callback, state)


@router.callback_query(F.data.startswith("spd_"))
async def speed_answer(callback: CallbackQuery, state: FSMContext):
    import time

    data = await state.get_data()
    elapsed = time.time() - data.get("start_time", time.time())

    if elapsed > SPEED_ROUND_TIME:
        score = data.get("score", 0)
        q_num = data.get("question_num", 0)
        await callback.message.edit_text(
            f"⏰ <b>Time's up!</b>\n\n"
            f"📊 You answered <b>{q_num}</b> questions!\n"
            f"🏆 Score: <b>{score}</b> points",
            reply_markup=continue_or_stop_kb("speed"),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    question = data.get("current_question")
    if not question:
        await callback.answer("Session expired.")
        await state.clear()
        return

    parts = callback.data.split("_")
    selected_idx = int(parts[1])
    correct_idx = int(parts[2])

    is_correct = selected_idx == correct_idx
    user = db.record_answer(callback.from_user.id, is_correct)

    points = 0
    if is_correct:
        points = POINTS_CORRECT + POINTS_SPEED_BONUS
        db.add_points(callback.from_user.id, points)

    score = data.get("score", 0) + points
    question_num = data.get("question_num", 0) + 1
    await state.update_data(score=score, question_num=question_num)

    remaining = max(0, int(SPEED_ROUND_TIME - elapsed))

    words = data.get("words", [])
    all_words = data.get("all_words", [])
    if not words:
        words = wlib.get_all_words()[:50]
        random.shuffle(words)
        await state.update_data(words=words)

    new_question = generate_quiz_question(words, all_words)
    await state.update_data(current_question=new_question)

    kb = speed_answer_kb(new_question["options"], new_question["correct_idx"])
    emoji = "✅" if is_correct else "❌"

    await callback.message.edit_text(
        f"⚡ <b>Speed Round!</b> ⏱ {remaining}s remaining\n\n"
        f"{emoji} Score: <b>{score}</b> | Q#{question_num}\n\n{new_question['question']}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()