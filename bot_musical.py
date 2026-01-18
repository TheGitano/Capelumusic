import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token del bot
TOKEN = os.getenv('TELEGRAM_TOKEN', '8472230810:AAF2Nfix6WumdeAUTjwvgQYd0hiIzMgClbA')

class MusicBot:
    def __init__(self):
        self.user_searches = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        wolf_logo = """
╔══════════════════════════════════════╗
║            🐺  TU LOBO  🐺           ║
║         ASISTENTE MUSICAL            ║
╚══════════════════════════════════════╝
        """
        
        welcome_message = (
            f"{wolf_logo}\n\n"
            "🎵 *¡Hola Verónica, yo soy tu Lobo asistente!* 🐺\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎸 *¿Qué puedo hacer por ti?*\n\n"
            "🎤 Buscar cualquier canción\n"
            "🎬 Reproducir con video o audio\n"
            "💿 Escuchar álbumes completos\n"
            "⭐ Crear playlists\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ *Solo escribe el nombre de una canción o artista*\n\n"
            "🐺 *Tu Lobo está listo para aullar contigo* 🎶"
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
            logger.error(f"Error búsqueda: {e}")
            return []
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto"""
        query = update.message.text
        user_id = update.effective_user.id
        
        await update.message.reply_text(
            f"🐺 *Tu Lobo está rastreando...*\n"
            f"🔍 Buscando: *{query}*",
            parse_mode='Markdown'
        )
        
        results = await self.search_music(query)
        
        if not results:
            await update.message.reply_text(
                "🐺 *¡Woof!*\n\n"
                "😔 No encontré nada...\n"
                "Intenta con otro término."
            )
            return
        
        self.user_searches[user_id] = {
            'query': query,
            'results': results
        }
        
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
            "Selecciona la que quieras:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los botones"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "new_search":
            await query.edit_message_text(
                "🐺 *Tu Lobo está listo*\n\n"
                "🎵 Escribe el nombre de una canción o artista"
            )
            return
        
        if data.startswith("select_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Sesión expirada. Busca de nuevo.")
                return
            
            selected = self.user_searches[user_id]['results'][idx]
            self.user_searches[user_id]['selected'] = selected
            
            keyboard = [
                [InlineKeyboardButton("🎵 Solo este tema", callback_data="play_single")],
                [InlineKeyboardButton("💿 Álbum completo", callback_data="play_album")],
                [InlineKeyboardButton("⭐ Mejores temas", callback_data="play_best")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🐺 *¡Excelente elección!*\n"
                f"🎵 {selected.get('title', 'Sin título')}\n\n"
                f"*¿Cómo quieres disfrutarla?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data in ["play_single", "play_album", "play_best"]:
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Sesión expirada.")
                return
            
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
                f"🐺 *Reproduciendo: {mode_text[data]}*\n\n"
                f"*¿Cómo lo prefieres?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("format_"):
            parts = data.split("_")
            format_type = parts[1]
            play_mode = "_".join(parts[2:])
            
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Sesión expirada.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await self.play_music(query, selected, format_type, play_mode)
    
    async def play_music(self, query, selected, format_type, play_mode):
        """Reproduce la música"""
        await query.edit_message_text(
            "🐺 *Tu Lobo está preparando tu música...*\n"
            "⏳ Un momento..."
        )
        
        try:
            video_id = selected.get('id')
            url = f"https://www.youtube.com/watch?v={video_id}"
            title = selected.get('title', 'Sin título')
            
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="new_search")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"🐺🎵 *{title}*\n\n"
                f"🔗 {url}\n\n"
                f"✅ ¡Listo Verónica!\n"
                f"Tu Lobo está aquí para ti 🐺💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await query.edit_message_text(
                "🐺 *¡Reproducción lista!*",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.edit_message_text(
                f"🐺 *¡Auch!*\n"
                f"❌ Hubo un problema: {str(e)}"
            )

def main():
    """Inicia el bot"""
    bot = MusicBot()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("🐺 Bot del Lobo iniciado correctamente")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
