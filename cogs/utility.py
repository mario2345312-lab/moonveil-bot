"""Utilidades: /recordatorio /say /anuncio."""

import re

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import utcnow
from datetime import timedelta

import config
from cogs.admin import staff_check
from i18n import t, user_lang
from logging_utils import send_log

DUR_RE = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)
DUR_MULT = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class TextModal(discord.ui.Modal):
    titulo = discord.ui.TextInput(
        label="Título", max_length=100, required=True)
    mensaje = discord.ui.TextInput(
        label="Mensaje", style=discord.TextStyle.paragraph,
        max_length=2000, required=True)

    def __init__(self, bot, titulo_modal: str, rol: discord.Role | None,
                 es_anuncio: bool):
        super().__init__(title=titulo_modal)
        self.bot = bot
        self.rol = rol
        self.es_anuncio = es_anuncio

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title=("📢 " if self.es_anuncio else "") + self.titulo.value,
            description=self.mensaje.value,
            color=(config.COLOR_WARNING if self.es_anuncio
                   else config.EMBED_COLOR))
        embed.timestamp = utcnow()
        if self.es_anuncio:
            embed.set_footer(
                text=f"Anuncio del equipo de {interaction.guild.name}")
        content = self.rol.mention if self.rol else None
        await interaction.channel.send(content=content, embed=embed)
        await interaction.followup.send("✅ Publicado.", ephemeral=True)


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    @app_commands.command(
        name="recordatorio",
        description="Te recuerda algo en un tiempo (ej: 10m, 2h, 1d).")
    @app_commands.describe(en="En cuánto tiempo (ej: 10m, 2h, 1d)",
                           texto="Qué quieres recordar")
    @app_commands.guild_only()
    async def recordatorio(self, interaction: discord.Interaction, en: str,
                           texto: str):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        m = DUR_RE.match(en.strip())
        if not m:
            return await interaction.followup.send(
                t(lang, "rem.bad_format"), ephemeral=True)
        secs = int(m.group(1)) * DUR_MULT[m.group(2).lower()]
        if secs < 10 or secs > 7 * 86400:
            return await interaction.followup.send(
                t(lang, "rem.range"), ephemeral=True)

        remind_at = (utcnow() + timedelta(seconds=secs)).isoformat()
        await self.bot.db.add_reminder(
            interaction.guild.id, interaction.channel.id,
            interaction.user.id, texto[:500], remind_at)
        ts = int((utcnow() + timedelta(seconds=secs)).timestamp())
        await interaction.followup.send(
            t(lang, "rem.set", ts=ts, text=texto), ephemeral=True)

    @app_commands.command(
        name="language",
        description="Elige tu idioma / Choose your language.")
    @app_commands.describe(idioma="Español, English o automático (por rol)")
    @app_commands.choices(idioma=[
        app_commands.Choice(name="🇪🇸 Español", value="es"),
        app_commands.Choice(name="🇺🇸 English", value="en"),
        app_commands.Choice(name="🌐 Automático / Auto", value="auto"),
    ])
    @app_commands.guild_only()
    async def language(self, interaction: discord.Interaction,
                       idioma: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        val = None if idioma.value == "auto" else idioma.value
        await self.bot.db.set_lang(interaction.guild.id,
                                   interaction.user.id, val)
        key = {"es": "lang.set_es", "en": "lang.set_en",
               "auto": "lang.auto"}[idioma.value]
        # responde en el idioma elegido (o el resuelto si es auto)
        lang = idioma.value if idioma.value != "auto" \
            else await user_lang(self.bot, interaction)
        await interaction.followup.send(t(lang, key), ephemeral=True)

    @app_commands.command(name="say",
                          description="El bot publica un mensaje tuyo (staff).")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def say(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            TextModal(self.bot, "Enviar mensaje", None, False))

    @app_commands.command(name="anuncio",
                          description="Publica un anuncio con ping opcional (staff).")
    @app_commands.describe(rol="Rol a mencionar (opcional)")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def anuncio(self, interaction: discord.Interaction,
                      rol: discord.Role | None = None):
        await interaction.response.send_modal(
            TextModal(self.bot, "Publicar anuncio", rol, True))

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        now = utcnow().isoformat()
        for r in await self.bot.db.due_reminders(now):
            await self.bot.db.delete_reminder(r["id"])
            guild = self.bot.get_guild(r["guild_id"])
            channel = guild.get_channel(r["channel_id"]) if guild else None
            if channel is None:
                continue
            try:
                user = await self.bot.db.get_user(r["guild_id"], r["user_id"])
                await channel.send(
                    t(user["lang"] or "es", "rem.ping",
                      user=f"<@{r['user_id']}>", text=r["text"]))
            except discord.HTTPException:
                pass

    @reminder_loop.before_loop
    async def before_reminders(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
