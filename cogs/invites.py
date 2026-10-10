"""Rastreo de invitaciones + mensaje de bienvenida.

Cachea las invites del servidor y detecta cuál se usó cuando entra un miembro.
Requiere: Server Members Intent + permiso Manage Server.
"""

import discord
from discord.ext import commands
from discord.utils import utcnow

import config
from i18n import t, member_lang
from logging_utils import send_log


class InvitesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cache: dict[int, dict[str, int]] = {}  # guild_id -> {code: uses}

    async def _sync_guild(self, guild: discord.Guild):
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            return
        self._cache[guild.id] = {i.code: i.uses for i in invites}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self._sync_guild(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self._cache.setdefault(invite.guild.id, {})[invite.code] = invite.uses

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self._cache.get(invite.guild.id, {}).pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        await self._send_welcome(member)

        old = self._cache.get(guild.id, {})
        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            return
        self._cache[guild.id] = {i.code: i.uses for i in new_invites}

        inviter = None
        for inv in new_invites:
            if inv.uses > old.get(inv.code, 0):
                inviter = inv.inviter
                break

        if inviter is None or inviter.id == member.id:
            return

        # solo cuenta la primera vez que entra el miembro
        if await self.bot.db.record_invite(guild.id, member.id, inviter.id):
            await self.bot.db.bump_stat(guild.id, inviter.id, "invites_count")
            await send_log(
                self.bot, guild, "Invitación registrada",
                f"{member.mention} entró con la invite de {inviter.mention}.",
                fields=[("Invitaciones del inviter",
                         str((await self.bot.db.get_user(
                             guild.id, inviter.id))["invites_count"]))])

    async def _send_welcome(self, member: discord.Member):
        guild = member.guild
        try:
            s = await self.bot.db.get_settings(guild.id)
        except Exception:
            return
        ch_id = s.get("welcome_channel_id")
        channel = guild.get_channel(ch_id) if ch_id else None
        if channel is None:
            return
        lang = member_lang(s, member)
        embed = discord.Embed(
            title=t(lang, "welcome.title", guild=guild.name),
            description=t(lang, "welcome.desc", user=member.mention,
                          n=guild.member_count),
            color=config.EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = utcnow()
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(InvitesCog(bot))
