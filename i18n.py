"""Internacionalización (es/en).

Cada texto del bot vive en STRINGS como {"clave": {"es": "...", "en": "..."}}.
Uso: t(lang, "economy.daily_title", hearts=100).

El idioma de un usuario se resuelve así:
1. Preferencia explícita (/language) — users.lang
2. Rol de idioma configurado (/setup rol-espanol / rol-ingles):
   solo ES→"es", solo EN→"en"
3. Ambos roles, ninguno, o sin configurar → "es"
"""

import discord

STRINGS: dict[str, dict[str, str]] = {}


def t(lang: str, key: str, **kw) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    s = entry.get(lang) or entry["es"]
    return s.format(**kw) if kw else s


async def user_lang(bot, interaction: discord.Interaction) -> str:
    """Idioma a usar para responder a esta interacción."""
    db = bot.db
    u = await db.get_user(interaction.guild.id, interaction.user.id)
    if u["lang"]:
        return u["lang"]
    s = await db.get_settings(interaction.guild.id)
    roles = {r.id for r in getattr(interaction.user, "roles", [])}
    es_r, en_r = s.get("lang_es_role_id"), s.get("lang_en_role_id")
    has_es = es_r is not None and es_r in roles
    has_en = en_r is not None and en_r in roles
    if has_en and not has_es:
        return "en"
    return "es"


def member_lang(settings: dict, member: discord.Member,
                pref: str | None = None) -> str:
    """Idioma para un miembro fuera de una interacción (ej: bienvenida)."""
    if pref:
        return pref
    roles = {r.id for r in member.roles}
    es_r = settings.get("lang_es_role_id")
    en_r = settings.get("lang_en_role_id")
    has_es = es_r is not None and es_r in roles
    has_en = en_r is not None and en_r in roles
    if has_en and not has_es:
        return "en"
    return "es"


# ==========================================================================
# TEXTOS
# ==========================================================================

