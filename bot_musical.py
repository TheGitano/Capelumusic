import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio
from datetime import datetime
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
        wolf_logo = "╔══════════════════════════╗\n║   🐺  TU LOBO  🐺      ║\n╚══════════════════════════╝"
        
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar música", callback_data="mode_music")],
            [InlineKeyboardButton("🎤 Karaokes", callback_data="mode_karaoke")],
            [InlineKeyboardButton("📝 Crear playlist", callback_data="mode_playlist")],
            [InlineKeyboardButton("📚 Mis playlists", callback_data="view_playlists")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{wolf_logo}\n\n🎵 *Vero, soy tu Lobo!* 🐺\n\n¿Qué quieres hacer?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def search_albums(self, artist: str):
        """Busca álbumes de un artista"""
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Buscar álbumes completos
                results = ydl.extract_info(f"ytsearch10:{artist} full album", download=False)
                if 'entries' in results:
                    albums = []
                    for entry in results['entries'][:5]:
                        duration = entry.get('duration', 0)
                        # Solo álbumes largos (más de 20 minutos)
                        if duration > 1200:
                            albums.append({
                                'title': entry.get('title', 'Sin título'),
                                'id': entry['id'],
                                'url': f"https://www.youtube.com/watch?v={entry['id']}",
                                'duration': duration
                            })
                    return albums
                return []
        except Exception as e:
            logger.error(f"Error álbumes: {e}")
            return []
    
    async def search_songs(self, query: str, max_results=5):
        """Busca canciones individuales"""
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                if 'entries' in results:
                    songs = []
                    for entry in results['entries'][:max_results]:
                        songs.append({
                            'title': entry.get('title', 'Sin título'),
                            'id': entry['id'],
                            'url': f"https://www.youtube.com/watch?v={entry['id']}"
                        })
                    return songs
                return []
        except Exception as e:
            logger.error(f"Error búsqueda: {e}")
            return []
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa voz RÁPIDO"""
        user_id = update.effective_user.id
        
        try:
            msg = await update.message.reply_text("🐺 *Escuchando...* 🎤", parse_mode='Markdown')
            
            voice_file = await update.message.voice.get_file()
            voice_path = f'voice_{user_id}.ogg'
            await voice_file.download_to_drive(voice_path)
            
            audio = AudioSegment.from_ogg(voice_path)
            wav_path = f'voice_{user_id}.wav'
            audio.export(wav_path, format='wav')
            
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio_data, language='es-ES')
                    
                    os.remove(voice_path)
                    os.remove(wav_path)
                    
                    await msg.edit_text(f"🐺 *Escuché:* \"{text}\"\n\n🔍 Buscando...", parse_mode='Markdown')
                    
                    # Buscar directamente
                    await self.quick_search(update, user_id, text)
                    
                except sr.UnknownValueError:
                    await msg.edit_text("🐺 No entendí. Intenta de nuevo.")
                    os.remove(voice_path)
                    os.remove(wav_path)
                except sr.RequestError:
                    await msg.edit_text("🐺 Error. Escríbeme el tema.")
                    os.remove(voice_path)
                    os.remove(wav_path)
                    
        except Exception as e:
            logger.error(f"Error voz: {e}")
            await update.message.reply_text("🐺 Escribe el tema, Vero.")
    
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
                f"✅ {songs_list}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Búsqueda directa
        await self.quick_search(update, user_id, text)
    
    async def quick_search(self, update, user_id, query):
        """Búsqueda RÁPIDA y DIRECTA"""
        msg = await update.message.reply_text(f"🔍 *{query}*", parse_mode='Markdown')
        
        # Detectar si es artista o canción
        # Si tiene palabras clave, es canción. Si no, es artista
        song_keywords = ['cancion', 'tema', 'song', 'track']
        is_song = any(kw in query.lower() for kw in song_keywords)
        
        if not is_song:
            # Buscar ÁLBUMES del artista
            albums = await self.search_albums(query)
            
            if albums:
                # Guardar en sesión
                self.user_searches[user_id] = {
                    'query': query,
                    'albums': albums,
                    'is_artist': True
                }
                
                keyboard = []
                for i, album in enumerate(albums):
                    mins = album['duration'] // 60
                    keyboard.append([InlineKeyboardButton(
                        f"💿 {album['title'][:45]} ({mins}min)",
                        callback_data=f"album_{i}"
                    )])
                
                # También búsqueda de canciones
                keyboard.append([InlineKeyboardButton("🎵 Ver canciones sueltas", callback_data="show_songs")])
                keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.edit_text(
                    f"🐺 *Álbumes de {query}:*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
        
        # Buscar CANCIONES
        songs = await self.search_songs(query)
        
        if not songs:
            await msg.edit_text("🐺 No encontré nada. Intenta otra búsqueda.")
            return
        
        self.user_searches[user_id] = {
            'query': query,
            'songs': songs,
            'is_artist': False
        }
        
        keyboard = []
        for i, song in enumerate(songs):
            keyboard.append([InlineKeyboardButton(
                f"🎵 {song['title'][:50]}",
                callback_data=f"play_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(
            f"🐺 *Encontré:*",
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
                [InlineKeyboardButton("🎵 Buscar música", callback_data="mode_music")],
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
                "🐺 *Dime qué quieres escuchar*\n\n🎤 Por voz o escrito\n💡 Artista o canción",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_karaoke":
            self.user_searches[user_id] = {'mode': 'karaoke'}
            await query.edit_message_text(
                "🐺 *Dime qué karaoke* 🎤",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_playlist":
            self.user_searches[user_id] = {'mode': 'playlist_input', 'playlist_songs': []}
            await query.edit_message_text(
                "🐺 *Playlist personalizada*\n\nEscribe canciones (una por mensaje):",
                parse_mode='Markdown'
            )
            return
        
        if data == "show_songs":
            if user_id not in self.user_searches:
                return
            
            artist = self.user_searches[user_id].get('query', '')
            songs = await self.search_songs(artist)
            
            self.user_searches[user_id]['songs'] = songs
            
            keyboard = []
            for i, song in enumerate(songs):
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {song['title'][:50]}",
                    callback_data=f"play_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🐺 *Canciones de {artist}:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("album_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                return
            
            album = self.user_searches[user_id]['albums'][idx]
            
            keyboard = [
                [InlineKeyboardButton("▶️ Reproducir álbum completo", callback_data=f"play_full_album_{idx}")],
                [InlineKeyboardButton("🎵 Ver canciones del álbum", callback_data=f"album_songs_{idx}")],
                [InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🐺 *{album['title']}*\n\n¿Qué quieres hacer?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("play_full_album_"):
            idx = int(data.split("_")[3])
            if user_id not in self.user_searches:
                return
            
            album = self.user_searches[user_id]['albums'][idx]
            
            await query.edit_message_text(f"🐺 *Reproduciendo álbum completo*", parse_mode='Markdown')
            
            await query.message.reply_text(
                f"💿 *{album['title']}*\n\n🔗 {album['url']}\n\n▶️ Click para reproducir",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🐺 *¡Disfruta!* 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("album_songs_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_searches:
                return
            
            album = self.user_searches[user_id]['albums'][idx]
            artist = self.user_searches[user_id].get('query', '')
            
            await query.edit_message_text("🔍 *Buscando canciones del álbum...*", parse_mode='Markdown')
            
            # Buscar canciones individuales del álbum
            album_name = album['title'].split('-')[0].strip() if '-' in album['title'] else album['title']
            songs = await self.search_songs(f"{artist} {album_name}", max_results=10)
            
            self.user_searches[user_id]['album_songs'] = songs
            
            keyboard = []
            for i, song in enumerate(songs[:8]):
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {song['title'][:50]}",
                    callback_data=f"play_album_song_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🐺 *Canciones del álbum:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("play_album_song_"):
            idx = int(data.split("_")[3])
            if user_id not in self.user_searches:
                return
            
            song = self.user_searches[user_id]['album_songs'][idx]
            await self.play_now(query, song)
            return
        
        if data.startswith("play_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                return
            
            song = self.user_searches[user_id]['songs'][idx]
            await self.play_now(query, song)
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
            
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            if user_id not in self.user_playlists:
                self.user_playlists[user_id] = []
            
            playlist_data = {'date': date_str, 'songs': songs, 'links': []}
            
            await query.edit_message_text(f"🐺 *Creando playlist...*", parse_mode='Markdown')
            
            for i, song in enumerate(songs, 1):
                results = await self.search_songs(song, max_results=1)
                if results:
                    playlist_data['links'].append(results[0]['url'])
                    await query.message.reply_text(
                        f"🎵 {i}/{len(songs)}: {results[0]['title'][:40]}\n🔗 {results[0]['url']}",
                        parse_mode='Markdown'
                    )
                    await asyncio.sleep(1)
            
            self.user_playlists[user_id].append(playlist_data)
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"✅ *Playlist guardada*\n📅 {date_str}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            del self.user_searches[user_id]
            return
        
        if data == "view_playlists":
            if user_id not in self.user_playlists or not self.user_playlists[user_id]:
                await query.edit_message_text("🐺 No tienes playlists.")
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
                "🐺 *Tus playlists:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("load_playlist_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_playlists:
                return
            
            playlist = self.user_playlists[user_id][idx]
            
            await query.edit_message_text(f"🐺 *Reproduciendo...*", parse_mode='Markdown')
            
            for i, (song, link) in enumerate(zip(playlist['songs'], playlist['links']), 1):
                await query.message.reply_text(f"🎵 {i}: {song}\n🔗 {link}", parse_mode='Markdown')
                await asyncio.sleep(1)
            
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("✅ *Listo*", reply_markup=reply_markup, parse_mode='Markdown')
            return
    
    async def play_now(self, query, song):
        """Reproduce AHORA - SIN RODEOS"""
        keyboard = [[InlineKeyboardButton("🔙 Buscar otra", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"▶️ *{song['title']}*\n\n🔗 {song['url']}\n\n💡 Click para reproducir",
            parse_mode='Markdown'
        )
        
        await query.edit_message_text(
            "🐺 *¡Disfrutala!* 💕",
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
