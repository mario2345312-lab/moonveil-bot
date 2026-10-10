"""Mini-juegos con animación: /flip /dice /slots /rps /guess."""

import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from i18n import t, user_lang

SLOT_SYMBOLS = ["🌸", "💕", "⭐", "🍀", "💎", "🌙"]
DICE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
ROULETTE_REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30,
                 32, 34, 36}
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]


def _card_value(rank: str) -> int:
    if rank == "A":
        return 11
    return 10 if rank in ("J", "Q", "K") else int(rank)


def _hand_value(cards: list[str]) -> int:
    total = sum(_card_value(c.split()[0]) for c in cards)
    aces = sum(1 for c in cards if c.startswith("A "))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def _new_card() -> str:
    rank = random.choice(["A"] + [str(n) for n in range(2, 11)]
                         + ["J", "Q", "K"])
    return f"{rank} {random.choice(CARD_SUITS)}"


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- helpers ----------

    async def _check_bet(self, interaction: discord.Interaction,
                         apuesta: int) -> bool:
        """La interacción ya debe estar deferida."""
        lang = await user_lang(self.bot, interaction)
        if apuesta < config.FLIP_MIN_BET:
            await interaction.followup.send(
                t(lang, "common.min_bet", min=config.FLIP_MIN_BET,
                  heart=config.HEART), ephemeral=True)
            return False
        u = await self.bot.db.get_user(interaction.guild.id,
                                       interaction.user.id)
        if u["hearts"] < apuesta:
            await interaction.followup.send(
                t(lang, "common.no_hearts", hearts=u["hearts"]),
                ephemeral=True)
            return False
        return True

    async def _result_embed(self, interaction, titulo, descripcion, color):
        nuevo = await self.bot.db.get_user(interaction.guild.id,
                                           interaction.user.id)
        lang = await user_lang(self.bot, interaction)
        embed = discord.Embed(title=titulo, description=descripcion,
                              color=color)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        embed.set_footer(
            text=t(lang, "common.new_balance", hearts=nuevo["hearts"],
                   heart=config.HEART))
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def _animate(self, interaction: discord.Interaction,
                       frames: list[str], delay: float = 0.8):
        """Edita la respuesta deferida con el primer frame y los siguientes.
        La interacción ya debe estar deferida."""
        await interaction.edit_original_response(
            embed=discord.Embed(description=frames[0],
                                color=config.EMBED_COLOR))
        for frame in frames[1:]:
            await asyncio.sleep(delay)
            await interaction.edit_original_response(
                embed=discord.Embed(description=frame,
                                    color=config.EMBED_COLOR))

    # ---------- /flip ----------

    @app_commands.command(
        name="flip",
        description="Apuesta tus Hearts lanzando una moneda (cara o cruz).")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar",
                           eleccion="Cara o cruz")
    @app_commands.choices(eleccion=[
        app_commands.Choice(name="Cara 🪙", value="cara"),
        app_commands.Choice(name="Cruz ❌", value="cruz"),
    ])
    @app_commands.guild_only()
    async def flip(self, interaction: discord.Interaction, apuesta: int,
                   eleccion: app_commands.Choice[str]):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        resultado = random.choice(["cara", "cruz"])
        ganaste = resultado == eleccion.value
        emoji_resultado = "🪙" if resultado == "cara" else "❌"
        lado = t(lang, f"games.coin_{resultado}")

        await db.bump_stat(guild_id, user_id, "flips_played")
        if ganaste:
            await db.add_hearts(guild_id, user_id, apuesta)
            await db.bump_stat(guild_id, user_id, "flips_won")
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.flip_lucky")
            detalle = f"**+{apuesta} {config.HEART}**"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_ERROR, t(lang, "games.flip_unlucky")
            detalle = f"**-{apuesta} {config.HEART}**"

        await self._animate(interaction, [
            t(lang, "games.flipping"),
            t(lang, "games.spinning", a=t(lang, "games.coin_cara"),
              b=t(lang, "games.coin_cruz")),
            t(lang, "games.landed"),
        ])
        embed = await self._result_embed(
            interaction, titulo,
            f"# {lado} {emoji_resultado}\n"
            f"{t(lang, 'games.your_choice', c=eleccion.name)}\n\n{detalle}",
            color)
        await interaction.edit_original_response(embed=embed)

    # ---------- /dice ----------

    @app_commands.command(
        name="dice",
        description="Apuesta tus Hearts al número del dado (1-6). Gana x4.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar",
                           numero="Número del dado (1-6)")
    @app_commands.guild_only()
    async def dice(self, interaction: discord.Interaction, apuesta: int,
                   numero: app_commands.Range[int, 1, 6]):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        resultado = random.randint(1, 6)
        ganaste = resultado == numero

        if ganaste:
            premio = apuesta * 4
            await db.add_hearts(guild_id, user_id, premio)
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.dice_exact")
            detalle = f"**+{premio} {config.HEART}** (x4)"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_ERROR, t(lang, "games.dice_no")
            detalle = f"**-{apuesta} {config.HEART}**"

        frames = [t(lang, "games.dice_roll"),
                  f"🎲 {random.choice(DICE_FACES)}",
                  f"🎲 {random.choice(DICE_FACES)}",
                  f"🎲 {random.choice(DICE_FACES)}"]
        await self._animate(interaction, frames)
        embed = await self._result_embed(
            interaction, titulo,
            f"# {DICE_FACES[resultado - 1]} {resultado}\n"
            f"{t(lang, 'games.dice_result', n=resultado, m=numero)}\n\n"
            f"{detalle}", color)
        await interaction.edit_original_response(embed=embed)

    # ---------- /slots ----------

    @app_commands.command(
        name="slots",
        description="Tragamonedas de Hearts: 3 iguales x10, 2 iguales x2.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar")
    @app_commands.guild_only()
    async def slots(self, interaction: discord.Interaction, apuesta: int):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        iguales = len(set(reels))

        if iguales == 1:
            premio = apuesta * 9
            await db.add_hearts(guild_id, user_id, premio)
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.jackpot")
            detalle = f"**+{premio} {config.HEART}** (x10)"
        elif iguales == 2:
            await db.add_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.pair")
            detalle = f"**+{apuesta} {config.HEART}** (x2)"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_ERROR, t(lang, "games.slots_none")
            detalle = f"**-{apuesta} {config.HEART}**"

        def rand_reels():
            return " ".join(random.choice(SLOT_SYMBOLS) for _ in range(3))

        spin = t(lang, "games.spinning_reels")
        await self._animate(interaction, [
            f"🎰 **{rand_reels()}**\n{spin}",
            f"🎰 **{rand_reels()}**\n{spin}",
            f"🎰 **{reels[0]} ⬛ ⬛**\n{t(lang, 'games.reel1')}",
            f"🎰 **{reels[0]} {reels[1]} ⬛**\n{t(lang, 'games.reel2')}",
            f"🎰 **{reels[0]} {reels[1]} {reels[2]}**\n"
            f"{t(lang, 'games.reel3')}",
        ], delay=0.9)
        embed = await self._result_embed(
            interaction, titulo,
            f"# {' '.join(reels)}\n\n{detalle}",
            color)
        await interaction.edit_original_response(embed=embed)

    # ---------- /rps ----------

    @app_commands.command(
        name="rps",
        description="Piedra, papel o tijera contra el bot. Gana x2.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar",
                           eleccion="Tu jugada")
    @app_commands.choices(eleccion=[
        app_commands.Choice(name="Piedra 🪨", value="piedra"),
        app_commands.Choice(name="Papel 📄", value="papel"),
        app_commands.Choice(name="Tijera ✂️", value="tijera"),
    ])
    @app_commands.guild_only()
    async def rps(self, interaction: discord.Interaction, apuesta: int,
                  eleccion: app_commands.Choice[str]):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        jugada_bot = random.choice(["piedra", "papel", "tijera"])
        emojis = {"piedra": "🪨", "papel": "📄", "tijera": "✂️"}
        nombres = {"piedra": {"es": "Piedra", "en": "Rock"}[lang],
                   "papel": {"es": "Papel", "en": "Paper"}[lang],
                   "tijera": {"es": "Tijera", "en": "Scissors"}[lang]}
        gana_a = {"piedra": "tijera", "papel": "piedra", "tijera": "papel"}

        if jugada_bot == eleccion.value:
            color, titulo = config.COLOR_WARNING, t(lang, "games.tie")
            detalle = t(lang, "games.tie_desc")
        elif gana_a[eleccion.value] == jugada_bot:
            await db.add_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.won")
            detalle = f"**+{apuesta} {config.HEART}**"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_ERROR, t(lang, "games.bot_wins")
            detalle = f"**-{apuesta} {config.HEART}**"

        await self._animate(interaction, [
            t(lang, "games.rps_1"),
            t(lang, "games.rps_2"),
            t(lang, "games.rps_3"),
            f"💥 **{t(lang, 'games.rps_go')}**",
        ], delay=0.7)
        embed = await self._result_embed(
            interaction, titulo,
            f"{t(lang, 'games.you')}: {emojis[eleccion.value]} "
            f"**{nombres[eleccion.value]}**\n"
            f"{t(lang, 'games.bot')}: {emojis[jugada_bot]} "
            f"**{nombres[jugada_bot]}**\n\n{detalle}",
            color)
        await interaction.edit_original_response(embed=embed)

    # ---------- /guess ----------

    @app_commands.command(
        name="guess",
        description="Adivina el número del 1 al 10. Gana x8.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar",
                           numero="Tu número (1-10)")
    @app_commands.guild_only()
    async def guess(self, interaction: discord.Interaction, apuesta: int,
                    numero: app_commands.Range[int, 1, 10]):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        resultado = random.randint(1, 10)
        ganaste = resultado == numero

        if ganaste:
            premio = apuesta * 7
            await db.add_hearts(guild_id, user_id, premio)
            color, titulo = config.COLOR_SUCCESS, t(lang, "games.guess_yes")
            detalle = f"**+{premio} {config.HEART}** (x8)"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            color, titulo = config.COLOR_ERROR, t(lang, "games.guess_no")
            detalle = f"**-{apuesta} {config.HEART}**"

        await self._animate(interaction, [
            t(lang, "games.guess_thinking"),
            t(lang, "games.guess_almost", n=random.randint(1, 10)),
            t(lang, "games.guess_almost", n=random.randint(1, 10)),
        ])
        embed = await self._result_embed(
            interaction, titulo,
            t(lang, "games.guess_result", n=resultado, m=numero)
            + f"\n\n{detalle}",
            color)
        await interaction.edit_original_response(embed=embed)


    # ---------- /blackjack ----------

    def _bj_embed(self, interaction, player, dealer, hide, lang="es",
                  note=None):
        pv = _hand_value(player)
        d_txt = "🂠 ?" if hide else f"{' • '.join(dealer)} (**{_hand_value(dealer)}**)"
        desc = (f"**{t(lang, 'games.bj_your_hand')}:** "
                f"{' • '.join(player)} (**{pv}**)\n"
                f"**{t(lang, 'games.bj_dealer')}:** {d_txt}")
        if note:
            desc += f"\n\n{note}"
        embed = discord.Embed(title="🃏 Blackjack", description=desc,
                              color=config.EMBED_COLOR)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        return embed

    @app_commands.command(
        name="blackjack",
        description="Juega 21 contra el dealer. Blackjack paga x2.5.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar")
    @app_commands.guild_only()
    async def blackjack(self, interaction: discord.Interaction, apuesta: int):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if not await self._check_bet(interaction, apuesta):
            return

        await db.spend_hearts(guild_id, user_id, apuesta)
        player, dealer = [_new_card(), _new_card()], [_new_card(), _new_card()]
        view = BlackjackView(self, interaction, apuesta, player, dealer, lang)
        await interaction.followup.send(
            embed=self._bj_embed(interaction, player, dealer, hide=True,
                                 lang=lang),
            view=view)
        view.message = await interaction.original_response()

    async def _bj_settle(self, interaction, apuesta, player, dealer, outcome,
                         lang="es"):
        db = self.bot.db
        gid, uid = interaction.guild.id, interaction.user.id
        if outcome == "blackjack":
            await db.add_hearts(gid, uid, int(apuesta * 2.5))
        elif outcome == "win":
            await db.add_hearts(gid, uid, apuesta * 2)
        elif outcome == "push":
            await db.add_hearts(gid, uid, apuesta)
        textos = {
            "blackjack": (t(lang, "games.bj_blackjack"), config.COLOR_SUCCESS,
                          f"+{int(apuesta * 2.5)} {config.HEART}"),
            "win": (t(lang, "games.won"), config.COLOR_SUCCESS,
                    f"+{apuesta} {config.HEART}"),
            "push": (t(lang, "games.bj_push"), config.COLOR_WARNING,
                     t(lang, "games.bj_push_desc")),
            "lose": (t(lang, "games.bj_dealer_wins"), config.COLOR_ERROR,
                     f"-{apuesta} {config.HEART}"),
            "bust": (t(lang, "games.bj_bust"), config.COLOR_ERROR,
                     f"-{apuesta} {config.HEART}"),
        }
        title_, color, detalle = textos[outcome]
        embed = await self._result_embed(
            interaction, title_,
            f"**{t(lang, 'games.bj_your_hand')}:** {' • '.join(player)} "
            f"(**{_hand_value(player)}**)\n"
            f"**{t(lang, 'games.bj_dealer')}:** {' • '.join(dealer)} "
            f"(**{_hand_value(dealer)}**)\n\n"
            f"{detalle}", color)
        await interaction.edit_original_response(embed=embed, view=None)

    # ---------- /ruleta ----------

    @app_commands.command(
        name="ruleta",
        description="Ruleta: color x2, número exacto x30.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar",
                           jugada="A qué le apuestas",
                           numero="Número exacto (solo si jugada=numero)")
    @app_commands.choices(jugada=[
        app_commands.Choice(name="🔴 Rojo", value="rojo"),
        app_commands.Choice(name="⚫ Negro", value="negro"),
        app_commands.Choice(name="🟢 Verde (0)", value="verde"),
        app_commands.Choice(name="🔢 Número exacto", value="numero"),
    ])
    @app_commands.guild_only()
    async def ruleta(self, interaction: discord.Interaction, apuesta: int,
                     jugada: app_commands.Choice[str],
                     numero: app_commands.Range[int, 0, 36] | None = None):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        if jugada.value == "numero" and numero is None:
            return await interaction.followup.send(
                t(lang, "games.roulette_need_number"), ephemeral=True)
        if not await self._check_bet(interaction, apuesta):
            return

        resultado = random.randint(0, 36)
        color_res = ("verde" if resultado == 0
                     else "rojo" if resultado in ROULETTE_REDS else "negro")

        if jugada.value == "numero":
            ganaste = resultado == numero
            premio = apuesta * 30
        else:
            ganaste = color_res == jugada.value
            premio = apuesta * 2

        if ganaste:
            await db.add_hearts(guild_id, user_id, premio)
            titulo, color = t(lang, "games.roulette_win"), config.COLOR_SUCCESS
            detalle = f"**+{premio} {config.HEART}**"
        else:
            await db.spend_hearts(guild_id, user_id, apuesta)
            titulo, color = t(lang, "games.roulette_lose"), config.COLOR_ERROR
            detalle = f"**-{apuesta} {config.HEART}**"

        iconos = {"rojo": "🔴", "negro": "⚫", "verde": "🟢"}
        await self._animate(interaction, [
            t(lang, "games.roulette_1"),
            t(lang, "games.roulette_2"),
            t(lang, "games.roulette_3"),
            t(lang, "games.roulette_4"),
        ])
        embed = await self._result_embed(
            interaction, titulo,
            f"# {iconos[color_res]} {resultado}\n"
            f"{t(lang, 'games.your_bet')}: **{jugada.name}"
            f"{f' {numero}' if numero is not None else ''}**\n\n{detalle}",
            color)
        await interaction.edit_original_response(embed=embed)

    # ---------- /trivia ----------

    @app_commands.command(
        name="trivia",
        description="Pregunta de Adopt Me — acierta y gana x2.")
    @app_commands.describe(apuesta="Cantidad de Hearts a apostar")
    @app_commands.guild_only()
    async def trivia(self, interaction: discord.Interaction, apuesta: int):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        if not await self._check_bet(interaction, apuesta):
            return

        q = random.choice(config.TRIVIA)
        opciones = q["o"]
        letras = ["🇦", "🇧", "🇨", "🇩"]
        desc = f"### {q['q']}\n\n" + "\n".join(
            f"{letras[i]} {op}" for i, op in enumerate(opciones))
        embed = discord.Embed(
            title=t(lang, "games.trivia_title"),
            description=desc + f"\n\n{t(lang, 'games.trivia_time')}",
            color=config.EMBED_COLOR)
        view = TriviaView(self, interaction, apuesta, q["a"], letras, lang)
        await interaction.followup.send(embed=embed, view=view)
        view.message = await interaction.original_response()