STRINGS.update({

# ---------- comunes ----------
"common.not_your_game": {
    "es": "Esta partida no es tuya.",
    "en": "This game isn't yours."},
"common.min_bet": {
    "es": "❌ La apuesta mínima es **{min} {heart}**.",
    "en": "❌ Minimum bet is **{min} {heart}**."},
"common.no_hearts": {
    "es": "💔 No tienes suficientes Hearts — tienes **{hearts}**.",
    "en": "💔 Not enough Hearts — you have **{hearts}**."},
"common.new_balance": {
    "es": "Nuevo saldo: **{hearts:,} {heart}**",
    "en": "New balance: **{hearts:,} {heart}**"},

# ---------- /language ----------
"lang.set_es": {
    "es": "🇪🇸 Idioma cambiado a **español**.",
    "en": "🇪🇸 Language set to **Spanish**."},
"lang.set_en": {
    "es": "🇺🇸 Idioma cambiado a **inglés**.",
    "en": "🇺🇸 Language set to **English**."},
"lang.auto": {
    "es": "🌐 Idioma en **automático** — se usará tu rol de idioma.",
    "en": "🌐 Language set to **auto** — your language role will be used."},

# ---------- /profile ----------
"profile.title": {
    "es": "✨ Perfil de {name}",
    "en": "✨ {name}'s Profile"},
"profile.streak": {
    "es": "🔥 **{n}** días de racha  •  🏅 récord **{best}**",
    "en": "🔥 **{n}**-day streak  •  🏅 record **{best}**"},
"profile.activity": {"es": "📊 Actividad", "en": "📊 Activity"},
"profile.earned": {"es": "▫️ Ganados", "en": "▫️ Earned"},
"profile.spent": {"es": "▫️ Gastados", "en": "▫️ Spent"},
"profile.dailies": {"es": "▫️ Dailies", "en": "▫️ Dailies"},
"profile.progress": {"es": "🎯 Progresión", "en": "🎯 Progress"},
"profile.achievements": {"es": "▫️ Logros", "en": "▫️ Achievements"},
"profile.missions": {"es": "▫️ Misiones", "en": "▫️ Missions"},
"profile.invited": {"es": "▫️ Invitados", "en": "▫️ Invited"},
"profile.game": {"es": "🎲 Juego", "en": "🎲 Game"},
"profile.flips": {"es": "▫️ Flips", "en": "▫️ Flips"},
"profile.purchases": {"es": "▫️ Compras", "en": "▫️ Purchases"},
"profile.set_dream": {
    "es": "*Define tu Dream Pet con `/dream-pet`*",
    "en": "*Set your Dream Pet with `/dream-pet`*"},
"profile.joined": {
    "es": "📥 En el server desde",
    "en": "📥 In the server since"},
"profile.created": {"es": "🗓️ Cuenta creada", "en": "🗓️ Account created"},
"profile.dates": {"es": "📅 Fechas", "en": "📅 Dates"},
"profile.rank_footer": {
    "es": "📍 Posición #{rank} en el leaderboard",
    "en": "📍 Rank #{rank} on the leaderboard"},

# ---------- /dream-pet ----------
"dream.saved_title": {
    "es": "🐣 ¡Dream Pet guardada!",
    "en": "🐣 Dream Pet saved!"},
"dream.saved_desc": {
    "es": "Tu mascota soñada ahora es **{pet}**.\nSe mostrará en tu `/profile`.",
    "en": "Your dream pet is now **{pet}**.\nIt will show on your `/profile`."},

# ---------- /hearts ----------
"hearts.title": {
    "es": "{heart} Hearts de {name}",
    "en": "{heart} {name}'s Hearts"},
"hearts.balance": {
    "es": "## 💰 Saldo: {hearts:,} {heart}",
    "en": "## 💰 Balance: {hearts:,} {heart}"},
"hearts.streak": {
    "es": "🔥 Racha: **{n} días**  •  🏅 Récord: **{best}**",
    "en": "🔥 Streak: **{n} days**  •  🏅 Record: **{best}**"},
"hearts.stats": {"es": "📊 Estadísticas", "en": "📊 Stats"},
"hearts.game_social": {"es": "🎲 Juego y social", "en": "🎲 Game & social"},
"hearts.flips_won": {"es": "▫️ Flips ganados", "en": "▫️ Flips won"},

# ---------- /daily ----------
"daily.already_title": {
    "es": "⏰ ¡Ya reclamaste hoy!",
    "en": "⏰ Already claimed today!"},
"daily.already_desc": {
    "es": "Vuelve **mañana** para mantener tu racha.\n"
          "⚠️ *Si pasas un día sin reclamar, tu racha se reinicia.*",
    "en": "Come back **tomorrow** to keep your streak.\n"
          "⚠️ *If you skip a day, your streak resets.*"},
"daily.title": {
    "es": "✨ ¡Recompensa diaria reclamada!",
    "en": "✨ Daily reward claimed!"},
"daily.streak_field": {"es": "🔥 Racha actual", "en": "🔥 Current streak"},
"daily.streak_value": {"es": "**{n} días**", "en": "**{n} days**"},
"daily.breakdown": {"es": "🎁 Desglose", "en": "🎁 Breakdown"},
"daily.breakdown_val": {
    "es": "{base} base + {bonus}×{streak} racha",
    "en": "{base} base + {bonus}×{streak} streak"},
"daily.footer": {
    "es": "💡 Vuelve mañana para que tu racha siga creciendo",
    "en": "💡 Come back tomorrow to keep your streak growing"},

# ---------- /streak ----------
"streak.title": {"es": "🔥 Tu racha de actividad", "en": "🔥 Your streak"},
"streak.desc": {
    "es": "# {n} días seguidos\n{bar}",
    "en": "# {n} days in a row\n{bar}"},
"streak.best": {"es": "🏅 Mejor racha", "en": "🏅 Best streak"},
"streak.best_val": {"es": "**{n} días**", "en": "**{n} days**"},
"streak.next": {"es": "🎁 Próximo /daily", "en": "🎁 Next /daily"},
"streak.footer": {
    "es": "⚠️ Si pasas un día sin usar /daily, tu racha se reinicia",
    "en": "⚠️ If you skip a day without /daily, your streak resets"},

# ---------- /leaderboard ----------
"lb.title": {
    "es": "🏆 Leaderboard — Top Hearts 💕",
    "en": "🏆 Leaderboard — Top Hearts 💕"},
"lb.empty": {
    "es": "😴 Aún nadie tiene Hearts.\n¡Usa `/daily` y sé el primero!",
    "en": "😴 Nobody has Hearts yet.\nUse `/daily` and be the first!"},
"lb.footer": {"es": "📍 Tu posición: #{rank}", "en": "📍 Your rank: #{rank}"},

# ---------- /work ----------
"work.tired": {
    "es": "⏰ Aún estás cansada/o — vuelve en **{left}**.",
    "en": "⏰ You're still tired — come back in **{left}**."},
"work.jobs": {
    "es": "cuidaste las mascotas de la guardería 🍼|"
          "hiciste delivery de pociones 🧪|"
          "limpiaste el Nursery 🧹|"
          "vendiste lemonades en el puesto 🍋|"
          "paseaste las mascotas del vecindario 🦮",
    "en": "you babysat the nursery pets 🍼|"
          "delivered potions 🧪|"
          "cleaned up the Nursery 🧹|"
          "sold lemonades at the stand 🍋|"
          "walked the neighborhood pets 🦮"},
"work.title": {"es": "💼 ¡A trabajar!", "en": "💼 Time to work!"},
"work.footer": {
    "es": "Vuelve en {h}h por más",
    "en": "Come back in {h}h for more"},

# ---------- /rob ----------
"rob.invalid": {
    "es": "❌ No puedes robarle a ese usuario.",
    "en": "❌ You can't rob that user."},
"rob.rest": {
    "es": "⏰ Descansa — podrás volver a intentarlo en **{left}**.",
    "en": "⏰ Rest up — you can try again in **{left}**."},
"rob.poor": {
    "es": "❌ {user} no tiene Hearts que robar (tiene **{n}**).",
    "en": "❌ {user} has no Hearts to steal (has **{n}**)."},
"rob.win_title": {"es": "🥷 ¡Robo exitoso!", "en": "🥷 Heist successful!"},
"rob.win_desc": {
    "es": "Le quitaste **{n} {heart}** a {user} sin que se diera cuenta 😏",
    "en": "You stole **{n} {heart}** from {user} without them noticing 😏"},
"rob.lose_title": {"es": "🚔 ¡Te atraparon!", "en": "🚔 You got caught!"},
"rob.lose_desc": {
    "es": "{user} te descubrió y perdiste **{n} {heart}** en la fuga 💨",
    "en": "{user} caught you and you lost **{n} {heart}** escaping 💨"},

# ---------- juegos (animaciones y resultados) ----------
"games.flipping": {
    "es": "🪙 Lanzas la moneda al aire...",
    "en": "🪙 You flip the coin..."},
"games.spinning": {
    "es": "🪙 Gira... gira... ¿{a}? ¿{b}?",
    "en": "🪙 It spins... spins... {a}? {b}?"},
"games.landed": {"es": "🪙 ¡Cayó!", "en": "🪙 It landed!"},
"games.won": {"es": "🎉 ¡Ganaste!", "en": "🎉 You won!"},
"games.lost": {"es": "💔 Perdiste", "en": "💔 You lost"},
"games.tie": {"es": "🤝 Empate", "en": "🤝 Tie"},
"games.your_choice": {
    "es": "Elegiste **{c}**",
    "en": "You picked **{c}**"},
"games.bot_choice": {
    "es": "El bot eligió **{c}**",
    "en": "The bot picked **{c}**"},

"games.dice_roll": {
    "es": "🎲 El dado rueda por la mesa...",
    "en": "🎲 The dice tumbles..."},
"games.dice_result": {
    "es": "Salió un **{n}** — tu número era **{m}**",
    "en": "It rolled a **{n}** — your number was **{m}**"},

"games.slots_spin": {
    "es": "🎰 Los rodillos giran...",
    "en": "🎰 The reels are spinning..."},

"games.rps_1": {"es": "✊ Piedra...", "en": "✊ Rock..."},
"games.rps_2": {"es": "✋ Papel...", "en": "✋ Paper..."},
"games.rps_3": {"es": "✌️ Tijera...", "en": "✌️ Scissors..."},
"games.rps_go": {"es": "¡YA!", "en": "SHOOT!"},

"games.guess_thinking": {
    "es": "🔮 El bot piensa un número del 1 al 10...",
    "en": "🔮 The bot is thinking of a number 1-10..."},
"games.guess_almost": {
    "es": "🔮 ¿Será el **{n}**?",
    "en": "🔮 Could it be **{n}**?"},
"games.guess_result": {
    "es": "El número era **{n}** — tú dijiste **{m}**",
    "en": "The number was **{n}** — you said **{m}**"},

"games.bj_hit": {"es": "Pedir carta", "en": "Hit"},
"games.bj_stand": {"es": "Plantarse", "en": "Stand"},
"games.bj_title": {"es": "🃏 Blackjack", "en": "🃏 Blackjack"},
"games.bj_your_hand": {"es": "Tu mano", "en": "Your hand"},
"games.bj_dealer": {"es": "Dealer", "en": "Dealer"},
"games.bj_blackjack": {"es": "🎉 ¡BLACKJACK!", "en": "🎉 BLACKJACK!"},
"games.bj_push": {"es": "🤝 Empate", "en": "🤝 Push"},
"games.bj_push_desc": {"es": "recuperas tu apuesta", "en": "you get your bet back"},
"games.bj_dealer_wins": {"es": "💔 El dealer gana", "en": "💔 Dealer wins"},
"games.bj_bust": {"es": "💥 Te pasaste de 21", "en": "💥 Bust — over 21"},

"games.roulette_1": {"es": "🎡 La ruleta gira...", "en": "🎡 The wheel spins..."},
"games.roulette_2": {"es": "🎡 La bola rebota... 🔴", "en": "🎡 The ball bounces... 🔴"},
"games.roulette_3": {"es": "🎡 La bola rebota... ⚫", "en": "🎡 The ball bounces... ⚫"},
"games.roulette_4": {"es": "🎡 Se está deteniendo...", "en": "🎡 It's slowing down..."},
"games.roulette_win": {
    "es": "🎉 ¡La bola cayó a tu favor!",
    "en": "🎉 The ball landed your way!"},
"games.roulette_lose": {
    "es": "💔 La ruleta no estuvo de tu lado",
    "en": "💔 The wheel wasn't on your side"},
"games.roulette_need_number": {
    "es": "❌ Indica el número exacto (0-36) en el parámetro `numero`.",
    "en": "❌ Pick the exact number (0-36) in the `numero` option."},
"games.your_bet": {"es": "Tu apuesta", "en": "Your bet"},
"games.result": {"es": "Salió", "en": "Result"},
"games.jackpot": {"es": "🎰 ¡JACKPOT! 🎰", "en": "🎰 JACKPOT! 🎰"},
"games.pair": {"es": "🎰 ¡Par ganador!", "en": "🎰 Winning pair!"},
"games.slots_none": {"es": "🎰 Nada esta vez...", "en": "🎰 Nothing this time..."},
"games.spinning_reels": {"es": "*Girando...*", "en": "*Spinning...*"},
"games.reel1": {
    "es": "*El primer rodillo se detiene...*",
    "en": "*First reel stops...*"},
"games.reel2": {"es": "*El segundo rodillo...*", "en": "*Second reel...*"},
"games.reel3": {"es": "*¡El último!*", "en": "*The last one!*"},
"games.you": {"es": "Tú", "en": "You"},
"games.bot": {"es": "Bot", "en": "Bot"},
"games.tie_desc": {"es": "Recuperas tu apuesta.", "en": "You get your bet back."},
"games.bot_wins": {"es": "💔 El bot gana...", "en": "💔 The bot wins..."},
"games.flip_lucky": {
    "es": "🎉 ¡La suerte te sonríe!",
    "en": "🎉 Luck is on your side!"},
"games.flip_unlucky": {"es": "💔 Mala suerte...", "en": "💔 Bad luck..."},
"games.dice_exact": {"es": "🎲 ¡Número exacto!", "en": "🎲 Exact number!"},
"games.dice_no": {"es": "🎲 No fue...", "en": "🎲 Not it..."},
"games.guess_yes": {"es": "🔮 ¡Lo adivinaste!", "en": "🔮 You guessed it!"},
"games.guess_no": {"es": "🔮 No era ese...", "en": "🔮 Not that one..."},
"games.your_number": {"es": "Tu número", "en": "Your number"},
"games.number_was": {"es": "El número era", "en": "The number was"},
"games.coin_cara": {"es": "CARA", "en": "HEADS"},
"games.coin_cruz": {"es": "CRUZ", "en": "TAILS"},

"games.trivia_title": {"es": "🧠 Trivia de Adopt Me", "en": "🧠 Adopt Me Trivia"},
"games.trivia_time": {"es": "*Tienes 15 segundos*", "en": "*You have 15 seconds*"},
"games.trivia_correct": {"es": "🎉 ¡Correcta!", "en": "🎉 Correct!"},
"games.trivia_correct_desc": {
    "es": "Acertaste la trivia 🧠",
    "en": "You got the trivia right 🧠"},
"games.trivia_wrong": {"es": "❌ Incorrecta", "en": "❌ Wrong"},
"games.trivia_wrong_desc": {
    "es": "La respuesta correcta era la opción **{n}**.",
    "en": "The correct answer was option **{n}**."},

# ---------- /loteria ----------
"lottery.title": {"es": "🎟️ Lotería de Hearts", "en": "🎟️ Hearts Lottery"},
"lottery.pot": {"es": "## 💰 Pozo: {pot:,} {heart}", "en": "## 💰 Pot: {pot:,} {heart}"},
"lottery.sold": {"es": "🎫 Tickets vendidos: **{n}**", "en": "🎫 Tickets sold: **{n}**"},
"lottery.yours": {"es": "🫵 Tus tickets: **{n}**", "en": "🫵 Your tickets: **{n}**"},
"lottery.chance": {"es": " ({pct} de ganar)", "en": " ({pct} chance to win)"},
"lottery.footer": {
    "es": "Cada ticket cuesta {price} {heart} • El staff sortea con /loteria sortear",
    "en": "Each ticket costs {price} {heart} • Staff draws with /loteria sortear"},
"lottery.min_one": {
    "es": "❌ Debes comprar al menos 1 ticket.",
    "en": "❌ You must buy at least 1 ticket."},
"lottery.cant_afford": {
    "es": "💔 Te faltan Hearts — {n} tickets cuestan **{cost} {heart}** "
          "y tienes **{have}**.",
    "en": "💔 Not enough Hearts — {n} tickets cost **{cost} {heart}** "
          "and you have **{have}**."},
"lottery.bought": {
    "es": "🎟️ Compraste **{n} ticket(s)** por **{cost} {heart}**\n"
          "Pozo actual: **{pot:,} {heart}** — ¡suerte!",
    "en": "🎟️ You bought **{n} ticket(s)** for **{cost} {heart}**\n"
          "Current pot: **{pot:,} {heart}** — good luck!"},
"lottery.no_tickets": {
    "es": "❌ No hay tickets vendidos todavía.",
    "en": "❌ No tickets sold yet."},
"lottery.winner_title": {"es": "🎊 ¡Tenemos ganadora/or!", "en": "🎊 We have a winner!"},
"lottery.winner_desc": {
    "es": "# {user}\nse lleva el pozo de **{pot:,} {heart}** 🎉",
    "en": "# {user}\nwins the **{pot:,} {heart}** pot 🎉"},
"lottery.drawn_by": {"es": "Sorteado por {name}", "en": "Drawn by {name}"},

# ---------- /recordatorio ----------
"rem.bad_format": {
    "es": "❌ Formato inválido — usa `10s`, `10m`, `2h` o `1d`.",
    "en": "❌ Invalid format — use `10s`, `10m`, `2h` or `1d`."},
"rem.range": {
    "es": "❌ El recordatorio debe ser entre 10 segundos y 7 días.",
    "en": "❌ Reminders must be between 10 seconds and 7 days."},
"rem.set": {
    "es": "⏰ Listo — te recordaré <t:{ts}:R>: *{text}*",
    "en": "⏰ Done — I'll remind you <t:{ts}:R>: *{text}*"},
"rem.ping": {
    "es": "⏰ {user} recordatorio: **{text}**",
    "en": "⏰ {user} reminder: **{text}**"},

# ---------- comunidad ----------
"giveaway.join_btn": {"es": "Participar", "en": "Join"},
"giveaway.ended": {"es": "Este sorteo ya terminó.", "en": "This giveaway is over."},
"giveaway.already": {"es": "Ya estás participando 🍀", "en": "You're already in 🍀"},
"giveaway.joined": {
    "es": "🎉 ¡Estás dentro! Mucha suerte.",
    "en": "🎉 You're in! Good luck."},
"giveaway.title": {"es": "🎉 ¡SORTEO!", "en": "🎉 GIVEAWAY!"},
"giveaway.tap": {"es": "Toca 🎉 para participar.", "en": "Tap 🎉 to enter."},
"giveaway.winners": {"es": "🏆 Ganadores: **{n}**", "en": "🏆 Winners: **{n}**"},
"giveaway.ends": {"es": "⏰ Termina", "en": "⏰ Ends"},
"giveaway.entries": {"es": "Participantes: {n}", "en": "Entries: {n}"},
"giveaway.done_title": {"es": "🎊 ¡Sorteo terminado!", "en": "🎊 Giveaway ended!"},
"giveaway.none_title": {
    "es": "😴 Sorteo terminado sin participantes",
    "en": "😴 Giveaway ended with no entries"},
"giveaway.cancelled": {"es": "🚫 Sorteo cancelado", "en": "🚫 Giveaway cancelled"},
"giveaway.not_found": {
    "es": "❌ Sorteo no encontrado o ya terminó.",
    "en": "❌ Giveaway not found or already over."},
"giveaway.created": {"es": "✅ Sorteo creado en {ch}", "en": "✅ Giveaway created in {ch}"},

"auction.title": {"es": "🔨 Subasta", "en": "🔨 Auction"},
"auction.current": {"es": "💰 Puja actual: **{n} {heart}**", "en": "💰 Current bid: **{n} {heart}**"},
"auction.min": {"es": "🔻 Puja mínima: **{n} {heart}**", "en": "🔻 Minimum bid: **{n} {heart}**"},
"auction.hint": {
    "es": "*Toca 🔨 Pujar para ofertar — si te superan te devuelven los Hearts.*",
    "en": "*Tap 🔨 Bid to offer — outbid? You get your Hearts back.*"},
"auction.bid_btn": {"es": "Pujar", "en": "Bid"},
"auction.modal_title": {"es": "Haz tu puja", "en": "Place your bid"},
"auction.modal_field": {"es": "Cantidad de Hearts", "en": "Amount of Hearts"},
"auction.ended": {"es": "Esta subasta ya terminó.", "en": "This auction is over."},
"auction.invalid": {"es": "❌ Cantidad inválida.", "en": "❌ Invalid amount."},
"auction.too_low": {
    "es": "❌ Tu puja debe ser de al menos **{n} {heart}**.",
    "en": "❌ Your bid must be at least **{n} {heart}**."},
"auction.already_top": {
    "es": "Ya eres el mejor postor.",
    "en": "You're already the top bidder."},
"auction.no_funds": {
    "es": "💔 No tienes suficientes Hearts para esa puja.",
    "en": "💔 Not enough Hearts for that bid."},
"auction.bid_ok": {
    "es": "🔨 ¡Puja de **{n} {heart}** registrada! Vas ganando.",
    "en": "🔨 Bid of **{n} {heart}** placed! You're winning."},
"auction.sold": {"es": "🔨 ¡Subasta vendida!", "en": "🔨 Auction sold!"},
"auction.sold_desc": {
    "es": "{item}\n\n🏆 Ganador: {user} por **{n} {heart}**",
    "en": "{item}\n\n🏆 Winner: {user} for **{n} {heart}**"},
"auction.no_bids": {"es": "🔨 Subasta sin pujas", "en": "🔨 Auction ended — no bids"},
"auction.created": {"es": "✅ Subasta creada en {ch}", "en": "✅ Auction created in {ch}"},
"auction.ends": {"es": "⏰ Termina", "en": "⏰ Ends"},

"poll.title": {"es": "📊 Encuesta", "en": "📊 Poll"},
"poll.by": {"es": "Encuesta de {name}", "en": "Poll by {name}"},
"poll.posted": {"es": "✅ Encuesta publicada.", "en": "✅ Poll posted."},

"suggest.title_es": {"es": "💡 Nueva sugerencia", "en": "💡 New suggestion"},

# ---------- /help ----------
"help.title": {"es": "📖 Centro de Ayuda - {bot}", "en": "📖 Help Center - {bot}"},
"help.desc": {
    "es": "Aquí tienes la lista completa de todos los comandos "
          "disponibles organizados por categorías:",
    "en": "Here's the complete list of all commands, "
          "organized by category:"},
"help.shop": {"es": "🛒 Tienda y Compras", "en": "🛒 Shop & Purchases"},
"help.shop_cmds": {
    "es": "• `/shop` - Muestra el catálogo con los productos disponibles.\n"
          "• `/buy` - Compra un artículo de la tienda usando tus Hearts.",
    "en": "• `/shop` - Browse the item catalog.\n"
          "• `/buy` - Buy a shop item with your Hearts."},
"help.economy": {"es": "💕 Economía y Actividad", "en": "💕 Economy & Activity"},
"help.economy_cmds": {
    "es": "• `/hearts` - Revisa tu saldo actual de Hearts y estadísticas.\n"
          "• `/profile` - Muestra tu perfil completo o el de otro usuario.\n"
          "• `/dream-pet` - Establece tu mascota soñada de Adopt Me.\n"
          "• `/daily` - Reclama tu recompensa diaria.\n"
          "• `/work` - Trabaja para ganar Hearts (cada 4h).\n"
          "• `/rob` - Intenta robar Hearts a otro usuario.\n"
          "• `/loteria` - Compra tickets para el pozo acumulado.\n"
          "• `/streak` - Muestra tu racha de actividad diaria actual.\n"
          "• `/pescar` - Ve de pesca y gana Hearts (cada hora).\n"
          "• `/leaderboard` - Tabla de usuarios con más Hearts.\n"
          "• `/language` - Elige tu idioma (español/inglés).",
    "en": "• `/hearts` - Check your Hearts balance and stats.\n"
          "• `/profile` - View your full profile or someone else's.\n"
          "• `/dream-pet` - Set your Adopt Me dream pet.\n"
          "• `/daily` - Claim your daily reward.\n"
          "• `/work` - Work for Hearts (every 4h).\n"
          "• `/rob` - Try to steal Hearts from another user.\n"
          "• `/loteria` - Buy tickets for the jackpot.\n"
          "• `/streak` - Show your daily streak.\n"
          "• `/pescar` - Go fishing for Hearts (hourly).\n"
          "• `/leaderboard` - Top Hearts leaderboard.\n"
          "• `/language` - Choose your language (English/Spanish)."},
"help.games": {"es": "🎮 Mini-juegos y Diversión", "en": "🎮 Minigames & Fun"},
"help.games_cmds": {
    "es": "• `/jugar` - Abre Moonveil: adopta mascotas, explóralas, "
          "batalla y haz Neon.\n"
          "• `/flip` - Apuesta tus Hearts lanzando una moneda (cara o cruz).\n"
          "• `/dice` - Adivina el número del dado (1-6). Gana x4.\n"
          "• `/slots` - Tragamonedas: 3 iguales x10, 2 iguales x2.\n"
          "• `/rps` - Piedra, papel o tijera contra el bot. Gana x2.\n"
          "• `/guess` - Adivina el número del 1 al 10. Gana x8.\n"
          "• `/blackjack` - 21 contra el bot con botones.\n"
          "• `/ruleta` - Apuesta a color (x2) o número (x30).\n"
          "• `/trivia` - Preguntas de Adopt Me con premio en Hearts.",
    "en": "• `/jugar` - Open Moonveil: adopt pets, explore, battle, "
          "make Neons.\n"
          "• `/flip` - Bet your Hearts on a coin flip (heads or tails).\n"
          "• `/dice` - Guess the dice roll (1-6). Wins x4.\n"
          "• `/slots` - Slot machine: 3 of a kind x10, pair x2.\n"
          "• `/rps` - Rock, paper, scissors vs the bot. Wins x2.\n"
          "• `/guess` - Guess the number 1-10. Wins x8.\n"
          "• `/blackjack` - Play 21 vs the bot with buttons.\n"
          "• `/ruleta` - Bet on color (x2) or exact number (x30).\n"
          "• `/trivia` - Adopt Me questions for Hearts."},
"help.community": {"es": "🎉 Comunidad", "en": "🎉 Community"},
"help.community_cmds": {
    "es": "• `#sugerencias` - Escribe en el canal de sugerencias y el bot "
          "publica tu idea con votos.\n"
          "• `/recordatorio` - Programa un recordatorio (10m, 2h, 1d).\n"
          "• `/sorteo` - Participa en sorteos con el botón 🎉.\n"
          "• `/subasta` - Puja por artículos en las subastas del staff.\n"
          "• `/cumple` - Registra tu cumpleaños para recibir felicitación.\n"
          "• `/afk` - Marca AFK con un mensaje opcional.\n"
          "• `/topmascotas` - Ranking de las mejores mascotas del server.\n"
          "• `/trade` - Envía captura de un trade en Adopt Me por Hearts.\n"
          "• `#confesiones` - Escribe allí y el bot lo publica anónimo.",
    "en": "• `#suggestions` - Post in the suggestions channel and the bot "
          "publishes your idea with votes.\n"
          "• `/recordatorio` - Set a reminder (10m, 2h, 1d).\n"
          "• `/sorteo` - Join giveaways with the 🎉 button.\n"
          "• `/subasta` - Bid on items in staff auctions.\n"
          "• `/cumple` - Register your birthday to get a shout-out.\n"
          "• `/afk` - Set AFK status with an optional message.\n"
          "• `/topmascotas` - Server's top pets leaderboard.\n"
          "• `/trade` - Submit an Adopt Me trade screenshot for Hearts.\n"
          "• `#confessions` - Write there and the bot posts it anonymously."},
"help.progress": {"es": "🏆 Logros y Misiones", "en": "🏆 Achievements & Missions"},
"help.progress_cmds": {
    "es": "• `/achievements` - Consulta tu lista de logros y estado.\n"
          "• `/missions` - Muestra las misiones disponibles y sus recompensas.\n"
          "• `/claim-achievement` - Reclama una recompensa por logro.\n"
          "• `/claim-mision` - Reclama una recompensa por misión.",
    "en": "• `/achievements` - View your achievements and status.\n"
          "• `/missions` - See available missions and rewards.\n"
          "• `/claim-achievement` - Claim an achievement reward.\n"
          "• `/claim-mision` - Claim a mission reward."},
"help.info": {"es": "ℹ️ Información", "en": "ℹ️ Info"},
"help.info_cmds": {
    "es": "• `/help` - Muestra este menú de ayuda.\n"
          "• `/language` - Cambia el idioma del bot.",
    "en": "• `/help` - Show this help menu.\n"
          "• `/language` - Change the bot's language."},

# ---------- Moonveil (/jugar) ----------
"mv.menu_title": {"es": "🌙 Moonveil", "en": "🌙 Moonveil"},
"mv.btn_menu": {"es": "Menú", "en": "Menu"},
"mv.btn_adopt": {"es": "Adoptar", "en": "Adopt"},
"mv.btn_pets": {"es": "Mis mascotas", "en": "My pets"},
"mv.btn_explore": {"es": "Explorar", "en": "Explore"},
"mv.btn_neon": {"es": "Neon", "en": "Neon"},
"mv.btn_battle": {"es": "Batalla", "en": "Battle"},
"mv.btn_missions": {"es": "Misiones", "en": "Missions"},
"mv.not_yours": {
    "es": "Este panel no es tuyo — usa `/jugar` para abrir el tuyo.",
    "en": "This panel isn't yours — use `/jugar` to open your own."},
"mv.rarity": {"es": "Rareza", "en": "Rarity"},
"mv.stage": {"es": "Etapa", "en": "Stage"},
"mv.progress": {"es": "Progreso", "en": "Progress"},
"mv.status": {"es": "Estado", "en": "Status"},
"mv.status_ready": {"es": "✅ Lista para explorar", "en": "✅ Ready to explore"},
"mv.status_exploring": {
    "es": "🗺️ Explorando — vuelve <t:{ts}:R>",
    "en": "🗺️ Exploring — back <t:{ts}:R>"},
"mv.status_returned": {
    "es": "🎒 ¡Volvió de explorar! Recoge su recompensa",
    "en": "🎒 Back from exploring! Collect the reward"},
"mv.status_resting": {
    "es": "😴 Descansando de batalla hasta <t:{ts}:R>",
    "en": "😴 Resting from battle until <t:{ts}:R>"},
"mv.adopt_title": {"es": "🥚 Adoptar mascota", "en": "🥚 Adopt a pet"},
"mv.first_free": {
    "es": "🎁 **¡Tu primera mascota es gratis!**",
    "en": "🎁 **Your first pet is FREE!**"},
"mv.choose_egg_hint": {
    "es": "Elige un huevo — las mejores rarezas salen en los mejores huevos:",
    "en": "Choose an egg — better eggs hatch better rarities:"},
"mv.neon_title": {"es": "✨ Mascotas Neon", "en": "✨ Neon Pets"},
"mv.neon_desc_none": {
    "es": "Combina **{n} mascotas iguales** en etapa 🐕 **Adulta** para crear "
          "una versión Neon (recompensas ×2).\n\n*Aún no tienes suficientes "
          "adultas de ninguna especie.*",
    "en": "Fuse **{n} identical pets** at 🐕 **Adult** stage to create a "
          "Neon version (×2 rewards).\n\n*You don't have enough adults of "
          "any species yet.*"},
"mv.neon_choose": {
    "es": "Elige la especie que quieres combinar:",
    "en": "Pick the species you want to fuse:"},
"mv.all_exploring": {
    "es": "Todas tus mascotas están explorando 🗺️\n"
          "*Espera a que vuelvan para pelear.*",
    "en": "All your pets are exploring 🗺️\n"
          "*Wait for them to come back to battle.*"},
"mv.battle_desc": {
    "es": "Elige la mascota que peleará contra una salvaje.\n"
          "*Cooldown: {mins} min por mascota.*",
    "en": "Pick the pet that will fight a wild one.\n"
          "*Cooldown: {mins} min per pet.*"},
"mv.still_exploring": {"es": "🗺️ Sigue explorando", "en": "🗺️ Still exploring"},
"mv.back_at": {
    "es": "Tu {emoji} **{pet}** vuelve <t:{ts}:R>.",
    "en": "Your {emoji} **{pet}** will be back <t:{ts}:R>."},
"mv.explore_done": {
    "es": "🎒 ¡Exploración completa!",
    "en": "🎒 Exploration complete!"},
"mv.explore_done_desc": {
    "es": "Tu {emoji} **{pet}** volvió de explorar.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**{bonus}",
    "en": "Your {emoji} **{pet}** is back from exploring.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**{bonus}"},
"mv.bonus_x3": {"es": " 🍀 ¡BONUS x3!", "en": " 🍀 BONUS x3!"},
"mv.explore_sent": {
    "es": "Tu {emoji} **{pet}** salió a explorar.\n"
          "Vuelve <t:{ts}:R> con recompensas.",
    "en": "Your {emoji} **{pet}** went exploring.\n"
          "It'll be back <t:{ts}:R> with rewards."},
"mv.explore_start": {"es": "🗺️ ¡A explorar!", "en": "🗺️ Off exploring!"},
"mv.starter_used": {
    "es": "Ya usaste tu huevo gratis.",
    "en": "You already used your free egg."},
"mv.no_hearts_egg": {
    "es": "💔 Te faltan Hearts — tienes **{have}** y el {egg} cuesta "
          "**{price} {heart}**.",
    "en": "💔 Not enough Hearts — you have **{have}** and the {egg} costs "
          "**{price} {heart}**."},
"mv.hatch_shiny": {"es": "🌟 ¡Eclosionó SHINY!", "en": "🌟 SHINY hatched!"},
"mv.hatch_normal": {"es": "🎉 ¡Eclosionó!", "en": "🎉 It hatched!"},
"mv.shiny_note": {
    "es": "\n\n*Variante Shiny — recompensas ×1.5*",
    "en": "\n\n*Shiny variant — ×1.5 rewards*"},
"mv.neon_few": {
    "es": "Ya no tienes suficientes adultas de esta especie.",
    "en": "You no longer have enough adults of this species."},
"mv.neon_done_desc2": {
    "es": "Las 4 adultas se combinaron en una mascota **Neon** que da "
          "recompensas ×2 al explorar.",
    "en": "The 4 adults fused into a **Neon** pet that earns ×2 "
          "rewards when exploring."},
"mv.choose_egg": {"es": "Elige un huevo:", "en": "Choose an egg:"},
"mv.starter_free": {"es": "Starter Egg — ¡GRATIS!", "en": "Starter Egg — FREE!"},
"mv.no_hearts_egg": {
    "es": "💔 No tienes suficientes Hearts para ese huevo.",
    "en": "💔 Not enough Hearts for that egg."},
"mv.hatching": {
    "es": "{emoji} El huevo está rompiendo...",
    "en": "{emoji} The egg is hatching..."},
"mv.crack": {"es": "*crack... crack...*", "en": "*crack... crack...*"},
"mv.hatched_common": {"es": "¡Salió una mascota!", "en": "A pet hatched!"},
"mv.no_pets": {
    "es": "Aún no tienes mascotas.\n¡Toca **🥚 Adoptar** para conseguir tu primera!",
    "en": "You don't have pets yet.\nTap **🥚 Adopt** to get your first!"},
"mv.your_pets": {"es": "🐾 Tus mascotas ({n})", "en": "🐾 Your pets ({n})"},
"mv.choose_pet": {
    "es": "Elige una para ver su ficha:",
    "en": "Pick one to see its card:"},
"mv.pick_pet": {"es": "Elige una mascota...", "en": "Pick a pet..."},
"mv.explore_title": {"es": "🗺️ Explorar", "en": "🗺️ Explore"},
"mv.explore_need_pet": {
    "es": "Necesitas una mascota primero — toca **🥚 Adoptar**.",
    "en": "You need a pet first — tap **🥚 Adopt**."},
"mv.explore_desc": {
    "es": "Elige una mascota para mandarla de expedición "
          "({mins} min — trae XP y Hearts):",
    "en": "Pick a pet to send on an expedition "
          "({mins} min — brings XP and Hearts):"},
"mv.pick_explorer": {"es": "Elige quién explorará...", "en": "Pick who explores..."},
"mv.opt_ready": {"es": "Lista", "en": "Ready"},
"mv.opt_returned": {"es": "¡Volvió!", "en": "Back!"},
"mv.opt_exploring": {"es": "Explorando", "en": "Exploring"},
"mv.sent_explore": {
    "es": "🗺️ **{pet}** salió de expedición.\nVolverá <t:{ts}:R> — "
          "vuelve a tocar **Explorar** para recoger la recompensa.",
    "en": "🗺️ **{pet}** went on an expedition.\nBack <t:{ts}:R> — "
          "tap **Explore** again to collect the reward."},
"mv.explore_reward": {
    "es": "🎒 **{pet}** volvió de explorar.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**",
    "en": "🎒 **{pet}** is back from exploring.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**"},
"mv.explore_lucky": {
    "es": "\n\n🍀 **¡Suerte! Encontró un tesoro x3**",
    "en": "\n\n🍀 **Lucky! Found a x3 treasure**"},
"mv.level_up": {
    "es": "\n\n🎉 **¡Creció a {stage}!**",
    "en": "\n\n🎉 **Grew to {stage}!**"},
"mv.neon_need": {
    "es": "Necesitas **4 mascotas iguales en etapa Adulta** para hacer Neon.",
    "en": "You need **4 identical Adult pets** to make a Neon."},
"mv.neon_none": {
    "es": "No tienes ninguna especie con 4+ adultas todavía.",
    "en": "You don't have any species with 4+ adults yet."},
"mv.pick_species": {"es": "Elige la especie a combinar...", "en": "Pick the species to combine..."},
"mv.have_adults": {"es": "Tienes {n} adultas", "en": "You have {n} adults"},
"mv.neon_confirm_title": {
    "es": "✨ Crear {species} Neon",
    "en": "✨ Create Neon {species}"},
"mv.neon_confirm_desc": {
    "es": "Vas a combinar **{n} {species}** adultas en **1 Neon**.\n\n"
          "⚠️ Las 4 mascotas se consumen (las ✨ Shiny no se usan).",
    "en": "You're about to fuse **{n} adult {species}** into **1 Neon**.\n\n"
          "⚠️ The 4 pets are consumed (✨ Shiny pets are not used)."},
"mv.btn_fuse": {"es": "Combinar en Neon", "en": "Fuse into Neon"},
"mv.neon_done": {"es": "✨ ¡Neon creado!", "en": "✨ Neon created!"},
"mv.neon_done_desc": {
    "es": "# {emoji} Neon {species}\nComienza en etapa **Reborn** — "
          "da el **doble** de recompensas.",
    "en": "# {emoji} Neon {species}\nStarts at **Reborn** stage — "
          "earns **double** rewards."},
"mv.battle_title": {"es": "⚔️ ¡Batalla!", "en": "⚔️ Battle!"},
"mv.pick_fighter": {"es": "Elige tu luchadora...", "en": "Pick your fighter..."},
"mv.battle_rest": {
    "es": "⏳ Tu {pet} está descansando — podrá pelear <t:{ts}:R>.",
    "en": "⏳ Your {pet} is resting — it can battle <t:{ts}:R>."},
"mv.battle_exploring": {
    "es": "🗺️ Tu {pet} está explorando.",
    "en": "🗺️ Your {pet} is out exploring."},
"mv.battle_fighting": {"es": "*Peleando...*", "en": "*Fighting...*"},
"mv.battle_win": {"es": "🏆 ¡Victoria!", "en": "🏆 Victory!"},
"mv.battle_win_desc": {
    "es": "Tu {e_pet} **{pet}** derrotó al {e_rival} **{rival}** salvaje.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**",
    "en": "Your {e_pet} **{pet}** defeated the wild {e_rival} **{rival}**.\n\n"
          "▫️ **+{xp} XP**\n▫️ **+{hearts} {heart}**"},
"mv.battle_lose": {"es": "💨 Derrota...", "en": "💨 Defeat..."},
"mv.battle_lose_desc": {
    "es": "El {e_rival} **{rival}** salvaje fue demasiado fuerte.\n\n"
          "▫️ **+{xp} XP** de consuelo\n"
          "*Podrás reintentarlo en {mins} min.*",
    "en": "The wild {e_rival} **{rival}** was too strong.\n\n"
          "▫️ **+{xp} XP** for trying\n"
          "*You can retry in {mins} min.*"},
"mv.missions_title": {"es": "📜 Misiones de Moonveil", "en": "📜 Moonveil Missions"},
"mv.mission_claimed": {"es": "✅ reclamada", "en": "✅ claimed"},
"mv.mission_ready": {"es": "🎁 ¡reclamable!", "en": "🎁 claimable!"},
"mv.pick_mission": {
    "es": "Reclama una misión cumplida...",
    "en": "Claim a completed mission..."},
"mv.mission_done": {
    "es": "🎁 ¡{name} reclamada! +{hearts} {heart}",
    "en": "🎁 {name} claimed! +{hearts} {heart}"},

# misiones internas de Moonveil (por id de config.MV_MISSIONS)
"mvm.explore1.name": {"es": "Primera expedición", "en": "First expedition"},
"mvm.explore1.desc": {
    "es": "Completa tu primera exploración.",
    "en": "Complete your first expedition."},
"mvm.explore5.name": {"es": "Explorador novato", "en": "Rookie explorer"},
"mvm.explore5.desc": {
    "es": "Completa 5 exploraciones.",
    "en": "Complete 5 expeditions."},
"mvm.explore15.name": {"es": "Explorador experto", "en": "Expert explorer"},
"mvm.explore15.desc": {
    "es": "Completa 15 exploraciones.",
    "en": "Complete 15 expeditions."},
"mvm.battle1.name": {"es": "Primera victoria", "en": "First victory"},
"mvm.battle1.desc": {
    "es": "Gana tu primera batalla.",
    "en": "Win your first battle."},
"mvm.battle5.name": {"es": "Guerrera", "en": "Warrior"},
"mvm.battle5.desc": {"es": "Gana 5 batallas.", "en": "Win 5 battles."},
"mvm.neon1.name": {"es": "Brillo Neón", "en": "Neon Glow"},
"mvm.neon1.desc": {
    "es": "Crea tu primera mascota Neon.",
    "en": "Create your first Neon pet."},
"mvm.pets5.name": {"es": "Coleccionista", "en": "Collector"},
"mvm.pets5.desc": {
    "es": "Ten 5 mascotas en tu colección.",
    "en": "Own 5 pets in your collection."},
"mvm.pets15.name": {"es": "Gran colección", "en": "Grand collection"},
"mvm.pets15.desc": {
    "es": "Ten 15 mascotas en tu colección.",
    "en": "Own 15 pets in your collection."},

# ---------- progresión ----------
"prog.ach_title": {"es": "🏆 Logros", "en": "🏆 Achievements"},
"prog.claimed": {"es": "reclamado", "en": "claimed"},
"prog.review": {"es": "en revisión por el staff", "en": "under staff review"},
"prog.claimable": {
    "es": "¡reclamable con `/claim-achievement`!",
    "en": "claimable with `/claim-achievement`!"},
"prog.progress": {"es": "progreso: {p}/{n}", "en": "progress: {p}/{n}"},
"prog.needs_proof": {
    "es": "requiere captura (`/claim-achievement`)",
    "en": "requires a screenshot (`/claim-achievement`)"},
"prog.reward_role": {"es": "rol **{name}**", "en": "role **{name}**"},
"prog.reward_special": {"es": "recompensa especial", "en": "special reward"},
"prog.ach_footer": {
    "es": "Completados: {done}/{total} • ✅ reclamado 🎁 reclamable "
          "⏳ revisión 🔒 progreso",
    "en": "Completed: {done}/{total} • ✅ claimed 🎁 claimable "
          "⏳ review 🔒 progress"},
"prog.mis_title": {"es": "📜 Misiones disponibles", "en": "📜 Available missions"},
"prog.mis_proof_review": {
    "es": "prueba en revisión por el staff",
    "en": "proof under staff review"},
"prog.mis_done": {"es": "completada", "en": "completed"},
"prog.mis_progress": {"es": "progreso {p}/{n}", "en": "progress {p}/{n}"},
"prog.mis_available": {"es": "disponible", "en": "available"},
"prog.mis_footer": {
    "es": "📸 Usa /claim-mision <misión> adjuntando la captura de tu objetivo",
    "en": "📸 Use /claim-mision <mission> attaching proof of your goal"},
"prog.not_found_ach": {"es": "❌ Logro no encontrado.", "en": "❌ Achievement not found."},
"prog.not_found_mis": {"es": "❌ Misión no encontrada.", "en": "❌ Mission not found."},
"prog.already_ach": {"es": "✅ Ya reclamaste este logro.", "en": "✅ You already claimed this achievement."},
"prog.pending_ach": {
    "es": "⏳ Ya tienes una solicitud pendiente para este logro.",
    "en": "⏳ You already have a pending request for this achievement."},
"prog.not_yet": {
    "es": "🔒 Aún no cumples el objetivo: **{p}/{n}**.",
    "en": "🔒 You haven't met the goal yet: **{p}/{n}**."},
"prog.ach_unlocked": {"es": "🏆 ¡Logro desbloqueado!", "en": "🏆 Achievement unlocked!"},
"prog.reward_label": {"es": "🎁 Recompensa:", "en": "🎁 Reward:"},
"prog.needs_capture": {
    "es": "📸 Este logro requiere adjuntar una **captura** del objetivo "
          "cumplido.\n*Vuelve a intentarlo con el parámetro `captura`.*",
    "en": "📸 This achievement requires a **screenshot** of the completed "
          "goal.\n*Try again with the `captura` parameter.*"},
"prog.needs_image": {
    "es": "📸 Debes adjuntar una **imagen** como prueba.",
    "en": "📸 You must attach an **image** as proof."},
"prog.mis_already": {
    "es": "✅ Ya completaste esta misión.",
    "en": "✅ You already completed this mission."},
"prog.mis_pending": {
    "es": "⏳ Ya tienes una prueba pendiente para esta misión.",
    "en": "⏳ You already have pending proof for this mission."},
"prog.no_channel": {
    "es": "❌ El canal de revisión no está configurado. Un administrador "
          "debe usar `/setup {cmd}`.",
    "en": "❌ The review channel isn't set up. An admin must use "
          "`/setup {cmd}`."},
"prog.proof_sent": {"es": "📨 ¡Prueba enviada!", "en": "📨 Proof sent!"},
"prog.proof_desc": {
    "es": "Tu reclamo de {label} ya está en manos del staff 🕵️\n\n"
          "Te llegará un mensaje cuando sea revisado.",
    "en": "Your claim for {label} is in the staff's hands 🕵️\n\n"
          "You'll get a message when it's reviewed."},

# ---------- tienda ----------
"shop.title": {"es": "🛒 Tienda de Hearts {heart}", "en": "🛒 Hearts Shop {heart}"},
"shop.desc": {
    "es": "*Usa `/buy [item]` para comprar cualquiera de los "
          "siguientes artículos:*",
    "en": "*Use `/buy [item]` to purchase any of these items:*"},
"shop.g_custom": {"es": "🎨 Rol Personalizado", "en": "🎨 Custom Role"},
"shop.g_colors": {"es": "🌈 Colores Exclusivos", "en": "🌈 Exclusive Colors"},
"shop.g_vip": {"es": "💎 Acceso VIP / Exclusivo", "en": "💎 VIP / Exclusive Access"},
"shop.g_channel": {"es": "🔒 Canal Privado Temporal", "en": "🔒 Temporary Private Channel"},
"shop.g_chests": {"es": "🎁 Cofres Misteriosos", "en": "🎁 Mystery Chests"},
"shop.footer": {
    "es": "{bot} • Las compras requieren aprobación del staff ⏳",
    "en": "{bot} • Purchases require staff approval ⏳"},
"shop.not_found": {
    "es": "❌ Ese artículo no existe. Usa `/shop` para ver el catálogo.",
    "en": "❌ That item doesn't exist. Use `/shop` to see the catalog."},
"shop.faltan": {"es": "💔 Te faltan Hearts", "en": "💔 Not enough Hearts"},
"shop.faltan_desc": {
    "es": "**{emoji} {name}** cuesta **{price} {heart}**\n"
          "Tu saldo: **{have} {heart}**",
    "en": "**{emoji} {name}** costs **{price} {heart}**\n"
          "Your balance: **{have} {heart}**"},
"shop.pending": {
    "es": "⏳ Ya tienes una solicitud pendiente para este artículo.\n"
          "*Espera a que el staff la revise.*",
    "en": "⏳ You already have a pending request for this item.\n"
          "*Wait for the staff to review it.*"},
"shop.has_role": {
    "es": "❌ Ya tienes un rol personalizado activo.",
    "en": "❌ You already have an active custom role."},
"shop.has_color": {
    "es": "❌ Ya tienes el color **{name}**.",
    "en": "❌ You already own the **{name}** color."},
"shop.has_vip": {"es": "❌ Ya tienes el rol VIP.", "en": "❌ You already have the VIP role."},
"shop.has_channel": {
    "es": "❌ Ya tienes un canal privado activo.",
    "en": "❌ You already have an active private channel."},
"shop.bad_color": {
    "es": "❌ Color inválido. Usa formato hexadecimal de 6 dígitos "
          "(ej: `FF5733`). No se envió ninguna solicitud.",
    "en": "❌ Invalid color. Use a 6-digit hex format "
          "(e.g. `FF5733`). No request was sent."},
"shop.modal_title": {"es": "Tu Rol Personalizado", "en": "Your Custom Role"},
"shop.modal_name": {"es": "Nombre del rol", "en": "Role name"},
"shop.modal_color": {"es": "Color en hexadecimal", "en": "Hex color"},
"shop.no_channel": {
    "es": "❌ El canal de compras no está configurado. Un administrador debe "
          "usar `/setup canal-compras`.",
    "en": "❌ The purchase channel isn't set up. An admin must use "
          "`/setup canal-compras`."},
"shop.sent": {"es": "📨 ¡Solicitud enviada!", "en": "📨 Request sent!"},
"shop.sent_desc": {
    "es": "{emoji} **{name}** — {price} {heart}\n\n"
          "Tu compra está en revisión por el staff ⏳\n"
          "*Los Hearts se descuentan solo si se aprueba.*",
    "en": "{emoji} **{name}** — {price} {heart}\n\n"
          "Your purchase is under staff review ⏳\n"
          "*Hearts are only deducted if approved.*"},
"shop.done": {"es": "🎉 ¡Compra realizada! {emoji}", "en": "🎉 Purchase complete! {emoji}"},
"shop.no_funds": {"es": "❌ Saldo insuficiente.", "en": "❌ Insufficient balance."},

# ---------- revisión (DM al usuario) ----------
"rev.approved": {
    "es": "🎉 ¡Tu solicitud fue aprobada!",
    "en": "🎉 Your request was approved!"},
"rev.rejected": {"es": "❌ Solicitud rechazada", "en": "❌ Request rejected"},
"rev.rejected_detail": {
    "es": "Solicitud rechazada por el staff.",
    "en": "Request rejected by the staff."},
"rev.role_fail": {
    "es": "No pude asignar el rol **{role}**: mi rol debe estar por encima "
          "en la jerarquía.",
    "en": "Couldn't assign role **{role}**: my role must be above it in "
          "the hierarchy."},
"rev.custom_ok": {"es": "Rol {role} creado y asignado.",
                  "en": "Role {role} created and assigned."},
"rev.custom_fail": {
    "es": "No tengo permiso de **Manage Roles** para crear el rol.",
    "en": "I don't have **Manage Roles** permission to create the role."},
"rev.color_fail": {
    "es": "No pude crear el rol de color (permiso **Manage Roles**).",
    "en": "Couldn't create the color role (**Manage Roles** permission)."},
"rev.color_ok": {"es": "Rol de color {role} asignado.",
                 "en": "Color role {role} assigned."},
"rev.vip_fail": {
    "es": "No pude crear el rol VIP (permiso **Manage Roles**).",
    "en": "Couldn't create the VIP role (**Manage Roles** permission)."},
"rev.vip_ok": {"es": "Rol {role} asignado. ¡Bienvenido al VIP!",
               "en": "Role {role} assigned. Welcome to VIP!"},
"rev.channel_fail": {
    "es": "No tengo permiso de **Manage Channels**.",
    "en": "I don't have **Manage Channels** permission."},
"rev.channel_ok": {
    "es": "Canal {channel} creado — se borra en {hours}h.",
    "en": "Channel {channel} created — it'll be deleted in {hours}h."},
"rev.chest": {
    "es": "🎁 El cofre contenía **{reward} {heart}** (pagó {price}).",
    "en": "🎁 The chest contained **{reward} {heart}** (paid {price})."},
"rev.unknown_item": {"es": "Tipo de item desconocido.", "en": "Unknown item type."},
"rev.item_gone": {"es": "Item de tienda no encontrado.", "en": "Shop item not found."},
"rev.no_funds": {
    "es": "Saldo insuficiente: necesita {price} {heart}.",
    "en": "Insufficient balance: needs {price} {heart}."},
"rev.mis_gone": {"es": "Misión no encontrada.", "en": "Mission not found."},
"rev.mis_done": {
    "es": "Misión **{name}** completada: +{hearts} {heart}",
    "en": "Mission **{name}** completed: +{hearts} {heart}"},
"rev.mis_progress": {
    "es": "Prueba aceptada para **{name}** ({p}/{n}).",
    "en": "Proof accepted for **{name}** ({p}/{n})."},
"rev.ach_gone": {"es": "Logro no encontrado.", "en": "Achievement not found."},
"rev.ach_done": {
    "es": "Logro **{name}** desbloqueado: {detail}.",
    "en": "Achievement **{name}** unlocked: {detail}."},
"rev.unknown_kind": {"es": "Tipo de solicitud desconocido.", "en": "Unknown request type."},
"rev.role_missing": {"es": "⚠️ rol configurado no encontrado", "en": "⚠️ configured role not found"},
"rev.role_perm": {"es": "⚠️ no pude crear el rol (permiso Manage Roles)", "en": "⚠️ couldn't create the role (Manage Roles permission)"},
"rev.role_part": {"es": "rol {role}", "en": "role {role}"},
"rev.delivered": {"es": "recompensa entregada", "en": "reward delivered"},
"mv.adopt_another": {"es": "Adoptar otro", "en": "Adopt another"},
"mv.menu_desc": {
    "es": "*Un mini Adopt Me dentro del servidor*\n\n"
          "🥚 **Adoptar** — abre huevos y consigue mascotas\n"
          "🐾 **Mis mascotas** — mira tu colección y su etapa\n"
          "🗺️ **Explorar** — expediciones de {mins} min que traen XP y Hearts\n"
          "✨ **Neon** — combina 4 adultas iguales en una Neon\n"
          "⚔️ **Batalla** — pelea contra salvajes por XP y Hearts\n"
          "📜 **Misiones** — objetivos con recompensas",
    "en": "*A mini Adopt Me inside the server*\n\n"
          "🥚 **Adopt** — hatch eggs and collect pets\n"
          "🐾 **My pets** — check your collection and their stage\n"
          "🗺️ **Explore** — {mins}-min expeditions that earn XP and Hearts\n"
          "✨ **Neon** — fuse 4 identical adults into a Neon\n"
          "⚔️ **Battle** — fight wild pets for XP and Hearts\n"
          "📜 **Missions** — goals with rewards"},
"mv.shiny_tag": {"es": " ✨Shiny", "en": " ✨Shiny"},
"mv.pet_gone": {"es": "Esa mascota ya no existe.", "en": "That pet no longer exists."},
"mv.egg_menu": {"es": "Elige un huevo...", "en": "Pick an egg..."},
"mv.hatch_desc": {
    "es": "# {emoji} {species}{shiny}\n{rarity} • Ahora es parte de tu colección 🐾",
    "en": "# {emoji} {species}{shiny}\n{rarity} • It's now part of your collection 🐾"},

# ---------- bienvenida ----------
"welcome.title": {"es": "🌙 ¡Bienvenida/o a {guild}!", "en": "🌙 Welcome to {guild}!"},
"welcome.desc": {
    "es": "¡Hola {user}! 🎉\n\nYa somos **{n}** miembros.\n"
          "Usa `/jugar` para adoptar tu primera mascota en **Moonveil** 🐣 "
          "y `/daily` para tus Hearts diarios 💕",
    "en": "Hi {user}! 🎉\n\nWe're now **{n}** members.\n"
          "Use `/jugar` to adopt your first pet in **Moonveil** 🐣 "
          "and `/daily` for your daily Hearts 💕"},

})



