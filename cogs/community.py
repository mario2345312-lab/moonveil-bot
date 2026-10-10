"""Comunidad: /sorteo /sugerencia /encuesta /subasta.

Los botones de Participar y Pujar son persistentes: identifican el sorteo o
subasta por el message_id guardado en la DB, así funcionan tras reinicios.
"""

import random
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import utcnow

import config
from cogs.admin import staff_check
from i18n import t, user_lang
from logging_utils import send_log

DURACIONES = {
    "10 minutos": timedelta(minutes=10),
    "1 hora": timedelta(hours=1),
    "6 horas": timedelta(hours=6),
    "1 día": timedelta(days=1),
    "3 días": timedelta(days=3),
}


def _duracion_choices():
    return [app_commands.Choice(name=k, value=k) for k in DURACIONES]


def giveaway_embed(g, entries: int, lang: str = "es") -> discord.Embed:
    premios = []
    if g["prize_hearts"]:
        premios.append(f"{g['prize_hearts']:,} {config.HEART}")
    if g["prize_text"]:
        premios.append(g["prize_text"])
    ends = int(datetime.fromisoformat(g["ends_at"]).timestamp())
    embed = discord.Embed(
        title=t(lang, "giveaway.title"),
        description=(f"## 🎁 {' + '.join(premios)}\n\n"
                     f"{t(lang, 'giveaway.tap')}\n"
                     + t(lang, "giveaway.winners", n=g["winners_count"])
                     + f"\n{t(lang, 'giveaway.ends')} <t:{ends}:R>"),
        color=0xF1C40F)
    embed.set_footer(text=t(lang, "giveaway.entries", n=entries))
    return embed


