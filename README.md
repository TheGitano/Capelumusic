# 🐺 Bot Musical Veronica - Versión 2.1 (UX Mejorada)

Bot de Telegram para búsqueda y descarga de música con interfaz hermosa, funcionalidades avanzadas y experiencia de usuario optimizada.

## ✨ Características Principales

- 🎵 **Búsqueda Ilimitada de Canciones** - Sin restricciones
- 🎤 **Karaokes del Mundo** - Versiones instrumentales
- 💿 **Discografías Completas** - Toda la obra de artistas
- 📀 **Álbumes Completos** - De cualquier artista del mundo
- 📝 **Playlists Personalizadas** - Crea tus propias listas
- ⬇️ **Descargas MP3 HD** - Calidad 192kbps
- 🔗 **Enlaces Directos** - Acceso rápido a YouTube

## 🚀 Despliegue en Railway

### Paso 1: Preparar GitHub

1. Ve a tu repositorio en GitHub
2. Asegúrate de tener estos archivos:
   - `bot_musical.py`
   - `requirements.txt`
   - `Dockerfile`
   - `Procfile`

### Paso 2: Actualizar Archivos

Reemplaza TODOS los archivos con las nuevas versiones:

```bash
# Copia los nuevos archivos a tu repositorio local
# Luego haz commit y push

git add .
git commit -m "✨ Update: Versión 2.0 con menú mejorado y nuevas funciones"
git push origin main
```

### Paso 3: Railway Deploy

Railway detectará automáticamente los cambios y hará el deploy.

Si necesitas hacer deploy manual:
1. Ve a tu proyecto en Railway
2. Click en "Deploy" o espera el auto-deploy
3. Verifica los logs

### Paso 4: Configurar Variable de Entorno

En Railway, asegúrate de tener configurada:
- `TELEGRAM_BOT_TOKEN` = tu_token_de_botfather

## 📱 Uso del Bot

### Comandos Disponibles

- `/start` - Menú principal con todas las opciones
- `/help` - Guía completa de uso

### Funciones del Menú

#### 🎵 Buscar Canciones
- Escribe el nombre de la canción o artista
- Resultados ilimitados
- Ejemplo: `Bad Bunny`, `Tusa`

#### 🎤 Buscar Karaokes
- Busca versiones karaoke
- Sin límite de resultados
- Ejemplo: `Bohemian Rhapsody`

#### 💿 Buscar Discografías
- Toda la discografía de un artista
- Álbumes, compilaciones, ediciones especiales
- Ejemplo: `Metallica`, `Queen`

#### 📀 Buscar Álbumes
- Álbumes completos del mundo
- Búsqueda sin restricciones
- Ejemplo: `The Wall`, `Thriller`

#### 📝 Crear Playlist
- Crea tu lista personalizada
- Agrega canciones ilimitadas
- Guarda y comparte tus playlists

## 🎨 Diseño del Menú

El bot cuenta con:
- ✨ Interfaz hermosa y profesional
- 🎨 Separadores visuales atractivos
- 📊 Organización clara de opciones
- 🔥 Emojis llamativos
- 💫 Mensajes informativos detallados

## ⚙️ Configuración Técnica

### Límites
- **Rate Limit**: 20 búsquedas por minuto por usuario
- **Tamaño de archivo**: Máximo 50MB por descarga
- **Calidad MP3**: 192kbps
- **Timeout búsqueda**: 60 segundos para canciones, 120 segundos para discografías/álbumes

### Tecnologías
- Python 3.11
- python-telegram-bot 21.0.1
- yt-dlp (última versión)
- FFmpeg para conversión de audio

## 🐛 Solución de Problemas

### El bot no responde
1. Verifica que Railway esté corriendo
2. Revisa los logs en Railway
3. Confirma que el token sea correcto

### Error en descargas
1. Verifica que FFmpeg esté instalado (ya incluido en Dockerfile)
2. Revisa los logs para errores específicos

### Búsquedas lentas
1. Es normal para discografías (pueden tardar 30-60 segundos)
2. Álbumes también requieren tiempo de búsqueda
3. El bot muestra mensajes de "cargando"

## 📝 Notas de Versión

### Versión 2.1 (Actual) - UX Mejorada
- ✨ Botón "Abrir en YouTube" más claro y honesto
- 📥 Descarga como opción principal destacada
- 💬 Mensajes más claros sobre qué hace cada opción
- 🎨 Mejor organización de botones
- 📱 Explicaciones sobre el diálogo de confirmación de Telegram
- 🐛 Mejoras en textos de descarga y audio enviado

### Versión 2.0
- ✨ Menú completamente rediseñado
- 💿 Nueva función: Búsqueda de discografías completas
- 📀 Nueva función: Búsqueda de álbumes completos
- 🎨 Interfaz visual mejorada con separadores
- 📊 Mejor organización de resultados
- 🔥 Mensajes más informativos y atractivos
- ⚡ Optimización de búsquedas
- 🐛 Corrección de bugs menores

### Versión 1.0
- 🎵 Búsqueda básica de canciones
- 🎤 Búsqueda de karaokes
- 📝 Creación de playlists
- ⬇️ Descarga de MP3

## 👨‍💻 Desarrollo

Creado con ❤️ para amantes de la música

## 📄 Licencia

Uso personal y educativo
