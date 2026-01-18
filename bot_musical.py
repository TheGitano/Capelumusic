import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN', '8472230810:AAF2Nfix6WumdeAUTjwvgQYd0hiIzMgClbA')

class MusicBot:
    def __init__(self):
        self.user_searches = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🐺 *¡Hola Verónica!*\n\n"
            "Soy tu Lobo asistente musical 🎵\n\n"
            "Escribe el nombre de una canción o artista",
            parse_mode='Markdown'
        )
    
    async def search_music(self, query: str):
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'default_search': 'ytsearch5'}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch5:{query}", download=False)
                return results['entries'][:5] if 'entries' in results else []
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text
        user_id = update.effective_user.id
        
        await update.message.reply_text(f"🔍 Buscando: *{query}*", parse_mode='Markdown')
        
        results = await self.search_music(query)
        
        if not results:
            await update.message.reply_text("🐺 No encontré nada. Intenta otra búsqueda.")
            return
        
        self.user_searches[user_id] = {'query': query, 'results': results}
        
        keyboard = []
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Sin título')
            keyboard.append([InlineKeyboardButton(f"🎵 {title[:50]}", callback_data=f"select_{i}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Nueva búsqueda", callback_data="new")])
        
        await update.message.reply_text(
            "🐺 *Resultados:*", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "new":
            await query.edit_message_text("🐺 Escribe otra canción")
            return
        
        user_id = update.effective_user.id
        if query.data.startswith("select_"):
            idx = int(query.data.split("_")[1])
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Busca de nuevo")
                return
            
            selected = self.user_searches[user_id]['results'][idx]
            url = f"https://www.youtube.com/watch?v={selected.get('id')}"
            
            await query.message.reply_text(
                f"🐺🎵 *{selected.get('title')}*\n\n🔗 {url}\n\n¡Listo! 💕",
                parse_mode='Markdown'
            )
            await query.edit_message_text("🐺 ¡Disfruta!")

def main():
    bot = MusicBot()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    print("🐺 Bot iniciado correctamente")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

4. **Commit**

---

### **PASO 4: Verificar que requirements.txt esté correcto**

1. Abre `requirements.txt` en GitHub
2. Asegúrate que tenga EXACTAMENTE esto:
```
python-telegram-bot==20.7
yt-dlp==2024.12.23