# ==========================================================================
# NUEVAS FEATURES: moderación, social, pesca, boss, multi-staff
# ==========================================================================

STRINGS.update({

# ---------- moderación ----------
"mod.no_perms": {
    "es": "❌ No tienes permisos para usar este comando.",
    "en": "❌ You don't have permission to use this command."},
"mod.cant_target_self": {
    "es": "❌ No puedes usar este comando contigo mismo.",
    "en": "❌ You can't use this command on yourself."},
"mod.cant_target_bot": {
    "es": "❌ No puedo aplicar esta acción (permisos o jerarquía).",
    "en": "❌ I can't apply this action (permissions or role hierarchy)."},
"mod.warn_done": {
    "es": "⚠️ {user} ha sido advertido.\n**Razón:** {reason}\n"
          "**Advertencias totales:** {count}",
    "en": "⚠️ {user} has been warned.\n**Reason:** {reason}\n"
          "**Total warnings:** {count}"},
"mod.warns_title": {
    "es": "⚠️ Advertencias de {user}", "en": "⚠️ Warnings for {user}"},
"mod.warns_empty": {
    "es": "Este usuario no tiene advertencias. ✅",
    "en": "This user has no warnings. ✅"},
"mod.warns_entry": {
    "es": "**#{id}** — {reason}\nPor {mod} • {date}",
    "en": "**#{id}** — {reason}\nBy {mod} • {date}"},
"mod.warns_cleared": {
    "es": "✅ Advertencias de {user} eliminadas.",
    "en": "✅ Warnings for {user} cleared."},
"mod.mute_done": {
    "es": "🔇 {user} ha sido silenciado por {minutes} minutos.\n"
          "**Razón:** {reason}",
    "en": "🔇 {user} has been timed out for {minutes} minutes.\n"
          "**Reason:** {reason}"},
"mod.mute_failed": {
    "es": "❌ No pude silenciar a ese usuario (jerarquía de roles).",
    "en": "❌ Couldn't time out that user (role hierarchy)."},
"mod.kick_done": {
    "es": "👢 {user} ha sido expulsado.\n**Razón:** {reason}",
    "en": "👢 {user} has been kicked.\n**Reason:** {reason}"},
"mod.kick_failed": {
    "es": "❌ No pude expulsar a ese usuario (jerarquía de roles).",
    "en": "❌ Couldn't kick that user (role hierarchy)."},
"mod.ban_done": {
    "es": "🔨 {user} ha sido baneado.\n**Razón:** {reason}",
    "en": "🔨 {user} has been banned.\n**Reason:** {reason}"},
"mod.ban_failed": {
    "es": "❌ No pude banear a ese usuario (jerarquía de roles).",
    "en": "❌ Couldn't ban that user (role hierarchy)."},
"mod.purge_done": {
    "es": "🧹 {n} mensajes eliminados.",
    "en": "🧹 {n} messages deleted."},
"mod.purge_fail": {
    "es": "❌ No pude borrar mensajes (permiso Manage Messages).",
    "en": "❌ Couldn't delete messages (Manage Messages permission)."},

# ---------- automod ----------
"automod.badword": {
    "es": "⚠️ {user}, ese mensaje contiene lenguaje no permitido.",
    "en": "⚠️ {user}, that message contains disallowed language."},
"automod.link": {
    "es": "⚠️ {user}, los enlaces no están permitidos aquí.",
    "en": "⚠️ {user}, links aren't allowed here."},
"automod.spam": {
    "es": "🔇 {user} fue silenciado {minutes} min por spam.",
    "en": "🔇 {user} was timed out {minutes} min for spam."},
"automod.caps": {
    "es": "⚠️ {user}, por favor no uses tantas mayúsculas.",
    "en": "⚠️ {user}, please don't use so many caps."},

# ---------- confesiones ----------
"conf.title": {
    "es": "🕊️ Confesión #{n}", "en": "🕊️ Confession #{n}"},
"conf.footer": {
    "es": "Escríbela aquí y el bot la publica anónima",
    "en": "Write it here and the bot posts it anonymously"},
"conf.too_long": {
    "es": "❌ La confesión es demasiado larga (máx 1500 caracteres).",
    "en": "❌ Confession too long (max 1500 characters)."},

# ---------- cumpleaños ----------
"cumple.set": {
    "es": "🎂 Tu cumpleaños quedó registrado: **{day}/{month}**.\n"
          "¡Ese día te felicitaremos! 🎉",
    "en": "🎂 Your birthday was saved: **{month}/{day}**.\n"
          "We'll celebrate you that day! 🎉"},
"cumple.invalid": {
    "es": "❌ Fecha inválida. Usa: `/cumple mes día` (ej: `/cumple 3 15`).",
    "en": "❌ Invalid date. Use: `/cumple month day` (e.g. `/cumple 3 15`)."},
"cumple.announce": {
    "es": "🎂🎉 ¡Hoy es el cumpleaños de {users}! ¡Felicidades! 🥳",
    "en": "🎂🎉 Today is {users}'s birthday! Happy birthday! 🥳"},
"cumple.next": {
    "es": "🎂 Próximos cumpleaños", "en": "🎂 Upcoming birthdays"},
"cumple.list_empty": {
    "es": "Nadie ha registrado su cumpleaños aún. Usa `/cumple`.",
    "en": "Nobody registered a birthday yet. Use `/cumple`."},

# ---------- QOTD ----------
"qotd.title": {"es": "💬 Pregunta del día", "en": "💬 Question of the day"},
"qotd.footer": {
    "es": "¡Responde abajo y comparte tu opinión! 👇",
    "en": "Reply below and share your thoughts! 👇"},

# ---------- AFK ----------
"afk.set": {
    "es": "😴 {user} ahora está AFK{reason}",
    "en": "😴 {user} is now AFK{reason}"},
"afk.back": {
    "es": "👋 ¡Bienvenido de vuelta, {user}! Ya no estás AFK.",
    "en": "👋 Welcome back, {user}! You're no longer AFK."},
"afk.mention": {
    "es": "😴 **{user}** está AFK{reason} (desde hace {time})",
    "en": "😴 **{user}** is AFK{reason} (for {time} now)"},
"afk.reason_fmt": {"es": ": {r}", "en": ": {r}"},

# ---------- comandos personalizados ----------
"ccmd.added": {
    "es": "✅ Comando `!{name}` creado.",
    "en": "✅ Command `!{name}` created."},
"ccmd.removed": {
    "es": "✅ Comando `!{name}` eliminado.",
    "en": "✅ Command `!{name}` removed."},
"ccmd.not_found": {
    "es": "❌ No existe el comando `!{name}`.",
    "en": "❌ Command `!{name}` doesn't exist."},
"ccmd.list_title": {
    "es": "📜 Comandos personalizados", "en": "📜 Custom commands"},
"ccmd.list_empty": {
    "es": "No hay comandos personalizados aún.",
    "en": "No custom commands yet."},
"ccmd.name_invalid": {
    "es": "❌ Nombre inválido (solo letras, números y `-_`, máx 30).",
    "en": "❌ Invalid name (letters, numbers, `-_` only, max 30)."},

# ---------- evento / recordatorio de server ----------
"event.created": {
    "es": "📅 Evento programado: **{text}**\n"
          "Se anunciará en {channel} {time}.",
    "en": "📅 Event scheduled: **{text}**\n"
          "It will be announced in {channel} {time}."},
"event.invalid_time": {
    "es": "❌ Tiempo inválido. Usa formato como `10m`, `2h`, `3d`.",
    "en": "❌ Invalid time. Use formats like `10m`, `2h`, `3d`."},
"event.announce": {
    "es": "📅 **Recordatorio de evento**\n{text}",
    "en": "📅 **Event reminder**\n{text}"},

# ---------- pescar ----------
"fish.cooldown": {
    "es": "⏳ Ya pescaste hace poco. Vuelve en **{time}**.",
    "en": "⏳ You fished recently. Come back in **{time}**."},
"fish.casting": {
    "es": "🎣 Lanzando la caña...", "en": "🎣 Casting the line..."},
"fish.bite": {
    "es": "🎣 ¡Algo picó!", "en": "🎣 Something's biting!"},
"fish.caught": {
    "es": "# 🎣 ¡Pescaste: {name}!\n+{hearts} 💕",
    "en": "# 🎣 You caught: {name}!\n+{hearts} 💕"},
"fish.nothing": {
    "es": "# 🎣 {name}\n+{hearts} 💕",
    "en": "# 🎣 {name}\n+{hearts} 💕"},

# ---------- boss semanal ----------
"boss.title": {"es": "👹 Boss Semanal: {name}",
               "en": "👹 Weekly Boss: {name}"},
"boss.status": {
    "es": "**HP:** {hp} / {max_hp}\n"
          "¡Gana batallas en `/jugar` → Batalla para dañarlo!",
    "en": "**HP:** {hp} / {max_hp}\n"
          "Win battles in `/jugar` → Battle to damage it!"},
"boss.damaged": {
    "es": "👹 Golpeaste al boss por **{damage}** de daño "
          "({hp}/{max_hp} HP restante)",
    "en": "👹 You hit the boss for **{damage}** damage "
          "({hp}/{max_hp} HP left)"},
"boss.dead": {
    "es": "# 🎉 ¡El boss **{name}** ha sido derrotado!\n"
          "El pozo de **{pool}** 💕 fue repartido entre {n} guerreros.",
    "en": "# 🎉 The boss **{name}** has been defeated!\n"
          "The pool of **{pool}** 💕 was shared between {n} warriors."},
"boss.no_active": {
    "es": "No hay boss activo esta semana aún.",
    "en": "There's no active boss this week yet."},
"boss.log_spawn": {
    "es": "👹 Boss semanal creado: {name} ({hp} HP)",
    "en": "👹 Weekly boss spawned: {name} ({hp} HP)"},

# ---------- racha login Moonveil ----------
"mv.login_streak": {
    "es": "🔥 Racha Moonveil: **{days} día(s)** · +{hearts} 💕",
    "en": "🔥 Moonveil streak: **{days} day(s)** · +{hearts} 💕"},

# ---------- top mascotas ----------
"top.pets_title": {
    "es": "🏆 Top Mascotas del servidor", "en": "🏆 Server Top Pets"},
"top.pets_empty": {
    "es": "Aún nadie tiene mascotas. Usa `/jugar` para adoptar.",
    "en": "Nobody has pets yet. Use `/jugar` to adopt."},
"top.pets_entry": {
    "es": "{rank}. {emoji} **{species}**{shiny} — {user}\n"
          "    Etapa {stage} · {xp} XP",
    "en": "{rank}. {emoji} **{species}**{shiny} — {user}\n"
          "    Stage {stage} · {xp} XP"},

# ---------- trades ----------
"trade.title": {
    "es": "🔄 Trade en Adopt Me", "en": "🔄 Adopt Me trade"},
"rev.trade_done": {
    "es": "Trade aprobado — +{hearts} {heart}",
    "en": "Trade approved — +{hearts} {heart}"},

# ---------- setup multi-staff ----------
"setup.staff_added": {
    "es": "✅ Rol staff añadido: {role}",
    "en": "✅ Staff role added: {role}"},
"setup.staff_removed": {
    "es": "✅ Rol staff eliminado: {role}",
    "en": "✅ Staff role removed: {role}"},
"setup.staff_roles": {"es": "Roles staff", "en": "Staff roles"},
"setup.staff_none": {"es": "Ninguno", "en": "None"},
"setup.confession_set": {
    "es": "✅ Canal de confesiones: {channel}",
    "en": "✅ Confession channel: {channel}"},
"setup.qotd_set": {
    "es": "✅ Canal de QOTD: {channel}",
    "en": "✅ QOTD channel: {channel}"},

})
