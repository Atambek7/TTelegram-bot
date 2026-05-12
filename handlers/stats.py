from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import stats_kb, main_menu_kb
import database as db
import words as wlib

router = Router()


def E(text):
    return wlib.esc(text)


@router.callback_query(F.data == "stats_progress")
async def stats_progress(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    total = user.get("total_answers", 0)
    correct = user.get("correct_answers", 0)
    accuracy = (correct / total * 100) if total > 0 else 0
    words_learned = len(user.get("words_learned", []))
    words_mastered = len(user.get("words_mastered", []))

    text = (
        f"📈 <b>Your Progress</b>\n\n"
        f"🏆 Points: <b>{user.get('points', 0)}</b>\n"
        f"🎮 Games Played: <b>{user.get('games_played', 0)}</b>\n"
        f"✅ Correct Answers: <b>{correct}</b>\n"
        f"📝 Total Answers: <b>{total}</b>\n"
        f"📊 Accuracy: <b>{accuracy:.1f}%</b>\n"
        f"🔥 Current Streak: <b>{user.get('streak', 0)}</b>\n"
        f"⚡ Best Streak: <b>{user.get('best_streak', 0)}</b>\n\n"
        f"📚 Words Learned: <b>{words_learned}</b>\n"
        f"🏆 Words Mastered: <b>{words_mastered}</b>"
    )
    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_leaderboard")
async def stats_leaderboard(callback: CallbackQuery):
    leaderboard = db.get_leaderboard(15)
    if not leaderboard:
        await callback.message.edit_text(
            "🏆 <b>Leaderboard</b>\n\nNo players yet!",
            reply_markup=stats_kb(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "🏆 <b>Leaderboard — Top 15</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, entry in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"{i + 1}."
        username = E(entry.get("username", "Unknown"))
        points = entry.get("points", 0)
        text += f"{medal} <b>{username}</b> — {points} pts\n"

    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_accuracy")
async def stats_accuracy(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    total = user.get("total_answers", 0)
    correct = user.get("correct_answers", 0)
    accuracy = (correct / total * 100) if total > 0 else 0

    bar_length = 20
    filled = int(accuracy / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)

    grade = "Beginner"
    if accuracy >= 90:
        grade = "Master"
    elif accuracy >= 80:
        grade = "Expert"
    elif accuracy >= 70:
        grade = "Advanced"
    elif accuracy >= 60:
        grade = "Intermediate"
    elif accuracy >= 40:
        grade = "Elementary"

    text = (
        f"📊 <b>Accuracy Stats</b>\n\n"
        f"{bar}\n"
        f"<b>{accuracy:.1f}%</b> accuracy\n\n"
        f"✅ Correct: <b>{correct}</b>\n"
        f"❌ Wrong: <b>{total - correct}</b>\n"
        f"📝 Total: <b>{total}</b>\n\n"
        f"🏅 Level: <b>{grade}</b>"
    )
    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_words")
async def stats_words(callback: CallbackQuery):
    all_words_data = wlib.load_adjectives()
    user = db.get_user(callback.from_user.id)
    learned = user.get("words_learned", [])
    mastered = user.get("words_mastered", [])
    total_words = len(all_words_data["adjectives"])

    learned_display = ", ".join(learned[-20:]) if learned else "None yet"
    mastered_display = ", ".join(mastered[-20:]) if mastered else "None yet"

    if len(learned) > 20:
        learned_display += f"... (+{len(learned) - 20} more)"
    if len(mastered) > 20:
        mastered_display += f"... (+{len(mastered) - 20} more)"

    pct_learned = (len(learned) / total_words * 100) if total_words > 0 else 0
    pct_mastered = (len(mastered) / total_words * 100) if total_words > 0 else 0

    text = (
        f"📚 <b>Words Overview</b>\n\n"
        f"📖 Total available: <b>{total_words}</b>\n"
        f"✅ Learned: <b>{len(learned)}</b> ({pct_learned:.0f}%)\n"
        f"🏆 Mastered: <b>{len(mastered)}</b> ({pct_mastered:.0f}%)\n\n"
        f"📝 <b>Recently Learned:</b>\n{learned_display}\n\n"
        f"🏆 <b>Recently Mastered:</b>\n{mastered_display}"
    )
    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="HTML")
    await callback.answer()