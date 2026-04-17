import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_ID   # пока закомментируем

logging.basicConfig(level=logging.INFO)

print("=== DEBUG ENVIRONMENT VARIABLES ===")
print("BOT_TOKEN from env:", os.getenv("BOT_TOKEN"))
print("API_FOOTBALL_KEY from env:", bool(os.getenv("API_FOOTBALL_KEY")))
print("ADMIN_ID from env:", os.getenv("ADMIN_ID"))
print("=================================")

# Временно жёстко прописываем токен для теста
BOT_TOKEN = "8618587406:AAFQI1WhoE3YGH2Y3OWCp1TbQLQCin2qcyc"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
