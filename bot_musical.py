import os
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError, NetworkError, TimedOut
import yt_dlp

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token desde variable de entorno
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")

# Logo mejorado del bot
LOGO = """
logo_combinado = r"""
⡔⢎⡲⢜⡒⣆⢣⡒⢆⠖⡲⣐⠲⡐⢆⠲⠄⣆⠰⡀⢆⠠⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⢀⠀⡠⢀⠤⣀⠤⡠⡔⣤⢢⠔⡤⢒⠤⡠⢄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢆⠲⡐⢆⢳⡘⢦⡙
⠩⢞⡰⢋⡴⢊⡵⢨⠍⣎⠱⣌⢣⡙⡌⢣⡉⡄⢣⠘⡠⠂⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠒⠤⠡⢌⡐⠤⣁⢎⡰⣩⠖⣥⠯⣵⣹⢶⢯⡾⣵⣫⣞⡵⣎⡖⣥⢊⠖⣰⡄⡀⢀⠀⠀⠀⣀⣤⢴⣲⢮⡿⣝⠖⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠌⡒⣉⠎⢦⡙⢦⠹
⡹⢢⠝⣸⠰⣍⠲⣉⠞⡤⢓⡌⢲⠰⡉⢆⠴⡁⢆⠱⢀⠡⠀⠀⠀⠀⢀⠀⡀⠄⡀⠠⠐⡌⢠⠑⠂⡌⣈⢆⡑⣎⠼⣡⢏⡾⣱⢯⣟⡾⣽⣳⢯⣟⣯⣟⡷⣻⡼⣻⢧⣟⡶⣫⣞⣱⢾⣱⣮⣶⡿⣿⣻⢾⣿⡟⢯⡿⡍⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡑⠌⡜⠢⢍⢆⠫
⡣⣍⠚⡥⢓⡌⠳⣌⠚⡔⢣⠜⡡⢊⠱⠈⠔⠈⠀⢂⠀⢂⠐⠌⢢⡑⣎⡔⣐⠢⢅⢧⣘⡔⣣⢋⠷⣈⠳⣎⠵⣊⢿⡹⣞⣷⡻⣟⡾⣝⣳⢯⣟⣾⣳⢯⣟⣳⢯⢽⡻⣾⣽⣳⢯⣿⢿⣿⢯⣷⣿⢿⡽⠏⠣⠘⣰⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⢨⠰⣉⠎⣌⠣
⠵⣌⡹⢰⢋⡜⡱⢌⠓⠌⠂⢉⠀⠡⠀⠄⠠⢈⠐⡠⢉⢆⡹⣜⢢⡜⣌⠻⣭⣟⡾⣮⣳⠞⣥⠻⡜⣭⢻⣜⢮⡝⣮⢷⡻⣼⣻⢭⣻⡝⣮⢟⣮⠷⣯⢿⡾⣭⢻⡔⢏⡷⡭⢯⣟⣿⣿⣻⣿⣻⠞⡯⠀⡀⢀⢣⣳⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⣠⢓⠰⣊⠔⣣
⠲⡌⢖⡩⢒⡬⡑⠎⠀⠄⠌⠠⢈⢀⡀⠄⣂⢦⣩⢱⣋⠮⡵⢎⡧⣝⣎⡳⡱⢎⠻⡵⣯⢿⣜⡷⣽⢶⣻⣞⣟⡾⣳⠯⡝⢧⣋⢾⣱⣻⢼⣛⡾⢻⠭⣏⠳⣍⠳⣜⢣⢞⡱⢫⡝⣾⢓⡯⢖⡣⣉⠐⣠⣐⣭⣻⣿⡝⣮⡁⠄⣤⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠲⣁⢎⡱⢌⡚⡴
⠳⡸⢡⡚⠅⠂⠁⠀⠌⡐⠈⠄⠂⢠⠐⡩⢜⢦⡓⢯⠼⡹⡜⢯⡜⡶⢪⠵⣋⢮⡑⠞⣬⢛⡾⣽⣳⢯⣗⢯⡞⣵⢣⣛⠼⣑⣎⢷⣫⡽⣯⣳⣝⡫⢞⡤⢳⡌⢷⣈⢣⠊⡔⢡⠚⡬⢏⣿⣻⢷⡿⣿⣻⢿⣻⣟⠿⣜⢲⡍⡖⢯⣷⣯⣿⣟⡾⣶⡒⠦⠀⠀⠠⢓⡌⢦⠱⢎⡱⢲
⡵⢃⡗⡘⠄⠀⠀⠀⠄⠐⠐⠈⠌⣂⢱⡙⣎⢧⢻⣌⡳⡽⣹⠮⡽⣍⢯⡳⡽⣎⢭⡓⢦⢫⣜⡳⢯⣟⣾⡹⣞⣥⢿⣜⡳⣝⣮⣟⢷⡻⣵⡛⡶⢍⡳⣜⢧⣛⡳⣎⢶⡱⡜⣤⠹⣜⡳⣺⡽⣣⢟⡷⣫⢏⡷⣞⡿⣌⠳⡼⡹⣭⢿⣿⣻⡽⠛⠄⠁⠀⠀⠀⡘⢥⠚⡔⡫⢬⡱⢣
⡲⣍⠒⠁⠀⠀⠀⢂⠠⠠⢄⢣⠞⣜⢧⡽⣘⣮⡓⢮⡳⡝⣧⣛⠶⣩⠳⣙⢷⣫⢮⡝⣎⠷⢮⡽⣳⣞⣳⢿⣹⣞⣯⢾⣹⡽⣾⡽⣎⢷⢢⢛⡌⢇⠳⣎⠟⡼⡱⡘⢮⡱⣟⣼⢣⢯⣜⣳⢭⣓⢎⣳⡙⣎⠱⣝⠾⣥⢃⠳⡵⣹⠾⣉⠁⠀⠀⠀⠀⠀⠀⠀⡍⢦⡙⢬⡑⠧⡜⢣
⠴⠈⠀⠀⠀⠀⠐⠠⢁⠒⣬⢚⡽⣞⣯⠾⣽⡲⣏⢧⡙⣙⢦⡙⢮⡥⢳⡜⣮⣛⢧⡻⣜⣫⢷⣹⣳⢾⡽⣯⢷⣻⢮⣟⠶⣽⡳⢏⡘⢧⠊⠂⠜⣈⠣⡘⢜⢲⡡⢓⠆⡱⢙⢮⡛⣮⢳⡽⣎⡝⣮⢧⡹⣤⢙⡮⢻⡜⣎⠱⣇⡛⡆⠁⠀⠀⠀⠀⠀⠀⠀⠰⡘⡰⡘⢆⡙⠲⡰⢍
⡣⠁⠀⠀⠀⠁⠠⡐⣌⠲⣬⢻⡽⣹⢞⣻⠴⣙⠬⣓⠹⡔⣢⠙⢦⣙⢣⠞⡶⢭⣎⡵⣎⢶⣫⣞⢷⡯⣿⡽⣯⣟⢿⣺⡝⡷⡍⢒⣾⢲⠡⡞⢀⠣⢒⠱⣊⡄⢧⢋⠔⡡⢎⠰⣹⡜⣧⢻⢶⠱⣌⢳⣛⢶⢫⡜⣣⠟⡴⣛⡬⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⢡⢂⠱⣈⠒⠬⡑⣘⠢
⡃⠀⠀⠀⠀⡈⢁⠒⠠⢃⢆⡣⢽⡹⢾⣭⢟⡼⣢⢥⢣⡙⡔⢫⠦⣍⢮⡝⣎⠷⣎⠷⣎⣗⡳⣮⢿⣼⣳⢿⣳⣯⣟⣳⣟⠱⡈⠶⣹⢃⢣⡝⠠⢂⠡⠒⢤⡘⢦⠣⡘⠴⣈⢇⠳⡼⣱⢻⣯⣇⡘⠢⡝⢮⡳⡜⢥⡛⡴⢣⠝⡂⠀⠀⠀⠀⠀⠀⠀⠀⠐⡠⢊⠐⠤⡉⠆⡑⡠⢃
⠀⠀⠀⠀⠀⢀⠂⡌⢢⠉⠦⠱⢣⢟⣳⢮⣟⡲⣍⢎⡣⡝⣜⢣⠞⣼⢣⡿⣽⣻⣎⠿⣜⢮⣳⢯⣟⡾⣽⣻⣟⣾⡝⡱⡎⢒⡍⢒⢡⣞⡰⡽⢰⡈⢄⡉⠆⡜⢢⢇⡱⢱⠈⣎⢳⣙⢧⡛⣼⣿⣌⢳⢈⠷⣹⣹⢢⠱⡙⢦⠙⠀⠀⠀⠀⠀⠀⠀⠀⢀⠂⠡⢀⠊⡐⢡⠘⠤⡁⢌
⠀⠀⠀⠀⠈⠄⡘⢄⠣⡘⠰⢩⡙⣮⢯⢿⣜⣳⡜⣦⢣⡝⣬⢳⢻⡜⣯⣛⡷⣳⣭⡟⣾⡹⣞⣻⢾⡽⣷⣿⣻⣾⠄⣹⠸⡄⢺⠄⡣⢞⠴⣙⣥⣞⠤⣘⠰⠌⠦⡌⡔⢣⠈⡔⢣⠜⣧⢑⣯⢸⣟⠮⡈⢏⡳⣇⢮⡓⣍⠂⠀⠀⠀⠀⠀⠀⠀⠀⢀⠂⠌⠠⢁⠂⡁⢆⡘⠄⡑⢂
⠀⠀⠀⢀⠁⠂⠌⡂⢦⢁⠣⣥⢻⣜⣯⢾⣹⢖⣹⠲⣇⠾⣔⢯⣳⣟⣳⣯⣟⣷⣳⣟⣶⣻⡽⣯⣟⡿⣷⣻⡿⣽⣧⡔⢉⠞⡠⢃⠱⣈⠶⣡⢟⣾⡷⢎⡱⡎⢱⠏⡘⡀⠂⠌⠡⢚⡵⣊⠼⣿⣏⡓⠸⣌⡷⣝⣮⡽⣞⣯⣿⣟⡷⣷⡶⣤⡀⢀⠂⠰⡈⢐⠂⢂⠅⠂⡔⠨⡐⠡
⠀⠀⠄⠂⢌⡘⠤⢓⠠⣌⢲⣬⢳⠾⣭⢿⡽⣛⣮⢟⡼⢻⡜⣯⣳⠾⣽⣞⡿⣞⣷⣻⣾⢷⣟⣯⡿⣽⡿⣿⡽⣟⡾⣽⣆⠢⡑⢨⠑⠤⡓⣌⠾⣽⠻⣌⡳⢁⢛⡆⢡⠀⡁⠈⠆⣙⠲⡭⣞⡿⢶⣭⢳⣮⠝⣋⠴⢩⢿⣻⣷⣯⢿⣜⡻⣷⣽⣣⡿⣤⡈⠢⡌⠀⢈⠐⠀⠡⢀⠡
⡐⢌⠢⢁⠢⣘⢱⡊⠴⣈⠧⣎⢣⡟⣼⢣⡟⡽⣎⢿⡼⢯⡽⣶⢯⣟⡷⣯⢿⡽⣯⡷⣿⣻⣾⡿⣽⡿⣽⡷⣟⣯⢟⡾⡵⢠⠑⢢⢉⠲⡱⢌⡳⣌⠳⣜⡧⠐⣊⠆⡁⠆⡐⢈⠰⡈⢇⡳⣝⣻⢳⢮⡻⢤⣌⡤⠘⠄⢫⢿⣷⣿⣿⡾⣽⣳⢯⣷⣻⠵⣛⢦⠺⡔⠀⢀⠈⠀⡀⠂
⣈⠦⢁⠂⡐⢌⡲⣍⢖⣡⢛⣬⣳⢽⣺⣝⡾⣵⣫⢟⡾⣯⣟⣷⣻⡾⣽⢯⣿⣽⣷⣿⣻⣿⣽⣿⣻⡽⣷⣻⡽⣞⡽⢾⡝⡠⢉⠦⣉⠖⣡⢏⡲⣍⣷⣻⡇⠱⣨⢃⠰⣁⠂⢄⠂⠱⣈⠷⣩⠷⠯⠳⡙⢶⣦⣉⠉⢆⠡⣎⣿⡿⣟⣿⢷⣯⣻⣿⣿⣻⡽⣾⣹⢮⡁⠄⢂⠔⡠⠘
⡔⠨⠄⡐⢈⢎⡵⣚⢮⢖⡯⡶⢯⡟⣧⢿⣽⣳⢯⣿⣟⣷⡿⣯⣿⣿⢿⣿⣾⣿⣾⢿⡽⣷⣻⡞⣷⢻⡵⣳⡝⣮⢽⡻⡜⠰⣉⠶⡱⢎⡵⢮⡵⣞⡷⣯⠇⡱⡇⢎⠔⣠⠋⡄⢂⠱⣈⢷⣡⠈⠤⠑⠌⢣⠂⠽⡐⢢⠱⢿⣧⣿⣿⢿⣿⢶⡿⣷⣻⣿⣳⣿⣳⣏⣿⢈⠢⢌⠠⡁
⢈⡑⠂⠄⡊⠜⡒⣭⢚⣎⡳⣝⢧⡿⣽⣻⢾⣽⣻⢷⣯⣟⣿⣿⣿⣿⡿⣟⣯⣷⣟⡿⣽⢳⢧⢻⡜⣧⢻⣕⡻⡼⢯⠷⣁⠳⣌⠳⣭⢻⡼⣯⣟⠾⣽⣻⠅⢾⡇⡎⠼⢠⠓⡌⢀⢆⡹⢮⣓⡙⠌⡐⢈⠀⢈⠠⢀⢃⡽⢾⣷⣿⣿⣿⣿⣯⣿⡷⣻⣿⢿⣽⣿⡞⣽⣣⠜⣠⢃⠜
⡡⢬⡑⢢⡑⢌⠲⡥⣏⢶⣙⢮⣻⢼⡳⣏⡿⣾⡽⣯⣟⣿⣿⣿⣻⣾⢿⣟⡿⣾⣜⡻⣜⢯⡺⡱⢎⡵⣋⢶⡹⣝⡯⢃⠤⡓⣬⢛⡼⢯⣟⡷⣯⡟⣷⣻⣌⠺⣷⣝⡺⣄⣛⠴⣬⢎⣵⢫⡙⠶⣌⠐⡂⢌⢂⢆⢣⡚⣥⢿⣿⣿⣿⣿⣿⢿⣷⣻⣵⣿⣻⡾⣽⣿⣝⣯⢎⡱⢊⡜
⡑⢦⡙⢦⡑⣌⣳⡽⣎⢷⡹⣎⢷⣫⢷⣏⣿⣳⢿⡽⣿⣿⣿⣽⣯⣟⡿⣾⣝⡳⣬⠳⣭⢲⠳⣍⣏⢶⡹⣎⢷⡙⢆⢡⠒⡝⢦⡻⣼⢿⣽⣻⢷⣻⡵⣻⡼⣥⠹⣾⡷⣯⢾⣿⣧⣛⢎⠡⣈⠒⡄⢣⠘⢤⢋⡜⢦⡹⢼⣩⣿⣿⣿⣯⣟⣿⣿⣳⣿⣿⣳⣿⣳⣿⣟⣾⢣⠜⡤⠰
⠙⣦⢹⢦⡗⣾⣱⢻⣼⣳⣟⡾⣯⣟⡿⣞⡷⣯⡿⣽⣿⣿⣯⣷⣟⡾⣽⢳⠮⣕⢎⡳⢬⢳⣙⢮⡜⣮⢳⡭⢎⠡⢌⢢⡛⣼⢣⣟⣽⣻⢾⡽⣯⣗⡻⣵⢻⣜⡻⣞⡽⡻⢿⡿⣿⣼⠎⠲⢄⡣⡔⢢⡉⢆⠎⣜⢢⣝⣿⡿⣟⣿⣿⣿⣿⣿⣿⣳⣿⣿⣿⣞⣿⣯⣟⣮⠃⡞⢌⠳
⡝⣆⢯⠳⣙⠶⣭⡟⣞⠷⣞⣽⣳⢯⡿⣽⣟⣷⡿⣯⣿⣿⣟⣷⢯⡿⣭⢏⡳⢎⢧⡙⣎⠳⣎⢧⣛⡼⣣⠟⠠⡁⢎⡲⣙⠶⣫⣞⡷⣯⣟⣿⡳⣭⢗⣯⢳⡞⣽⢲⡽⡹⣇⡻⣍⣏⡐⠠⢀⠀⡉⢳⢟⡞⡾⣜⡶⣽⢾⣿⣿⣾⣿⣿⣻⣷⣿⣯⣿⣿⣿⣞⣯⣿⡞⣧⠓⡌⢌⡑
⣟⡌⣆⢣⡝⡺⣵⢫⢯⣟⢮⡷⣯⢿⡽⣷⣻⣿⣿⣿⣟⣿⣯⣟⣯⢷⣫⢞⣱⢫⢖⡹⢬⢳⢎⡳⢎⡷⡍⢂⠱⡘⢦⢳⡭⣻⢵⣻⢞⣷⣻⢾⣝⢮⡻⣜⣧⢻⡽⣓⠞⡱⠋⠑⠉⠀⠁⠂⠄⢂⠐⡈⣾⢿⣽⣯⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣻⣯⣿⣷⣿⣿⡽⣿⣽⠣⡉⠔⢢⠐
⣿⡜⡆⢧⢺⡵⣫⢟⡾⣞⣭⢷⣯⢿⣽⣿⣿⡿⣷⣿⣻⣯⣿⣾⣽⡳⣏⢾⣡⠟⣬⡝⣎⢧⡫⣝⡹⡞⢠⠁⢦⡙⣎⢧⢷⣹⢾⣭⣟⢾⡹⣏⢾⣫⢷⣻⣾⢿⡜⢁⡒⠤⡑⣌⠢⡐⠀⠄⠠⡈⢜⣣⢿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⢿⣽⣿⣿⣿⣾⣿⡿⣿⡽⣇⡘⠌⡄⢃
⣷⡹⣞⣭⢷⣹⣳⢯⡿⣽⣞⣿⣾⣿⣿⣿⡿⣿⣟⣷⡿⣯⣷⢿⡾⣽⣝⡮⢧⣛⢦⡽⡸⡖⣽⣘⢧⠑⡂⢍⢦⡹⣎⣟⣮⢟⣯⢾⣹⢾⣽⣹⣳⡽⢾⡽⣯⣿⡤⢣⠜⣡⠓⣌⢒⡡⢊⠌⢢⠑⡎⡴⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢷⣿⣿⣿⣿⣿⢿⣿⡽⣿⢷⣿⣻⡜⠰⡈⠆
⢷⣻⡵⣯⣟⣷⣯⢿⣽⣳⣿⣿⣾⡿⣟⣷⣿⡿⣟⡾⣽⣳⢯⣟⡿⣽⢾⣽⣳⡽⣞⣶⡹⣜⢶⣩⠆⡱⢌⠎⣶⣹⡾⣽⡞⣿⣚⣯⢯⣟⣾⣳⡽⣞⣯⢿⣽⡾⣷⡡⢞⢤⢫⡔⣣⠜⣥⠪⣅⠯⣔⢣⢏⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⡿⣟⣿⡿⣿⣟⣾⣿⡼⣧⣟⣿⣽⠡⡜⡰
⣿⣳⡿⣿⡽⣷⣿⣻⣿⣿⡿⣯⣷⢿⣻⣯⣷⢿⡿⣽⣳⢯⣛⣮⡝⣯⢻⣎⡷⣽⣫⢶⣻⠽⣞⠧⢨⡑⢎⡾⣵⣫⢷⣝⡾⢧⣟⣾⣻⣞⡷⣽⣳⣟⡾⣻⣞⣿⡿⣧⣏⢮⢳⡜⣥⢻⡔⡯⣜⡞⣬⠳⣞⡼⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⢯⣿⣽⣿⣿⣿⣿⣽⣷⣟⣾⢣⡛⡴⢣
⡷⣏⠿⣝⣻⢯⡷⣿⡿⣷⣿⣟⣯⣿⣳⣟⡾⣯⣟⡷⣯⡟⣵⢯⡞⣵⠳⣎⢷⡳⣭⢳⣏⠿⣭⠓⡤⣙⣾⡽⣾⣽⣻⢾⡽⣟⣾⢷⣯⣿⣽⢷⣻⢾⣹⣗⡿⣞⣿⣿⣿⣮⢷⡹⣎⢷⡺⡵⣳⢺⠵⣻⡜⢶⣻⣿⣿⣿⣾⣿⢿⣿⣿⣿⣽⣿⣿⣿⣿⣿⣽⣿⣿⣻⣿⣯⡇⢻⡜⢣
⠶⣭⢻⡼⣭⢿⣹⢷⡿⣽⢿⣾⣟⣾⣳⢯⣟⣳⢯⣽⡳⣿⡹⣞⡽⣞⡽⣎⢷⡹⣎⢷⡺⣝⢧⢫⢔⣣⣟⣿⣷⣳⣯⢿⣽⢯⣟⡿⣾⢷⣯⢿⡽⣯⢷⡾⣽⣻⣾⣽⣿⣿⣿⣳⡽⣎⢷⡹⢧⣏⢯⢧⣝⣳⣿⣿⣿⣿⣿⣾⣻⣿⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡿⣷⣜⢣
⡽⣎⡷⣹⢖⡯⣻⢽⢯⣻⢯⣿⣿⣷⣻⣟⡾⣝⡯⣖⡻⢵⣫⢷⡹⣎⢷⡹⣎⢷⡹⣎⢷⣩⠞⡽⣎⣷⣻⣿⡿⣿⣽⣿⣾⣟⣯⣿⣽⢿⡾⣯⡿⣽⣯⣟⡷⣟⣾⣿⣾⢿⣿⣿⣿⣯⢿⣽⣳⢮⣛⢮⣾⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣾⣿⣿⣷⣛⢮⣿⣝⢻⡇
⢷⡹⣞⣥⢻⡜⣧⡟⣯⢳⡿⣾⣿⣾⢿⣽⣻⡽⣞⡵⣭⢣⢇⢯⡱⢏⠾⣱⢫⡞⣵⢫⡞⡵⣫⢗⡽⣞⣷⡿⣿⣿⣿⣯⣿⢿⣻⣽⣾⣿⢿⣿⣽⣿⢾⣟⣿⢿⣻⣾⢿⣿⣽⣿⣻⣿⣿⣏⢷⣫⣽⣾⣿⣿⣿⣿⣿⣿⣿⣷⣻⣿⣿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢯⣿⣷⢳⡮⢧⢇
⣧⣝⡻⣼⢣⡟⣵⡻⣜⢯⣳⡟⣿⣿⡿⣯⣟⡿⣽⣷⣫⢗⡺⢦⡝⢮⣝⣣⢯⡽⣎⢳⡜⡱⢣⢞⡳⣿⣻⣽⡷⣿⣻⣿⣿⣿⣿⣿⣿⣯⣿⣯⣿⢾⣟⣿⡾⣟⣯⣿⣿⣿⣾⣿⣟⣿⣷⣿⣷⣯⣿⣿⣿⣿⣿⣿⣿⣿⣟⣾⣿⣿⣿⣿⣿⣿⣿⣿⢿⡽⣿⣿⣻⡿⣿⢿⣯⣿⣶⣈
⣳⣎⠷⣭⢻⣼⣳⢻⡜⣧⢳⡿⣹⣷⣿⢷⣻⣽⣻⢾⣽⣫⣝⣣⢛⢧⡞⣵⢫⡞⣥⠳⣌⠱⣋⢮⡱⢏⡿⣻⢿⣟⣿⣿⣾⣿⣽⣾⣿⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣿⣾⣿⣽⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⣿⣿⢿⣯⣿⢯⣷⢻⡞
⡿⣞⠿⣜⡳⣮⢳⡏⣞⡱⣏⢾⡱⢿⣻⣯⡷⣯⣟⣻⣞⡷⣎⢧⣛⢮⡽⣎⢷⡹⢆⠳⣌⠳⣘⢦⣙⢯⣞⣽⣫⢿⡿⢾⣻⣽⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣝⣻⣿⣿⣾⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⣿⣿⣿⣯⣗⢯⣻⣿⣿⣦
⡳⢭⡻⣭⢷⣫⠗⡮⣑⠳⣜⡯⡝⢯⣟⣷⣿⣳⢯⡷⢾⣽⣹⢯⣎⢷⡹⣎⢧⡝⢮⡑⢆⠳⣘⢦⡹⣞⡼⣎⣟⡧⣟⢧⣻⣞⡷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⣿⣎⣷⢻⣿⣳
⡝⣲⠹⣜⣫⢞⡹⡔⢬⢳⡹⣞⡹⣎⡽⣾⡷⣟⣯⣟⣟⡶⣏⣟⢾⣣⢟⡽⣺⡜⣣⠜⣎⡱⢣⢎⡵⣫⢞⡽⣞⡽⣞⣽⣳⢯⣟⡷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣾⣯⣿⣿⣷
⡜⣧⢻⡼⣱⢮⡱⢎⢧⡳⣝⢮⢳⡹⣜⠷⣿⣟⣷⣻⢾⡽⣞⠾⣭⢷⣛⣞⢧⡻⣼⡹⢦⣝⣣⢞⡵⣫⢯⢿⡽⣞⡽⣾⣽⣻⢾⡽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣞⣿⣾⣿⣿⣿⣿⣿⡽⣿
⣜⢧⡟⡼⢧⣻⢼⣩⠖⣯⢝⡮⢣⣝⠾⣭⢳⡿⣯⣟⣯⣟⣾⡻⣵⢫⣞⢮⣻⣵⡳⣽⠳⣎⡜⢯⡞⡷⣯⢿⣽⢻⣞⡷⣯⣟⣯⣟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣳⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣿⣿⣿⣿⣿⣽⣿⣿⣿⣟
⣮⢟⡾⣝⣳⡝⣮⣒⢻⡜⣮⢵⢫⣜⡻⣼⢳⣝⣻⣯⣿⢾⣳⢿⣝⣯⡞⣽⢲⣳⠽⣎⠽⣸⢙⢮⣹⢳⢯⡿⣞⣧⢿⣻⢷⣻⡾⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣯⣟⣷⣻⣿⣽⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣾⢿⣽⣻
⢞⣯⢿⣭⢗⣿⡱⣏⠷⣺⢼⡹⣞⡼⣳⣭⢳⣎⢷⡹⣯⣿⣟⣿⣞⣷⡿⣭⣟⣾⢻⣌⡳⢥⡚⢦⢣⣏⢯⡽⣯⣟⣯⣟⣯⡷⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣽⣻⢷⣻⡞⣽⣳⢯⡿⣷⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣟⣿⣿⣾⣽
⣻⡞⣟⡾⣯⢞⣽⣭⢷⡭⣞⡟⡶⣹⢓⢮⡳⣮⢷⣫⣽⢻⣯⣷⡿⣯⣿⡿⣽⣞⡿⣼⡹⣖⡹⢎⡳⣜⢧⣿⣱⣯⣿⢾⣯⣟⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⢯⣟⡷⣯⢟⣯⢷⣛⡷⣯⢿⣽⣻⣿⣞⣿⣿⣿⣿⣿⣻⣿⣿⣿⣿⣽⣿⣿⣟⣿⣾
⣵⣻⡽⣯⢷⣻⢾⡽⣞⣷⣹⢾⣷⡹⣎⢷⡹⣎⢿⣳⢯⣟⡾⣽⣟⡿⣿⠿⣿⣽⣻⣵⣻⣼⣳⢏⣷⣹⡞⣞⡷⣯⡿⣿⡾⣽⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢯⣟⡾⣽⡞⣿⣺⡽⣯⡽⣞⡿⣞⣷⣻⣿⡽⣾⣿⣿⣿⢿⣿⣿⣟⣿⣿⣿⣯⣿⣯⣿
⣞⣷⣻⡽⣯⣟⣾⢿⣿⣶⢯⣟⣾⣳⡝⣾⣹⡽⣫⣟⡿⣼⡹⢧⣻⣝⢯⣟⡷⣾⣱⣎⡗⣎⢗⡻⢞⡳⢻⣝⡻⣽⣙⣧⣿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣿⣿⣿⣿⣿⣿⣿⣻⢾⣽⣳⣟⡷⣯⢷⣯⢿⣽⡻⣽⣞⣿⣻⣽⢿⣿⣟⣯⣿⣿⣻⣾⣿⣿⣻⣿⣽⡿⣽
⣞⡷⣯⣟⡷⣯⣟⣿⣿⣿⣿⣞⡷⣯⣟⡶⣯⢷⣻⢮⣗⢧⣛⢯⣳⢾⡹⢮⡽⣳⠿⣼⣳⡞⣮⡱⣯⣞⡷⣾⣽⣷⣿⣻⣾⣭⣯⣽⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣟⣾⣳⢯⡿⣽⣻⠾⣝⣶⣻⣳⢟⡾⣽⡾⣟⣯⣿⣽⢿⣿⣻⣯⣷⣿⢿⣯⣿⢿⣻
⡾⣝⠳⣍⣿⢯⣿⣿⣾⣿⣿⣿⣟⣷⣯⢿⡽⣯⣳⣟⡾⣯⣟⣮⠽⣯⡟⣿⣳⣿⣻⣟⣷⣻⢳⢿⣽⣾⣿⣯⣿⣷⡿⣟⣿⡿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣳⣟⣯⣟⡷⣯⣟⡽⢶⣫⡽⢯⣻⢷⣻⣽⣻⣷⢿⣻⣿⣿⣳⣿⣽⡿⣿⣽⣿⣻
⠰⣌⣳⢾⣯⣿⣿⣽⣿⣿⣿⣿⣿⣿⣾⣿⣽⣳⡗⣾⣽⣳⢿⣞⡿⣵⢿⡧⣟⣷⡿⣿⣝⠯⣏⣎⢿⣳⣿⣻⡿⣏⣿⣿⣯⣷⢯⣿⡿⣿⣷⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣷⣾⣹⠾⣽⣳⢯⣟⣯⢷⣻⢯⣟⣯⢷⣯⢷⣻⣿⣻⣿⡿⣽⣷⡿⣿⡿⣽⣾⢿
⠽⣞⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣷⢯⣟⣯⣿⣽⣻⢞⣽⡞⣷⣻⢷⣋⠛⠶⣩⢞⡳⢻⡿⣽⢯⡷⣯⣿⣿⣿⣷⣿⣿⣿⣧⣻⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣞⣿⣽⣻⣭⠛⣿⢾⣽⣯⣟⡿⣾⣽⣻⣞⡿⣽⣾⣟⣷⡿⣟⣷⣿⣻⣽⡿⣽⣿
⢿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⢿⣻⢾⣳⣿⣛⡾⣽⣳⢿⣻⡼⣍⢲⢡⡚⣔⠫⡜⢯⢿⣽⣷⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢮⣟⣷⣯⡿⣶⣉⡻⢾⣽⣻⢷⣯⢷⣯⢿⣻⣷⣻⣽⢿⣻⣽⣾⣟⣯⣿⣟⣷

