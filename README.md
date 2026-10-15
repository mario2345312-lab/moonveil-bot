# Moonveil Bot

Bot de Discord con economía de Hearts para la comunidad Moonveil (Adopt Me): tienda con aprobación del staff, rachas diarias, logros, misiones, minijuegos, lotería, sorteos, subastas, bienvenidas, subida automática de emojis/stickers, moderación con automod, confesiones anónimas, cumpleaños, QOTD, AFK, comandos personalizados, eventos, y **Moonveil** — un juego de mascotas de Adopt Me con exploración, batallas, Neon, Shiny y boss semanal.

## Instalación

```bash
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y pega tu token:

```env
DISCORD_TOKEN=tu_token
GUILD_ID=123456789   # opcional: sync instantáneo en tu servidor de prueba
```

## Discord Developer Portal

1. **Bot → Privileged Gateway Intents**: activa **Server Members Intent** (logro de invites) y **Message Content Intent** (subida automática de emojis/stickers).
2. Invita el bot con scopes `bot` + `applications.commands` y estos permisos:
   - **Manage Server** (para leer las invites)
   - **Manage Roles** (la tienda y los logros crean/asignan roles — el rol del bot debe estar *por encima* de los roles que asigna)
   - **Manage Channels** (canal privado temporal)
   - **Manage Emojis and Stickers** (staff sube emojis/stickers con el bot)
   - **Manage Messages** (automod y `/purge`)
   - **Moderate Members** (`/mute` y timeout por spam)
   - **Kick Members** / **Ban Members** (`/kick`, `/ban`)
   - Enviar mensajes / embeds / usar comandos de aplicación

## Ejecutar

```bash
python bot.py
```

O simplemente haz doble clic en **`ejecutar.bat`** (Windows).

## Configurar el servidor (una vez dentro)

Con permiso de *Manage Server*, usa `/setup`:

| Comando | Para qué |
|---|---|
| `/setup canal-compras #canal` | Solicitudes de `/buy` |
| `/setup canal-logros #canal` | Reclamos de logros con captura |
| `/setup canal-misiones #canal` | Reclamos de misiones con captura |
| `/setup canal-logs #canal` | Registro de acciones del bot (opcional) |
| `/setup rol-staff @rol` | **Añade** un rol staff — puedes tener varios (repite el comando) |
| `/setup rol-staff-quitar @rol` | Quita un rol de la lista de staff |
| `/setup rol-vip @rol` | Rol que entrega "Acceso VIP" (si no, el bot crea "VIP") |
| `/setup categoria-canales #cat` | Dónde se crean los canales temporales |
| `/setup canal-emojis` | Crea `#emojis-auto` (sube imágenes → emojis automáticos) |
| `/setup canal-stickers` | Crea `#stickers-auto` (sube imágenes → stickers automáticos) |
| `/setup canal-bienvenida #canal` | Canal donde el bot saluda a los nuevos |
| `/setup canal-sugerencias #canal` | Canal de sugerencias en español (mensajes → votos) |
| `/setup canal-sugerencias-en #canal` | Canal de sugerencias en inglés (mensajes → votos) |
| `/setup canal-confesiones #canal` | Canal de confesiones anónimas (mensajes → confesión numerada) |
| `/setup canal-trades #canal` | Revisión del staff de `/trade` |

## Beneficios VIP

El rol **VIP** (obtenible en la tienda) incluye:

- **+50% Hearts** en `/daily`, `/work`, `/pescar`, `/trade` y recompensas de Moonveil (exploración/batallas)
- **Cooldowns a la mitad** en `/work` (4h→2h), `/pescar` (1h→30m), `/rob` (24h→12h)
- **15 usos diarios de /pescar** (vs 10 normales)
- **Perfil premium** con diseño dorado/púrpura, banner grande y estadísticas VIP exclusivas


| `/setup canal-qotd #canal` | Canal de la pregunta del día (diaria, bilingüe) |
| `/setup canal-confesiones #canal` | Canal de confesiones anónimas (mensajes → confesión sin autor) |
| `/setup canal-qotd #canal` | Canal donde el bot publica la pregunta del día |
| `/setup rol-espanol @rol` | Rol de miembros que hablan español |
| `/setup rol-ingles @rol` | Rol de miembros que hablan inglés |
| `/setup estado` | Ver qué está configurado y qué falta |

## Idioma del bot (español / English)

El bot responde a cada miembro en su idioma, resuelto así:

1. **Preferencia manual** — cada usuario elige con `/language` (🇪🇸 Español, 🇺🇸 English o 🌐 Auto)
2. **Rol de idioma** — si tiene solo el rol de español → español; solo el de inglés → inglés
3. **Ambos roles o ninguno** → español por defecto (o lo que eligió en `/language`)

Cubre: economía, juegos, Moonveil, tienda, progresión, sorteos/subastas, DMs de aprobación y bienvenida.

## Comandos de usuarios

- `/shop`, `/buy` — tienda (las compras las aprueba el staff antes de ejecutarse)
- `/hearts`, `/daily`, `/work`, `/rob`, `/streak`, `/leaderboard`, `/profile`, `/dream-pet`, `/pescar` — economía
- `/jugar` — **Moonveil**: adopta mascotas de Adopt Me, explóralas, batalla contra salvajes, combina Neon y consigue ✨ Shiny (incluye racha de login diario)
- `/boss`, `/topmascotas` — boss semanal comunitario (las batallas lo dañan y reparten pozo) y ranking de mascotas
- `/cumple`, `/afk` — cumpleaños con felicitación diaria y estado AFK con avisos
- `/trade` — envía captura de un trade en Adopt Me; el staff lo aprueba y ganas Hearts
- `/flip`, `/dice`, `/slots`, `/rps`, `/guess` — minijuegos con animación
- `/blackjack`, `/ruleta`, `/trivia` — más juegos de apuestas
- `/loteria` — tickets para un pozo acumulado de Hearts
- `/recordatorio` — recordatorios programados
- `/language` — elegir tu idioma (español/English/auto)
- Canal de sugerencias: escribes ahí y el bot publica tu idea con votos ✅/❌
- `/achievements`, `/missions`, `/claim-achievement`, `/claim-mision` — progresión (los reclamos con prueba adjuntan captura)
- `/help` — menú de ayuda

## Comandos de staff

- `/hearts-admin` — dar/quitar/fijar Hearts
- `/sorteo crear`, `/sorteo cancelar` — sorteos con botón de participar (premios: Hearts + texto + rol)
- `/subasta` — subastas por Hearts con reembolso al superado
- `/encuesta` — encuestas con votos 1️⃣-4️⃣
- `/say`, `/anuncio` — publicar mensajes/embeds del bot
- `/warn`, `/warns`, `/warns-limpiar`, `/mute`, `/kick`, `/ban`, `/purge` — moderación (con automod: links, groserías, spam y caps)
- `/comando agregar`, `/comando quitar`, `/comando lista` — comandos personalizados `!nombre`
- `/evento` — recordatorios/anuncios programados para todo el servidor
- `/emoji-add`, `/emoji-tomar`, `/sticker-add`, `/emoji-borrar`, `/sticker-borrar` — gestión de emojis/stickers

## Personalizar

Todo el contenido está en `config.py`: precios e items de la tienda, recompensas de daily, logros, misiones, nombre del bot y colores. Los canales/roles se guardan por servidor en la base de datos (`data/bot.db`).
