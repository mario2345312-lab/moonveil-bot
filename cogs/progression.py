"""Progresión: /achievements /missions /claim-achievement /claim-mision."""

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.review import grant_achievement_reward, submit_for_review
from i18n import t, user_lang
from logging_utils import send_log


def _is_image(att: discord.Attachment) -> bool:
    ct = att.content_type or ""
    return ct.startswith("image/") or att.filename.lower().endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".webp"))


class ProgressionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- /achievements ----------

    @app_commands.command(name="achievements",
                          description="Consulta tu lista de logros y su estado.")
    @app_commands.guild_only()
    async def achievements(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        user = await db.get_user(guild_id, user_id)
        claimed = await db.claimed_achievement_ids(guild_id, user_id)
        pending = await db.pending_submission_ids(guild_id, user_id,
                                                  "achievement")

        lines = []
        done_count = 0
        for ach in config.ACHIEVEMENTS:
            reward = []
            if ach.get("reward_hearts"):
                reward.append(f"{ach['reward_hearts']} {config.HEART}")
            if ach.get("role_name"):
                reward.append(t(lang, "prog.reward_role",
                                name=ach["role_name"]))
            reward_txt = " + ".join(reward) or t(lang, "prog.reward_special")

            if ach["id"] in claimed:
                estado = "✅"
                extra = t(lang, "prog.claimed")
                done_count += 1
            elif ach["id"] in pending:
                estado = "⏳"
                extra = t(lang, "prog.review")
            elif ach["verify"] == "auto":
                prog = user[ach["stat"]]
                if prog >= ach["threshold"]:
                    estado, extra = "🎁", t(lang, "prog.claimable")
                else:
                    estado, extra = "🔒", t(lang, "prog.progress", p=prog,
                                            n=ach["threshold"])
            else:
                estado, extra = "🔒", t(lang, "prog.needs_proof")

            lines.append(
                f"{estado} {ach['emoji']} **{ach['name']}**\n"
                f"╰─ *{ach['description']}* → {reward_txt} **·** {extra}")

        embed = discord.Embed(
            title=t(lang, "prog.ach_title"),
            description="\n\n".join(lines),
            color=config.EMBED_COLOR)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=t(lang, "prog.ach_footer", done=done_count,
                                total=len(config.ACHIEVEMENTS)))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    # ---------- /missions ----------

    @app_commands.command(
        name="missions",
        description="Muestra las misiones disponibles para ganar recompensas.")
    @app_commands.guild_only()
    async def missions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        rows = await db.get_mission_rows(guild_id, user_id)
        pending = await db.pending_submission_ids(guild_id, user_id, "mission")

        lines = []
        for m in config.MISSIONS:
            row = rows.get(m["id"])
            prog = row["progress"] if row else 0
            done = bool(row and row["completed"])
            reward = f"{m['reward_hearts']} {config.HEART}"

            if m["id"] in pending:
                estado, extra = "⏳", t(lang, "prog.mis_proof_review")
            elif done and not m.get("repeatable"):
                estado, extra = "✅", t(lang, "prog.mis_done")
            elif m["required_count"] > 1:
                estado, extra = "🎯", t(lang, "prog.mis_progress", p=prog,
                                        n=m["required_count"])
            else:
                estado, extra = "🎯", t(lang, "prog.mis_available")
                if m.get("repeatable") and done:
                    extra += " 🔁"

            lines.append(
                f"{estado} {m['emoji']} **{m['name']}** → {reward}\n"
                f"╰─ *{m['description']}* — {extra}")

        embed = discord.Embed(
            title=t(lang, "prog.mis_title"),
            description="\n\n".join(lines),
            color=config.EMBED_COLOR)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=t(lang, "prog.mis_footer"))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    # ---------- /claim-achievement ----------

    @app_commands.command(
        name="claim-achievement",
        description="Reclama una recompensa por logro completado.")
    @app_commands.describe(logro="Logro a reclamar",
                           captura="Captura del objetivo (obligatoria en logros de prueba)")
    @app_commands.guild_only()
    async def claim_achievement(self, interaction: discord.Interaction,
                                logro: str,
                                captura: discord.Attachment | None = None):
        db = self.bot.db
        guild, user = interaction.guild, interaction.user
        ach = config.get_achievement(logro)
        lang = await user_lang(self.bot, interaction)
        if ach is None:
            return await interaction.response.send_message(
                t(lang, "prog.not_found_ach"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        if ach["id"] in await db.claimed_achievement_ids(guild.id, user.id):
            return await interaction.followup.send(
                t(lang, "prog.already_ach"), ephemeral=True)
        if await db.has_pending(guild.id, user.id, "achievement", ach["id"]):
            return await interaction.followup.send(
                t(lang, "prog.pending_ach"), ephemeral=True)

        if ach["verify"] == "auto":
            u = await db.get_user(guild.id, user.id)
            if u[ach["stat"]] < ach["threshold"]:
                return await interaction.followup.send(
                    t(lang, "prog.not_yet", p=u[ach["stat"]],
                      n=ach["threshold"]), ephemeral=True)
            await db.claim_achievement(guild.id, user.id, ach["id"])
            detail = await grant_achievement_reward(self.bot, guild, user, ach)
            await interaction.followup.send(embed=discord.Embed(
                title=t(lang, "prog.ach_unlocked"),
                description=f"## {ach['emoji']} {ach['name']}\n"
                            f"*{ach['description']}*\n\n"
                            f"{t(lang, 'prog.reward_label')} {detail}",
                color=config.COLOR_SUCCESS))
            await send_log(self.bot, guild, "Logro reclamado",
                           f"{user.mention} reclamó **{ach['name']}** — {detail}",
                           config.COLOR_SUCCESS)
            return

        # proof: captura obligatoria -> canal de logros
        if captura is None or not _is_image(captura):
            return await interaction.followup.send(
                t(lang, "prog.needs_capture"), ephemeral=True)

        sub_id = await submit_for_review(
            self.bot, guild, user,
            kind="achievement", ref_id=ach["id"],
            title=ach["name"],
            description=f"Reclama el logro {ach['emoji']} **{ach['name']}** "
                        f"({ach['reward_hearts']} {config.HEART})\n"
                        f"*{ach['description']}*",
            proof_url=captura.url, payload=None,
            origin_channel_id=interaction.channel_id)
        label = "achievement" if lang == "en" else "logro"
        await _after_proof_submit(interaction, sub_id, lang,
                                  f"{label} **{ach['name']}**",
                                  "canal-logros")

    @claim_achievement.autocomplete("logro")
    async def ach_autocomplete(self, interaction: discord.Interaction,
                               current: str):
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        claimed = await db.claimed_achievement_ids(guild_id, user_id)
        pending = await db.pending_submission_ids(guild_id, user_id,
                                                  "achievement")
        return [
            app_commands.Choice(
                name=f"{a['emoji']} {a['name']}", value=a["id"])
            for a in config.ACHIEVEMENTS
            if a["id"] not in claimed and a["id"] not in pending
            and current.lower() in a["name"].lower()
        ][:25]

    # ---------- /claim-mision ----------

    @app_commands.command(
        name="claim-mision",
        description="Reclama una recompensa por misión completada.")
    @app_commands.describe(mision="Misión a reclamar",
                           captura="Captura del objetivo cumplido")
    @app_commands.guild_only()
    async def claim_mision(self, interaction: discord.Interaction,
                           mision: str, captura: discord.Attachment):
        db = self.bot.db
        guild, user = interaction.guild, interaction.user
        m = config.get_mission(mision)
        lang = await user_lang(self.bot, interaction)
        if m is None:
            return await interaction.response.send_message(
                t(lang, "prog.not_found_mis"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        if not _is_image(captura):
            return await interaction.followup.send(
                t(lang, "prog.needs_image"), ephemeral=True)

        row = (await db.get_mission_rows(guild.id, user.id)).get(m["id"])
        if row and row["completed"] and not m.get("repeatable"):
            return await interaction.followup.send(
                t(lang, "prog.mis_already"), ephemeral=True)
        if await db.has_pending(guild.id, user.id, "mission", m["id"]):
            return await interaction.followup.send(
                t(lang, "prog.mis_pending"), ephemeral=True)

        sub_id = await submit_for_review(
            self.bot, guild, user,
            kind="mission", ref_id=m["id"],
            title=m["name"],
            description=f"Reclama la misión {m['emoji']} **{m['name']}** "
                        f"({m['reward_hearts']} {config.HEART})\n"
                        f"*{m['description']}*",
            proof_url=captura.url, payload=None,
            origin_channel_id=interaction.channel_id)
        label = "mission" if lang == "en" else "misión"
        await _after_proof_submit(interaction, sub_id, lang,
                                  f"{label} **{m['name']}**",
                                  "canal-misiones")

    @claim_mision.autocomplete("mision")
    async def mis_autocomplete(self, interaction: discord.Interaction,
                               current: str):
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        rows = await db.get_mission_rows(guild_id, user_id)
        pending = await db.pending_submission_ids(guild_id, user_id, "mission")
        return [
            app_commands.Choice(name=f"{m['emoji']} {m['name']}", value=m["id"])
            for m in config.MISSIONS
            if m["id"] not in pending
            and not (rows.get(m["id"]) and rows[m["id"]]["completed"]
                     and not m.get("repeatable"))
            and current.lower() in m["name"].lower()
        ][:25]


async def _after_proof_submit(interaction: discord.Interaction,
                              sub_id: int | None, lang: str, label: str,
                              setup_cmd: str):
    if sub_id is None:
        return await interaction.followup.send(
            t(lang, "prog.no_channel", cmd=setup_cmd), ephemeral=True)
    await interaction.followup.send(
        embed=discord.Embed(
            title=t(lang, "prog.proof_sent"),
            description=t(lang, "prog.proof_desc", label=label),
            color=config.COLOR_WARNING),
        ephemeral=True)


async def setup(bot):
    await bot.add_cog(ProgressionCog(bot))