class BlackjackView(discord.ui.View):
    def __init__(self, cog, interaction, apuesta, player, dealer, lang="es"):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = interaction.user.id
        self.interaction = interaction
        self.apuesta = apuesta
        self.player = player
        self.dealer = dealer
        self.lang = lang
        self.message = None
        self.hit.label = t(lang, "games.bj_hit")
        self.stand.label = t(lang, "games.bj_stand")

    async def interaction_check(self, interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                t(self.lang, "common.not_your_game"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Pedir carta", emoji="🃏",
                       style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
        await interaction.response.defer()
        self.player.append(_new_card())
        if _hand_value(self.player) > 21:
            await self.cog._bj_settle(self.interaction, self.apuesta,
                                      self.player, self.dealer, "bust",
                                      self.lang)
            self.stop()
        else:
            await interaction.edit_original_response(
                embed=self.cog._bj_embed(self.interaction, self.player,
                                         self.dealer, hide=True,
                                         lang=self.lang))

    @discord.ui.button(label="Plantarse", emoji="✋",
                       style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        await interaction.response.defer()
        while _hand_value(self.dealer) < 17:
            self.dealer.append(_new_card())
        pv, dv = _hand_value(self.player), _hand_value(self.dealer)
        if pv == 21 and len(self.player) == 2:
            outcome = "blackjack"
        elif dv > 21 or pv > dv:
            outcome = "win"
        elif pv == dv:
            outcome = "push"
        else:
            outcome = "lose"
        await self.cog._bj_settle(self.interaction, self.apuesta,
                                  self.player, self.dealer, outcome,
                                  self.lang)
        self.stop()

    async def on_timeout(self):
        try:
            await self.interaction.edit_original_response(view=None)
        except discord.HTTPException:
            pass


class TriviaView(discord.ui.View):
    def __init__(self, cog, interaction, apuesta, correcta, letras,
                 lang="es"):
        super().__init__(timeout=15)
        self.cog = cog
        self.user_id = interaction.user.id
        self.interaction = interaction
        self.apuesta = apuesta
        self.correcta = correcta
        self.lang = lang
        self.message = None
        for i, letra in enumerate(letras):
            btn = discord.ui.Button(emoji=letra,
                                    style=discord.ButtonStyle.primary,
                                    row=0)
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    async def interaction_check(self, interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                t(self.lang, "common.not_your_game"), ephemeral=True)
            return False
        return True

    def _make_cb(self, idx: int):
        async def cb(interaction: discord.Interaction):
            await interaction.response.defer()
            gid, uid = self.interaction.guild.id, self.interaction.user.id
            db = self.cog.bot.db
            lang = self.lang
            if idx == self.correcta:
                await db.add_hearts(gid, uid, self.apuesta)
                embed = await self.cog._result_embed(
                    self.interaction, t(lang, "games.trivia_correct"),
                    f"{t(lang, 'games.trivia_correct_desc')}\n\n"
                    f"**+{self.apuesta} {config.HEART}**",
                    config.COLOR_SUCCESS)
            else:
                await db.spend_hearts(gid, uid, self.apuesta)
                embed = await self.cog._result_embed(
                    self.interaction, t(lang, "games.trivia_wrong"),
                    t(lang, "games.trivia_wrong_desc",
                      n=self.correcta + 1)
                    + f"\n\n**-{self.apuesta} {config.HEART}**",
                    config.COLOR_ERROR)
            await interaction.edit_original_response(embed=embed, view=None)
            self.stop()
        return cb

    async def on_timeout(self):
        try:
            await self.interaction.edit_original_response(view=None)
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(GamesCog(bot))
