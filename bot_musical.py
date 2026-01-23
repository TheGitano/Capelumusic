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

# Token desde variable de entorno (IMPORTANTE para Railway)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")


class RateLimiter:
    """Control de rate limiting por usuario"""
    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = datetime.now()
        # Limpiar requests antiguos
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
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.download_folder = 'downloads'
        
        # Crear carpeta de descargas si no existe
        os.makedirs(self.download_folder, exist_ok=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_name = update.effective_user.first_name
        await update.message.reply_text(
            f"🐺 *¡Hola {user_name}!*\n\n"
            "Soy tu Lobo asistente musical 🎵\n\n"
            "*Comandos disponibles:*\n"
            "• Escribe el nombre de una canción o artista\n"
            "• /help - Ver ayuda\n"
            "• /cancel - Cancelar búsqueda actual\n\n"
            "💡 *Tip:* Puedes elegir descargar el audio o solo obtener el enlace",
            parse_mode='Markdow
