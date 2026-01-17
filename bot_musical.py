import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio
from datetime import datetime
import json
import speech_recognition as sr
from pydub import AudioSegment

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8472230810:AAF2Nfix6WumdeAUTjwvgQYd0hiIzMgClbA'

class MusicBot:
    def __init__(self):
        self.user_searches = {}
        self.user_playlists = {}
        self.recognizer = sr.Recognizer()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        wolf_logo = """
        ╔══════════════════════════════════════╗
        ║            🐺  TU LOBO  🐺           ║
        ║         ASISTENTE MUSICAL            ║
        ╚══════════════════════════════════════╝
        """
        
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
            [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
            [InlineKeyboardButton("📝 Crear playlist", callback_data="mode_playlist")],
            [InlineKeyboardButton("📚 Mis playlists", callback_data="view_playlists")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{wolf_logo}\n\n🎵 *¡Hola Verónica, yo soy tu Lobo!* 🐺\n\n¿Qué quieres hacer?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def search_music(self, query: str):
        """Busca música y devuelve URLs directas"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch5:{query}", download=False)
                if 'entries' in results:
                    videos = []
                    for entry in results['entries'][:5]:
                        # Obtener URLs de streaming
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        videos.append({
                            'title': entry.get('title', 'Sin título'),
                            'id': entry['id'],
                            'url': video_url,
                            'duration': entry.get('duration', 0),
                            'has_video': True
                        })
                    return videos
                return []
        except Exception as e:
            logger.error(f"Error búsqueda: {e}")
            return []
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa notas de voz y las convierte a texto"""
        user_id = update.effective_user.id
        
        try:
            await update.message.reply_text("🐺 *Escuchando tu voz...* 🎤", parse_mode='Markdown')
            
            # Descargar audio
            voice_file = await update.message.voice.get_file()
            voice_path = f'voice_{user_id}.ogg'
            await voice_file.download_to_drive(voice_path)
            
            # Convertir OGG a WAV
            audio = AudioSegment.from_ogg(voice_path)
            wav_path = f'voice_{user_id}.wav'
            audio.export(wav_path, format='wav')
            
            # Reconocer voz
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio_data, language='es-ES')
                    
                    # Limpiar archivos
                    os.remove(voice_path)
                    os.remove(wav_path)
                    
                    await update.message.reply_text(
                        f"🐺 *Escuché:* \"{text}\"\n\n🔍 Buscando...",
                        parse_mode='Markdown'
                    )
                    
                    # Buscar directamente
                    await self.process_search(update, user_id, text)
                    
                except sr.UnknownValueError:
                    await update.message.reply_text("🐺 No pude entender. Intenta de nuevo o escríbeme.")
                    os.remove(voice_path)
                    os.remove(wav_path)
                except sr.RequestError:
                    await update.message.reply_text("🐺 Error de conexión. Escribe el tema que buscas.")
                    os.remove(voice_path)
                    os.remove(wav_path)
                    
        except Exception as e:
            logger.error(f"Error voz: {e}")
            await update.message.reply_text("🐺 Escribe el tema que buscas, Vero.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Modo playlist
        if user_id in self.user_searches and self.user_searches[user_id].get('mode') == 'playlist_input':
            if 'playlist_songs' not in self.user_searches[user_id]:
                self.user_searches[user_id]['playlist_songs'] = []
            
            self.user_searches[user_id]['playlist_songs'].append(text)
            
            keyboard = [
                [InlineKeyboardButton("➕ Agregar otra", callback_data="playlist_add_more")],
                [InlineKeyboardButton("✅ Crear playlist", callback_data="playlist_create")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            songs_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(self.user_searches[user_id]['playlist_songs'])])
            await update.message.reply_text(
                f"🐺 *Agregado*\n\n📝 {songs_list}\n\n¿Qué hago?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Verificar modo activo
        if user_id not in self.user_searches or 'mode' not in self.user_searches[user_id]:
            keyboard = [
                [InlineKeyboardButton("🎵 Canciones", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Karaokes", callback_data="mode_karaoke")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🐺 *Elige modo:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Buscar
        await self.process_search(update, user_id, text)
    
    async def process_search(self, update, user_id, query):
        """Procesa búsqueda y muestra resultados RÁPIDO"""
        mode = self.user_searches[user_id].get('mode', 'music')
        
        # Buscar según modo
        if mode == 'karaoke':
            search_query = f"{query} karaoke lyrics"
        else:
            search_query = query
        
        await update.message.reply_text(f"🐺 🔍 *{query}*", parse_mode='Markdown')
        
        # Buscar original
        results = await self.search_music(search_query)
        
        # Buscar español si es música normal
        spanish_results = []
        if mode == 'music':
            spanish_results = await self.search_music(f"{query} español")
        
        if not results and not spanish_results:
            await update.message.reply_text("🐺 No encontré nada. Intenta otra búsqueda.")
            return
        
        # Guardar
        self.user_searches[user_id].update({
            'query': query,
            'results': results,
            'spanish_results': spanish_results
        })
        
        # Mostrar opciones DIRECTO
        keyboard = []
        
        # Versión original
        for i, r in enumerate(results[:3]):
            emoji = "🎤" if mode == 'karaoke' else "🎵"
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {r['title'][:50]}", 
                callback_data=f"play_{i}"
            )])
        
        # Versión español
        if spanish_results:
            keyboard.append([InlineKeyboardButton("🇪🇸 VERSIONES EN ESPAÑOL", callback_data="dummy")])
            for i, r in enumerate(spanish_results[:3]):
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {r['title'][:50]}", 
                    callback_data=f"play_es_{i}"
                )])
        
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🐺 *Encontré esto, Vero:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "back_to_menu":
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            
            keyboard = [
                [InlineKeyboardButton("🎵 Canciones", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Karaokes", callback_data="mode_karaoke")],
                [InlineKeyboardButton("📝 Crear playlist", callback_data="mode_playlist")],
                [InlineKeyboardButton("📚 Mis playlists", callback_data="view_playlists")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🐺 *¿Qué quieres hacer?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_music":
            self.user_searches[user_id] = {'mode': 'music'}
            await query.edit_message_text(
                "🐺 *Escribe o canta el tema que buscas*\n\n💡 Buscaré versiones en español también",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_karaoke":
            self.user_searches[user_id] = {'mode': 'karaoke'}
            await query.edit_message_text(
                "🐺 *Dime qué karaoke quieres* 🎤\n\n📝 Todos incluyen letra",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_playlist":
            self.user_searches[user_id] = {'mode': 'playlist_input', 'playlist_songs': []}
            await query.edit_message_text(
                "🐺 *Crea tu playlist*\n\nEscribe temas o artistas (uno por mensaje):",
                parse_mode='Markdown'
            )
            return
        
        if data == "playlist_add_more":
            await query.edit_message_text("🐺 *Escribe otra canción:*", parse_mode='Markdown')
            return
        
        if data == "playlist_create":
            if user_id not in self.user_searches:
                return
            
            songs = self.user_searches[user_id].get('playlist_songs', [])
            if not songs:
                return
            
            # Guardar playlist
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            if user_id not in self.user_playlists:
                self.user_playlists[user_id] = []
            
            playlist_data = {
                'date': date_str,
                'songs': songs,
                'links': []
            }
            
            await query.edit_message_text(f"🐺 *Creando playlist...*\n{len(songs)} canciones", parse_mode='Markdown')
            
            # Buscar y enviar
            for i, song in enumerate(songs, 1):
                results = await self.search_music(song)
                if results:
                    video = results[0]
                    playlist_data['links'].append(video['url'])
                    
                    await query.message.reply_text(
                        f"🎵 *{i}/{len(songs)}:* {video['title'][:50]}\n🔗 {video['url']}",
                        parse_mode='Markdown'
                    )
                    await asyncio.sleep(1)
            
            self.user_playlists[user_id].append(playlist_data)
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"🐺 *¡Playlist guardada!*\n📅 {date_str}\n\n✅ {len(songs)} canciones listas",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            del self.user_searches[user_id]
            return
        
        if data == "view_playlists":
            if user_id not in self.user_playlists or not self.user_playlists[user_id]:
                await query.edit_message_text("🐺 No tienes playlists guardadas aún.")
                return
            
            keyboard = []
            for i, pl in enumerate(self.user_playlists[user_id]):
                keyboard.append([InlineKeyboardButton(
                    f"📅 {pl['date']} ({len(pl['songs'])} canciones)",
                    callback_data=f"load_playlist_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🐺 *Tus playlists guardadas:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("load_playlist_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_playlists:
                return
            
            playlist = self.user_playlists[user_id][idx]
            
            await query.edit_message_text(f"🐺 *Reproduciendo playlist...*\n📅 {playlist['date']}", parse_mode='Markdown')
            
            for i, (song, link) in enumerate(zip(playlist['songs'], playlist['links']), 1):
                await query.message.reply_text(
                    f"🎵 *{i}/{len(playlist['songs'])}:* {song}\n🔗 {link}",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(1)
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🐺 *¡Playlist completada!* 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("play_es_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_searches:
                return
            
            video = self.user_searches[user_id]['spanish_results'][idx]
            await self.send_video_link(query, video, is_spanish=True)
            return
        
        if data.startswith("play_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                return
            
            video = self.user_searches[user_id]['results'][idx]
            await self.send_video_link(query, video)
            return
    
    async def send_video_link(self, query, video, is_spanish=False):
        """Envía link directo para reproducción"""
        title = video['title']
        url = video['url']
        
        lang_text = "🇪🇸 Español" if is_spanish else "🌍 Original"
        
        keyboard = [[InlineKeyboardButton("🔙 Buscar otra", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"🐺 *{title}*\n{lang_text}\n\n"
            f"🔗 Reproducir: {url}\n\n"
            f"💡 Click en el link para ver/escuchar",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await query.edit_message_text(
            f"🐺 *¡Listo!* Reproduciendo...\n\n¿Quieres otra?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def main():
    bot = MusicBot()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("🐺 Bot iniciado")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
