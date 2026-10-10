"""Economía: /hearts /daily /streak /leaderboard /work /rob."""

import random
from datetime import date, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import config
from i18n import t, user_lang


def _cd_left(last_iso: str | None, hours: int) -> int:
    """Segundos restantes de cooldown (0 si ya pasó)."""
    if not last_iso:
        return 0
    nxt = datetime.fromisoformat(last_iso) + timedelta(hours=hours)
    return max(0, int((nxt - discord.utils.utcnow().replace(tzinfo=None))
                        .total_seconds()))


def _fmt_cd(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    return f"{h}h {rem // 60}m" if h else f"{rem // 60}m {rem % 60}s"


class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile",
                          description="Muestra tu perfil o el de otro usuario.")
    @app_commands.describe(usuario="Usuario a consultar (opcional)")
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction,
                      usuario: discord.Member | None = None):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        target = usuario or interaction.user
        db = self.bot.db
        guild = interaction.guild

        u = await db.get_user(guild.id, target.id)
        claimed = await db.claimed_achievement_ids(guild.id, target.id)
        missions = await db.get_mission_rows(guild.id, target.id)
        done_missions = sum(1 for r in missions.values() if r["completed"])

        # roles de la tienda que posee
        insignias = []
        for cid in config.COLOR_ITEM_IDS:
            it = config.SHOP_ITEMS[cid]
            if any(r.name == it["name"] for r in target.roles):
                insignias.append(f"{it['emoji']} {it['name']}")
        s = await db.get_settings(guild.id)
        vip = guild.get_role(s.get("vip_role_id") or 0) or \
            discord.utils.get(guild.roles, name="VIP")
        if vip and vip in target.roles:
            insignias.append(f"💎 {vip.name}")
        if u["custom_role_id"]:
            cr = guild.get_role(u["custom_role_id"])
            if cr:
                insignias.append(f"🎨 {cr.name}")

        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_author(name=t(lang, "profile.title",
                                name=target.display_name),
                         icon_url=target.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.description = (
            f"## 💰 {u['hearts']:,} {config.HEART}\n"
            + t(lang, "profile.streak", n=u["streak"],
                best=u["best_streak"])
        )
        if insignias:
            embed.description += "\n\n" + "  ".join(insignias)

        embed.add_field(
            name=t(lang, "profile.activity"),
            value=(
                f"{t(lang, 'profile.earned')}: **{u['total_earned']:,}**\n"
                f"{t(lang, 'profile.spent')}: **{u['total_spent']:,}**\n"
                f"{t(lang, 'profile.dailies')}: **{u['dailies_claimed']}**"
            ), inline=True)
        embed.add_field(
            name=t(lang, "profile.progress"),
            value=(
                f"{t(lang, 'profile.achievements')}: "
                f"**{len(claimed)}/{len(config.ACHIEVEMENTS)}**\n"
                f"{t(lang, 'profile.missions')}: "
                f"**{done_missions}/{len(config.MISSIONS)}**\n"
                f"{t(lang, 'profile.invited')}: **{u['invites_count']}**"
            ), inline=True)
        embed.add_field(
            name=t(lang, "profile.game"),
            value=(
                f"{t(lang, 'profile.flips')}: "
                f"**{u['flips_won']}/{u['flips_played']}**\n"
                f"{t(lang, 'profile.purchases')}: **{u['items_bought']}**"
            ), inline=True)

        if u["dream_pet"]:
            embed.description += (f"\n\n🐣 Dream Pet: **{u['dream_pet']}**")
        elif target.id == interaction.user.id:
            embed.description += f"\n\n{t(lang, 'profile.set_dream')}"

        fechas = [
            f"{t(lang, 'profile.joined')} "
            f"<t:{int(target.joined_at.timestamp())}:D>"
        ] if target.joined_at else []
        fechas.append(f"{t(lang, 'profile.created')} "
                      f"<t:{int(target.created_at.timestamp())}:D>")
        embed.add_field(name=t(lang, "profile.dates"),
                        value="\n".join(fechas), inline=False)

        rank = await db.user_rank(guild.id, target.id)
        embed.set_footer(text=t(lang, "profile.rank_footer", rank=rank))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="dream-pet",
        description="Establece tu mascota soñada de Adopt Me para tu perfil.")
    @app_commands.describe(mascota="Nombre de tu mascota soñada",
                           emoji="Emoji que la representa (opcional)")
    @app_commands.guild_only()
    async def dream_pet(self, interaction: discord.Interaction, mascota: str,
                        emoji: str | None = None):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        pet = f"{emoji} {mascota}" if emoji else mascota
        await self.bot.db.set_dream_pet(interaction.guild.id,
                                        interaction.user.id, pet[:100])
        await interaction.followup.send(
            embed=discord.Embed(
                title=t(lang, "dream.saved_title"),
                description=t(lang, "dream.saved_desc", pet=pet),
                color=config.COLOR_SUCCESS),
            ephemeral=True)


    @app_commands.command(name="hearts",
                          description="Revisa tu saldo de Hearts y estadísticas.")
    @app_commands.guild_only()
    async def hearts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        u = await self.bot.db.get_user(interaction.guild.id,
                                       interaction.user.id)
        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_author(
            name=t(lang, "hearts.title", heart=config.HEART,
                   name=interaction.user.display_name),
            icon_url=interaction.user.display_avatar.url)
        embed.description = (
            t(lang, "hearts.balance", hearts=u["hearts"],
              heart=config.HEART) + "\n"
            + t(lang, "hearts.streak", n=u["streak"],
                best=u["best_streak"])
        )
        embed.add_field(
            name=t(lang, "hearts.stats"),
            value=(
                f"{t(lang, 'profile.earned')}: **{u['total_earned']:,}**\n"
                f"{t(lang, 'profile.spent')}: **{u['total_spent']:,}**\n"
                f"{t(lang, 'profile.dailies')}: **{u['dailies_claimed']}**\n"
                f"{t(lang, 'profile.purchases')}: **{u['items_bought']}**"
            ), inline=True)
        embed.add_field(
            name=t(lang, "hearts.game_social"),
            value=(
                f"{t(lang, 'hearts.flips_won')}: "
                f"**{u['flips_won']}/{u['flips_played']}**\n"
                f"{t(lang, 'profile.invited')}: **{u['invites_count']}**"
            ), inline=True)
        embed.set_footer(text=f"{config.BOT_NAME} • {config.BOT_TAGLINE}")
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="daily",
                          description="Reclama tu recompensa diaria.")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        today = date.today()
        result = await self.bot.db.claim_daily(
            interaction.guild.id, interaction.user.id,
            today.isoformat(), (today - timedelta(days=1)).isoformat(),
            config.DAILY_BASE, config.DAILY_STREAK_BONUS)

        if result is None:
            embed = discord.Embed(
                title=t(lang, "daily.already_title"),
                description=t(lang, "daily.already_desc"),
                color=config.COLOR_WARNING)
            return await interaction.followup.send(embed=embed,
                                                 ephemeral=True)

        reward, streak = result
        embed = discord.Embed(
            title=t(lang, "daily.title"),
            description=f"# +{reward} {config.HEART}",
            color=config.COLOR_SUCCESS)
        embed.add_field(name=t(lang, "daily.streak_field"),
                        value=t(lang, "daily.streak_value", n=streak),
                        inline=True)
        embed.add_field(
            name=t(lang, "daily.breakdown"),
            value=t(lang, "daily.breakdown_val", base=config.DAILY_BASE,
                    bonus=config.DAILY_STREAK_BONUS, streak=streak),
            inline=True)
        embed.set_footer(text=t(lang, "daily.footer"))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="streak",
                          description="Muestra tu racha de actividad diaria actual.")
    @app_commands.guild_only()
    async def streak(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        u = await self.bot.db.get_user(interaction.guild.id,
                                       interaction.user.id)
        streak = u["streak"]
        bar = "🟥" * min(streak, 10) + "⬜" * max(0, 10 - streak)
        embed = discord.Embed(
            title=t(lang, "streak.title"),
            description=t(lang, "streak.desc", n=streak, bar=bar),
            color=config.EMBED_COLOR)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        next_bonus = config.DAILY_BASE + config.DAILY_STREAK_BONUS * (streak + 1)
        embed.add_field(name=t(lang, "streak.best"),
                        value=t(lang, "streak.best_val", n=u["best_streak"]),
                        inline=True)
        embed.add_field(name=t(lang, "streak.next"),
                        value=f"**{next_bonus} {config.HEART}**", inline=True)
        embed.set_footer(text=t(lang, "streak.footer"))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard",
                          description="Tabla de clasificación de usuarios con más Hearts.")
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        rows = await self.bot.db.leaderboard(interaction.guild.id, 10)
        embed = discord.Embed(title=t(lang, "lb.title"),
                              color=config.EMBED_COLOR)
        if not rows:
            embed.description = t(lang, "lb.empty")
        else:
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for i, r in enumerate(rows):
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                lines.append(
                    f"{medal} <@{r['user_id']}>\n"
                    f"╰─ **{r['hearts']:,} {config.HEART}**")
            embed.description = "\n".join(lines)

        rank = await self.bot.db.user_rank(interaction.guild.id,
                                           interaction.user.id)
        embed.set_footer(text=t(lang, "lb.footer", rank=rank))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)


    @app_commands.command(
        name="work",
        description="Trabaja para ganar Hearts (cooldown de 4 horas).")
    @app_commands.guild_only()
    async def work(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        u = await db.get_user(guild_id, user_id)

        left = _cd_left(u["last_work"], config.WORK_COOLDOWN_HOURS)
        if left:
            return await interaction.followup.send(
                t(lang, "work.tired", left=_fmt_cd(left)), ephemeral=True)

        reward = random.randint(*config.WORK_REWARD)
        await db.claim_work(guild_id, user_id,
                            discord.utils.utcnow().replace(tzinfo=None)
                            .isoformat(), reward)

        trabajos = t(lang, "work.jobs").split("|")
        embed = discord.Embed(
            title=t(lang, "work.title"),
            description=f"{random.choice(trabajos)}\n\n"
                        f"# +{reward} {config.HEART}",
            color=config.COLOR_SUCCESS)
        embed.set_footer(
            text=t(lang, "work.footer", h=config.WORK_COOLDOWN_HOURS))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="rob",
        description="Intenta robarle Hearts a otro usuario (arriesgado).")
    @app_commands.describe(usuario="A quién intentas robarle")
    @app_commands.guild_only()
    async def rob(self, interaction: discord.Interaction,
                  usuario: discord.Member):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild, user = interaction.guild, interaction.user

        if usuario.bot or usuario.id == user.id:
            return await interaction.followup.send(
                t(lang, "rob.invalid"), ephemeral=True)

        u = await db.get_user(guild.id, user.id)
        left = _cd_left(u["last_rob"], config.ROB_COOLDOWN_HOURS)
        if left:
            return await interaction.followup.send(
                t(lang, "rob.rest", left=_fmt_cd(left)), ephemeral=True)

        victima = await db.get_user(guild.id, usuario.id)
        if victima["hearts"] < config.ROB_MIN_STEAL:
            return await interaction.followup.send(
                t(lang, "rob.poor", user=usuario.mention,
                  n=victima["hearts"]), ephemeral=True)

        await db.set_timestamp(
            guild.id, user.id, "last_rob",
            discord.utils.utcnow().replace(tzinfo=None).isoformat())

        if random.random() < config.ROB_SUCCESS:
            robado = max(config.ROB_MIN_STEAL,
                         int(victima["hearts"] * config.ROB_MAX_PCT))
            robado = min(robado, victima["hearts"])
            await db.spend_hearts(guild.id, usuario.id, robado)
            await db.add_hearts(guild.id, user.id, robado)
            embed = discord.Embed(
                title=t(lang, "rob.win_title"),
                description=t(lang, "rob.win_desc", n=robado,
                              heart=config.HEART, user=usuario.mention),
                color=config.COLOR_SUCCESS)
        else:
            perdida = max(10, int(u["hearts"] * config.ROB_FAIL_LOSS))
            perdida = min(perdida, u["hearts"])
            await db.spend_hearts(guild.id, user.id, perdida)
            embed = discord.Embed(
                title=t(lang, "rob.lose_title"),
                description=t(lang, "rob.lose_desc", user=usuario.mention,
                              n=perdida, heart=config.HEART),
                color=config.COLOR_ERROR)
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
