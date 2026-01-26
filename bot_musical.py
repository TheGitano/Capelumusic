import os
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError, NetworkError, TimedOut
import yt_dlp

# Configuración de logging MÁS DETALLADA
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Cambiado a DEBUG
)
logger = logging.getLogger(__name__)

# Token desde variable de entorno
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")

# Verificar yt-dlp al inicio
logger.info(f"✅ yt-dlp version: {yt_dlp.version.__version__}")


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
        logger.info(f"🔍 Iniciando búsqueda: {query}")
        
        ydl_opts = {
            'quiet': False,  # Cambiar a False para ver errores
            'no_warnings': False,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'source_address': '0.0.0.0',
            'force_generic_extractor': False,
            'cookiefile': None,
        }
        
        try:
            logger.debug(f"Opciones yt-dlp: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f"ytsearch5:{query}"
                logger.info(f"Query de búsqueda: {search_query}")
                
                info = ydl.extract_info(search_query, download=False)
                
                logger.debug(f"Respuesta completa: {info}")
                
                if not info:
                    logger.error("❌ Info es None")
                    return []
                
                if 'entries' not in info:
                    logger.error(f"❌ No hay 'entries' en info. Keys: {info.keys()}")
                    return []
                
                entries = info['entries']
                logger.info(f"✅ Se encontraron {len(entries)} resultados")
                
                # Filtrar resultados None
                valid_entries = [e for e in entries if e is not None]
                logger.info(f"✅ Resultados válidos: {len(valid_entries)}")
                
                return valid_entries[:5]
                
        except Exception as e:
            logger.error(f"❌ ERROR CRÍTICO en búsqueda:")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensaje: {str(e)}")
            logger.error(f"   Args: {e.args}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
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
            'quiet': False,
            'no_warnings': False,
            'max_filesize': 50 * 1024 * 1024,
            'nocheckcertificate': True,
        }
        
        try:
            logger.info(f"Descargando: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                logger.info(f"✅ Descarga exitosa: {filename}")
                return filename, info.get('title', 'Audio')
        except Exception as e:
            logger.error(f"❌ Error en descarga: {type(e).__name__} - {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        logger.info(f"📩 Mensaje de usuario {user_id}: {query}")
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"🐺 ¡Calma! Espera {wait_time} segundos."
            )
            return
        
        if len(query) < 2:
            await update.message.reply_text("🐺 Escribe al menos 2 caracteres.")
            return
        
        search_msg = await update.message.reply_text(
            f"🔍 Buscando: *{query}*...",
            parse_mode='Markdown'
        )
        
        try:
            logger.info("Llamando a search_music...")
            results = await asyncio.wait_for(
                self.search_music(query),
                timeout=45.0
            )
            logger.info(f"search_music retornó {len(results)} resultados")
            
        except asyncio.TimeoutError:
            logger.error("❌ Timeout en búsqueda")
            await search_msg.edit_text("🐺 La búsqueda tardó mucho. Intenta de nuevo.")
            return
        except Exception as e:
            logger.error(f"❌ Error inesperado en handle_message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await search_msg.edit_text(
                f"🐺 Error: {type(e).__name__}\n"
                "Revisa los logs en Railway para más detalles."
            )
            return
        
        if not results:
            logger.warning("⚠️ No se encontraron resultados")
            await search_msg.edit_text(
                "🐺 No encontré nada. Intenta con otro término."
            )
            return
        
        # Guardar resultados
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now()
        }
        
        # Crear teclado
        keyboard = []
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Sin título')
            duration = result.get('duration', 0)
            duration_str = f" ({duration//60}:{duration%60:02d})" if duration else ""
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🎵 {title[:45]}{duration_str}",
                    callback_data=f"select_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new_search")])
        
        await search_msg.edit_text(
            f"🐺 *Resultados para:* {query}\n\nSelecciona una canción:",
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
        
        if query.data == "new_search":
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            await query.edit_message_text("🐺 Escribe otra canción 🎵")
            return
        
        if query.data.startswith("select_"):
            idx = int(query.data.split("_")[1])
            
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            
            if datetime.now() - user_data['timestamp'] > timedelta(minutes=10):
                del self.user_searches[user_id]
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            selected = user_data['results'][idx]
            video_id = selected.get('id')
            title = selected.get('title', 'Audio')
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            self.user_searches[user_id]['selected'] = {
                'url': url,
                'title': title,
                'id': video_id
            }
            
            keyboard = [
                [InlineKeyboardButton("🔗 Solo enlace", callback_data=f"link_{idx}")],
                [InlineKeyboardButton("⬇️ Descargar MP3", callback_data=f"download_{idx}")],
                [InlineKeyboardButton("🔙 Volver", callback_data="back_to_results")]
            ]
            
            await query.edit_message_text(
                f"🐺🎵 *{title}*\n\n¿Qué quieres hacer?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        if query.data.startswith("link_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error. Busca de nuevo.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await query.message.reply_text(
                f"🐺🎵 *{selected['title']}*\n\n"
                f"🔗 {selected['url']}\n\n¡Disfruta! 💕",
                parse_mode='Markdown'
            )
            await query.edit_message_text("🐺 ¡Listo! 🎵")
            return
        
        if query.data.startswith("download_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await query.edit_message_text("🐺 ⬇️ Descargando...")
            
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
                    await query.message.reply_text("🐺 ¡Listo! 🎵")
                    
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    await query.message.reply_text(
                        f"🐺 No pude descargar. Enlace:\n\n🔗 {selected['url']}"
                    )
                
            except asyncio.TimeoutError:
                await query.message.reply_text(
                    f"🐺 Descarga lenta. Enlace:\n\n🔗 {selected['url']}"
                )
            except Exception as e:
                logger.error(f"Error descarga: {e}")
                await query.message.reply_text(
                    f"🐺 Error al descargar:\n\n🔗 {selected['url']}"
                )
            return
        
        if query.data == "back_to_results":
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            
            keyboard = []
            for i, result in enumerate(results[:5]):
                title = result.get('title', 'Sin título')
                duration = result.get('duration', 0)
                duration_str = f" ({duration//60}:{duration%60:02d})" if duration else ""
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎵 {title[:45]}{duration_str}",
                        callback_data=f"select_{i}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new_search")])
            
            await query.edit_message_text(
                f"🐺 *Resultados:* {user_data['query']}\n\nSelecciona:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores globales"""
        logger.error(f"❌ Error global: {context.error}")
        import traceback
        logger.error(traceback.format_exc())
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    f"🐺 Error: {type(context.error).__name__}"
                )
        except:
            pass


def main():
    """Función principal"""
    logger.info("=" * 50)
    logger.info("🐺 INICIANDO BOT MUSICAL")
    logger.info("=" * 50)
    
    bot = MusicBot()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("cancel", bot.cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    app.add_error_handler(bot.error_handler)
    
    logger.info("🐺 Bot configurado correctamente")
    logger.info("🐺 Iniciando polling...")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
