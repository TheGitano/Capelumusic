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

# Logo del lobo en ASCII
LOGO = """
🐺═══════════════════════════🐺
     BOT MUSICAL VERONICA
     Tu asistente de música
🐺═══════════════════════════🐺
"""


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
        self.user_playlists = {}
        self.rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
        self.download_folder = 'downloads'
        os.makedirs(self.download_folder, exist_ok=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menú principal"""
        user_name = update.effective_user.first_name
        
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar Canciones", callback_data="menu_search_songs")],
            [InlineKeyboardButton("🎤 Buscar Karaokes", callback_data="menu_search_karaoke")],
            [InlineKeyboardButton("💿 Buscar Discografías", callback_data="menu_search_discography")],
            [InlineKeyboardButton("📀 Buscar Álbumes", callback_data="menu_search_albums")],
            [InlineKeyboardButton("📝 Crear Playlist", callback_data="menu_create_playlist")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="menu_help")]
        ]
        
        await update.message.reply_text(
            f"{LOGO}\n"
            f"*¡Hola {user_name}!* 🎵\n\n"
            "¿Qué deseas hacer?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_main_menu(self, query):
        """Muestra el menú principal"""
        keyboard = [
            [InlineKeyboardButton("🎵 Buscar Canciones", callback_data="menu_search_songs")],
            [InlineKeyboardButton("🎤 Buscar Karaokes", callback_data="menu_search_karaoke")],
            [InlineKeyboardButton("💿 Buscar Discografías", callback_data="menu_search_discography")],
            [InlineKeyboardButton("📀 Buscar Álbumes", callback_data="menu_search_albums")],
            [InlineKeyboardButton("📝 Crear Playlist", callback_data="menu_create_playlist")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="menu_help")]
        ]
        
        await query.edit_message_text(
            f"{LOGO}\n"
            "*¿Qué deseas hacer?*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")]]
        
        await update.message.reply_text(
            "🐺 *GUÍA DE USO*\n\n"
            "*🎵 Buscar Canciones:*\n"
            "Busca por nombre de canción o artista. Muestra TODOS los resultados disponibles.\n\n"
            "*🎤 Buscar Karaokes:*\n"
            "Busca versiones karaoke de canciones o artistas.\n\n"
            "*💿 Buscar Discografías:*\n"
            "Busca toda la discografía completa de un artista o grupo.\n\n"
            "*📀 Buscar Álbumes:*\n"
            "Busca álbumes completos específicos de cualquier artista.\n\n"
            "*📝 Crear Playlist:*\n"
            "Crea tu propia lista de reproducción personalizada.\n\n"
            "*Límites:*\n"
            "• Máximo 20 búsquedas por minuto\n\n"
            "*Ejemplos:*\n"
            "• `Bad Bunny`\n"
            "• `Monaco Bad Bunny`\n"
            "• `The Weeknd Blinding Lights`\n"
            "• `Metallica discography`\n"
            "• `Pink Floyd The Wall album`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    def format_duration(self, duration):
        """Formatea la duración de forma segura"""
        try:
            if duration is None or duration == 0:
                return ""
            duration = int(float(duration))
            minutes = duration // 60
            seconds = duration % 60
            return f" ({minutes}:{seconds:02d})"
        except (ValueError, TypeError):
            return ""
    
    async def search_music(self, query: str, max_results=100, karaoke=False):
        """Busca música en YouTube - TODOS LOS RESULTADOS"""
        search_query = f"{query} karaoke" if karaoke else query
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': f'ytsearch{max_results}',
            'socket_timeout': 30,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            'no_check_certificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Buscando: {search_query} (max: {max_results})")
                results = ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False)
                entries = results.get('entries', []) if results else []
                logger.info(f"Encontrados: {len(entries)} resultados")
                return entries
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def search_discography(self, artist: str, max_results=200):
        """Busca discografía completa de un artista"""
        search_queries = [
            f"{artist} discography full",
            f"{artist} all albums",
            f"{artist} complete discography",
            f"{artist} full album",
            f"{artist} álbum completo"
        ]
        
        all_results = []
        seen_ids = set()
        
        for search_query in search_queries:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{max_results // len(search_queries)}',
                'socket_timeout': 30,
                'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
                'no_check_certificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Buscando discografía: {search_query}")
                    results = ydl.extract_info(f"ytsearch{max_results // len(search_queries)}:{search_query}", download=False)
                    entries = results.get('entries', []) if results else []
                    
                    # Filtrar duplicados y videos muy cortos (menos de 10 minutos probablemente no sean álbumes)
                    for entry in entries:
                        video_id = entry.get('id')
                        duration = entry.get('duration', 0)
                        
                        if video_id and video_id not in seen_ids and duration >= 600:  # Mínimo 10 minutos
                            seen_ids.add(video_id)
                            all_results.append(entry)
                    
                    await asyncio.sleep(1)  # Pequeña pausa entre búsquedas
            except Exception as e:
                logger.error(f"Error en búsqueda de discografía: {e}")
                continue
        
        logger.info(f"Total discografía encontrada: {len(all_results)} álbumes/compilaciones")
        return all_results
    
    async def search_albums(self, query: str, max_results=200):
        """Busca álbumes completos"""
        search_queries = [
            f"{query} full album",
            f"{query} álbum completo",
            f"{query} complete album",
            f"{query} disco completo"
        ]
        
        all_results = []
        seen_ids = set()
        
        for search_query in search_queries:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{max_results // len(search_queries)}',
                'socket_timeout': 30,
                'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
                'no_check_certificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Buscando álbumes: {search_query}")
                    results = ydl.extract_info(f"ytsearch{max_results // len(search_queries)}:{search_query}", download=False)
                    entries = results.get('entries', []) if results else []
                    
                    # Filtrar duplicados y videos muy cortos
                    for entry in entries:
                        video_id = entry.get('id')
                        duration = entry.get('duration', 0)
                        
                        if video_id and video_id not in seen_ids and duration >= 600:  # Mínimo 10 minutos
                            seen_ids.add(video_id)
                            all_results.append(entry)
                    
                    await asyncio.sleep(1)  # Pequeña pausa entre búsquedas
            except Exception as e:
                logger.error(f"Error en búsqueda de álbumes: {e}")
                continue
        
        logger.info(f"Total álbumes encontrados: {len(all_results)}")
        return all_results
    
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
    
    def create_results_keyboard(self, results, page=0, results_per_page=10, search_type="normal"):
        """Crea teclado con paginación para resultados"""
        start_idx = page * results_per_page
        end_idx = start_idx + results_per_page
        page_results = results[start_idx:end_idx]
        
        keyboard = []
        
        for i, result in enumerate(page_results):
            global_idx = start_idx + i
            title = result.get('title', 'Sin título')
            channel = result.get('channel', result.get('uploader', ''))
            duration = result.get('duration')
            duration_str = self.format_duration(duration)
            
            # Icono especial para discografías y álbumes
            if search_type in ["discography", "albums"]:
                icon = "💿" if search_type == "discography" else "📀"
            else:
                icon = "🎵"
            
            # Mostrar artista si está disponible
            display_text = f"{icon} {title[:35]}"
            if channel and search_type not in ["discography", "albums"]:
                display_text += f" - {channel[:15]}"
            display_text += duration_str
            
            keyboard.append([
                InlineKeyboardButton(
                    display_text,
                    callback_data=f"select_{search_type}_{global_idx}"
                )
            ])
        
        # Botones de navegación
        nav_buttons = []
        total_pages = (len(results) + results_per_page - 1) // results_per_page
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"page_{search_type}_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="page_info"))
        
        if end_idx < len(results):
            nav_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"page_{search_type}_{page+1}"))
        
        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main_menu")])
        
        return keyboard
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsquedas)"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        # Verificar si está en modo búsqueda
        user_state = self.user_searches.get(user_id, {}).get('state')
        
        if user_state == 'waiting_search':
            await self.process_search(update, context, query, karaoke=False)
        elif user_state == 'waiting_karaoke':
            await self.process_search(update, context, query, karaoke=True)
        elif user_state == 'waiting_discography':
            await self.process_discography_search(update, context, query)
        elif user_state == 'waiting_albums':
            await self.process_albums_search(update, context, query)
        elif user_state == 'waiting_playlist_song':
            await self.process_playlist_search(update, context, query)
        else:
            # Mensaje por defecto
            keyboard = [[InlineKeyboardButton("🔙 Ir al Menú", callback_data="back_to_main_menu")]]
            await update.message.reply_text(
                "🐺 Usa el menú para navegar por las opciones.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def process_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, karaoke=False):
        """Procesa búsqueda de canciones o karaokes"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(f"🐺 ¡Calma! Espera {wait_time} segundos.")
            return
        
        search_type = "karaoke" if karaoke else "songs"
        search_msg = await update.message.reply_text(
            f"🔍 Buscando {'karaokes' if karaoke else 'canciones'}: *{query}*...\n"
            "Esto puede tardar un momento...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_music(query, max_results=100, karaoke=karaoke),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text("🐺 La búsqueda tardó mucho. Intenta con un término más específico.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text("🐺 Ocurrió un error. Intenta de nuevo.")
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"🐺 No encontré {'karaokes' if karaoke else 'canciones'} con ese nombre.\n"
                "Intenta con otro término.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Guardar resultados
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': search_type,
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type=search_type)
        
        await search_msg.edit_text(
            f"🐺 *Encontré {len(results)} {'karaokes' if karaoke else 'resultados'}* para: _{query}_\n\n"
            "Selecciona una opción:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_discography_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda de discografía completa"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(f"🐺 ¡Calma! Espera {wait_time} segundos.")
            return
        
        search_msg = await update.message.reply_text(
            f"💿 Buscando discografía completa de: *{query}*...\n"
            "Esto puede tardar varios segundos...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_discography(query, max_results=200),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text("🐺 La búsqueda tardó mucho. Intenta de nuevo.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text("🐺 Ocurrió un error. Intenta de nuevo.")
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"🐺 No encontré discografías de: *{query}*\n"
                "Intenta con otro artista o grupo.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Guardar resultados
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': 'discography',
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type='discography')
        
        await search_msg.edit_text(
            f"💿 *Encontré {len(results)} álbumes/compilaciones* de: _{query}_\n\n"
            "Selecciona para ver detalles:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_albums_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda de álbumes completos"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            wait_time = self.rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(f"🐺 ¡Calma! Espera {wait_time} segundos.")
            return
        
        search_msg = await update.message.reply_text(
            f"📀 Buscando álbumes completos: *{query}*...\n"
            "Esto puede tardar varios segundos...",
            parse_mode='Markdown'
        )
        
        try:
            results = await asyncio.wait_for(
                self.search_albums(query, max_results=200),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            await search_msg.edit_text("🐺 La búsqueda tardó mucho. Intenta de nuevo.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            await search_msg.edit_text("🐺 Ocurrió un error. Intenta de nuevo.")
            return
        
        if not results:
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")]]
            await search_msg.edit_text(
                f"🐺 No encontré álbumes con: *{query}*\n"
                "Intenta con otro término de búsqueda.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Guardar resultados
        self.user_searches[user_id] = {
            'query': query,
            'results': results,
            'timestamp': datetime.now(),
            'search_type': 'albums',
            'page': 0
        }
        
        keyboard = self.create_results_keyboard(results, page=0, search_type='albums')
        
        await search_msg.edit_text(
            f"📀 *Encontré {len(results)} álbumes completos* para: _{query}_\n\n"
            "Selecciona para ver detalles:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_playlist_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Procesa búsqueda para agregar a playlist"""
        user_id = update.effective_user.id
        
        search_msg = await update.message.reply_text(f"🔍 Buscando: *{query}*...", parse_mode='Markdown')
        
        try:
            results = await asyncio.wait_for(
                self.search_music(query, max_results=20),
                timeout=30.0
            )
        except Exception as e:
            await search_msg.edit_text("🐺 Error en búsqueda. Intenta de nuevo.")
            return
        
        if not results:
            await search_msg.edit_text("🐺 No encontré resultados. Intenta otro término.")
            return
        
        self.user_searches[user_id]['results'] = results
        self.user_searches[user_id]['search_type'] = 'playlist'
        
        keyboard = self.create_results_keyboard(results, page=0, results_per_page=10, search_type="playlist")
        
        await search_msg.edit_text(
            f"🐺 Resultados para: _{query}_\n\n"
            "Selecciona una canción para agregar:",
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
            logger.error(f"Error en callback: {e}")
        
        data = query.data
        
        # Menú principal
        if data == "back_to_main_menu":
            if user_id in self.user_searches:
                self.user_searches[user_id] = {}
            await self.show_main_menu(query)
            return
        
        # Menú: Buscar canciones
        if data == "menu_search_songs":
            self.user_searches[user_id] = {'state': 'waiting_search'}
            await query.edit_message_text(
                "🐺 *BUSCAR CANCIONES* 🎵\n\n"
                "Escribe el nombre de la canción o artista que quieres buscar.\n\n"
                "Ejemplo: `Bad Bunny` o `Monaco Bad Bunny`",
                parse_mode='Markdown'
            )
            return
        
        # Menú: Buscar karaokes
        if data == "menu_search_karaoke":
            self.user_searches[user_id] = {'state': 'waiting_karaoke'}
            await query.edit_message_text(
                "🐺 *BUSCAR KARAOKES* 🎤\n\n"
                "Escribe el nombre de la canción o artista para buscar karaokes.\n\n"
                "Ejemplo: `The Weeknd Blinding Lights`",
                parse_mode='Markdown'
            )
            return
        
        # Menú: Buscar discografías
        if data == "menu_search_discography":
            self.user_searches[user_id] = {'state': 'waiting_discography'}
            await query.edit_message_text(
                "🐺 *BUSCAR DISCOGRAFÍAS* 💿\n\n"
                "Escribe el nombre del artista o grupo para buscar su discografía completa.\n\n"
                "Ejemplo: `Metallica`, `Pink Floyd`, `Bad Bunny`\n\n"
                "_Se buscarán todos los álbumes, compilaciones y ediciones disponibles._",
                parse_mode='Markdown'
            )
            return
        
        # Menú: Buscar álbumes
        if data == "menu_search_albums":
            self.user_searches[user_id] = {'state': 'waiting_albums'}
            await query.edit_message_text(
                "🐺 *BUSCAR ÁLBUMES* 📀\n\n"
                "Escribe el nombre del álbum o artista para buscar álbumes completos.\n\n"
                "Ejemplo: `The Wall Pink Floyd`, `Thriller`, `Un Verano Sin Ti`\n\n"
                "_Se buscarán álbumes completos de cualquier artista._",
                parse_mode='Markdown'
            )
            return
        
        # Menú: Crear playlist
        if data == "menu_create_playlist":
            if user_id not in self.user_playlists:
                self.user_playlists[user_id] = []
            
            self.user_searches[user_id] = {'state': 'waiting_playlist_song'}
            
            playlist_text = "🐺 *CREAR PLAYLIST* 📝\n\n"
            if self.user_playlists[user_id]:
                playlist_text += "*Tu playlist actual:*\n"
                for i, song in enumerate(self.user_playlists[user_id], 1):
                    playlist_text += f"{i}. {song['title']} - {song['artist']}\n"
                playlist_text += "\n"
            
            playlist_text += "Escribe el nombre de una canción para agregar a tu playlist."
            
            keyboard = []
            if self.user_playlists[user_id]:
                keyboard.append([InlineKeyboardButton("✅ Finalizar Playlist", callback_data="playlist_finish")])
                keyboard.append([InlineKeyboardButton("🗑️ Borrar Playlist", callback_data="playlist_clear")])
            keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")])
            
            await query.edit_message_text(
                playlist_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Menú: Ayuda
        if data == "menu_help":
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main_menu")]]
            await query.edit_message_text(
                "🐺 *GUÍA DE USO*\n\n"
                "*🎵 Buscar Canciones:*\n"
                "Busca por nombre o artista. Muestra TODOS los resultados.\n\n"
                "*🎤 Buscar Karaokes:*\n"
                "Busca versiones karaoke.\n\n"
                "*💿 Buscar Discografías:*\n"
                "Busca TODA la discografía de un artista o grupo.\n\n"
                "*📀 Buscar Álbumes:*\n"
                "Busca álbumes completos específicos.\n\n"
                "*📝 Crear Playlist:*\n"
                "Crea tu lista personalizada.\n\n"
                "*Límites:* 20 búsquedas/minuto",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Paginación
        if data.startswith("page_") and data != "page_info":
            parts = data.split("_")
            search_type = parts[1]
            page = int(parts[2])
            
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            
            keyboard = self.create_results_keyboard(results, page=page, search_type=search_type)
            
            await query.edit_message_text(
                f"🐺 *Resultados* (página {page+1}):\n\nSelecciona una opción:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Selección de canción
        if data.startswith("select_"):
            parts = data.split("_")
            search_type = parts[1]
            idx = int(parts[2])
            
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            
            if datetime.now() - user_data['timestamp'] > timedelta(minutes=15):
                del self.user_searches[user_id]
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            selected = user_data['results'][idx]
            video_id = selected.get('id')
            title = selected.get('title', 'Audio')
            artist = selected.get('channel', selected.get('uploader', 'Desconocido'))
            url = f"https://www.youtube.com/watch?v={video_id}"
            duration = selected.get('duration', 0)
            
            self.user_searches[user_id]['selected'] = {
                'url': url,
                'title': title,
                'artist': artist,
                'id': video_id
            }
            
            # Si es para playlist
            if search_type == "playlist":
                self.user_playlists[user_id].append({
                    'title': title,
                    'artist': artist,
                    'url': url
                })
                
                keyboard = [
                    [InlineKeyboardButton("➕ Agregar otra canción", callback_data="menu_create_playlist")],
                    [InlineKeyboardButton("✅ Finalizar Playlist", callback_data="playlist_finish")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="back_to_main_menu")]
                ]
                
                await query.edit_message_text(
                    f"✅ *Agregado a tu playlist:*\n\n"
                    f"🎵 {title}\n"
                    f"👤 {artist}\n\n"
                    f"*Total en playlist:* {len(self.user_playlists[user_id])} canciones",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            
            # Mostrar info según tipo
            duration_str = self.format_duration(duration)
            icon = "💿" if search_type == "discography" else "📀" if search_type == "albums" else "🎵"
            
            # Opciones
            keyboard = [
                [InlineKeyboardButton("🔗 Ver enlace", callback_data=f"link_{idx}")],
                [InlineKeyboardButton("⬇️ Descargar MP3", callback_data=f"download_{idx}")],
                [InlineKeyboardButton("🔙 Volver a resultados", callback_data="back_to_results")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_main_menu")]
            ]
            
            await query.edit_message_text(
                f"🐺{icon} *{title}*\n"
                f"👤 {artist}\n"
                f"⏱️ Duración: {duration_str}\n\n"
                "¿Qué quieres hacer?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Enviar enlace
        if data.startswith("link_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await query.message.reply_text(
                f"🐺🎵 *{selected['title']}*\n"
                f"👤 {selected['artist']}\n\n"
                f"🔗 {selected['url']}\n\n"
                "¡Disfruta! 💕",
                parse_mode='Markdown'
            )
            await query.edit_message_text("🐺 ¡Enlace enviado! 🎵")
            return
        
        # Descargar audio
        if data.startswith("download_"):
            if user_id not in self.user_searches or 'selected' not in self.user_searches[user_id]:
                await query.edit_message_text("🐺 Error.")
                return
            
            selected = self.user_searches[user_id]['selected']
            await query.edit_message_text("🐺 ⬇️ Descargando audio...")
            
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
                    await query.message.reply_text("🐺 ¡Audio enviado! 🎵")
                    
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    await query.message.reply_text(
                        f"🐺 No pude descargar. Enlace:\n\n🔗 {selected['url']}"
                    )
            except Exception as e:
                logger.error(f"Error descarga: {e}")
                await query.message.reply_text(
                    f"🐺 Error al descargar:\n\n🔗 {selected['url']}"
                )
            return
        
        # Volver a resultados
        if data == "back_to_results":
            if user_id not in self.user_searches:
                await query.edit_message_text("🐺 Búsqueda expirada.")
                return
            
            user_data = self.user_searches[user_id]
            results = user_data['results']
            search_type = user_data.get('search_type', 'songs')
            page = user_data.get('page', 0)
            
            keyboard = self.create_results_keyboard(results, page=page, search_type=search_type)
            
            await query.edit_message_text(
                f"🐺 *Resultados:* {user_data['query']}\n\nSelecciona:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Finalizar playlist
        if data == "playlist_finish":
            if user_id not in self.user_playlists or not self.user_playlists[user_id]:
                await query.edit_message_text("🐺 Tu playlist está vacía.")
                return
            
            playlist_text = "🐺 *TU PLAYLIST ESTÁ LISTA* 📝✅\n\n"
            for i, song in enumerate(self.user_playlists[user_id], 1):
                playlist_text += f"{i}. 🎵 {song['title']}\n   👤 {song['artist']}\n   🔗 {song['url']}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🗑️ Borrar Playlist", callback_data="playlist_clear")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="back_to_main_menu")]
            ]
            
            await query.edit_message_text(
                playlist_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Borrar playlist
        if data == "playlist_clear":
            if user_id in self.user_playlists:
                self.user_playlists[user_id] = []
            
            keyboard = [[InlineKeyboardButton("🔙 Menú Principal", callback_data="back_to_main_menu")]]
            await query.edit_message_text(
                "🐺 Playlist borrada correctamente.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores globales"""
        logger.error(f"Error: {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🐺 Ocurrió un error. Intenta de nuevo."
                )
        except:
            pass


def main():
    """Función principal"""
    logger.info("🐺 Iniciando bot musical...")
    
    bot = MusicBot()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    app.add_error_handler(bot.error_handler)
    
    logger.info("🐺 Bot iniciado correctamente")
    logger.info("🐺 Presiona Ctrl+C para detener")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
