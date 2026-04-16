import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import learn_card_kb, learn_answer_kb, main_menu_kb, grade_selection_kb
import database as db
import words as wlib

router = Router()

E = wlib.esc


class LearnStates(StatesGroup):
    learning = State()


@router.callback_query(F.data.startswith("learn_grade_"))
async def start_learning(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    grade = int(callback.data.split("_")[-1])
    all_words = wlib.get_words_for_grade(grade)

    if not all_words:
        await callback.message.edit_text("No words available for this grade.", reply_markup=main_menu_kb())
        await callback.answer()
        return

    await state.set_state(LearnStates.learning)
    await state.update_data(words=all_words, current_index=0, grade=grade)

    word = all_words[0]
    text = (
        f"📚 <b>Learn Mode — Grade {grade}</b>\n\n"
        f"{word['emoji']} <b>{E(word['word'].upper())}</b>\n\n"
        f"Try to remember the translation!\n"
        f"Tap <b>Show Answer</b> to check."
    )
    await callback.message.edit_text(text, reply_markup=learn_card_kb(word["id"]), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("show_"), LearnStates.learning)
async def show_answer(callback: CallbackQuery, state: FSMContext):
    word_id = int(callback.data.split("_")[1])
    word = wlib.get_word_by_id(word_id)

    if not word:
        await callback.answer("Word not found.")
        return

    antonym_text = f"\n🔄 <b>Antonym:</b> {E(word['antonym'])}" if word.get('antonym') else ""
    synonyms_text = f"\n🔗 <b>Synonyms:</b> {E(', '.join(word['synonyms']))}" if word.get('synonyms') else ""

    if word.get("degrees") and word["degrees"].get("comparative"):
        degrees_text = f"\n📊 <b>Degrees:</b> {word['word']} → {word['degrees']['comparative']} → {word['degrees']['superlative']}"
    else:
        degrees_text = ""

    text = (
        f"📚 <b>Answer</b>\n\n"
        f"{word['emoji']} <b>{E(word['word'].upper())}</b> — {E(word['translation'])}\n\n"
        f"💬 <i>\"{E(word['example'])}\"</i>\n"
        f"📝 {E(word.get('example_translation', ''))}\n"
        f"{antonym_text}"
        f"{synonyms_text}"
        f"{degrees_text}"
    )
    await callback.message.edit_text(text, reply_markup=learn_answer_kb(word["id"]), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("rate_"), LearnStates.learning)
async def rate_word(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    word_id = int(parts[1])
    difficulty = parts[2]

    quality_map = {"easy": 5, "medium": 3, "hard": 1}
    quality = quality_map.get(difficulty, 3)

    word = wlib.get_word_by_id(word_id)
    if word:
        db.update_spaced_repetition(callback.from_user.id, word["word"], quality)
        if difficulty in ("easy", "medium"):
            db.mark_word_learned(callback.from_user.id, word["word"])

    emoji_map = {"easy": "✅", "medium": "📝", "hard": "🔁"}
    await callback.answer(f"{emoji_map.get(difficulty, '📝')} Rated as {difficulty}!")


@router.callback_query(F.data.startswith("learned_"), LearnStates.learning)
async def mark_learned(callback: CallbackQuery, state: FSMContext):
    word_id = int(callback.data.split("_")[1])
    word = wlib.get_word_by_id(word_id)

    if word:
        db.mark_word_learned(callback.from_user.id, word["word"])
        await callback.answer(f"✅ '{word['word']}' marked as learned!")
    else:
        await callback.answer("Word not found.")


@router.callback_query(F.data.startswith("mastered_"), LearnStates.learning)
async def mark_mastered(callback: CallbackQuery, state: FSMContext):
    word_id = int(callback.data.split("_")[1])
    word = wlib.get_word_by_id(word_id)

    if word:
        db.mark_word_mastered(callback.from_user.id, word["word"])
        db.add_points(callback.from_user.id, 5)
        await callback.answer(f"🏆 '{word['word']}' mastered! +5 points!")
    else:
        await callback.answer("Word not found.")


@router.callback_query(F.data == "learn_next", LearnStates.learning)
async def next_word(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    words = data.get("words", [])
    current_index = data.get("current_index", 0) + 1
    grade = data.get("grade", 5)

    if current_index >= len(words):
        await callback.message.edit_text(
            "🎉 <b>You've reviewed all words for this session!</b>\n\n"
            "Great job! Come back later or try a different grade.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(current_index=current_index)
    word = words[current_index]

    text = (
        f"📚 <b>Learn Mode — Grade {grade}</b> ({current_index + 1}/{len(words)})\n\n"
        f"{word['emoji']} <b>{E(word['word'].upper())}</b>\n\n"
        f"Try to remember the translation!\n"
        f"Tap <b>Show Answer</b> to check."
    )
    await callback.message.edit_text(text, reply_markup=learn_card_kb(word["id"]), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("skip_"), LearnStates.learning)
async def skip_word(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    words = data.get("words", [])
    current_index = data.get("current_index", 0) + 1

    if current_index >= len(words):
        await callback.message.edit_text(
            "🎉 <b>Session complete!</b>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(current_index=current_index)
    word = words[current_index]
    grade = data.get("grade", 5)

    text = (
        f"📚 <b>Learn Mode — Grade {grade}</b> ({current_index + 1}/{len(words)})\n\n"
        f"{word['emoji']} <b>{E(word['word'].upper())}</b>\n\n"
        f"Try to remember the translation!"
    )
    await callback.message.edit_text(text, reply_markup=learn_card_kb(word["id"]), parse_mode="HTML")
    await callback.answer()