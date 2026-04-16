import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_kb, grade_selection_kb, stats_kb, reply_menu_kb
import database as db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user(message.from_user.id)
    db.set_username(message.from_user.id, message.from_user.username or message.from_user.first_name)
    text = (
        "👋 Welcome to <b>Adjective Master</b>!\n\n"
        "🥰 My name is Jane and I'm your English adjective learning assistant!\n\n"
        "Learn, play, and master adjectives for grades 5-9.\n\n"
        "Use the buttons below or the menu to get started:"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Adjective Master — Help</b>\n\n"
        "📚 <b>Learn</b> — Browse flashcards with adjectives\n"
        "🎮 <b>Games</b> — Quiz, Antonyms, Comparison, Context, Speed\n"
        "📊 <b>Comparison</b> — Practice degrees of comparison\n"
        "👥 <b>Multiplayer</b> — Compete with others\n"
        "📈 <b>Stats</b> — Track your progress\n\n"
        "Commands:\n"
        "/start — Main menu\n"
        "/help — This help message\n"
        "/cancel — Cancel current action\n"
        "/setgrade — Change your grade level\n"
        "/stats — View statistics"
    )
    await message.answer(text, reply_markup=reply_menu_kb(), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✅ Action cancelled. You're back to the main menu.",
        reply_markup=reply_menu_kb(),
        parse_mode="HTML"
    )


@router.message(Command("setgrade"))
async def cmd_setgrade(message: Message):
    await message.answer("Select your grade level:", reply_markup=grade_selection_kb("setgrade"))


@router.message(Command("stats"))
async def cmd_stats_menu(message: Message):
    await message.answer("📈 <b>Statistics</b>", reply_markup=stats_kb(), parse_mode="HTML")


@router.message(F.text == "📚 Learn")
async def text_learn(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📚 <b>Learn Mode</b>\n\nSelect your grade to start learning adjectives:",
        reply_markup=grade_selection_kb("learn"),
        parse_mode="HTML"
    )


@router.message(F.text == "🎮 Games")
async def text_games(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import games_menu_kb
    await message.answer(
        "🎮 <b>Games</b>\n\nChoose a game mode:",
        reply_markup=games_menu_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Comparison")
async def text_comparison(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📊 <b>Comparison Practice</b>\n\nSelect your grade:",
        reply_markup=grade_selection_kb("comp"),
        parse_mode="HTML"
    )


@router.message(F.text == "👥 Multiplayer")
async def text_multiplayer(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import multiplayer_menu_kb
    await message.answer(
        "👥 <b>Multiplayer</b>\n\nChallenge others or check the leaderboard!",
        reply_markup=multiplayer_menu_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📈 Stats")
async def text_stats(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import stats_kb as st_kb
    await message.answer(
        "📈 <b>Statistics</b>\n\nChoose what to view:",
        reply_markup=st_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "❓ Help")
async def text_help(message: Message):
    await cmd_help(message)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Main Menu</b>\n\nChoose an option:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setgrade_grade_"))
async def set_grade(callback: CallbackQuery):
    grade = int(callback.data.split("_")[-1])
    db.set_grade(callback.from_user.id, grade)
    await callback.message.edit_text(
        f"✅ Grade level set to <b>{grade}</b>!\n\nYou'll get adjectives appropriate for your level.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_learn")
async def menu_learn(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📚 <b>Learn Mode</b>\n\nSelect your grade to start learning adjectives:",
        reply_markup=grade_selection_kb("learn"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_games")
async def menu_games(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards import games_menu_kb
    await callback.message.edit_text(
        "🎮 <b>Games</b>\n\nChoose a game mode:",
        reply_markup=games_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_comparison")
async def menu_comparison(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📊 <b>Comparison Practice</b>\n\nSelect your grade:",
        reply_markup=grade_selection_kb("comp"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_multiplayer")
async def menu_multiplayer(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards import multiplayer_menu_kb
    await callback.message.edit_text(
        "👥 <b>Multiplayer</b>\n\nChallenge others or check the leaderboard!",
        reply_markup=multiplayer_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_stats")
async def menu_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards import stats_kb as st_kb
    await callback.message.edit_text(
        "📈 <b>Statistics</b>\n\nChoose what to view:",
        reply_markup=st_kb(),
        parse_mode="HTML"
    )
    await callback.answer()