╔════════════════════════╗
║ 🐺🎸 BOT MUSICAL VERONICA 🎸🐺 ║
║ ♪♫ Tu Asistente Musical ♫♪ ║
╠════════════════════════╣
"""

print(logo_combinado)

"""

# Separadores visuales
SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
MINI_SEP = "─────────────────────"


class RateLimiter:
    """Control de rate limiting por usuario"""
    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = datetime.now()
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]
        
        if len(self.user_requests[user_id]) >= self.max_requests:
            return False
        
        self.user_requests[user_id].append(now)
        return True
    
    def get_wait_time(self, user_id):
        if not self.user_requests[user_id]:
            return 0
        oldest = min(self.user_requests[user_id])
        wait = self.window_seconds - (datetime.now() - oldest).seconds
        return max(0, wait)


class MusicBot:
    def __init__(self):
        self.user_searches = {}
        self.user_playlists = {}
        self.rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
        self.download_folder = 'downloads'
        os.makedirs(self.download_folder, exist_ok=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menú principal mejorado"""
        user_name = update.effective_user.first_name
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 Canciones", callback_data="menu_search_songs"),
                InlineKeyboardButton("🎤 Karaokes", callback_data="menu_search_karaoke")
            ],
            [
                InlineKeyboardButton("💿 Discografías", callback_data="menu_search_discography"),
                InlineKeyboardButton("📀 Álbumes", callback_data="menu_search_albums")
            ],
            [
                InlineKeyboardButton("📝 Crear Playlist Personalizada", callback_data="menu_create_playlist")
            ],
            [
                InlineKeyboardButton("❓ Ayuda & Guía", callback_data="menu_help"),
                InlineKeyboardButton("ℹ️ Info del Bot", callback_data="menu_info")
            ]
        ]
        
        welcome_text = f"{LOGO}\n"
        welcome_text += f"╭─────────────────────────╮\n"
        welcome_text += f"│  ✨ ¡Hola *{user_name}*! ✨  \n"
        welcome_text += f"╰─────────────────────────╯\n\n"
        welcome_text += f"🎼 *Bienvenido a tu asistente musical* 🎼\n\n"
        welcome_text += f"🔥 *Funciones disponibles:*\n"
        welcome_text += f"   • Búsqueda ilimitada de canciones\n"
        welcome_text += f"   • Karaokes de todo el mundo\n"
        welcome_text += f"   • Discografías completas\n"
        welcome_text += f"   • Álbumes completos\n"
        welcome_text += f"   • Playlists personalizadas\n\n"
        welcome_text += f"{SEPARATOR}\n"
        welcome_text += f"👇 *Selecciona una opción:* 👇"
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_main_menu(self, query):
        """Muestra el menú principal mejorado"""
        keyboard = [
            [
                InlineKeyboardButton("🎵 Canciones", callback_data="menu_search_songs"),
                InlineKeyboardButton("🎤 Karaokes", callback_data="menu_search_karaoke")
            ],
            [
                InlineKeyboardButton("💿 Discografías", callback_data="menu_search_discography"),
                InlineKeyboardButton("📀 Álbumes", callback_data="menu_search_albums")
            ],
            [
                InlineKeyboardButton("📝 Crear Playlist Personalizada", callback_data="menu_create_playlist")
            ],
            [
                InlineKeyboardButton("❓ Ayuda & Guía", callback_data="menu_help"),
                InlineKeyboardButton("ℹ️ Info del Bot", callback_data="menu_info")
            ]
        ]
        
        menu_text = f"{LOGO}\n"
        menu_text += f"🎼 *MENÚ PRINCIPAL* 🎼\n\n"
        menu_text += f"{SEPARATOR}\n"
        menu_text += f"👇 *Selecciona una opción:* 👇"
        
        await query.edit_message_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help mejorado"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main_menu")]]
        
        help_text = f"╔═══════════════════════════════╗\n"
        help_text += f"║    🐺 GUÍA COMPLETA DE USO 🐺   ║\n"
        help_text += f"╚═══════════════════════════════╝\n\n"
        
        help_text += f"┌─────────────────────────┐\n"
        help_text += f"│  🎵 *BUSCAR CANCIONES*  │\n"
        help_text += f"└─────────────────────────┘\n"
        help_text += f"Busca canciones por nombre o artista.\n"
        help_text += f"✨ Resultados ilimitados\n"
        help_text += f"📝 Ejemplo: `🕯️🩸🦇𝕍𝕀𝕃𝕄𝔸 𝔓𝔸𝕃𝕄𝔸 𝔢 𝕍𝔸𝕄𝔓𝕀ℝ𝕆𝕊🦇🕯️🩸` o `🌙🕌✨ 🐪💃 🕯️🔥🌵 𝕋𝔞𝔯𝔨𝔞𝔫 🌙🕌✨ 🐪💃 🕯️🔥🌵`\n\n"
        
        help_text += f"┌─────────────────────────┐\n"
        help_text += f"│  🎤 *BUSCAR KARAOKES*   │\n"
        help_text += f"└─────────────────────────┘\n"
        help_text += f"Encuentra versiones karaoke.\n"
        help_text += f"✨ Sin límites de búsqueda\n"
        help_text += f"📝 Ejemplo: `Bohemian Rhapsody`\n\n"
        
        help_text += f"┌─────────────────────────┐\n"
        help_text += f"│ 💿 *BUSCAR DISCOGRAFÍAS*│\n"
        help_text += f"└─────────────────────────┘\n"
        help_text += f"Toda la discografía de un artista.\n"
        help_text += f"✨ Álbumes, compilaciones, ediciones\n"
        help_text += f"📝 Ejemplo: `Metallica`, `Queen`\n\n"
        
        help_text += f"┌─────────────────────────┐\n"
        help_text += f"│  📀 *BUSCAR ÁLBUMES*    │\n"
        help_text += f"└─────────────────────────┘\n"
        help_text += f"Álbumes completos del mundo.\n"
        help_text += f"✨ Búsqueda sin restricciones\n"
        help_text += f"📝 Ejemplo: `The Wall`, `Thriller`\n\n"
        
        help_text += f"┌─────────────────────────┐\n"
        help_text += f"│  📝 *CREAR PLAYLIST*    │\n"
        help_text += f"└─────────────────────────┘\n"
        help_text += f"Tu lista personalizada de música.\n"
        help_text += f"✨ Agrega todas las que quieras\n\n"
        
        help_text += f"{SEPARATOR}\n\n"
        help_text += f"⚡ *LÍMITES:* 20 búsquedas/minuto\n"
        help_text += f"💾 *DESCARGAS:* MP3 de alta calidad\n"
        help_text += f"🔗 *ENLACES:* Directos de YouTube\n\n"
        help_text += f"{SEPARATOR}"
        
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    def format_duration(self, duration):
        """Formatea la duración de forma segura"""
        try:
            if duration is None or duration == 0:
                return ""
            duration = int(float(duration))
            minutes = duration // 60
            seconds = duration % 60
            return f" ⏱️{minutes}:{seconds:02d}"
        except (ValueError, TypeError):
            return ""
    
    async def search_music(self, query: str, max_results=100, karaoke=False):
        """Busca música en YouTube - TODOS LOS RESULTADOS"""
        search_query = f"{query} karaoke" if karaoke else query
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': f'ytsearch{max_results}',
            'socket_timeout': 30,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            'no_check_certificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Buscando: {search_query} (max: {max_results})")
                results = ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False)
                entries = results.get('entries', []) if results else []
                logger.info(f"Encontrados: {len(entries)} resultados")
                return entries
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def search_discography(self, artist: str, max_results=200):
        """Busca discografía completa de un artista"""
        search_queries = [
            f"{artist} discography full",
            f"{artist} all albums",
            f"{artist} complete discography",
            f"{artist} full album",
            f"{artist} álbum completo"
        ]
        
        all_results = []
        seen_ids = set()
        
        for search_query in search_queries:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{max_results // len(search_queries)}',
                'socket_timeout': 30,
                'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
                'no_check_certificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Buscando discografía: {search_query}")
                    results = ydl.extract_info(f"ytsearch{max_results // len(search_queries)}:{search_query}", download=False)
                    entries = results.get('entries', []) if results else []
                    
                    for entry in entries:
                        video_id = entry.get('id')
                        duration = entry.get('duration', 0)
                        
                        if video_id and video_id not in seen_ids and duration >= 600:
                            seen_ids.add(video_id)
                            all_results.append(entry)
                    
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error en búsqueda de discografía: {e}")
                continue
        
        logger.info(f"Total discografía encontrada: {len(all_results)} álbumes/compilaciones")
        return all_results
    
    async def search_albums(self, query: str, max_results=200):
        """Busca álbumes completos"""
        search_queries = [
            f"{query} full album",
            f"{query} álbum completo",
            f"{query} complete album",
            f"{query} disco completo"
        ]
        
        all_results = []
        seen_ids = set()
        
        for search_query in search_queries:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{max_results // len(search_queries)}',
                'socket_timeout': 30,
                'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
                'no_check_certificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Buscando álbumes: {search_query}")
                    results = ydl.extract_info(f"ytsearch{max_results // len(search_queries)}:{search_query}", download=False)
                    entries = results.get('entries', []) if results else []
                    
                    for entry in entries:
                        video_id = entry.get('id')
                        duration = entry.get('duration', 0)
                        
                        if video_id and video_id not in seen_ids and duration >= 600:
                            seen_ids.add(video_id)
                            all_results.append(entry)
                    
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error en búsqueda de álbumes: {e}")
                continue
        
        logger.info(f"Total álbumes encontrados: {len(all_results)}")
        return all_results
    
    async def download_audio(self, url: str, user_id: int):
        """Descarga audio de YouTube con múltiples intentos"""
        output_path = os.path.join(self.download_folder, f"{user_id}_%(title)s.%(ext)s")
        
        # Intentar primero con mejor calidad
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,  # Cambiado para ver errores
            'no_warnings': False,  # Ver advertencias
            'max_filesize': 50 * 1024 * 1024,
            'socket_timeout': 60,
            'no_check_certificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"🎵 Descargando: {url}")
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    logger.error("❌ No se pudo obtener info del video")
                    return None, None
                
                # Buscar el archivo descargado
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                
                logger.info(f"✅ Archivo generado: {filename}")
                
                # Verificar que el archivo existe
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    logger.info(f"✅ Archivo existe, tamaño: {file_size} bytes")
                    return filename, info.get('title', 'Audio')
                else:
                    logger.error(f"❌ Archivo no existe: {filename}")
                    return None, None
                    
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"❌ Error de descarga de yt-dlp: {e}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Error general en descarga: {type(e).__name__}: {e}")
            return None, None
    
    def create_results_keyboard(self, results, page=0, results_per_page=10, search_type="normal"):
        """Crea teclado con paginación para resultados"""
        start_idx = page * results_per_page
        end_idx = start_idx + results_per_page
        page_results = results[start_idx:end_idx]
        
        keyboard = []
        
        for i, result in enumerate(page_results):
            global_idx = start_idx + i
            title = result.get('title', 'Sin título')
            channel = result.get('channel', result.get('uploader', ''))
            duration = result.get('duration')
            duration_str = self.format_duration(duration)
            
            if search_type in ["discography", "albums"]:
                icon = "💿" if search_type == "discography" else "📀"
            else:
                icon = "♪"
            
            display_text = f"{icon} {title[:32]}"
            if channel and search_type not in ["discography", "albums"]:
                display_text += f" • {channel[:12]}"
            display_text += duration_str
            
            keyboard.append([
                InlineKeyboardButton(
                    display_text,
                    callback_data=f"select_{search_type}_{global_idx}"
                )
            ])
        
        nav_buttons = []
        total_pages = (len(results) + results_per_page - 1) // results_per_page
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"page_{search_type}_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="page_info"))
        
        if end_idx < len(results):
            nav_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"page_{search_type}_{page+1}"))
        
        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")])
        
        return keyboard
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        user_state = self.user_searches.get(user_id, {}).get('state')
        
        if user_state == 'waiting_search':
            await self.process_search(update, context, query, karaoke=False)
        elif user_state == 'waiting_karaoke':
            await self.process_search(update, context, query, karaoke=True)
        elif user_state == 'waiting_discography':
            await self.process_discography_search(update, context, query)
        elif user_state == 'waiting_albums':
            await self.process_albums_search(update, context, query)
        elif user_state == 'waiting_playlist_song':
            await self.process_playlist_search(update, context, query)
        else:
            keyboard = [[InlineKeyboardButton("🏠 Ir al Menú Principal", callback_data="back_to_main_menu")]]
            await update.message.reply_text(
                "🐺 Usa el menú para navegar por las opciones.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def process_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, karaoke=False):
        """Procesa búsqueda de canciones o karaokes"""
        user_id = update.effective_user.id
        
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"⏰ *Espera {wait_time} segundos*\n\n"
                f"Has alcanzado el límite temporal.\n"
                f"🐺 ¡Relájate un momento!",
                parse_mode='Markdown'
            )
            return
        
        search_type = "karaoke" if karaoke else "songs"
        icon = "🎤" if karaoke else "🎵"
        
        search_msg = await update.message.reply_text(
            f"╭─────────────────────╮\n"
            f"│  {icon} *BUSCANDO...*  │\n"
            f"╰─────────────────────╯\n\n"
            f"🔍 *Búsqueda:* _{query}_\n"
            f"⏳ Esto puede tardar unos segundos...\n"
            f"🐺 Preparando resultados ilimitados...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_music(query, max_results=100, karaoke=karaoke),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text(
                "⏰ *Tiempo agotado*\n\n"
                "La búsqueda tardó demasiado.\n"
                "Intenta con un término más específico."
            )
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text(
                "❌ *Error en la búsqueda*\n\n"
                "Ocurrió un problema. Intenta de nuevo."
            )
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"😔 *Sin resultados*\n\n"
                f"No encontré {'karaokes' if karaoke else 'canciones'}\n"
                f"con el término: _{query}_\n\n"
                f"💡 Intenta con otro término.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': search_type,
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type=search_type)
        
        result_text = f"╔═══════════════════════════╗\n"
        result_text += f"║  {icon} *RESULTADOS ENCONTRADOS* {icon}  ║\n"
        result_text += f"╚═══════════════════════════╝\n\n"
        result_text += f"🔍 *Búsqueda:* _{query}_\n"
        result_text += f"✅ *Total:* {len(results)} {'karaokes' if karaoke else 'resultados'}\n\n"
        result_text += f"{MINI_SEP}\n"
        result_text += f"👇 *Selecciona una opción:*"
        
        await search_msg.edit_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_discography_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda de discografía completa"""
        user_id = update.effective_user.id
        
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"⏰ *Espera {wait_time} segundos*\n\n"
                f"Has alcanzado el límite temporal.\n"
                f"🐺 ¡Relájate un momento!",
                parse_mode='Markdown'
            )
            return
        
        search_msg = await update.message.reply_text(
            f"╭─────────────────────────╮\n"
            f"│  💿 *BUSCANDO DISCOGRAFÍA*  │\n"
            f"╰─────────────────────────╯\n\n"
            f"🎸 *Artista:* _{query}_\n"
            f"⏳ Buscando TODOS los álbumes...\n"
            f"🔍 Compilaciones, ediciones especiales...\n"
            f"🐺 Esto puede tardar varios segundos...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_discography(query, max_results=200),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text(
                "⏰ *Tiempo agotado*\n\n"
                "La búsqueda de discografía tardó mucho.\n"
                "Intenta de nuevo."
            )
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text(
                "❌ *Error en la búsqueda*\n\n"
                "Ocurrió un problema. Intenta de nuevo."
            )
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"😔 *Sin resultados*\n\n"
                f"No encontré discografías de:\n"
                f"🎸 _{query}_\n\n"
                f"💡 Intenta con otro artista o grupo.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': 'discography',
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type='discography')
        
        result_text = f"╔═══════════════════════════════╗\n"
        result_text += f"║  💿 *DISCOGRAFÍA COMPLETA* 💿  ║\n"
        result_text += f"╚═══════════════════════════════╝\n\n"
        result_text += f"🎸 *Artista:* _{query}_\n"
        result_text += f"✅ *Total encontrado:* {len(results)} álbumes\n"
        result_text += f"📀 Incluye: Álbumes, compilaciones\n\n"
        result_text += f"{MINI_SEP}\n"
        result_text += f"👇 *Selecciona para ver detalles:*"
        
        await search_msg.edit_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_albums_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda de álbumes completos"""
        user_id = update.effective_user.id
        
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"⏰ *Espera {wait_time} segundos*\n\n"
                f"Has alcanzado el límite temporal.\n"
                f"🐺 ¡Relájate un momento!",
                parse_mode='Markdown'
            )
            return
        
        search_msg = await update.message.reply_text(
            f"╭─────────────────────────╮\n"
            f"│  📀 *BUSCANDO ÁLBUMES*  │\n"
            f"╰─────────────────────────╯\n\n"
            f"🎼 *Búsqueda:* _{query}_\n"
            f"⏳ Buscando álbumes completos...\n"
            f"🌍 Buscando en todo el mundo...\n"
            f"🐺 Esto puede tardar varios segundos...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_albums(query, max_results=200),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text(
                "⏰ *Tiempo agotado*\n\n"
                "La búsqueda de álbumes tardó mucho.\n"
                "Intenta de nuevo."
            )
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text(
                "❌ *Error en la búsqueda*\n\n"
                "Ocurrió un problema. Intenta de nuevo."
            )
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"😔 *Sin resultados*\n\n"
                f"No encontré álbumes con:\n"
                f"🎼 _{query}_\n\n"
                f"💡 Intenta con otro término.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': 'albums',
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type='albums')
        
        result_text = f"╔═══════════════════════════════╗\n"
        result_text += f"║  📀 *ÁLBUMES COMPLETOS* 📀  ║\n"
        result_text += f"╚═══════════════════════════════╝\n\n"
        result_text += f"🎼 *Búsqueda:* _{query}_\n"
        result_text += f"✅ *Total encontrado:* {len(results)} álbumes\n"
        result_text += f"🌍 De todo el mundo\n\n"
        result_text += f"{MINI_SEP}\n"
        result_text += f"👇 *Selecciona para ver detalles:*"
        
        await search_msg.edit_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_playlist_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda para agregar a playlist"""
        user_id = update.effective_user.id
        
        search_msg = await update.message.reply_text(
            f"🔍 *Buscando:* _{query}_\n"
            f"⏳ Un momento...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_music(query, max_results=20),
                timeout=30.0
            )
        except Exception as e:
            await search_msg.edit_text(
                "❌ Error en búsqueda.\n"
                "Intenta de nuevo."
            )
            return
        
        if not results:
            await search_msg.edit_text(
                "😔 No encontré resultados.\n"
                "Intenta otro término."
            )
            return
        
        self.user_searches[user_id]['results'] = results
        self.user_searches[user_id]['search_type'] = 'playlist'
        
        keyboard = self.create_results_keyboard(results, page=0, results_per_page=10, search_type="playlist")
        
        await search_msg.edit_text(
            f"✅ *Resultados para:* _{query}_\n\n"
            f"👇 Selecciona una canción para agregar:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja callbacks de botones"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Error en callback: {e}")
        
        data = query.data
        
        # Menú principal
        if data == "back_to_main_menu":
            if user_id in self.user_searches:
                self.user_searches[user_id] = {}
            await self.show_main_menu(query)
            return
        
        # Menú: Buscar canciones
        if data == "menu_search_songs":
            self.user_searches[user_id] = {'state': 'waiting_search'}
            menu_text = f"╔═══════════════════════════╗\n"
            menu_text += f"║  🎵 *BUSCAR CANCIONES* 🎵  ║\n"
            menu_text += f"╚═══════════════════════════╝\n\n"
            menu_text += f"🎼 Escribe el nombre de la canción\n"
            menu_text += f"   o artista que quieres buscar.\n\n"
            menu_text += f"✨ *Resultados ilimitados*\n"
            menu_text += f"🌍 *De todo el mundo*\n\n"
            menu_text += f"{MINI_SEP}\n\n"
            menu_text += f"📝 *Ejemplos:*\n"
            menu_text += f"   • `🕯️🩸🦇𝕍𝕀𝕃𝕄𝔸 𝔓𝔸𝕃𝕄𝔸 𝔢 𝕍𝔸𝕄𝔓𝕀ℝ𝕆𝕊🦇🕯️🩸`\n"
            menu_text += f"   • `🌙🕌✨ 🐪💃 🕯️🔥🌵 𝕋𝔞𝔯𝔨𝔞𝔫 🌙🕌✨ 🐪💃 🕯️🔥🌵`\n"
            
            
            await query.edit_message_text(menu_text, parse_mode='Markdown')
            return
        
        # Menú: Buscar karaokes
        if data == "menu_search_karaoke":
            self.user_searches[user_id] = {'state': 'waiting_karaoke'}
            menu_text = f"╔═══════════════════════════╗\n"
            menu_text += f"║  🎤 *BUSCAR KARAOKES* 🎤  ║\n"
            menu_text += f"╚═══════════════════════════╝\n\n"
            menu_text += f"🎤 Escribe el nombre de la canción\n"
            menu_text += f"   o artista para buscar karaokes.\n\n"
            menu_text += f"✨ *Sin límites de búsqueda*\n"
            menu_text += f"🎵 *Versiones instrumentales*\n\n"
            menu_text += f"{MINI_SEP}\n\n"
            menu_text += f"📝 *Ejemplos:*\n"
            menu_text += f"   • `Gloria Trevi Dr. Psiquiatra`\n"
            menu_text += f"   • `Raphael Como yo te amo`\n"
            menu_text += f"   • `Air Supply Goodbye`"
            
            await query.edit_message_text(menu_text, parse_mode='Markdown')
            return
        
        # Menú: Buscar discografías
        if data == "menu_search_discography":
            self.user_searches[user_id] = {'state': 'waiting_discography'}
            menu_text = f"╔═══════════════════════════════╗\n"
            menu_text += f"║  💿 *BUSCAR DISCOGRAFÍAS* 💿  ║\n"
            menu_text += f"╚═══════════════════════════════╝\n\n"
            menu_text += f"🎸 Escribe el nombre del artista o\n"
            menu_text += f"   grupo para buscar su discografía\n"
            menu_text += f"   COMPLETA.\n\n"
            menu_text += f"✨ *Álbumes completos*\n"
            menu_text += f"📀 *Compilaciones*\n"
            menu_text += f"🎼 *Ediciones especiales*\n"
            menu_text += f"🌍 *De todo el mundo*\n\n"
            menu_text += f"{MINI_SEP}\n\n"
            menu_text += f"📝 *Ejemplos:*\n"
            menu_text += f"   • `Metallica`\n"
            menu_text += f"   • `Pink Floyd`\n"
            menu_text += f"   • `ACDC`\n"
            menu_text += f"   • `IRON MAIDEN`"
            
            await query.edit_message_text(menu_text, parse_mode='Markdown')
            return
        
        # Menú: Buscar álbumes
        if data == "menu_search_albums":
            self.user_searches[user_id] = {'state': 'waiting_albums'}
            menu_text = f"╔═══════════════════════════════╗\n"
            menu_text += f"║  📀 *BUSCAR ÁLBUMES* 📀  ║\n"
            menu_text += f"╚═══════════════════════════════╝\n\n"
            menu_text += f"🎼 Escribe el nombre del álbum o\n"
            menu_text += f"   artista para buscar álbumes\n"
            menu_text += f"   COMPLETOS.\n\n"
            menu_text += f"✨ *Álbumes completos*\n"
            menu_text += f"🌍 *De cualquier artista del mundo*\n"
            menu_text += f"🎵 *Resultados ilimitados*\n\n"
            menu_text += f"{MINI_SEP}\n\n"
            menu_text += f"📝 *Ejemplos:*\n"
            menu_text += f"   • `Vilma Palma E Vampiros 3980`\n"
            menu_text += f"   • `Luis Miguel Soy Como Quiero Ser`\n"
            menu_text += f"   • `Patricio Rey y Sus Redonditos de Ricota La Mosca Y La Sopa`\n"
            menu_text += f"   • `Franco Simone Italia 77`"
            
            await query.edit_message_text(menu_text, parse_mode='Markdown')
            return
        
        # Menú: Crear playlist
        if data == "menu_create_playlist":
            if user_id not in self.user_playlists:
                self.user_playlists[user_id] = []
            
            self.user_searches[user_id] = {'state': 'waiting_playlist_song'}
            
            playlist_text = f"╔═══════════════════════════════╗\n"
            playlist_text += f"║  📝 *CREAR PLAYLIST* 📝  ║\n"
            playlist_text += f"╚═══════════════════════════════╝\n\n"
            
            if self.user_playlists[user_id]:
                playlist_text += f"🎵 *Tu playlist actual:*\n"
                playlist_text += f"{MINI_SEP}\n"
                for i, song in enumerate(self.user_playlists[user_id], 1):
                    playlist_text += f"{i}. ♪ {song['title'][:30]}\n"
                    playlist_text += f"   👤 {song['artist'][:25]}\n\n"
                playlist_text += f"{MINI_SEP}\n\n"
            
            playlist_text += f"✏️ Escribe el nombre de una\n"
            playlist_text += f"   canción para agregar."
            
            keyboard = []
            if self.user_playlists[user_id]:
                keyboard.append([InlineKeyboardButton("✅ Finalizar Playlist", callback_data="playlist_finish")])
                keyboard.append([InlineKeyboardButton("🗑️ Borrar Playlist", callback_data="playlist_clear")])
            keyboard.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")])
            
            await query.edit_message_text(
                playlist_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Menú: Info del bot
        if data == "menu_info":
            keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")]]
            
            info_text = f"╔═══════════════════════════════╗\n"
            info_text += f"║  ℹ️ *INFO DEL BOT* ℹ️  ║\n"
            info_text += f"╚═══════════════════════════════╝\n\n"
            info_text += f"🐺 *Bot Musical Veronica*\n"
            info_text += f"📱 Versión 2.0 Premium\n\n"
            info_text += f"{MINI_SEP}\n\n"
            info_text += f"✨ *Características:*\n"
            info_text += f"   • Búsqueda ilimitada\n"
            info_text += f"   • Descargas MP3 HD\n"
            info_text += f"   • Karaokes sin límite\n"
            info_text += f"   • Discografías completas\n"
            info_text += f"   • Álbumes del mundo\n"
            info_text += f"   • Playlists personalizadas\n\n"
            info_text += f"⚡ *Velocidad:* Ultra rápida\n"
            info_text += f"🌍 *Alcance:* Mundial\n"
            info_text += f"💾 *Calidad:* 192kbps MP3\n\n"
            info_text += f"{SEPARATOR}\n"
            info_text += f"🐺 Creado con ❤️ para melómanos"
            
            await query.edit_message_text(
                info_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Menú: Ayuda
        if data == "menu_help":
            keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="back_to_main_menu")]]
            
            help_text = f"╔═══════════════════════════════╗\n"
            help_text += f"║  ❓ *GUÍA DE USO* ❓  ║\n"
            help_text += f"╚═══════════════════════════════╝\n\n"
            
            help_text += f"┌─────────────────────────┐\n"
            help_text += f"│  🎵 *BUSCAR CANCIONES*  │\n"
            help_text += f"└─────────────────────────┘\n"
            help_text += f"Busca canciones ilimitadas.\n"
            help_text += f"📝 `Bad Bunny`, `Tusa`\n\n"
            
            help_text += f"┌─────────────────────────┐\n"
            help_text += f"│  🎤 *BUSCAR KARAOKES*   │\n"
            help_text += f"└─────────────────────────┘\n"
            help_text += f"Versiones instrumentales.\n"
            help_text += f"📝 `Bohemian Rhapsody`\n\n"
            
            help_text += f"┌─────────────────────────┐\n"
            help_text += f"│ 💿 *DISCOGRAFÍAS*│\n"
            help_text += f"└─────────────────────────┘\n"
            help_text += f"Toda la discografía completa.\n"
            help_text += f"📝 `Metallica`, `Queen`\n\n"
            
            help_text += f"┌─────────────────────────┐\n"
            help_text += f"│  📀 *ÁLBUMES*    │\n"
            help_text += f"└─────────────────────────┘\n"
            help_text += f"Álbumes completos del mundo.\n"
            help_text += f"📝 `The Wall`, `Thriller`\n\n"
            
            help_text += f"{SEPARATOR}\n\n"
            help_text += f"⚡ *Límite:* 20 búsquedas/min\n"
            help_text += f"💾 *Formato:* MP3 HD"
            
            await query.edit_message_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Paginación
        if data.startswith("page_") and data != "page_info":
            parts = data.split("_")
            search_type = parts[1]
            page = int(parts[2])
            
            if user_id not in self.user_searches:
                await query.edit_message_text("⏰ Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            
            keyboard = self.create_results_keyboard(results, page=page, search_type=search_type)
            
            await query.edit_message_text(
                f"📄 *Resultados* (página {page+1})\n\n"
                f"👇 Selecciona una opción:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Selección de canción
        if data.startswith("select_"):
            parts = data.split("_")
            search_type = parts[1]
            idx = int(parts[2])
            
            if user_id not in self.user_searches:
                await query.edit_message_text("⏰ Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            
            if datetime.now() - user_data['timestamp'] > timedelta(minutes=15):
                del self.user_searches[user_id]
                await query.edit_message_text("⏰ Búsqueda expirada.")
                return
            
            selected = user_data['results'][idx]
            video_id = selected.get('id')
            title = selected.get('title', 'Audio')
            artist = selected.get('channel', selected.get('uploader', 'Desconocido'))
            url = f"https://www.youtube.com/watch?v={video_id}"
            duration = selected.get('duration', 0)
            
            self.user_searches[user_id]['selected'] = {
                'url': url,
                'title': title,
                'artist': artist,
                'id': video_id
            }
            
            # Si es para playlist
            if search_type == "playlist":
                self.user_playlists[user_id].append({
                    'title': title,
                    'artist': artist,
                    'url': url
                })
                
                keyboard = [
                    [InlineKeyboardButton("➕ Agregar otra canción", callback_data="menu_create_playlist")],
                    [InlineKeyboardButton("✅ Finalizar Playlist", callback_data="playlist_finish")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                success_text = f"╔═══════════════════════════════╗\n"
                success_text += f"║  ✅ *AGREGADO A PLAYLIST* ✅  ║\n"
                success_text += f"╚═══════════════════════════════╝\n\n"
                success_text += f"🎵 *Canción:*\n"
                success_text += f"   {title[:40]}\n\n"
                success_text += f"👤 *Artista:*\n"
                success_text += f"   {artist[:40]}\n\n"
                success_text += f"{MINI_SEP}\n"
                success_text += f"📝 *Total en playlist:* {len(self.user_playlists[user_id])} canciones"
                
                await query.edit_message_text(
                    success_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            
            # Mostrar info según tipo
            duration_str = self.format_duration(duration)
            icon = "💿" if search_type == "discography" else "📀" if search_type == "albums" else "🎵"
            
            # Determinar tipo de contenido para el texto
            content_type = ""
            if search_type == "discography":
                content_type = "discografía"
            elif search_type == "albums":
                content_type = "álbum"
            elif search_type == "karaoke":
                content_type = "karaoke"
            else:
                content_type = "canción"
            
            # Opciones con botón de agregar a playlist
            keyboard = [
                [
                    InlineKeyboardButton("▶️ Reproducir", callback_data=f"link_{idx}"),
                    InlineKeyboardButton("⬇️ Descargar", callback_data=f"download_{idx}")
                ],
                [InlineKeyboardButton(f"➕ Agregar esta {content_type} a Playlist", callback_data=f"add_to_playlist_{idx}")],
                [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
            ]
            
            detail_text = f"╔═══════════════════════════════╗\n"
            detail_text += f"║  {icon} *DETALLES* {icon}  ║\n"
            detail_text += f"╚═══════════════════════════════╝\n\n"
            detail_text += f"🎵 *Título:*\n"
            detail_text += f"   {title[:50]}\n\n"
            detail_text += f"👤 *Artista:*\n"
            detail_text += f"   {artist[:50]}\n\n"
            detail_text += f"⏱️ *Duración:* {duration_str}\n\n"
            detail_text += f"{MINI_SEP}\n"
            detail_text += f"👇 *¿Qué quieres hacer?*"
            
            await query.edit_message_text(
                detail_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Reproducir audio directamente (antes era solo "link")
        if data.startswith("link_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("❌ Error.")
                return
            
            selected = self.user_searches[user_id]['selected']
            search_type = self.user_searches[user_id].get('search_type', 'songs')
            
            # Determinar tipo de contenido
            content_type = ""
            if search_type == "discography":
                content_type = "discografía"
            elif search_type == "albums":
                content_type = "álbum"
            elif search_type == "karaoke":
                content_type = "karaoke"
            else:
                content_type = "canción"
            
            # Mostrar mensaje de carga
            await query.edit_message_text(
                f"🎵 *Reproduciendo...*\n\n"
                f"⏳ Preparando el audio de:\n"
                f"_{selected['title'][:40]}_\n\n"
                f"🐺 Un momento por favor...",
                parse_mode='Markdown'
            )
            
            # Intentar descargar y reproducir
            try:
                filename, title = await asyncio.wait_for(
                    self.download_audio(selected['url'], user_id),
                    timeout=120.0
                )
                
                if filename and os.path.exists(filename):
                    # Botones para el audio
                    keyboard = [
                        [InlineKeyboardButton(f"➕ ¿Agregar a tu Playlist?", callback_data=f"add_to_playlist_from_link")],
                        [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                        [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                    ]
                    
                    with open(filename, 'rb') as audio_file:
                        caption = f"🐺🎵 *{title[:50]}*\n\n"
                        caption += f"👤 {selected['artist'][:40]}\n"
                        caption += f"💾 Formato: MP3 HD\n"
                        caption += f"🐺 ¡Disfruta! 💕"
                        
                        await query.message.reply_audio(
                            audio=audio_file,
                            title=title,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                    
                    # Actualizar mensaje
                    await query.edit_message_text(
                        "✅ ¡Audio reproduciendo abajo! 🎵",
                        parse_mode='Markdown'
                    )
                    
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    # Si no se pudo descargar, mostrar botón directo a YouTube
                    keyboard = [
                        [InlineKeyboardButton("▶️ REPRODUCIR ", url=selected['url'])],
                        [InlineKeyboardButton(f"➕ ¿Agregar a tu Playlist?", callback_data=f"add_to_playlist_from_link")],
                        [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                        [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                    ]
                    
                    warning_text = f"╔═══════════════════════════════╗\n"
                    warning_text += f"║  ⚠️ *NO PUDE DESCARGAR* ⚠️  ║\n"
                    warning_text += f"╚═══════════════════════════════╝\n\n"
                    warning_text += f"🎵 *Título:*\n"
                    warning_text += f"   {selected['title'][:50]}\n\n"
                    warning_text += f"👤 *Artista:*\n"
                    warning_text += f"   {selected['artist'][:50]}\n\n"
                    warning_text += f"{MINI_SEP}\n\n"
                    warning_text += f"💡 Pero puedes reproducirlo aquí:\n"
                    warning_text += f"👇 *Presiona el botón de abajo*\n\n"
                    warning_text += f"🐺 ¡Solo toca el botón! 💕"
                    
                    await query.edit_message_text(
                        warning_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    
            except asyncio.TimeoutError:
                # Timeout - material no disponible
                keyboard = [
                    [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                error_text = f"╔═══════════════════════════════╗\n"
                error_text += f"║  ⚠️ *MATERIAL NO DISPONIBLE* ⚠️  ║\n"
                error_text += f"╚═══════════════════════════════╝\n\n"
                error_text += f"😔 Lo siento mucho...\n\n"
                error_text += f"🚫 *Este material ya no se encuentra*\n"
                error_text += f"   *disponible en la red.*\n\n"
                error_text += f"💡 Por favor, elige otro tema.\n\n"
                error_text += f"{SEPARATOR}\n"
                error_text += f"🐺 ¡Disculpa las molestias!\n"
                error_text += f"   *- Vero* 💕"
                
                await query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error al reproducir: {e}")
                # Error general - material no disponible
                keyboard = [
                    [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                error_text = f"╔═══════════════════════════════╗\n"
                error_text += f"║  ⚠️ *MATERIAL NO DISPONIBLE* ⚠️  ║\n"
                error_text += f"╚═══════════════════════════════╝\n\n"
                error_text += f"😔 Lo siento mucho...\n\n"
                error_text += f"🚫 *Este material ya no se encuentra*\n"
                error_text += f"   *disponible en la red.*\n\n"
                error_text += f"💡 Por favor, elige otro tema.\n\n"
                error_text += f"{SEPARATOR}\n"
                error_text += f"🐺 ¡Disculpa las molestias!\n"
                error_text += f"   *- Vero* 💕"
                
                await query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            return
        
        # Descargar audio
        if data.startswith("download_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("❌ Error.")
                return
            
            selected = self.user_searches[user_id]['selected']
            search_type = self.user_searches[user_id].get('search_type', 'songs')
            
            # Determinar tipo de contenido
            content_type = ""
            if search_type == "discography":
                content_type = "discografía"
            elif search_type == "albums":
                content_type = "álbum"
            elif search_type == "karaoke":
                content_type = "karaoke"
            else:
                content_type = "canción"
            
            download_text = f"╔═══════════════════════════════╗\n"
            download_text += f"║  ⬇️ *DESCARGANDO...* ⬇️  ║\n"
            download_text += f"╚═══════════════════════════════╝\n\n"
            download_text += f"🎵 {selected['title'][:40]}\n\n"
            download_text += f"⏳ Esto puede tardar un momento...\n"
            download_text += f"🐺 Preparando tu MP3 HD..."
            
            await query.edit_message_text(download_text, parse_mode='Markdown')
            
            try:
                filename, title = await asyncio.wait_for(
                    self.download_audio(selected['url'], user_id),
                    timeout=120.0
                )
                
                if filename and os.path.exists(filename):
                    # Botones para el mensaje del audio
                    keyboard = [
                        [InlineKeyboardButton(f"➕ ¿Agregar a tu Playlist?", callback_data=f"add_to_playlist_from_download")],
                        [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                        [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                    ]
                    
                    with open(filename, 'rb') as audio_file:
                        caption = f"🐺🎵 *{title[:50]}*\n\n"
                        caption += f"💾 Formato: MP3 HD\n"
                        caption += f"✅ Descargado exitosamente\n"
                        caption += f"🐺 ¡Disfruta! 💕"
                        
                        await query.message.reply_audio(
                            audio=audio_file,
                            title=title,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                    
                    # Actualizar mensaje anterior
                    await query.edit_message_text(
                        "✅ ¡Audio enviado abajo! 🎵",
                        parse_mode='Markdown'
                    )
                    
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    # No se pudo descargar - material no disponible
                    keyboard = [
                        [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                        [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                    ]
                    
                    error_text = f"╔═══════════════════════════════╗\n"
                    error_text += f"║  ⚠️ *MATERIAL NO DISPONIBLE* ⚠️  ║\n"
                    error_text += f"╚═══════════════════════════════╝\n\n"
                    error_text += f"😔 Lo siento mucho...\n\n"
                    error_text += f"🚫 *Este material ya no se encuentra*\n"
                    error_text += f"   *disponible en la red.*\n\n"
                    error_text += f"💡 Por favor, elige otro tema.\n\n"
                    error_text += f"{SEPARATOR}\n"
                    error_text += f"🐺 ¡Disculpa las molestias!\n"
                    error_text += f"   *- Vero* 💕"
                    
                    await query.edit_message_text(
                        error_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
            except asyncio.TimeoutError:
                # Timeout - material no disponible
                keyboard = [
                    [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                error_text = f"╔═══════════════════════════════╗\n"
                error_text += f"║  ⚠️ *MATERIAL NO DISPONIBLE* ⚠️  ║\n"
                error_text += f"╚═══════════════════════════════╝\n\n"
                error_text += f"😔 Lo siento mucho...\n\n"
                error_text += f"🚫 *Este material ya no se encuentra*\n"
                error_text += f"   *disponible en la red.*\n\n"
                error_text += f"💡 Por favor, elige otro tema.\n\n"
                error_text += f"{SEPARATOR}\n"
                error_text += f"🐺 ¡Disculpa las molestias!\n"
                error_text += f"   *- Vero* 💕"
                
                await query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error descarga: {e}")
                keyboard = [
                    [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                error_text = f"╔═══════════════════════════════╗\n"
                error_text += f"║  ⚠️ *MATERIAL NO DISPONIBLE* ⚠️  ║\n"
                error_text += f"╚═══════════════════════════════╝\n\n"
                error_text += f"😔 Lo siento mucho...\n\n"
                error_text += f"🚫 *Este material ya no se encuentra*\n"
                error_text += f"   *disponible en la red.*\n\n"
                error_text += f"💡 Por favor, elige otro tema.\n\n"
                error_text += f"{SEPARATOR}\n"
                error_text += f"🐺 ¡Disculpa las molestias!\n"
                error_text += f"   *- Vero* 💕"
                
                await query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            return
        
        # Volver a resultados
        if data == "back_to_results":
            if user_id not in self.user_searches:
                await query.edit_message_text("⏰ Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            search_type = user_data.get('search_type', 'songs')
            page = user_data.get('page', 0)
            
            keyboard = self.create_results_keyboard(results, page=page, search_type=search_type)
            
            await query.edit_message_text(
                f"🔍 *Búsqueda:* {user_data['query']}\n\n"
                f"👇 Selecciona una opción:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Finalizar playlist
        if data == "playlist_finish":
            if user_id not in self.user_playlists or not self.user_playlists[user_id]:
                await query.edit_message_text("😔 Tu playlist está vacía.")
                return
            
            playlist_text = f"╔═══════════════════════════════╗\n"
            playlist_text += f"║  ✅ *PLAYLIST COMPLETA* ✅  ║\n"
            playlist_text += f"╚═══════════════════════════════╝\n\n"
            playlist_text += f"🎵 *Tu Playlist Personal*\n"
            playlist_text += f"📝 Total: {len(self.user_playlists[user_id])} canciones\n\n"
            playlist_text += f"{SEPARATOR}\n\n"
            
            for i, song in enumerate(self.user_playlists[user_id], 1):
                playlist_text += f"*{i}.* 🎵 {song['title'][:35]}\n"
                playlist_text += f"    👤 {song['artist'][:30]}\n"
                playlist_text += f"    🔗 {song['url']}\n\n"
            
            playlist_text += f"{SEPARATOR}\n"
            playlist_text += f"🐺 ¡Disfruta tu playlist! 💕"
            
            keyboard = [
                [InlineKeyboardButton("🗑️ Borrar Playlist", callback_data="playlist_clear")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
            ]
            
            await query.edit_message_text(
                playlist_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Borrar playlist
        if data == "playlist_clear":
            if user_id in self.user_playlists:
                self.user_playlists[user_id] = []
            
            keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]]
            
            clear_text = f"╔═══════════════════════════════╗\n"
            clear_text += f"║  🗑️ *PLAYLIST BORRADA* 🗑️  ║\n"
            clear_text += f"╚═══════════════════════════════╝\n\n"
            clear_text += f"✅ Tu playlist ha sido eliminada.\n"
            clear_text += f"🐺 Puedes crear una nueva cuando quieras."
            
            await query.edit_message_text(
                clear_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Agregar a playlist (desde el botón en detalles)
        if data.startswith("add_to_playlist_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("❌ Error: No hay contenido seleccionado.")
                return
            
            selected = self.user_searches[user_id]['selected']
            search_type = self.user_searches[user_id].get('search_type', 'songs')
            
            # Determinar tipo de contenido
            content_type = ""
            if search_type == "discography":
                content_type = "discografía"
            elif search_type == "albums":
                content_type = "álbum"
            elif search_type == "karaoke":
                content_type = "karaoke"
            else:
                content_type = "canción"
            
            # Verificar si tiene playlist, si no, ofrecer crear una
            if user_id not in self.user_playlists or not self.user_playlists[user_id]:
                # No tiene playlist, ofrecer crear una
                keyboard = [
                    [InlineKeyboardButton("✅ Sí, crear mi playlist", callback_data=f"create_playlist_and_add")],
                    [InlineKeyboardButton("❌ No, volver", callback_data="back_to_results")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                guide_text = f"╔═══════════════════════════════╗\n"
                guide_text += f"║  📝 *CREAR PLAYLIST* 📝  ║\n"
                guide_text += f"╚═══════════════════════════════╝\n\n"
                guide_text += f"🎵 Quieres agregar esta {content_type}:\n"
                guide_text += f"   *{selected['title'][:40]}*\n\n"
                guide_text += f"💡 *¡Aún no tienes una playlist!*\n\n"
                guide_text += f"📝 Una playlist te permite:\n"
                guide_text += f"   • Guardar tus canciones favoritas\n"
                guide_text += f"   • Organizarlas en una lista\n"
                guide_text += f"   • Acceder a ellas cuando quieras\n\n"
                guide_text += f"{MINI_SEP}\n"
                guide_text += f"❓ *¿Quieres crear tu playlist ahora?*"
                
                await query.edit_message_text(
                    guide_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            else:
                # Ya tiene playlist, agregar directamente
                # Verificar si ya está en la playlist
                is_duplicate = any(
                    song['url'] == selected['url'] 
                    for song in self.user_playlists[user_id]
                )
                
                if is_duplicate:
                    keyboard = [
                        [InlineKeyboardButton("📝 Ver mi Playlist", callback_data="playlist_finish")],
                        [InlineKeyboardButton("🔙 Volver a Resultados", callback_data="back_to_results")],
                        [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                    ]
                    
                    await query.edit_message_text(
                        f"⚠️ *Ya está en tu playlist*\n\n"
                        f"Esta {content_type} ya fue agregada anteriormente.\n\n"
                        f"🎵 *{selected['title'][:40]}*\n"
                        f"👤 {selected['artist'][:40]}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    return
                
                # Agregar a la playlist
                self.user_playlists[user_id].append({
                    'title': selected['title'],
                    'artist': selected['artist'],
                    'url': selected['url']
                })
                
                keyboard = [
                    [InlineKeyboardButton("➕ Agregar otra", callback_data="back_to_results")],
                    [InlineKeyboardButton("📝 Ver mi Playlist", callback_data="playlist_finish")],
                    [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                success_text = f"╔═══════════════════════════════╗\n"
                success_text += f"║  ✅ *AGREGADO A PLAYLIST* ✅  ║\n"
                success_text += f"╚═══════════════════════════════╝\n\n"
                success_text += f"🎵 *{content_type.capitalize()} agregada:*\n"
                success_text += f"   {selected['title'][:40]}\n\n"
                success_text += f"👤 *Artista:*\n"
                success_text += f"   {selected['artist'][:40]}\n\n"
                success_text += f"{MINI_SEP}\n"
                success_text += f"📝 *Total en playlist:* {len(self.user_playlists[user_id])} canciones\n"
                success_text += f"🐺 ¡Sigue agregando más!"
                
                await query.edit_message_text(
                    success_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
        
        # Crear playlist y agregar el contenido seleccionado
        if data == "create_playlist_and_add":
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("❌ Error: No hay contenido seleccionado.")
                return
            
            selected = self.user_searches[user_id]['selected']
            search_type = self.user_searches[user_id].get('search_type', 'songs')
            
            # Determinar tipo de contenido
            content_type = ""
            if search_type == "discography":
                content_type = "discografía"
            elif search_type == "albums":
                content_type = "álbum"
            elif search_type == "karaoke":
                content_type = "karaoke"
            else:
                content_type = "canción"
            
            # Crear la playlist con el primer elemento
            self.user_playlists[user_id] = [{
                'title': selected['title'],
                'artist': selected['artist'],
                'url': selected['url']
            }]
            
            keyboard = [
                [InlineKeyboardButton("➕ Agregar otra", callback_data="back_to_results")],
                [InlineKeyboardButton("📝 Ver mi Playlist", callback_data="playlist_finish")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
            ]
            
            guide_text = f"╔═══════════════════════════════╗\n"
            guide_text += f"║  🎉 *PLAYLIST CREADA* 🎉  ║\n"
            guide_text += f"╚═══════════════════════════════╝\n\n"
            guide_text += f"✅ *¡Tu playlist ha sido creada!*\n\n"
            guide_text += f"🎵 *Primera {content_type} agregada:*\n"
            guide_text += f"   {selected['title'][:40]}\n\n"
            guide_text += f"👤 *Artista:*\n"
            guide_text += f"   {selected['artist'][:40]}\n\n"
            guide_text += f"{MINI_SEP}\n\n"
            guide_text += f"💡 *Próximos pasos:*\n"
            guide_text += f"   • Agrega más canciones a tu playlist\n"
            guide_text += f"   • Busca y selecciona cualquier contenido\n"
            guide_text += f"   • Usa el botón '➕ Agregar a Playlist'\n"
            guide_text += f"   • Cuando termines, ve a 'Ver mi Playlist'\n\n"
            guide_text += f"🐺 ¡Sigue agregando más música!"
            
            await query.edit_message_text(
                guide_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores globales"""
        logger.error(f"Error: {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "╔═══════════════════════════════╗\n"
                    "║  ⚠️ *ERROR* ⚠️  ║\n"
                    "╚═══════════════════════════════╝\n\n"
                    "😔 Ocurrió un error inesperado.\n"
                    "🐺 Por favor, intenta de nuevo.\n\n"
                    "💡 Usa /start para volver al menú.",
                    parse_mode='Markdown'
                )
        except:
            pass


def main():
    """Función principal"""
    logger.info("╔═══════════════════════════════════╗")
    logger.info("║  🐺 INICIANDO BOT MUSICAL 🐺  ║")
    logger.info("╚═══════════════════════════════════╝")
    
    bot = MusicBot()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    app.add_error_handler(bot.error_handler)
    
    logger.info("✅ Bot iniciado correctamente")
    logger.info("🐺 Bot Musical Veronica activo")
    logger.info("⏹️ Presiona Ctrl+C para detener")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
