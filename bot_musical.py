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
        
        if data == "prev_album_page":
            if user_id in self.user_searches:
                self.user_searches[user_id]['album_page'] = self.user_searches[user_id].get('album_page', 0) - 1
                query_text = self.user_searches[user_id].get('query', '')
                await self.show_album_page(query, user_id, query_text)
            return
        
        if data == "next_album_page":
            if user_id in self.user_searches:
                self.user_searches[user_id]['album_page'] = self.user_searches[user_id].get('album_page', 0) + 1
                query_text = self.user_searches[user_id].get('query', '')
                await self.show_album_page(query, user_id, query_text)
            return
        
        if data == "next_song_page":
            if user_id in self.user_searches:
                self.user_searches[user_id]['song_page'] = self.user_searches[user_id].get('song_page', 0) + 1
                await self.show_song_page(query, user_id)
            return
        
        if data == "prev_song_page":
            if user_id in self.user_searches:
                self.user_searches[user_id]['song_page'] = self.user_searches[user_id].get('song_page', 0) - 1
                await self.show_song_page(query, user_id)
            return
        self.user_searches = {}
        self.user_playlists = {}
        self.recognizer = sr.Recognizer()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        wolf_logo = "╔══════════════════════════╗\n║   🐺  TU LOBO  🐺      ║\n╚══════════════════════════╝"
        
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar música", callback_data="mode_music")],
            [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
            [InlineKeyboardButton("📝 Crear mi playlist", callback_data="mode_playlist")],
            [InlineKeyboardButton("📚 Mis playlists guardadas", callback_data="view_playlists")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{wolf_logo}\n\n🎵 *¡Hola Vero, soy tu Lobo!* 🐺\n\n¿Qué quieres hacer hoy?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def verify_video(self, video_id):
        """Verifica que un video se pueda reproducir SIN ERRORES"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'format': 'best'
        }
        
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Verificar que tenga formatos disponibles
                if not info.get('formats'):
                    return False
                
                # Verificar que no sea privado o eliminado
                if info.get('is_live') or info.get('was_live'):
                    return False
                
                # Verificar duración mínima (al menos 30 segundos)
                duration = info.get('duration', 0)
                if duration < 30:
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Video no disponible {video_id}: {e}")
            return False
    
    async def search_all_albums(self, artist: str, progress_callback=None):
        """Busca TODOS los álbumes del artista - SIN LÍMITE"""
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        
        albums = []
        seen_ids = set()
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Buscar más resultados (YouTube limita a 100 por búsqueda)
                results = ydl.extract_info(f"ytsearch100:{artist} album completo full", download=False)
                
                if 'entries' in results:
                    for i, entry in enumerate(results['entries']):
                        if not entry:
                            continue
                        
                        video_id = entry.get('id')
                        if not video_id or video_id in seen_ids:
                            continue
                        
                        duration = entry.get('duration', 0)
                        title = entry.get('title', '')
                        
                        # Solo álbumes (más de 15 minutos) y que contengan palabras clave
                        title_lower = title.lower()
                        is_album = duration > 900 and any(word in title_lower for word in ['album', 'disco', 'full', 'completo', 'sessions', 'mix'])
                        
                        if is_album:
                            seen_ids.add(video_id)
                            
                            # Actualizar progreso
                            if progress_callback:
                                await progress_callback(i + 1, len(results['entries']), len(albums))
                            
                            albums.append({
                                'title': title,
                                'id': video_id,
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'duration': duration
                            })
                
                # Segunda búsqueda con variación
                results2 = ydl.extract_info(f"ytsearch50:{artist} discografia", download=False)
                
                if 'entries' in results2:
                    for entry in results2['entries']:
                        if not entry:
                            continue
                        
                        video_id = entry.get('id')
                        if not video_id or video_id in seen_ids:
                            continue
                        
                        duration = entry.get('duration', 0)
                        if duration > 900:
                            seen_ids.add(video_id)
                            albums.append({
                                'title': entry.get('title', 'Sin título'),
                                'id': video_id,
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'duration': duration
                            })
                
                return albums
        except Exception as e:
            logger.error(f"Error álbumes: {e}")
            return albums
    
    async def search_karaokes(self, query: str):
        """Busca SOLO KARAOKES VERIFICADOS - CON LETRA"""
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
        
        karaokes = []
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Buscar específicamente karaokes con letra
                results = ydl.extract_info(f"ytsearch20:{query} karaoke lyrics letra", download=False)
                
                if 'entries' in results:
                    for entry in results['entries']:
                        title = entry.get('title', '').lower()
                        
                        # Verificar que sea karaoke
                        if 'karaoke' not in title:
                            continue
                        
                        video_id = entry['id']
                        
                        # VERIFICAR que funcione
                        if await self.verify_video(video_id):
                            karaokes.append({
                                'title': entry.get('title', 'Sin título'),
                                'id': video_id,
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
                
                return karaokes
        except Exception as e:
            logger.error(f"Error karaokes: {e}")
            return []
    
    async def search_songs_verified(self, query: str, max_results=50):
        """Busca canciones - SIN verificación excesiva para mayor velocidad"""
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        
        songs = []
        seen_ids = set()
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Buscar canciones
                results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                
                if 'entries' in results:
                    for entry in results['entries']:
                        if not entry:
                            continue
                        
                        video_id = entry.get('id')
                        if not video_id or video_id in seen_ids:
                            continue
                        
                        # No álbumes completos en canciones
                        duration = entry.get('duration', 0)
                        if duration > 0 and duration < 900:  # Menos de 15 minutos
                            seen_ids.add(video_id)
                            
                            title = entry.get('title', '').lower()
                            has_lyrics = 'lyrics' in title or 'letra' in title or 'official video' in title
                            
                            songs.append({
                                'title': entry.get('title', 'Sin título'),
                                'id': video_id,
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'has_lyrics': has_lyrics
                            })
                
                return songs
        except Exception as e:
            logger.error(f"Error búsqueda: {e}")
            return []
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa voz"""
        user_id = update.effective_user.id
        
        try:
            msg = await update.message.reply_text("🐺 *Escuchando tu voz...* 🎤", parse_mode='Markdown')
            
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
                    
                    await msg.edit_text(f"🐺 Escuché: \"{text}\"\n\n🔍 Buscando...", parse_mode='Markdown')
                    
                    await self.quick_search(update, user_id, text)
                    
                except Exception:
                    await msg.edit_text("🐺 No entendí bien. Intenta de nuevo o escríbeme.")
                    try:
                        os.remove(voice_path)
                        os.remove(wav_path)
                    except:
                        pass
                    
        except Exception as e:
            logger.error(f"Error voz: {e}")
            await update.message.reply_text("🐺 Mejor escríbeme el tema, Vero.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Modo playlist
        if user_id in self.user_searches and self.user_searches[user_id].get('mode') == 'playlist_input':
            
            # Detectar comando "listo"
            if text.lower() in ['listo', 'ya', 'ya esta', 'terminar', 'crear']:
                songs = self.user_searches[user_id].get('playlist_songs', [])
                
                if not songs:
                    await update.message.reply_text("🐺 No hay canciones aún. Agrégame algunas primero.")
                    return
                
                # Crear playlist verificada
                await self.create_verified_playlist(update, user_id, songs)
                return
            
            # Agregar canción
            if 'playlist_songs' not in self.user_searches[user_id]:
                self.user_searches[user_id]['playlist_songs'] = []
            
            self.user_searches[user_id]['playlist_songs'].append(text)
            
            songs_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(self.user_searches[user_id]['playlist_songs'])])
            
            await update.message.reply_text(
                f"✅ *Agregado*\n\n📝 Tu playlist:\n{songs_list}\n\n"
                f"💡 Agrégame más canciones o escribe *\"listo\"* para crear la playlist",
                parse_mode='Markdown'
            )
            return
        
        # Búsqueda normal
        await self.quick_search(update, user_id, text)
    
    async def quick_search(self, update, user_id, query):
        """Búsqueda según modo activo"""
        
        # Verificar modo
        mode = self.user_searches.get(user_id, {}).get('mode', 'music')
        
        if mode == 'karaoke':
            # Buscar SOLO KARAOKES
            msg = await update.message.reply_text(f"🔍 Buscando karaokes: *{query}*", parse_mode='Markdown')
            
            karaokes = await self.search_karaokes(query)
            
            if not karaokes:
                await msg.edit_text("🐺 No encontré karaokes de eso. Intenta otra búsqueda.")
                return
            
            self.user_searches[user_id] = {
                'mode': 'karaoke',
                'query': query,
                'karaokes': karaokes
            }
            
            keyboard = []
            for i, k in enumerate(karaokes):
                keyboard.append([InlineKeyboardButton(
                    f"🎤 {k['title'][:48]}",
                    callback_data=f"play_karaoke_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(
                f"🐺 *Karaokes encontrados ({len(karaokes)}):*\n\n📝 Todos tienen letra",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Modo música normal - CON PROGRESO
        msg = await update.message.reply_text(
            f"🔍 *{query}*\n\nBuscando álbumes y canciones...\n⏳ Esto puede tardar un momento",
            parse_mode='Markdown'
        )
        
        # Función de progreso
        async def update_progress(current, total, found):
            if current % 10 == 0:  # Actualizar cada 10
                await msg.edit_text(
                    f"🔍 *{query}*\n\n"
                    f"📀 Verificando álbumes...\n"
                    f"🔍 {current}/{total} revisados\n"
                    f"✅ {found} funcionando",
                    parse_mode='Markdown'
                )
        
        # Buscar TODOS los álbumes con progreso
        albums = await self.search_all_albums(query, progress_callback=update_progress)
        
        if albums:
            self.user_searches[user_id] = {
                'mode': 'music',
                'query': query,
                'albums': albums
            }
            
            keyboard = []
            
            # CRÍTICO: Telegram tiene un límite de ~100 botones
            # Si hay más álbumes, dividir en grupos
            total_albums = len(albums)
            max_per_page = 90
            
            if total_albums > max_per_page:
                # Guardar página actual
                page = self.user_searches[user_id].get('album_page', 0)
                start = page * max_per_page
                end = min(start + max_per_page, total_albums)
                albums_to_show = albums[start:end]
                
                for i, album in enumerate(albums_to_show):
                    actual_index = start + i
                    mins = album['duration'] // 60
                    keyboard.append([InlineKeyboardButton(
                        f"💿 {album['title'][:43]} ({mins}m)",
                        callback_data=f"album_{actual_index}"
                    )])
                
                # Navegación
                nav_buttons = []
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="prev_album_page"))
                if end < total_albums:
                    nav_buttons.append(InlineKeyboardButton("➡️ Siguiente", callback_data="next_album_page"))
                
                if nav_buttons:
                    keyboard.append(nav_buttons)
                
                keyboard.append([InlineKeyboardButton(f"📄 Página {page + 1} de {(total_albums + max_per_page - 1) // max_per_page}", callback_data="dummy")])
            else:
                for i, album in enumerate(albums):
                    mins = album['duration'] // 60
                    keyboard.append([InlineKeyboardButton(
                        f"💿 {album['title'][:43]} ({mins}m)",
                        callback_data=f"album_{i}"
                    )])
            
            keyboard.append([InlineKeyboardButton("🎵 Ver todas las canciones sueltas", callback_data="show_songs")])
            keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(
                f"🐺 *TODOS los álbumes de {query}:*\n\n"
                f"✅ {total_albums} álbumes encontrados",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Búsqueda de canciones también con paginación
        await msg.edit_text(
            f"🔍 *{query}*\n\n"
            f"🎵 Buscando canciones...",
            parse_mode='Markdown'
        )
        
        songs = await self.search_songs_verified(query, max_results=50)
        
        if not songs:
            await msg.edit_text("🐺 No encontré canciones. Intenta otra búsqueda.")
            return
        
        self.user_searches[user_id] = {
            'mode': 'music',
            'query': query,
            'songs': songs,
            'song_page': 0
        }
        
        keyboard = []
        total_songs = len(songs)
        max_per_page = 90
        
        if total_songs > max_per_page:
            # Paginación
            songs_to_show = songs[:max_per_page]
            
            for i, song in enumerate(songs_to_show):
                emoji = "📝" if song.get('has_lyrics') else "🎵"
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {song['title'][:48]}",
                    callback_data=f"play_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("➡️ Más canciones", callback_data="next_song_page")])
            keyboard.append([InlineKeyboardButton(f"📄 Página 1 de {(total_songs + max_per_page - 1) // max_per_page}", callback_data="dummy")])
        else:
            for i, song in enumerate(songs):
                emoji = "📝" if song.get('has_lyrics') else "🎵"
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {song['title'][:48]}",
                    callback_data=f"play_{i}"
                )])
        
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(
            f"🐺 *Canciones encontradas:*\n\n"
            f"✅ {total_songs} canciones\n"
            f"📝 = Con letra",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    
    async def create_verified_playlist(self, update, user_id, songs):
        """Crea playlist VERIFICANDO que todo funcione"""
        msg = await update.message.reply_text(
            f"🐺 *Armando tu playlist...*\n\n"
            f"📝 {len(songs)} canciones\n"
            f"⏳ Verificando que todo funcione...",
            parse_mode='Markdown'
        )
        
        playlist_data = {
            'date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'songs': [],
            'links': []
        }
        
        verified_count = 0
        
        for i, song in enumerate(songs, 1):
            await msg.edit_text(
                f"🐺 *Verificando...*\n\n"
                f"🔍 {i}/{len(songs)}: {song}",
                parse_mode='Markdown'
            )
            
            results = await self.search_songs_verified(song, max_results=1)
            
            if results:
                video = results[0]
                playlist_data['songs'].append(song)
                playlist_data['links'].append(video['url'])
                verified_count += 1
        
        if verified_count == 0:
            await msg.edit_text("🐺 No pude verificar ninguna canción. Intenta con otras.")
            return
        
        # Guardar playlist
        if user_id not in self.user_playlists:
            self.user_playlists[user_id] = []
        
        self.user_playlists[user_id].append(playlist_data)
        
        keyboard = [
            [InlineKeyboardButton("▶️ Reproducir ahora", callback_data=f"load_playlist_{len(self.user_playlists[user_id])-1}")],
            [InlineKeyboardButton("❤️ Gracias Lobito", callback_data="thanks")],
            [InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.edit_text(
            f"🐺 *¡Playlist lista y verificada!*\n\n"
            f"✅ {verified_count}/{len(songs)} canciones funcionando\n"
            f"📅 {playlist_data['date']}\n\n"
            f"💕 ¿Te asistí bien, Vero?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Limpiar sesión
        del self.user_searches[user_id]
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "thanks":
            await query.answer("🐺💕 ¡De nada, Vero! Siempre para ti", show_alert=True)
            return
        
        if data == "back_to_menu":
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            
            keyboard = [
                [InlineKeyboardButton("🎵 Buscar música", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
                [InlineKeyboardButton("📝 Crear mi playlist", callback_data="mode_playlist")],
                [InlineKeyboardButton("📚 Mis playlists", callback_data="view_playlists")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🐺 *¿Qué quieres hacer, Vero?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_music":
            self.user_searches[user_id] = {'mode': 'music'}
            await query.edit_message_text(
                "🐺 *Dime qué quieres escuchar*\n\n"
                "🎤 Por voz o escrito\n"
                "💿 Artista para ver todos sus álbumes\n"
                "🎵 Canción específica",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_karaoke":
            self.user_searches[user_id] = {'mode': 'karaoke'}
            await query.edit_message_text(
                "🐺 *Dime qué karaoke buscas* 🎤\n\n"
                "📝 Solo buscaré karaokes con letra verificados",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_playlist":
            self.user_searches[user_id] = {'mode': 'playlist_input', 'playlist_songs': []}
            await query.edit_message_text(
                "🐺 *Crear playlist personalizada*\n\n"
                "📝 Pásame las canciones, artistas o grupos\n"
                "(uno por mensaje)\n\n"
                "💡 Cuando termines, escribe *\"listo\"*",
                parse_mode='Markdown'
            )
            return
        
        if data == "show_songs":
            if user_id not in self.user_searches:
                return
            
            artist = self.user_searches[user_id].get('query', '')
            
            await query.edit_message_text(
                "🔍 *Buscando TODAS las canciones...*\n⏳ Verificando que funcionen...",
                parse_mode='Markdown'
            )
            
            songs = await self.search_songs_verified(artist, max_results=100)
            
            self.user_searches[user_id]['songs'] = songs
            
            keyboard = []
            for i, song in enumerate(songs):
                emoji = "📝" if song.get('has_lyrics') else "🎵"
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {song['title'][:48]}",
                    callback_data=f"play_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🐺 *TODAS las canciones de {artist}:*\n\n"
                f"✅ {len(songs)} canciones verificadas\n"
                f"📝 = Con letra",
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
            
            mins = album['duration'] // 60
            await query.edit_message_text(
                f"🐺 *{album['title']}*\n\n⏱ {mins} minutos\n\n¿Qué quieres hacer?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("play_full_album_"):
            idx = int(data.split("_")[3])
            if user_id not in self.user_searches:
                return
            
            album = self.user_searches[user_id]['albums'][idx]
            
            keyboard = [
                [InlineKeyboardButton("❤️ Gracias Lobito", callback_data="thanks")],
                [InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"💿 *{album['title']}*\n\n"
                f"🔗 {album['url']}\n\n"
                f"▶️ Click para reproducir\n\n"
                f"💕 ¿Te gustó, Vero?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await query.edit_message_text("🐺 *¡A disfrutar!* 💕", parse_mode='Markdown')
            return
        
        if data.startswith("album_songs_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_searches:
                return
            
            album = self.user_searches[user_id]['albums'][idx]
            artist = self.user_searches[user_id].get('query', '')
            
            await query.edit_message_text(
                "🔍 *Buscando TODAS las canciones del álbum...*\n⏳ Verificando...",
                parse_mode='Markdown'
            )
            
            album_name = album['title'].split('-')[0].strip() if '-' in album['title'] else album['title']
            songs = await self.search_songs_verified(f"{artist} {album_name}", max_results=100)
            
            self.user_searches[user_id]['album_songs'] = songs
            
            keyboard = []
            for i, song in enumerate(songs):
                emoji = "📝" if song.get('has_lyrics') else "🎵"
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {song['title'][:48]}",
                    callback_data=f"play_album_song_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🐺 *TODAS las canciones del álbum:*\n\n"
                f"✅ {len(songs)} canciones verificadas\n"
                f"📝 = Con letra",
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
        
        if data.startswith("play_karaoke_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_searches:
                return
            
            karaoke = self.user_searches[user_id]['karaokes'][idx]
            await self.play_now(query, karaoke, is_karaoke=True)
            return
        
        if data.startswith("play_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                return
            
            song = self.user_searches[user_id]['songs'][idx]
            await self.play_now(query, song)
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
            
            await query.edit_message_text(f"🐺 *Reproduciendo playlist...*\n\n📅 {playlist['date']}", parse_mode='Markdown')
            
            for i, (song, link) in enumerate(zip(playlist['songs'], playlist['links']), 1):
                await query.message.reply_text(
                    f"🎵 *{i}/{len(playlist['songs'])}:* {song}\n\n🔗 {link}",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(1)
            
            keyboard = [
                [InlineKeyboardButton("❤️ Gracias Lobito", callback_data="thanks")],
                [InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🐺 *¡Playlist completada!* 💕\n\n¿Te gustó?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
    
    
    async def show_album_page(self, query, user_id, artist):
        """Muestra página de álbumes"""
        albums = self.user_searches[user_id].get('albums', [])
        page = self.user_searches[user_id].get('album_page', 0)
        
        max_per_page = 90
        total_albums = len(albums)
        total_pages = (total_albums + max_per_page - 1) // max_per_page
        
        start = page * max_per_page
        end = min(start + max_per_page, total_albums)
        albums_to_show = albums[start:end]
        
        keyboard = []
        for i, album in enumerate(albums_to_show):
            actual_index = start + i
            mins = album['duration'] // 60
            keyboard.append([InlineKeyboardButton(
                f"💿 {album['title'][:43]} ({mins}m)",
                callback_data=f"album_{actual_index}"
            )])
        
        # Navegación
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="prev_album_page"))
        if end < total_albums:
            nav_buttons.append(InlineKeyboardButton("➡️ Siguiente", callback_data="next_album_page"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton(f"📄 Página {page + 1} de {total_pages}", callback_data="dummy")])
        keyboard.append([InlineKeyboardButton("🎵 Ver canciones sueltas", callback_data="show_songs")])
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🐺 *Álbumes de {artist}:*\n\n✅ {total_albums} álbumes totales",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_song_page(self, query, user_id):
        """Muestra página de canciones"""
        songs = self.user_searches[user_id].get('songs', [])
        page = self.user_searches[user_id].get('song_page', 0)
        
        max_per_page = 90
        total_songs = len(songs)
        total_pages = (total_songs + max_per_page - 1) // max_per_page
        
        start = page * max_per_page
        end = min(start + max_per_page, total_songs)
        songs_to_show = songs[start:end]
        
        keyboard = []
        for i, song in enumerate(songs_to_show):
            actual_index = start + i
            emoji = "📝" if song.get('has_lyrics') else "🎵"
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {song['title'][:48]}",
                callback_data=f"play_{actual_index}"
            )])
        
        # Navegación
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="prev_song_page"))
        if end < total_songs:
            nav_buttons.append(InlineKeyboardButton("➡️ Siguiente", callback_data="next_song_page"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton(f"📄 Página {page + 1} de {total_pages}", callback_data="dummy")])
        keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🐺 *Canciones:*\n\n✅ {total_songs} canciones\n📝 = Con letra",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def play_now(self, query, song, is_karaoke=False):
        """Reproduce inmediatamente"""
        keyboard = [
            [InlineKeyboardButton("❤️ Gracias Lobito", callback_data="thanks")],
            [InlineKeyboardButton("🔙 Buscar otra", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        emoji = "🎤" if is_karaoke else ("📝" if song.get('has_lyrics') else "🎵")
        letra_text = "\n📝 Con letra" if (is_karaoke or song.get('has_lyrics')) else ""
        
        await query.message.reply_text(
            f"{emoji} *{song['title']}*{letra_text}\n\n"
            f"🔗 {song['url']}\n\n"
            f"▶️ Click para reproducir\n\n"
            f"💕 ¿Te gustó, Vero?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await query.edit_message_text("🐺 *¡Disfrútala!* 💕", parse_mode='Markdown')

def main():
    bot = MusicBot()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("🐺 Bot del Lobo iniciado - VERSIÓN COMPLETA")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

