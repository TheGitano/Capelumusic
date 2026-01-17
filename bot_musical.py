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
            "🎤 ¡Modo KARAOKE para cantar!\n"
            "🌍 Versiones en español e idioma original\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ *Elige qué quieres hacer:*"
        )
        
        # Menú principal con botones
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
            [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
            [InlineKeyboardButton("ℹ️ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def search_music(self, query: str, max_results=5):
        """Busca música en YouTube"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': f'ytsearch{max_results}',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                if 'entries' in results:
                    return results['entries'][:max_results]
                return []
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def check_video_availability(self, video_id):
        """Verifica si un video se puede descargar"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration', 0)
                if duration < 60:
                    return False
                return True
        except Exception as e:
            logger.error(f"Video no disponible {video_id}: {e}")
            return False
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto y voz (búsquedas)"""
        user_id = update.effective_user.id
        
        # Verificar si hay un modo activo
        if user_id not in self.user_searches or 'mode' not in self.user_searches[user_id]:
            keyboard = [
                [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🐺 *Primero elige qué quieres hacer:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        mode = self.user_searches[user_id]['mode']
        query = update.message.text
        
        # Añadir "karaoke" a la búsqueda si está en modo karaoke
        search_query = f"{query} karaoke" if mode == 'karaoke' else query
        
        await update.message.reply_text(
            f"🐺 *Tu Lobo está rastreando...*\n"
            f"🔍 Buscando: *{query}*\n"
            f"{'🎤 Modo: KARAOKE' if mode == 'karaoke' else ''}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
        
        # Buscar versión original
        results = await self.search_music(search_query)
        
        # Buscar versión en español
        spanish_results = await self.search_music(f"{query} español spanish") if mode == 'music' else []
        
        if not results and not spanish_results:
            await update.message.reply_text(
                "🐺 *¡Woof!*\n\n"
                "😔 No encontré nada en mi territorio...\n"
                "Intenta con otro término de búsqueda.\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        # Guardar resultados para este usuario
        self.user_searches[user_id]['query'] = query
        self.user_searches[user_id]['results'] = results
        self.user_searches[user_id]['spanish_results'] = spanish_results
        
        # Mostrar opciones
        keyboard = []
        
        if mode == 'music' and spanish_results:
            keyboard.append([InlineKeyboardButton(
                "🌍 Ver versiones (Original y Español)", 
                callback_data="show_versions"
            )])
        
        # Mostrar resultados principales
        emojis = ["🎵", "🎸", "🎹", "🎺", "🎻"]
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Sin título')
            emoji = "🎤" if mode == 'karaoke' else emojis[i]
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {title[:55]}", 
                callback_data=f"select_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Volver al menú", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            f"🐺 *¡Tu Lobo encontró {'karaokes' if mode == 'karaoke' else 'canciones'}!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        if mode == 'music' and spanish_results:
            message_text += "💡 *Vero, encontré versiones en español e idioma original*\n\n"
        
        message_text += "Selecciona la que quieras:"
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los botones presionados"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "back_to_menu":
            # Limpiar datos del usuario
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            
            wolf_logo = """
        ╔══════════════════════════════════════╗
        ║            🐺  TU LOBO  🐺           ║
        ╚══════════════════════════════════════╝
            """
            keyboard = [
                [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"{wolf_logo}\n\n🎵 *¿Qué quieres hacer, Vero?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_music":
            self.user_searches[user_id] = {'mode': 'music'}
            await query.edit_message_text(
                "🐺 *Modo: Búsqueda de Canciones*\n\n"
                "🎵 Escribe el nombre de una canción, artista\n"
                "o canta una estrofa para buscar.\n\n"
                "💡 Buscaré versiones en español e idioma original\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        if data == "mode_karaoke":
            self.user_searches[user_id] = {'mode': 'karaoke'}
            await query.edit_message_text(
                "🐺 *Modo: Búsqueda de KARAOKES* 🎤\n\n"
                "🎵 Escribe el nombre de la canción\n"
                "que quieres cantar.\n\n"
                "💡 Puedes escribir o enviar nota de voz\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        if data == "help":
            await query.edit_message_text(
                "🐺 *Ayuda - Tu Lobo Asistente*\n\n"
                "🎵 *Modo Canciones:*\n"
                "Busca música normal, álbumes y playlists\n\n"
                "🎤 *Modo Karaoke:*\n"
                "Busca versiones karaoke para cantar\n\n"
                "✨ *Funciones:*\n"
                "• Versiones en español e idioma original\n"
                "• Con o sin letra en pantalla\n"
                "• Video o solo audio\n"
                "• Álbumes completos\n"
                "• Playlists personalizadas\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        
        if data == "show_versions":
            if user_id not in self.user_searches:
                return
            
            results = self.user_searches[user_id].get('results', [])
            spanish_results = self.user_searches[user_id].get('spanish_results', [])
            
            keyboard = []
            keyboard.append([InlineKeyboardButton("🌍 VERSIÓN ORIGINAL", callback_data="dummy")])
            
            for i, result in enumerate(results[:3]):
                title = result.get('title', 'Sin título')
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {title[:55]}", 
                    callback_data=f"select_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🇪🇸 VERSIÓN EN ESPAÑOL", callback_data="dummy")])
            
            for i, result in enumerate(spanish_results[:3]):
                title = result.get('title', 'Sin título')
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {title[:55]}", 
                    callback_data=f"select_spanish_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_search")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🐺 *Vero, aquí están las versiones:*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Elige la que prefieras:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("select_spanish_"):
            idx = int(data.split("_")[2])
            if user_id not in self.user_searches:
                return
            
            selected = self.user_searches[user_id]['spanish_results'][idx]
            self.user_searches[user_id]['selected'] = selected
            self.user_searches[user_id]['is_spanish'] = True
            
            mode = self.user_searches[user_id].get('mode', 'music')
            
            if mode == 'karaoke':
                # Ir directo a preguntar con/sin letra
                keyboard = [
                    [InlineKeyboardButton("📝 Con letra", callback_data="lyrics_yes")],
                    [InlineKeyboardButton("🎵 Sin letra", callback_data="lyrics_no")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🐺 *¡Perfecto para cantar!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎤 {selected.get('title', 'Sin título')}\n\n"
                    f"*Vero, ¿te gustaría que el video tenga la letra?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Mostrar opciones normales
                keyboard = [
                    [InlineKeyboardButton("🎵 Solo este tema", callback_data="play_single")],
                    [InlineKeyboardButton("💿 Álbum completo", callback_data="play_album")],
                    [InlineKeyboardButton("⭐ Playlist mejores temas", callback_data="play_best")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🐺 *¡Excelente elección!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎵 {selected.get('title', 'Sin título')}\n"
                    f"🇪🇸 *Versión en Español*\n\n"
                    f"*¿Cómo quieres disfrutarla?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            return
        
        if data.startswith("select_"):
            idx = int(data.split("_")[1])
            if user_id not in self.user_searches:
                return
            
            selected = self.user_searches[user_id]['results'][idx]
            self.user_searches[user_id]['selected'] = selected
            
            mode = self.user_searches[user_id].get('mode', 'music')
            
            if mode == 'karaoke':
                # Preguntar si quiere con o sin letra
                keyboard = [
                    [InlineKeyboardButton("📝 Con letra", callback_data="lyrics_yes")],
                    [InlineKeyboardButton("🎵 Sin letra", callback_data="lyrics_no")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🐺 *¡Perfecto para cantar!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎤 {selected.get('title', 'Sin título')}\n\n"
                    f"*Vero, ¿te gustaría que el video tenga la letra?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Mostrar opciones de reproducción
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
        
        if data in ["lyrics_yes", "lyrics_no"]:
            with_lyrics = data == "lyrics_yes"
            self.user_searches[user_id]['with_lyrics'] = with_lyrics
            
            # Preguntar formato
            keyboard = [
                [InlineKeyboardButton("🎥 Video", callback_data="format_video_karaoke")],
                [InlineKeyboardButton("🎧 Solo audio", callback_data="format_audio_karaoke")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🐺 *Karaoke {'con' if with_lyrics else 'sin'} letra*\n\n"
                f"*¿Cómo lo prefieres?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data in ["play_single", "play_album", "play_best"]:
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                return
            
            self.user_searches[user_id]['play_mode'] = data
            
            # Preguntar si quiere con letra
            keyboard = [
                [InlineKeyboardButton("📝 Con letra en pantalla", callback_data="lyrics_video_yes")],
                [InlineKeyboardButton("🎵 Sin letra", callback_data="lyrics_video_no")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            mode_text = {
                "play_single": "este tema",
                "play_album": "el álbum completo",
                "play_best": "playlist de mejores temas"
            }
            
            await query.edit_message_text(
                f"🐺 *Reproduciendo: {mode_text[data]}*\n\n"
                f"*Vero, ¿te gustaría que tenga la letra en pantalla?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data in ["lyrics_video_yes", "lyrics_video_no"]:
            with_lyrics = data == "lyrics_video_yes"
            self.user_searches[user_id]['with_lyrics'] = with_lyrics
            play_mode = self.user_searches[user_id].get('play_mode', 'play_single')
            
            # Preguntar formato
            keyboard = [
                [InlineKeyboardButton("🎥 Con video", callback_data=f"format_video_{play_mode}")],
                [InlineKeyboardButton("🎧 Solo audio", callback_data=f"format_audio_{play_mode}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🐺 *{'Con' if with_lyrics else 'Sin'} letra en pantalla*\n\n"
                f"*¿Cómo lo prefieres?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        if data.startswith("format_"):
            parts = data.split("_")
            format_type = parts[1]  # video o audio
            play_mode = "_".join(parts[2:])  # play_single, play_album, karaoke, etc
            
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                return
            
            selected = self.user_searches[user_id]['selected']
            with_lyrics = self.user_searches[user_id].get('with_lyrics', False)
            
            # Si pidió con letra, agregar "lyrics" a la búsqueda
            if with_lyrics and format_type == "video":
                # Re-buscar con lyrics
                query_text = self.user_searches[user_id].get('query', '')
                lyrics_results = await self.search_music(f"{query_text} lyrics video")
                if lyrics_results:
                    selected = lyrics_results[0]
                    self.user_searches[user_id]['selected'] = selected
            
            await self.play_music(query, selected, format_type, play_mode, user_id)
    
    async def play_music(self, query, selected, format_type, play_mode, user_id):
        """Reproduce la música seleccionada"""
        await query.edit_message_text(
            "🐺 *Tu Lobo está preparando tu música...*\n"
            "⏳ Un momento por favor...\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            if play_mode in ["play_single", "karaoke"]:
                await self.download_and_send(query, selected, format_type)
            
            elif play_mode == "play_album":
                artist = selected.get('channel', '') or selected.get('uploader', '')
                title = selected.get('title', '')
                
                await query.edit_message_text(
                    f"🐺 *Buscando el álbum completo...*\n"
                    f"🔍 Rastreando videos relacionados\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                album_query = f"{artist} {title} full album"
                album_results = await self.search_music(album_query, max_results=10)
                
                if not album_results:
                    await query.message.reply_text(
                        "🐺 *No encontré un álbum completo*\n"
                        "Reproduciendo la canción que seleccionaste...\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    await self.download_and_send(query, selected, format_type)
                else:
                    await query.message.reply_text(
                        "🐺 *Verificando disponibilidad...*\n"
                        "Esto puede tardar un momento\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    
                    available_videos = []
                    for video in album_results:
                        video_id = video.get('id')
                        if video_id and await self.check_video_availability(video_id):
                            available_videos.append(video)
                    
                    if not available_videos:
                        await query.message.reply_text(
                            "🐺 *Los videos del álbum no están disponibles*\n"
                            "Reproduciendo la canción original...\n"
                            "━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        await self.download_and_send(query, selected, format_type)
                    else:
                        await query.message.reply_text(
                            f"🐺 *¡Encontré {len(available_videos)} videos del álbum!*\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"Creando tu playlist exclusiva...\n"
                            f"🎵 Enviando canciones una por una"
                        )
                        
                        for i, video in enumerate(available_videos[:5], 1):
                            await query.message.reply_text(
                                f"🎵 *Canción {i} de {min(len(available_videos), 5)}*\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            await self.download_and_send(query, video, format_type, is_playlist=True)
                            await asyncio.sleep(2)
            
            elif play_mode == "play_best":
                artist_query = selected.get('channel', '') or selected.get('uploader', '')
                await query.edit_message_text(
                    f"🐺 *Buscando los mejores temas...*\n"
                    f"⭐ {artist_query}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                best_results = await self.search_music(f"{artist_query} best hits greatest", max_results=10)
                
                if best_results:
                    available_videos = []
                    for video in best_results:
                        video_id = video.get('id')
                        if video_id and await self.check_video_availability(video_id):
                            available_videos.append(video)
                    
                    if available_videos:
                        await query.message.reply_text(
                            f"🐺 *¡Encontré {len(available_videos)} grandes éxitos!*\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"Preparando tu playlist..."
                        )
                        
                        for i, video in enumerate(available_videos[:5], 1):
                            await query.message.reply_text(
                                f"⭐ *Hit {i} de {min(len(available_videos), 5)}*\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            await self.download_and_send(query, video, format_type, is_playlist=True)
                            await asyncio.sleep(2)
                    else:
                        await self.download_and_send(query, best_results[0], format_type)
                else:
                    await self.download_and_send(query, selected, format_type)
            
            # Volver al menú
            keyboard = [[InlineKeyboardButton("🔙 Volver al menú principal", callback_data="back_to_menu")]]
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
            await query.message.reply_text(
                f"🐺 *¡Auch!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ Hubo un problema: {str(e)}\n\n"
                f"Intenta con otra búsqueda."
            )
    
    async def download_and_send(self, query, video_info, format_type, is_playlist=False):
        """Descarga y envía el archivo"""
        video_id = video_info.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        if format_type == "video":
            ydl_opts = {
                'format': 'best[ext=mp4][height<=480]/best',
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
            os.makedirs('downloads', exist_ok=True)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if format_type == "audio":
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
            
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
            
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            if not is_playlist:
                await query.message.reply_text(
                    f"🐺 *{video_info.get('title', 'Sin título')}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 Link: {url}\n\n"
                    f"(No pude descargar este archivo,\npero puedes usar el link)",
                    parse_mode='Markdown'
                )

def main():
    """Inicia el bot"""
    bot = MusicBot()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("🐺 Bot del Lobo iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