class GiveawayJoinView(discord.ui.View):
    """Botón persistente de participación en sorteos."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Participar", emoji="🎉",
                       style=discord.ButtonStyle.success,
                       custom_id="giveaway:join")
    async def join(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        lang = await user_lang(self.bot, interaction)
        g = await self.bot.db.get_giveaway_by_message(interaction.message.id)
        if g is None or g["ended"]:
            return await interaction.response.send_message(
                t(lang, "giveaway.ended"), ephemeral=True)
        if not await self.bot.db.add_entry(g["id"], interaction.user.id):
            return await interaction.response.send_message(
                t(lang, "giveaway.already"), ephemeral=True)
        entries = await self.bot.db.giveaway_entries(g["id"])
        try:
            await interaction.message.edit(
                embed=giveaway_embed(g, len(entries)))
        except discord.HTTPException:
            pass
        await interaction.response.send_message(
            t(lang, "giveaway.joined"), ephemeral=True)


class BidModal(discord.ui.Modal):
    cantidad = discord.ui.TextInput(
        label="Cantidad de Hearts", placeholder="Ej: 500",
        min_length=1, max_length=10, required=True)

    def __init__(self, bot, auction, lang="es"):
        super().__init__(title=t(lang, "auction.modal_title"))
        self.bot = bot
        self.auction = auction
        self.lang = lang
        self.cantidad.label = t(lang, "auction.modal_field")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        lang = self.lang
        db = self.bot.db
        a = await db.get_auction_by_message(interaction.message.id)
        if a is None or a["ended"]:
            return await interaction.followup.send(
                t(lang, "auction.ended"), ephemeral=True)
        try:
            monto = int(self.cantidad.value.strip())
        except ValueError:
            return await interaction.followup.send(
                t(lang, "auction.invalid"), ephemeral=True)
        minimo = max(a["min_bid"], a["current_bid"] + 1)
        if monto < minimo:
            return await interaction.followup.send(
                t(lang, "auction.too_low", n=minimo, heart=config.HEART),
                ephemeral=True)
        if interaction.user.id == a["bidder_id"]:
            return await interaction.followup.send(
                t(lang, "auction.already_top"), ephemeral=True)

        if not await db.spend_hearts(interaction.guild.id,
                                     interaction.user.id, monto):
            return await interaction.followup.send(
                t(lang, "auction.no_funds"), ephemeral=True)

        # reembolso al postor anterior
        anterior = a["bidder_id"]
        if anterior is not None:
            await db.add_hearts(interaction.guild.id, anterior,
                                a["current_bid"])

        await db.place_bid(a["id"], monto, interaction.user.id)
        await interaction.followup.send(
            t(lang, "auction.bid_ok", n=monto, heart=config.HEART),
            ephemeral=True)
        try:
            a = await db.get_auction_by_message(interaction.message.id)
            await interaction.message.edit(
                embed=auction_embed(a, self.lang))
        except discord.HTTPException:
            pass


def auction_embed(a, lang: str = "es") -> discord.Embed:
    ends = int(datetime.fromisoformat(a["ends_at"]).timestamp())
    embed = discord.Embed(
        title=t(lang, "auction.title"),
        description=(f"## {a['item_text']}\n\n"
                     + t(lang, "auction.current", n=a["current_bid"],
                         heart=config.HEART)
                     + (f" — <@{a['bidder_id']}>" if a["bidder_id"] else "")
                     + ("\n" + t(lang, "auction.min", n=a["min_bid"],
                                 heart=config.HEART)
                        if not a["bidder_id"] else "")
                     + f"\n{t(lang, 'auction.ends')} <t:{ends}:R>\n\n"
                     + t(lang, "auction.hint")),
        color=config.COLOR_WARNING)
    return embed


class AuctionBidView(discord.ui.View):
    """Botón persistente de puja en subastas."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Pujar", emoji="🔨",
                       style=discord.ButtonStyle.primary,
                       custom_id="auction:bid")
    async def bid(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
        lang = await user_lang(self.bot, interaction)
        a = await self.bot.db.get_auction_by_message(interaction.message.id)
        if a is None or a["ended"]:
            return await interaction.response.send_message(
                t(lang, "auction.ended"), ephemeral=True)
        await interaction.response.send_modal(BidModal(self.bot, a, lang))


class CommunityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ends_loop.start()

    def cog_unload(self):
        self.ends_loop.cancel()

    # ---------- /sorteo ----------

    sorteo = app_commands.Group(name="sorteo",
                                description="Sorteos del servidor.")

    @sorteo.command(name="crear",
                    description="Crea un sorteo con botón de participar (staff).")
    @app_commands.describe(
        premio="Qué se sortea (ej: 'Un Shadow Dragon')",
        hearts="Hearts de premio adicionales (opcional)",
        rol="Rol de premio adicional (opcional)",
        duracion="Cuánto dura el sorteo",
        ganadores="Número de ganadores (1-10)")
    @app_commands.choices(duracion=_duracion_choices())
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def sorteo_crear(self, interaction: discord.Interaction,
                           premio: str,
                           duracion: app_commands.Choice[str],
                           hearts: int = 0, rol: discord.Role | None = None,
                           ganadores: int = 1):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        ganadores = max(1, min(10, ganadores))
        ends = (utcnow() + DURACIONES[duracion.value]).isoformat()
        gid = await self.bot.db.create_giveaway(
            interaction.guild.id, interaction.channel.id, premio,
            hearts, rol.id if rol else None, ganadores, ends,
            interaction.user.id)
        g = await self.bot.db.get_giveaway(gid)
        msg = await interaction.channel.send(
            embed=giveaway_embed(g, 0, lang),
            view=GiveawayJoinView(self.bot))
        await self.bot.db.set_giveaway_message(gid, msg.id)
        await interaction.followup.send(
            t(lang, "giveaway.created", ch=interaction.channel.mention),
            ephemeral=True)
        await send_log(self.bot, interaction.guild, "Sorteo creado",
                       f"{interaction.user.mention} creó un sorteo: "
                       f"**{premio}** (+{hearts} {config.HEART})")

    @sorteo.command(name="cancelar",
                    description="Cancela un sorteo activo (staff).")
    @app_commands.describe(mensaje_id="ID del mensaje del sorteo")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def sorteo_cancelar(self, interaction: discord.Interaction,
                              mensaje_id: str):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        try:
            g = await self.bot.db.get_giveaway_by_message(int(mensaje_id))
        except ValueError:
            g = None
        if g is None or g["ended"]:
            return await interaction.followup.send(
                t(lang, "giveaway.not_found"), ephemeral=True)
        await self.bot.db.end_giveaway(g["id"])
        try:
            msg = await interaction.guild.get_channel(
                g["channel_id"]).fetch_message(g["message_id"])
            embed = discord.Embed(title=t(lang, "giveaway.cancelled"),
                                  description=f"~~{g['prize_text']}~~",
                                  color=config.COLOR_ERROR)
            await msg.edit(embed=embed, view=None)
        except (discord.HTTPException, AttributeError):
            pass
        await interaction.followup.send(t(lang, "giveaway.cancelled"),
                                        ephemeral=True)

    # ---------- sugerencias (canal automático) ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Todo mensaje en el canal de sugerencias se convierte en embed
        votable y el original se borra."""
        if message.author.bot or message.guild is None:
            return
        s = await self.bot.db.get_settings(message.guild.id)
        if message.channel.id == s.get("suggestion_channel_id"):
            titulo = "💡 Nueva sugerencia"
        elif message.channel.id == s.get("suggestion_channel_en_id"):
            titulo = "💡 New suggestion"
        else:
            return

        # sin texto (imagen sola, sticker, etc.) → solo limpiar el canal
        if not message.content.strip():
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return

        embed = discord.Embed(title=titulo,
                              description=message.content[:2000],
                              color=config.EMBED_COLOR)
        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.display_avatar.url)
        embed.timestamp = utcnow()
        try:
            msg = await message.channel.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            await message.delete()
        except discord.HTTPException:
            pass

    # ---------- /encuesta ----------

    @app_commands.command(name="encuesta",
                          description="Crea una encuesta con votos (staff).")
    @app_commands.describe(pregunta="La pregunta",
                           opcion1="Opción 1", opcion2="Opción 2",
                           opcion3="Opción 3 (opcional)",
                           opcion4="Opción 4 (opcional)")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def encuesta(self, interaction: discord.Interaction, pregunta: str,
                       opcion1: str, opcion2: str,
                       opcion3: str | None = None,
                       opcion4: str | None = None):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        opciones = [o for o in (opcion1, opcion2, opcion3, opcion4) if o]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        embed = discord.Embed(
            title=t(lang, "poll.title"),
            description=(f"### {pregunta}\n\n" + "\n".join(
                f"{emojis[i]} {o}" for i, o in enumerate(opciones))),
            color=config.EMBED_COLOR)
        embed.set_footer(
            text=t(lang, "poll.by", name=interaction.user.display_name))
        embed.timestamp = utcnow()
        msg = await interaction.channel.send(embed=embed)
        for i in range(len(opciones)):
            await msg.add_reaction(emojis[i])
        await interaction.followup.send(t(lang, "poll.posted"),
                                        ephemeral=True)

    # ---------- /subasta ----------

    @app_commands.command(name="subasta",
                          description="Crea una subasta por Hearts (staff).")
    @app_commands.describe(item="Qué se subasta (ej: 'Un Frost Dragon')",
                           duracion="Cuánto dura",
                           puja_inicial="Puja mínima para empezar")
    @app_commands.choices(duracion=_duracion_choices())
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def subasta(self, interaction: discord.Interaction, item: str,
                      duracion: app_commands.Choice[str],
                      puja_inicial: int = 50):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        ends = (utcnow() + DURACIONES[duracion.value]).isoformat()
        aid = await self.bot.db.create_auction(
            interaction.guild.id, interaction.channel.id, item,
            max(0, puja_inicial), ends, interaction.user.id)
        a = await self.bot.db.get_auction(aid)
        msg = await interaction.channel.send(
            embed=auction_embed(a, lang), view=AuctionBidView(self.bot))
        await self.bot.db.set_auction_message(aid, msg.id)
        await interaction.followup.send(
            t(lang, "auction.created", ch=interaction.channel.mention),
            ephemeral=True)
        await send_log(self.bot, interaction.guild, "Subasta creada",
                       f"{interaction.user.mention} subastó **{item}**")

    # ---------- cierre de sorteos y subastas ----------

    @tasks.loop(minutes=1)
    async def ends_loop(self):
        db = self.bot.db
        now = utcnow().isoformat()

        for g in await db.due_giveaways(now):
            await db.end_giveaway(g["id"])
            await self._finish_giveaway(g)

        for a in await db.due_auctions(now):
            await db.end_auction(a["id"])
            await self._finish_auction(a)

    @ends_loop.before_loop
    async def before_ends(self):
        await self.bot.wait_until_ready()

    async def _finish_giveaway(self, g):
        guild = self.bot.get_guild(g["guild_id"])
        if guild is None:
            return
        channel = guild.get_channel(g["channel_id"])
        if channel is None:
            return
        host = await self.bot.db.get_user(g["guild_id"], g["host_id"])
        lang = host["lang"] or "es"
        entries = await self.bot.db.giveaway_entries(g["id"])
        embed = discord.Embed(color=config.COLOR_SUCCESS)
        if entries:
            n = min(g["winners_count"], len(entries))
            winners = random.sample(entries, n)
            embed.title = t(lang, "giveaway.done_title")
            embed.description = (
                f"🎁 **{g['prize_text']}**\n\n"
                + "\n".join(f"🏆 <@{w}>" for w in winners))
            await channel.send(
                content="🎉 " + " ".join(f"<@{w}>" for w in winners),
                embed=embed)
            for w in winners:
                if g["prize_hearts"]:
                    await self.bot.db.add_hearts(g["guild_id"], w,
                                                 g["prize_hearts"])
                if g["prize_role_id"]:
                    member = guild.get_member(w)
                    rol = guild.get_role(g["prize_role_id"])
                    if member and rol:
                        try:
                            await member.add_roles(
                                rol, reason="Premio de sorteo")
                        except discord.HTTPException:
                            pass
        else:
            embed.title = t(lang, "giveaway.none_title")
            embed.description = f"🎁 {g['prize_text']}"
            await channel.send(embed=embed)

        try:
            msg = await channel.fetch_message(g["message_id"])
            await msg.edit(view=None)
        except discord.HTTPException:
            pass
        await send_log(self.bot, guild, "Sorteo finalizado",
                       f"Premio **{g['prize_text']}** — "
                       f"{len(entries)} participantes")

    async def _finish_auction(self, a):
        guild = self.bot.get_guild(a["guild_id"])
        if guild is None:
            return
        channel = guild.get_channel(a["channel_id"])
        if channel is None:
            return
        host = await self.bot.db.get_user(a["guild_id"], a["host_id"])
        lang = host["lang"] or "es"
        embed = discord.Embed(color=config.COLOR_SUCCESS)
        if a["bidder_id"]:
            embed.title = t(lang, "auction.sold")
            embed.description = t(
                lang, "auction.sold_desc", item=a["item_text"],
                user=f"<@{a['bidder_id']}>", n=a["current_bid"],
                heart=config.HEART)
            await channel.send(embed=embed)
            # los Hearts van al creador de la subasta
            await self.bot.db.add_hearts(guild.id, a["host_id"],
                                         a["current_bid"])
        else:
            embed.title = t(lang, "auction.no_bids")
            embed.description = a["item_text"]
            await channel.send(embed=embed)
        try:
            msg = await channel.fetch_message(a["message_id"])
            await msg.edit(view=None)
        except discord.HTTPException:
            pass
        await send_log(self.bot, guild, "Subasta finalizada",
                       f"{a['item_text']} — puja final: "
                       f"{a['current_bid']} {config.HEART}")


async def setup(bot):
    await bot.add_cog(CommunityCog(bot))
