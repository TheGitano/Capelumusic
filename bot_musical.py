import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token del bot (obténlo de @BotFather en Telegram)
TOKEN = '8472230810:AAF2Nfix6WumdeAUTjwvgQYd0hiIzMgClbA'

class MusicBot:
    def __init__(self):
        self.user_searches = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida personalizado"""
        # Logo del lobo en arte ASCII
        wolf_logo = """
        ╔══════════════════════════════════════╗
        ║                                      ║
        ║            🐺  TU LOBO  🐺           ║
        ║         ASISTENTE MUSICAL            ║
        ║                                      ║
        ╚══════════════════════════════════════╝
        """
        
        welcome_message = (
            f"{wolf_logo}\n\n"
            "🎵 *¡Hola Verónica, yo soy tu Lobo asistente!* 🐺\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎸 *¿Qué puedo hacer por ti?*\n\n"
            "🎤 Buscar cualquier canción que desees\n"
            "🎬 Reproducir con video o solo audio\n"
            "💿 Escuchar álbumes completos\n"
            "⭐ Crear playlists de lo mejor\n"
            "🎵 ¡Y mucho más!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ *Solo escribe:*\n"
            "• El nombre de una canción\n"
            "• El nombre de un artista\n"
            "• O canta una estrofa\n\n"
            "🐺 *Tu Lobo está listo para aullar contigo* 🎶\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def search_music(self, query: str):
        """Busca música en YouTube"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch5',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch5:{query}", download=False)
                if 'entries' in results:
                    return results['entries'][:5]
                return []
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        query = update.message.text
        user_id = update.effective_user.id
        
        # Mensaje de búsqueda personalizado
        await update.message.reply_text(
            f"🐺 *Tu Lobo está rastreando...*\n"
            f"🔍 Buscando: *{query}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
        
        results = await self.search_music(query)
        
        if not results:
            await update.message.reply_text(
                "🐺 *¡Woof!*\n\n"
                "😔 No encontré nada en mi territorio...\n"
                "Intenta con otro término de búsqueda.\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        # Guardar resultados para este usuario
        self.user_searches[user_id] = {
            'query': query,
            'results': results
        }
        
        # Mostrar opciones con emojis
        keyboard = []
        emojis = ["🎵", "🎸", "🎹", "🎺", "🎻"]
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Sin título')
            keyboard.append([InlineKeyboardButton(
                f"{emojis[i]} {title[:55]}", 
                callback_data=f"select_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new_search")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🐺 *¡Tu Lobo encontró estas canciones!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Selecciona la que quieras escuchar:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los botones presionados"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "new_search":
            await query.edit_message_text(
                "🐺 *Tu Lobo está listo para buscar de nuevo*\n\n"
                "🎵 Escribe el nombre de una canción, artista\n"
                "o canta una estrofa para buscar.\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        if data.startswith("select_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                await query.edit_message_text(
                    "🐺 *¡Ups!*\n"
                    "❌ El rastro se perdió...\n"
                    "Realiza una nueva búsqueda."
                )
                return
            
            selected = self.user_searches[user_id]['results'][idx]
            self.user_searches[user_id]['selected'] = selected
            
            # Mostrar opciones de reproducción con estilo
            keyboard = [
                [InlineKeyboardButton("🎵 Solo este tema", callback_data="play_single")],
                [InlineKeyboardButton("💿 Álbum completo", callback_data="play_album")],
                [InlineKeyboardButton("⭐ Playlist mejores temas", callback_data="play_best")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🐺 *¡Excelente elección!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎵 {selected.get('title', 'Sin título')}\n\n"
                f"*¿Cómo quieres disfrutarla?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data in ["play_single", "play_album", "play_best"]:
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text(
                    "🐺 ❌ Sesión expirada.\nRealiza una nueva búsqueda."
                )
                return
            
            selected = self.user_searches[user_id]['selected']
            
            # Opciones de formato
            keyboard = [
                [InlineKeyboardButton("🎥 Con video", callback_data=f"format_video_{data}")],
                [InlineKeyboardButton("🎧 Solo audio", callback_data=f"format_audio_{data}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            mode_text = {
                "play_single": "este tema 🎵",
                "play_album": "el álbum completo 💿",
                "play_best": "playlist de mejores temas ⭐"
            }
            
            await query.edit_message_text(
                f"🐺 *Reproduciendo: {mode_text[data]}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"*¿Cómo lo prefieres?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("format_"):
            parts = data.split("_")
            format_type = parts[1]  # video o audio
            play_mode = "_".join(parts[2:])  # play_single, play_album, etc
            
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 ❌ Sesión expirada. Realiza una nueva búsqueda.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await self.play_music(query, selected, format_type, play_mode, user_id)
    
    async def play_music(self, query, selected, format_type, play_mode, user_id):
        """Reproduce la música seleccionada"""
        await query.edit_message_text(
            "🐺 *Tu Lobo está preparando tu música...*\n"
            "⏳ Un momento por favor...\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            if play_mode == "play_single":
                await self.download_and_send(query, selected, format_type)
            
            elif play_mode == "play_album":
                # Buscar más canciones del mismo artista/álbum
                artist_query = selected.get('channel', '') or selected.get('uploader', '')
                await query.edit_message_text(
                    f"🐺 *Buscando álbum completo...*\n"
                    f"🔍 {artist_query}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                album_results = await self.search_music(f"{artist_query} full album")
                if album_results:
                    await self.download_and_send(query, album_results[0], format_type)
                else:
                    await self.download_and_send(query, selected, format_type)
            
            elif play_mode == "play_best":
                # Buscar playlist de mejores temas
                artist_query = selected.get('channel', '') or selected.get('uploader', '')
                await query.edit_message_text(
                    f"🐺 *Buscando los mejores temas...*\n"
                    f"⭐ {artist_query}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                best_results = await self.search_music(f"{artist_query} best hits greatest")
                if best_results:
                    await self.download_and_send(query, best_results[0], format_type)
                else:
                    await self.download_and_send(query, selected, format_type)
            
            # Volver al menú con mensaje del lobo
            keyboard = [[InlineKeyboardButton("🔙 Volver al inicio", callback_data="new_search")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "🐺 *¡Listo Verónica!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Reproducción completada\n\n"
                "🎵 ¿Quieres buscar algo más?\n"
                "Tu Lobo está aquí para ti 🐺💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error en reproducción: {e}")
            await query.edit_message_text(
                f"🐺 *¡Auch!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ Hubo un problema: {str(e)}\n\n"
                f"Intenta con otra búsqueda."
            )
    
    async def download_and_send(self, query, video_info, format_type):
        """Descarga y envía el archivo"""
        video_id = video_info.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        if format_type == "video":
            ydl_opts = {
                'format': 'best[ext=mp4][height<=720]/best',
                'outtmpl': f'downloads/{video_id}.%(ext)s',
                'quiet': True,
            }
        else:  # audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'downloads/{video_id}.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
        
        try:
            # Crear directorio si no existe
            os.makedirs('downloads', exist_ok=True)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if format_type == "audio":
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            # Enviar archivo con mensaje personalizado
            title = video_info.get('title', 'Sin título')
            
            if format_type == "video":
                with open(filename, 'rb') as video_file:
                    await query.message.reply_video(
                        video=video_file,
                        caption=f"🐺🎥 {title}\n━━━━━━━━━━━━━━━━━━━━━━\n¡Disfruta tu video, Verónica! 💕",
                        supports_streaming=True
                    )
            else:
                with open(filename, 'rb') as audio_file:
                    await query.message.reply_audio(
                        audio=audio_file,
                        caption=f"🐺🎵 {title}\n━━━━━━━━━━━━━━━━━━━━━━\n¡A disfrutar esta música! 💕",
                        title=title
                    )
            
            # Limpiar archivo
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            # Si falla la descarga, enviar link
            await query.message.reply_text(
                f"🐺 *{video_info.get('title', 'Sin título')}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 Link: {url}\n\n"
                f"(No pude descargar el archivo,\npero puedes usar el link para reproducir)",
                parse_mode='Markdown'
            )

def main():
    """Inicia el bot"""
    bot = MusicBot()
    
    # Crear aplicación
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # Iniciar bot
    print("🐺 Bot del Lobo iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()