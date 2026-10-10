"""Social: confesiones, cumpleaños, QOTD, AFK, comandos personalizados y eventos."""

import re
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from cogs.review import is_staff
from i18n import t, user_lang, member_lang
from logging_utils import send_log
from discord.utils import utcnow

CCMD_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,30}$")
TIME_RE = re.compile(r"^(\d+)\s*([smhd])$", re.I)
UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
QOTD_HOUR = 15  # UTC, hora de publicación de la pregunta del día


def _humanize(seconds: int, lang: str) -> str:
    if seconds < 3600:
        return f"{seconds // 60} min"
    if seconds < 86400:
        return f"{seconds // 3600} h"
    return f"{seconds // 86400} d"


class SocialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_loop.start()
        self.qotd_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()
        self.qotd_loop.cancel()

    # ---------------- confesiones (canal automático) ----------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        s = await self.bot.db.get_settings(message.guild.id)

        # --- canal de confesiones ---
        if message.channel.id == s.get("confession_channel_id"):
            await self._handle_confession(message, s)
            return

        # --- AFK: el autor vuelve ---
        if isinstance(message.author, discord.Member):
            afk = await self.bot.db.get_afk(message.guild.id,
                                            message.author.id)
            if afk:
                await self.bot.db.remove_afk(message.guild.id,
                                             message.author.id)
                lang = member_lang(s, message.author)
                try:
                    await message.channel.send(
                        t(lang, "afk.back", user=message.author.mention),
                        delete_after=15)
                except discord.HTTPException:
                    pass

            # --- AFK: menciones a usuarios AFK ---
            for member in message.mentions:
                if member.id == message.author.id:
                    continue
                afk = await self.bot.db.get_afk(message.guild.id, member.id)
                if afk:
                    lang = member_lang(s, message.author)
                    reason = (t(lang, "afk.reason_fmt", r=afk["reason"])
                              if afk["reason"] else "")
                    try:
                        since = max(0, int(
                            (utcnow() - datetime.fromisoformat(
                                afk["set_at"])).total_seconds()))
                    except (TypeError, ValueError):
                        since = 0
                    try:
                        await message.channel.send(
                            t(lang, "afk.mention", user=member.display_name,
                              reason=reason,
                              time=_humanize(since, lang)),
                            delete_after=20)
                    except discord.HTTPException:
                        pass

        # --- comandos personalizados (!nombre) ---
        if message.content.startswith("!"):
            name = message.content[1:].split()[0].lower() \
                if message.content[1:].strip() else ""
            if name:
                row = await self.bot.db.get_custom_command(
                    message.guild.id, name)
                if row:
                    try:
                        await message.channel.send(
                            row["response"],
                            reference=message,
                            allowed_mentions=discord.AllowedMentions(
                                users=True, roles=False, everyone=False))
                    except discord.HTTPException:
                        pass

    async def _handle_confession(self, message: discord.Message, s: dict):
        content = message.content.strip()
        if not content:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return
        if len(content) > 1500:
            lang = member_lang(s, message.author)
            try:
                await message.delete()
                await message.channel.send(t(lang, "conf.too_long"),
                                           delete_after=10)
            except discord.HTTPException:
                pass
            return
        n = await self.bot.db.bump_confession(message.guild.id)
        embed = discord.Embed(title=t("es", "conf.title", n=n),
                              description=content,
                              color=config.EMBED_COLOR)
        embed.set_footer(text=t("es", "conf.footer"))
        embed.timestamp = utcnow()
        try:
            await message.channel.send(embed=embed)
            await message.delete()
        except discord.HTTPException:
            return
        # registro interno para el staff
        await send_log(
            self.bot, message.guild, f"Confesión #{n}",
            fields=[("Autor", f"{message.author} ({message.author.id})"),
                    ("Contenido", content[:500])])

    # ---------------- /cumple ----------------

    @app_commands.command(
        name="cumple",
        description="Registra tu cumpleaños para recibir felicitación.")
    @app_commands.describe(mes="Mes (1-12)", dia="Día (1-31)")
    @app_commands.guild_only()
    async def cumple(self, interaction: discord.Interaction,
                     mes: app_commands.Range[int, 1, 12],
                     dia: app_commands.Range[int, 1, 31]):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        try:
            datetime(2000, mes, dia)
        except ValueError:
            return await interaction.followup.send(
                t(lang, "cumple.invalid"), ephemeral=True)
        await self.bot.db.set_birthday(interaction.guild.id,
                                       interaction.user.id, mes, dia)
        await interaction.followup.send(
            t(lang, "cumple.set", day=dia, month=mes), ephemeral=True)

    @tasks.loop(minutes=30)
    async def birthday_loop(self):
        now = utcnow()
        for guild in self.bot.guilds:
            s = await self.bot.db.get_settings(guild.id)
            rows = await self.bot.db.todays_birthdays(
                guild.id, now.month, now.day, now.year)
            if not rows:
                continue
            channel_id = (s.get("welcome_channel_id")
                          or s.get("qotd_channel_id"))
            channel = guild.get_channel(channel_id) if channel_id else None
            users = " y ".join(f"<@{r['user_id']}>" for r in rows)
            for r in rows:
                await self.bot.db.mark_birthday_wished(
                    guild.id, r["user_id"], now.year)
            if channel:
                try:
                    await channel.send(
                        f"{t('es', 'cumple.announce', users=users)}\n"
                        f"{t('en', 'cumple.announce', users=users)}")
                except discord.HTTPException:
                    pass

    @birthday_loop.before_loop
    async def before_birthdays(self):
        await self.bot.wait_until_ready()

    # ---------------- QOTD ----------------

    @tasks.loop(minutes=30)
    async def qotd_loop(self):
        now = utcnow()
        if now.hour < QOTD_HOUR:
            return
        today = now.date().isoformat()
        for guild in self.bot.guilds:
            s = await self.bot.db.get_settings(guild.id)
            if s.get("qotd_last") == today:
                continue
            channel = guild.get_channel(s.get("qotd_channel_id") or 0)
            if channel is None:
                continue
            await self.bot.db.set_setting(guild.id, "qotd_last", today)
            idx = await self.bot.db.qotd_next_index(guild.id, len(config.QOTD))
            q_es, q_en = config.QOTD[idx]
            embed = discord.Embed(
                title=t("es", "qotd.title"),
                description=f"🇪🇸 {q_es}\n🇺🇸 {q_en}",
                color=config.EMBED_COLOR)
            embed.set_footer(text=t("es", "qotd.footer"))
            embed.timestamp = now
            try:
                await channel.send(embed=embed)
            except discord.HTTPException:
                pass

    @qotd_loop.before_loop
    async def before_qotd(self):
        await self.bot.wait_until_ready()

    # ---------------- /afk ----------------

    @app_commands.command(name="afk",
                          description="Márcate como AFK con un motivo opcional.")
    @app_commands.describe(razon="Motivo opcional")
    @app_commands.guild_only()
    async def afk(self, interaction: discord.Interaction,
                  razon: str | None = None):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        await self.bot.db.set_afk(interaction.guild.id, interaction.user.id,
                                  razon or "", utcnow().isoformat())
        reason = t(lang, "afk.reason_fmt", r=razon) if razon else ""
        await interaction.followup.send(
            t(lang, "afk.set", user=interaction.user.mention, reason=reason))

    # ---------------- comandos personalizados ----------------

    ccmd = app_commands.Group(
        name="comando",
        description="Comandos personalizados del servidor (!nombre).",
        guild_only=True)

    async def _cmd_staff(self, interaction: discord.Interaction) -> bool:
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not (isinstance(interaction.user, discord.Member)
                and is_staff(interaction.user, s)):
            await interaction.followup.send(t(lang, "mod.no_perms"),
                                            ephemeral=True)
            return False
        return True

    @ccmd.command(name="agregar",
                  description="Crea un comando personalizado !nombre (staff).")
    @app_commands.describe(nombre="Nombre del comando",
                           texto="Respuesta que dará el bot")
    async def ccmd_agregar(self, interaction: discord.Interaction,
                           nombre: str, texto: str):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        if not await self._cmd_staff(interaction):
            return
        name = nombre.lower().lstrip("!")
        if not CCMD_NAME_RE.match(name):
            return await interaction.followup.send(
                t(lang, "ccmd.name_invalid"), ephemeral=True)
        await self.bot.db.add_custom_command(
            interaction.guild.id, name, texto[:2000], interaction.user.id)
        await interaction.followup.send(
            t(lang, "ccmd.added", name=name), ephemeral=True)

    @ccmd.command(name="quitar",
                  description="Elimina un comando personalizado (staff).")
    async def ccmd_quitar(self, interaction: discord.Interaction,
                          nombre: str):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        if not await self._cmd_staff(interaction):
            return
        name = nombre.lower().lstrip("!")
        ok = await self.bot.db.remove_custom_command(interaction.guild.id,
                                                     name)
        key = "ccmd.removed" if ok else "ccmd.not_found"
        await interaction.followup.send(t(lang, key, name=name),
                                        ephemeral=True)

    @ccmd.command(name="lista",
                  description="Lista los comandos personalizados.")
    async def ccmd_lista(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        rows = await self.bot.db.get_custom_commands(interaction.guild.id)
        embed = discord.Embed(title=t(lang, "ccmd.list_title"),
                              color=config.EMBED_COLOR)
        embed.description = ("\n".join(f"• `!{r['name']}`" for r in rows)
                             if rows else t(lang, "ccmd.list_empty"))
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ---------------- /evento (recordatorio del server) ----------------

    @app_commands.command(
        name="evento",
        description="Programa un anuncio de evento para todo el server (staff).")
    @app_commands.describe(
        texto="Texto del anuncio",
        tiempo="En cuánto tiempo (ej: 10m, 2h, 3d)",
        canal="Canal donde anunciarlo (por defecto, este)")
    @app_commands.guild_only()
    async def evento(self, interaction: discord.Interaction, texto: str,
                     tiempo: str,
                     canal: discord.TextChannel | None = None):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not (isinstance(interaction.user, discord.Member)
                and is_staff(interaction.user, s)):
            return await interaction.followup.send(
                t(lang, "mod.no_perms"), ephemeral=True)
        m = TIME_RE.match(tiempo.strip())
        if not m:
            return await interaction.followup.send(
                t(lang, "event.invalid_time"), ephemeral=True)
        seconds = int(m.group(1)) * UNIT_SECONDS[m.group(2).lower()]
        if seconds < 30 or seconds > 30 * 86400:
            return await interaction.followup.send(
                t(lang, "event.invalid_time"), ephemeral=True)
        channel = canal or interaction.channel
        remind_at = (utcnow() + timedelta(seconds=seconds)).isoformat()
        await self.bot.db.add_reminder(
            interaction.guild.id, channel.id, interaction.user.id,
            texto[:500], remind_at, kind="event")
        await interaction.followup.send(
            t(lang, "event.created", text=texto[:100],
              channel=channel.mention,
              time=discord.utils.format_dt(
                  utcnow() + timedelta(seconds=seconds), style="R")),
            ephemeral=True)


async def setup(bot):
    await bot.add_cog(SocialCog(bot))
