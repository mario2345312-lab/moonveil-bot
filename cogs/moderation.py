"""Moderación: /warn, /warns, /mute, /kick, /ban, /purge + automod."""

import datetime
import re
import time

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.review import is_staff
from i18n import t, user_lang, member_lang
from logging_utils import send_log

LINK_RE = re.compile(r"https?://|discord\.gg/|www\.", re.I)


def _staff_check(interaction: discord.Interaction, settings: dict) -> bool:
    return isinstance(interaction.user, discord.Member) and is_staff(
        interaction.user, settings)


async def _deny(interaction: discord.Interaction, lang: str):
    msg = t(lang, "mod.no_perms")
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # anti-spam: {(guild_id, user_id): [timestamps]}
        self._msg_history: dict[tuple[int, int], list[float]] = {}

    # ---------------- comandos ----------------

    @app_commands.command(name="warn",
                          description="Advierte a un usuario (staff).")
    @app_commands.describe(usuario="Usuario a advertir",
                           razon="Motivo de la advertencia")
    @app_commands.guild_only()
    async def warn(self, interaction: discord.Interaction,
                   usuario: discord.Member, razon: str):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        if usuario.id == interaction.user.id:
            return await interaction.followup.send(
                t(lang, "mod.cant_target_self"), ephemeral=True)
        if usuario.bot:
            return await interaction.followup.send(
                t(lang, "mod.cant_target_bot"), ephemeral=True)
        await self.bot.db.add_warning(
            interaction.guild.id, usuario.id, interaction.user.id, razon)
        warns = await self.bot.db.get_warnings(interaction.guild.id,
                                               usuario.id)
        await interaction.followup.send(
            t(lang, "mod.warn_done", user=usuario.mention, reason=razon,
              count=len(warns)))
        await send_log(
            self.bot, interaction.guild, "Advertencia",
            fields=[("Usuario", f"{usuario} ({usuario.id})"),
                    ("Moderador", f"{interaction.user}"),
                    ("Razón", razon), ("Total", str(len(warns)))])

    @app_commands.command(name="warns",
                          description="Muestra las advertencias de un usuario.")
    @app_commands.describe(usuario="Usuario a revisar")
    @app_commands.guild_only()
    async def warns(self, interaction: discord.Interaction,
                    usuario: discord.Member | None = None):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        target = usuario or interaction.user
        if target.id != interaction.user.id:
            s = await self.bot.db.get_settings(interaction.guild.id)
            if not _staff_check(interaction, s):
                return await _deny(interaction, lang)
        warns = await self.bot.db.get_warnings(interaction.guild.id,
                                               target.id)
        embed = discord.Embed(
            title=t(lang, "mod.warns_title", user=target.display_name),
            color=config.EMBED_COLOR)
        if not warns:
            embed.description = t(lang, "mod.warns_empty")
        else:
            embed.description = "\n\n".join(
                t(lang, "mod.warns_entry", id=w["id"], reason=w["reason"],
                  mod=f"<@{w['moderator_id']}>",
                  date=w["created_at"][:10]) for w in warns[:10])
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warns-limpiar",
                          description="Elimina las advertencias de un usuario (staff).")
    @app_commands.guild_only()
    async def warns_limpiar(self, interaction: discord.Interaction,
                            usuario: discord.Member):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        await self.bot.db.clear_warnings(interaction.guild.id, usuario.id)
        await interaction.followup.send(
            t(lang, "mod.warns_cleared", user=usuario.mention),
            ephemeral=True)

    @app_commands.command(name="mute",
                          description="Silencia a un usuario N minutos (staff).")
    @app_commands.describe(usuario="Usuario a silenciar",
                           minutos="Duración del silencio",
                           razon="Motivo")
    @app_commands.guild_only()
    async def mute(self, interaction: discord.Interaction,
                   usuario: discord.Member,
                   minutos: app_commands.Range[int, 1, 40320],
                   razon: str = "Sin razón"):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        if usuario.id == interaction.user.id or usuario.bot:
            return await interaction.followup.send(
                t(lang, "mod.cant_target_self"
                        if usuario.id == interaction.user.id
                        else "mod.cant_target_bot"), ephemeral=True)
        try:
            await usuario.timeout(
                discord.utils.utcnow() + datetime.timedelta(minutes=minutos),
                reason=f"{interaction.user}: {razon}")
        except discord.Forbidden:
            return await interaction.followup.send(
                t(lang, "mod.mute_failed"), ephemeral=True)
        await interaction.followup.send(
            t(lang, "mod.mute_done", user=usuario.mention, minutes=minutos,
              reason=razon))
        await send_log(
            self.bot, interaction.guild, "Mute",
            fields=[("Usuario", f"{usuario} ({usuario.id})"),
                    ("Moderador", f"{interaction.user}"),
                    ("Duración", f"{minutos} min"), ("Razón", razon)])

    @app_commands.command(name="kick",
                          description="Expulsa a un usuario del servidor (staff).")
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction,
                   usuario: discord.Member, razon: str = "Sin razón"):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        if usuario.id == interaction.user.id or usuario.bot:
            return await interaction.followup.send(
                t(lang, "mod.cant_target_self"
                        if usuario.id == interaction.user.id
                        else "mod.cant_target_bot"), ephemeral=True)
        try:
            await usuario.kick(reason=f"{interaction.user}: {razon}")
        except discord.Forbidden:
            return await interaction.followup.send(
                t(lang, "mod.kick_failed"), ephemeral=True)
        await interaction.followup.send(
            t(lang, "mod.kick_done", user=f"{usuario}", reason=razon))
        await send_log(
            self.bot, interaction.guild, "Expulsión",
            fields=[("Usuario", f"{usuario} ({usuario.id})"),
                    ("Moderador", f"{interaction.user}"), ("Razón", razon)])

    @app_commands.command(name="ban",
                          description="Banea a un usuario del servidor (staff).")
    @app_commands.guild_only()
    async def ban(self, interaction: discord.Interaction,
                  usuario: discord.Member, razon: str = "Sin razón"):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        if usuario.id == interaction.user.id or usuario.bot:
            return await interaction.followup.send(
                t(lang, "mod.cant_target_self"
                        if usuario.id == interaction.user.id
                        else "mod.cant_target_bot"), ephemeral=True)
        try:
            await usuario.ban(reason=f"{interaction.user}: {razon}",
                              delete_message_seconds=0)
        except discord.Forbidden:
            return await interaction.followup.send(
                t(lang, "mod.ban_failed"), ephemeral=True)
        await interaction.followup.send(
            t(lang, "mod.ban_done", user=f"{usuario}", reason=razon))
        await send_log(
            self.bot, interaction.guild, "Ban",
            fields=[("Usuario", f"{usuario} ({usuario.id})"),
                    ("Moderador", f"{interaction.user}"), ("Razón", razon)])

    @app_commands.command(name="purge",
                          description="Borra los últimos N mensajes del canal (staff).")
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction,
                    cantidad: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        s = await self.bot.db.get_settings(interaction.guild.id)
        if not _staff_check(interaction, s):
            return await _deny(interaction, lang)
        try:
            deleted = await interaction.channel.purge(limit=cantidad)
        except discord.Forbidden:
            return await interaction.followup.send(
                t(lang, "mod.purge_fail"), ephemeral=True)
        await interaction.followup.send(
            t(lang, "mod.purge_done", n=len(deleted)), ephemeral=True)
        await send_log(
            self.bot, interaction.guild, "Purge",
            description=f"{interaction.user} borró {len(deleted)} mensajes "
                        f"en {interaction.channel.mention}")

    # ---------------- automod ----------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not isinstance(message.author, discord.Member):
            return
        s = await self.bot.db.get_settings(message.guild.id)
        if is_staff(message.author, s):
            return  # el staff está exento
        lang = member_lang(s, message.author)

        content = message.content
        low = content.lower()

        # palabras prohibidas
        if any(w in low for w in config.BAD_WORDS):
            return await self._strike(
                message, t(lang, "automod.badword", user=message.author.mention),
                "Automod: lenguaje no permitido", content)

        # links
        if LINK_RE.search(content):
            return await self._strike(
                message, t(lang, "automod.link", user=message.author.mention),
                "Automod: link", content)

        # caps
        letters = [c for c in content if c.isalpha()]
        if (len(content) >= config.CAPS_MIN_LEN and letters
                and sum(c.isupper() for c in letters) / len(letters)
                >= config.CAPS_RATIO):
            return await self._strike(
                message, t(lang, "automod.caps", user=message.author.mention),
                "Automod: mayúsculas", content)

        # spam → timeout
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        hist = [ts for ts in self._msg_history.get(key, [])
                if now - ts < config.SPAM_WINDOW_SECONDS]
        hist.append(now)
        self._msg_history[key] = hist
        if len(hist) >= config.SPAM_MESSAGES:
            self._msg_history[key] = []
            try:
                await message.author.timeout(
                    discord.utils.utcnow()
                    + datetime.timedelta(minutes=config.AUTOMOD_TIMEOUT_MIN),
                    reason="Automod: spam")
            except discord.Forbidden:
                pass
            try:
                await message.channel.send(
                    t(lang, "automod.spam", user=message.author.mention,
                      minutes=config.AUTOMOD_TIMEOUT_MIN),
                    delete_after=15)
            except discord.HTTPException:
                pass
            await send_log(self.bot, message.guild, "Automod: spam",
                           description=f"{message.author} silenciado "
                                       f"{config.AUTOMOD_TIMEOUT_MIN} min")

    async def _strike(self, message: discord.Message, notice: str,
                      log_title: str, content: str):
        try:
            await message.delete()
        except discord.HTTPException:
            return
        try:
            await message.channel.send(notice, delete_after=10)
        except discord.HTTPException:
            pass
        await send_log(self.bot, message.guild, log_title,
                       description=f"{message.author} en "
                                   f"{message.channel.mention}",
                       fields=[("Mensaje", content[:300])])


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
