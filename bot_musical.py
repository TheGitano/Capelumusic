import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio
import json

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token del bot
TOKEN = '8472230810:AAF2Nfix6WumdeAUTjwvgQYd0hiIzMgClbA'

class MusicBot:
    def __init__(self):
        self.user_searches = {}
        self.user_playlists = {}  # Guardar playlists personalizadas
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida personalizado"""
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
            "📝 Crear tu playlist personalizada\n"
            "🌍 Versiones en español e idioma original\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ *Elige qué quieres hacer:*"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
            [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
            [InlineKeyboardButton("📝 Crear mi playlist", callback_data="mode_playlist")],
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
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja notas de voz"""
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
        
        await update.message.reply_text(
            "🐺 *¡Escuché tu voz!*\n\n"
            "Por ahora, escribe el nombre de la canción que quieres.\n"
            "La función de reconocimiento de voz está en desarrollo 🎤"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        user_id = update.effective_user.id
        
        # Verificar si está en modo playlist
        if user_id in self.user_searches and self.user_searches[user_id].get('mode') == 'playlist_input':
            query = update.message.text.strip()
            
            # Agregar a la lista de canciones
            if 'playlist_songs' not in self.user_searches[user_id]:
                self.user_searches[user_id]['playlist_songs'] = []
            
            self.user_searches[user_id]['playlist_songs'].append(query)
            
            keyboard = [
                [InlineKeyboardButton("➕ Agregar otra canción", callback_data="playlist_add_more")],
                [InlineKeyboardButton("✅ Crear playlist ahora", callback_data="playlist_create")],
                [InlineKeyboardButton("🔙 Cancelar", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            songs_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(self.user_searches[user_id]['playlist_songs'])])
            
            await update.message.reply_text(
                f"🐺 *¡Agregado!*\n\n"
                f"📝 *Tu playlist hasta ahora:*\n"
                f"{songs_list}\n\n"
                f"¿Qué quieres hacer?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Verificar si hay un modo activo
        if user_id not in self.user_searches or 'mode' not in self.user_searches[user_id]:
            keyboard = [
                [InlineKeyboardButton("🎵 Buscar canciones", callback_data="mode_music")],
                [InlineKeyboardButton("🎤 Buscar karaokes", callback_data="mode_karaoke")],
                [InlineKeyboardButton("📝 Crear mi playlist", callback_data="mode_playlist")]
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
        
        # Añadir términos específicos según el modo
        if mode == 'karaoke':
            search_query = f"{query} karaoke lyrics"
        else:
            search_query = query
        
        await update.message.reply_text(
            f"🐺 *Tu Lobo está rastreando...*\n"
            f"🔍 Buscando: *{query}*\n"
            f"{'🎤 Modo: KARAOKE (con letra)' if mode == 'karaoke' else ''}\n"
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
        
        # Guardar resultados
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
                [InlineKeyboardButton("📝 Crear mi playlist", callback_data="mode_playlist")],
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
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_karaoke":
            self.user_searches[user_id] = {'mode': 'karaoke'}
            await query.edit_message_text(
                "🐺 *Modo: Búsqueda de KARAOKES* 🎤\n\n"
                "🎵 Escribe el nombre de la canción\n"
                "que quieres cantar.\n\n"
                "💡 Los karaokes siempre incluyen la letra\n"
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
            return
        
        if data == "mode_playlist":
            self.user_searches[user_id] = {'mode': 'playlist_input', 'playlist_songs': []}
            await query.edit_message_text(
                "🐺 *Crear tu Playlist Personalizada* 📝\n\n"
                "✨ *Vero, dime qué canciones o artistas quieres:*\n\n"
                "Escribe una canción o artista por mensaje.\n"
                "Ejemplo:\n"
                "- Bohemian Rhapsody\n"
                "- The Beatles\n"
                "- Hotel California\n\n"
                "Envía tu primera canción:",
                parse_mode='Markdown'
            )
            return
        
        if data == "playlist_add_more":
            await query.edit_message_text(
                "🐺 *Escribe otra canción o artista:*\n\n"
                "Tu Lobo está listo para agregarla a tu playlist 📝",
                parse_mode='Markdown'
            )
            return
        
        if data == "playlist_create":
            if user_id not in self.user_searches or 'playlist_songs' not in self.user_searches[user_id]:
                return
            
            songs = self.user_searches[user_id]['playlist_songs']
            
            await query.edit_message_text(
                f"🐺 *Creando tu playlist...*\n"
                f"📝 {len(songs)} canciones\n\n"
                f"Esto puede tardar un momento ⏳",
                parse_mode='Markdown'
            )
            
            # Buscar y enviar cada canción
            for i, song in enumerate(songs, 1):
                await query.message.reply_text(
                    f"🎵 *Buscando {i}/{len(songs)}:* {song}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━",
                    parse_mode='Markdown'
                )
                
                results = await self.search_music(song)
                if results:
                    # Enviar solo audio para playlists
                    await self.download_and_send_simple(query, results[0], "audio")
                    await asyncio.sleep(2)
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "🐺 *¡Playlist completada, Vero!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Todas tus canciones están listas\n\n"
                "Puedes reproducirlas una tras otra 🎵💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Limpiar
            if user_id in self.user_searches:
                del self.user_searches[user_id]
            return
        
        if data == "help":
            await query.edit_message_text(
                "🐺 *Ayuda - Tu Lobo Asistente*\n\n"
                "🎵 *Modo Canciones:*\n"
                "Busca música normal, álbumes y playlists\n\n"
                "🎤 *Modo Karaoke:*\n"
                "Busca karaokes con letra para cantar\n\n"
                "📝 *Crear Playlist:*\n"
                "Crea tu lista personalizada de canciones\n\n"
                "✨ *Funciones:*\n"
                "• Versiones en español e idioma original\n"
                "• Con o sin letra en pantalla\n"
                "• Video o solo audio\n"
                "• Álbumes completos\n"
                "• Playlists personalizadas\n"
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
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
                # Karaoke va directo a elegir formato (siempre con letra)
                keyboard = [
                    [InlineKeyboardButton("🎥 Video", callback_data="format_video_karaoke")],
                    [InlineKeyboardButton("🎧 Solo audio", callback_data="format_audio_karaoke")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🐺 *¡Perfecto para cantar!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎤 {selected.get('title', 'Sin título')}\n"
                    f"📝 Con letra incluida\n\n"
                    f"*¿Cómo lo prefieres?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
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
                # Karaoke: directo a elegir formato
                keyboard = [
                    [InlineKeyboardButton("🎥 Video", callback_data="format_video_karaoke")],
                    [InlineKeyboardButton("🎧 Solo audio", callback_data="format_audio_karaoke")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🐺 *¡Perfecto para cantar!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎤 {selected.get('title', 'Sin título')}\n"
                    f"📝 Con letra incluida\n\n"
                    f"*¿Cómo lo prefieres?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
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
            
            # Si pidió con letra, re-buscar con lyrics
            if with_lyrics and format_type == "video":
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
                
                await query.message.reply_text(
                    f"🐺 *Buscando el álbum completo...*\n"
                    f"🔍 Rastreando videos relacionados\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                album_query = f"{artist} {title} full album"
                album_results = await self.search_music(album_query, max_results=10)
                
                if not album_results:
                    await query.message.reply_text("🐺 Reproduciendo la canción seleccionada...")
                    await self.download_and_send(query, selected, format_type)
                else:
                    available_videos = []
                    for video in album_results:
                        video_id = video.get('id')
                        if video_id and await self.check_video_availability(video_id):
                            available_videos.append(video)
                    
                    if available_videos:
                        await query.message.reply_text(
                            f"🐺 *¡Encontré {len(available_videos)} videos del álbum!*\n"
                            f"Creando tu playlist..."
                        )
                        
                        for i, video in enumerate(available_videos[:5], 1):
                            await query.message.reply_text(f"🎵 *{i}/{min(len(available_videos), 5)}*")
                            await self.download_and_send(query, video, format_type, is_playlist=True)
                            await asyncio.sleep(2)
                    else:
                        await self.download_and_send(query, selected, format_type)
            
            elif play_mode == "play_best":
                artist_query = selected.get('channel', '') or selected.get('uploader', '')
                best_results = await self.search_music(f"{artist_query} best hits", max_results=10)
                
                if best_results:
                    available_videos = [v for v in best_results if await self.check_video_availability(v.get('id'))]
                    
                    if available_videos:
                        await query.message.reply_text(f"🐺 *¡{len(available_videos)} grandes éxitos!*")
                        for i, video in enumerate(available_videos[:5], 1):
                            await query.message.reply_text(f"⭐ *{i}/{min(len(available_videos), 5)}*")
                            await self.download_and_send(query, video, format_type, is_playlist=True)
                            await asyncio.sleep(2)
                    else:
                        await self.download_and_send(query, best_results[0], format_type)
                else:
                    await self.download_and_send(query, selected, format_type)
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al menú principal", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "🐺 *¡Listo Verónica!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Reproducción completada\n\n"
                "Tu Lobo está aquí para ti 🐺💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error en reproducción: {e}")
            await query.message.reply_text(f"🐺 ❌ Error: {str(e)}")
    
    async def download_and_send(self, query, video_info, format_type, is_playlist=False):
        """Descarga y envía el archivo - VERSIÓN MEJORADA"""
        video_id = video_info.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        title = video_info.get('title', 'Sin título')
        
        try:
            os.makedirs('downloads', exist_ok=True)
            
            if format_type == "video":
                ydl_opts = {
                    'format': 'best[height<=480][ext=mp4]/best[ext=mp4]/best',
                    'outtmpl': f'downloads/{video_id}.mp4',
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                filename = f'downloads/{video_id}.mp4'
                
                # Enviar como documento para evitar problemas
                with open(filename, 'rb') as video_file:
                    await query.message.reply_document(
                        document=video_file,
                        caption=f"🐺🎥 {title}\n━━━━━━━━━━━━━━━━━━━━━━\n¡Disfruta, Verónica! 💕",
                        filename=f"{title[:50]}.mp4"
                    )
            
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
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                filename = f'downloads/{video_id}.mp3'
                
                with open(filename, 'rb') as audio_file:
                    await query.message.reply_audio(
                        audio=audio_file,
                        caption=f"🐺🎵 {title}\n━━━━━━━━━━━━━━━━━━━━━━\n¡A disfrutar! 💕",
                        title=title,
                        performer="YouTube"
                    )
            
            # Limpiar archivo
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            if not is_playlist:
                await query.message.reply_text(
                    f"🐺 *{title}*\n"
                    f"🔗 {url}\n\n"
                    f"(Usa el link para reproducir)",
                    parse_mode='Markdown'
                )
    
    async def download_and_send_simple(self, query, video_info, format_type):
        """Versión simple para playlists"""
        video_id = video_info.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        title = video_info.get('title', 'Sin título')
        
        try:
            os.makedirs('downloads', exist_ok=True)
            
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
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            filename = f'downloads/{video_id}.mp3'
            
            with open(filename, 'rb') as audio_file:
                await query.message.reply_audio(
                    audio=audio_file,
                    caption=f"🎵 {title}",
                    title=title
                )
            
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"Error: {e}")

def main():
    """Inicia el bot"""
    bot = MusicBot()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("🐺 Bot del Lobo iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
