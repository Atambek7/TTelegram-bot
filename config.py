import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMINS = []

GRADES = [5, 6, 7, 8, 9]

POINTS_CORRECT = 10
POINTS_SPEED_BONUS = 5
POINTS_STREAK_BONUS = 3

QUESTIONS_PER_ROUND = 10
SPEED_ROUND_TIME = 60

REPETITION_INTERVALS = [1, 3, 7, 14, 30]