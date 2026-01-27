# 🚀 GUÍA RÁPIDA DE ACTUALIZACIÓN - RAILWAY

## 📋 Pasos para Actualizar tu Bot

### 1️⃣ DESCARGAR LOS ARCHIVOS

Descarga estos archivos que te he proporcionado:
- ✅ `bot_musical.py` (PRINCIPAL - con menú mejorado)
- ✅ `requirements.txt`
- ✅ `Dockerfile`
- ✅ `Procfile`
- ✅ `.gitignore`
- ✅ `README.md`

### 2️⃣ ACTUALIZAR EN GITHUB

Opción A - Usando GitHub Web:
1. Ve a tu repositorio en GitHub
2. Para cada archivo:
   - Click en el archivo existente
   - Click en el icono del lápiz (Edit)
   - Borra todo el contenido
   - Copia y pega el contenido del nuevo archivo
   - Click en "Commit changes"

Opción B - Usando Git en terminal:
```bash
# Clona tu repositorio (si no lo tienes)
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO

# Copia los nuevos archivos a la carpeta
# (reemplaza los archivos viejos)

# Sube los cambios
git add .
git commit -m "✨ Versión 2.0: Menú mejorado + Discografías + Álbumes"
git push origin main
```

### 3️⃣ RAILWAY AUTO-DEPLOY

Railway detectará automáticamente los cambios:
1. Ve a tu proyecto en Railway (https://railway.app)
2. Verás que empieza el deploy automáticamente
3. Espera a que aparezca "Success" o "Deployed"
4. Revisa los logs para confirmar: "🐺 Bot iniciado correctamente"

### 4️⃣ VERIFICAR EN TELEGRAM

1. Abre tu bot en Telegram
2. Envía `/start`
3. Deberías ver el nuevo menú con:
   - 🎵 Canciones
   - 🎤 Karaokes
   - 💿 Discografías ← **NUEVO**
   - 📀 Álbumes ← **NUEVO**
   - 📝 Crear Playlist
   - ❓ Ayuda & Guía
   - ℹ️ Info del Bot ← **NUEVO**

### 5️⃣ SOLUCIÓN DE PROBLEMAS

❌ **Si el bot no actualiza:**
1. Ve a Railway
2. Click en tu proyecto
3. Click en "Settings"
4. Baja hasta "Danger Zone"
5. Click en "Redeploy"
6. Confirma el redeploy

❌ **Si ves errores en Railway:**
1. Click en "Deployments"
2. Click en el último deploy
3. Revisa los "Logs"
4. Si ves errores de dependencias:
   - Verifica que `requirements.txt` esté correcto
   - Hace redeploy

❌ **Si el menú no cambia en Telegram:**
1. Detén el bot en Telegram (Block)
2. Vuelve a iniciarlo (Unblock)
3. Envía `/start` de nuevo

## 🎉 ¡LISTO!

Tu bot ahora tiene:
- ✨ Menú hermoso y profesional
- 💿 Búsqueda de discografías completas
- 📀 Búsqueda de álbumes completos
- 🎨 Diseño visual mejorado
- 🔥 Mensajes más atractivos

## 📞 Contacto de Soporte

Si tienes problemas:
1. Revisa los logs en Railway
2. Verifica que todos los archivos estén actualizados
3. Confirma que la variable TELEGRAM_BOT_TOKEN esté configurada

## 🔍 Comandos de Prueba

Prueba estas búsquedas para verificar:
- 🎵 Canciones: `Bad Bunny`
- 🎤 Karaokes: `Bohemian Rhapsody karaoke`
- 💿 Discografías: `Metallica`
- 📀 Álbumes: `The Wall Pink Floyd`
