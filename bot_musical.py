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
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.download_folder = 'downloads'
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
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        await update.message.reply_text(
            "🐺 *Guía de uso:*\n\n"
            "1️⃣ Escribe el nombre de una canción o artista\n"
            "2️⃣ Selecciona de los resultados\n"
            "3️⃣ Elige si quieres el enlace o descargar el audio\n\n"
            "*Límites:*\n"
            "• Máximo 10 búsquedas por minuto\n\n"
            "*Ejemplos:*\n"
            "• `Bad Bunny Monaco`\n"
            "• `The Weeknd Blinding Lights`",
            parse_mode='Markdown'
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /cancel"""
        user_id = update.effective_user.id
        if user_id in self.user_searches:
            del self.user_searches[user_id]
            await update.message.reply_text("🐺 Búsqueda cancelada.")
        else:
            await update.message.reply_text("🐺 No hay búsqueda activa.")
    
    async def search_music(self, query: str):
        """Busca música en YouTube"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
            'socket_timeout': 30,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            'no_check_certificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Buscando: {query}")
                results = ydl.extract_info(f"ytsearch10:{query}", download=False)
                return results['entries'][:5] if 'entries' in results else []
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def download_audio(self, url: str, user_id: int):
        """Descarga audio de YouTube"""
        output_path = os.path.join(self.download_folder, f"{user_id}_%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 50 * 1024 * 1024,
            'socket_timeout': 60,
            'no_check_certificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Descargando: {url}")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                return filename, info.get('title', 'Audio')
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            return None, None
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"🐺 ¡Calma! Espera {wait_time} segundos antes de buscar de nuevo."
            )
            return
        
        if len(query) < 2:
            await update.message.reply_text("🐺 Escribe al menos 2 caracteres para buscar.")
            return
        
        # Mensaje de búsqueda
        search_msg = await update.message.reply_text(
            f"🔍 Buscando: *{query}*...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_music(query),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text("🐺 La búsqueda tardó mucho. Intenta de nuevo.")
            return
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            await search_msg.edit_text("🐺 Ocurrió un error. Intenta de nuevo.")
            return
        
        if not results:
            await search_msg.edit_text(
                "🐺 No encontré nada con ese nombre.\n"
                "Intenta con otro término de búsqueda."
            )
            return
        
        # Guardar resultados del usuario
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now()
        }
        
        # Crear teclado con resultados
        keyboard = []
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Sin título')
            duration = result.get('duration', 0)
            duration_str = f" ({int(duration)//60}:{int(duration)%60:02d})" if duration else ""
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🎵 {title[:45]}{duration_str}",
                    callback_data=f"select_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new_search")])
        
        await search_msg.edit_text(
            f"🐺 *Resultados para:* {query}\n\n"
            "Selecciona una canción:",
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
            logger.error(f"Error en callback answer: {e}")
        
        # Nueva búsqueda
        if query.data == "new_search":
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            await query.edit_message_text("🐺 Escribe el nombre de otra canción 🎵")
            return
        
        # Selección de canción
        if query.data.startswith("select_"):
            idx = int(query.data.split("_")[1])
            
            if user_id not in self.user_searches:
                await query.edit_message_text(
                    "🐺 La búsqueda expiró. Realiza una nueva búsqueda."
                )
                return
            
            user_data = self.user_searches[user_id]
            
            # Verificar expiración (10 minutos)
            if datetime.now() - user_data['timestamp'] > timedelta(minutes=10):
                del self.user_searches[user_id]
                await query.edit_message_text(
                    "🐺 La búsqueda expiró. Realiza una nueva búsqueda."
                )
                return
            
            selected = user_data['results'][idx]
            video_id = selected.get('id')
            title = selected.get('title', 'Audio')
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Guardar selección
            self.user_searches[user_id]['selected'] = {
                'url': url,
                'title': title,
                'id': video_id
            }
            
            # Opciones: Enlace o Descarga
            keyboard = [
                [InlineKeyboardButton("🔗 Solo enlace", callback_data=f"link_{idx}")],
                [InlineKeyboardButton("⬇️ Descargar audio (MP3)", callback_data=f"download_{idx}")],
                [InlineKeyboardButton("🔙 Volver", callback_data="back_to_results")]
            ]
            
            await query.edit_message_text(
                f"🐺🎵 *{title}*\n\n"
                "¿Qué quieres hacer?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Enviar solo enlace
        if query.data.startswith("link_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error. Busca de nuevo.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await query.message.reply_text(
                f"🐺🎵 *{selected['title']}*\n\n"
                f"🔗 {selected['url']}\n\n"
                "¡Disfruta! 💕",
                parse_mode='Markdown'
            )
            await query.edit_message_text("🐺 ¡Listo! Disfruta tu música 🎵")
            return
        
        # Descargar audio
        if query.data.startswith("download_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error. Busca de nuevo.")
                return
            
            selected = self.user_searches[user_id]['selected']
            
            await query.edit_message_text("🐺 ⬇️ Descargando audio... Esto puede tardar un momento.")
            
            try:
                filename, title = await asyncio.wait_for(
                    self.download_audio(selected['url'], user_id),
                    timeout=120.0
                )
                
                if filename and os.path.exists(filename):
                    with open(filename, 'rb') as audio_file:
                        await query.message.reply_audio(
                            audio=audio_file,
                            title=title,
                            caption=f"🐺🎵 *{title}*\n\n¡Disfruta! 💕",
                            parse_mode='Markdown'
                        )
                    await query.message.reply_text("🐺 ¡Audio enviado exitosamente! 🎵")
                    
                    # Eliminar archivo después de enviar
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    await query.message.reply_text(
                        "🐺 No pude descargar el audio. Aquí está el enlace:\n\n"
                        f"🔗 {selected['url']}"
                    )
                
            except asyncio.TimeoutError:
                await query.message.reply_text(
                    "🐺 La descarga tardó mucho. Aquí está el enlace:\n\n"
                    f"🔗 {selected['url']}"
                )
            except Exception as e:
                logger.error(f"Error en descarga: {e}")
                await query.message.reply_text(
                    "🐺 Ocurrió un error al descargar. Aquí está el enlace:\n\n"
                    f"🔗 {selected['url']}"
                )
            return
        
        # Volver a resultados
        if query.data == "back_to_results":
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada. Realiza una nueva.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            
            keyboard = []
            for i, result in enumerate(results[:5]):
                title = result.get('title', 'Sin título')
                duration = result.get('duration', 0)
                duration_str = f" ({int(duration)//60}:{int(duration)%60:02d})" if duration else ""
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎵 {title[:45]}{duration_str}",
                        callback_data=f"select_{i}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new_search")])
            
            await query.edit_message_text(
                f"🐺 *Resultados para:* {user_data['query']}\n\n"
                "Selecciona una canción:",
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
                    "🐺 Ocurrió un error inesperado. Intenta de nuevo en un momento."
                )
        except:
            pass


def main():
    """Función principal"""
    logger.info("🐺 Iniciando bot musical...")
    
    bot = MusicBot()
    
    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("cancel", bot.cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # Error handler
    app.add_error_handler(bot.error_handler)
    
    logger.info("🐺 Bot iniciado correctamente")
    logger.info("🐺 Presiona Ctrl+C para detener")
    
    # Polling con reintentos
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
