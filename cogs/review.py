"""Sistema de revisión: solicitudes con botones Aprobar/Rechazar para staff.

Todos los efectos (compras, reclamos de logro y misión) pasan por aquí.
La vista es persistente (timeout=None, custom_id fijos) para sobrevivir reinicios;
el id de la solicitud viaja en el footer del embed ("SID:<id>").
"""

import json
import random
from datetime import timedelta

import discord
from discord.ext import commands

import config
from i18n import member_lang, t
from logging_utils import send_log

KIND_CHANNEL_KEY = {
    "purchase": "buy_channel_id",
    "achievement": "ach_channel_id",
    "mission": "mis_channel_id",
    "trade": "trade_channel_id",
}

KIND_LABEL = {
    "purchase": "🛒 Compra",
    "achievement": "🏆 Reclamo de logro",
    "mission": "📜 Reclamo de misión",
    "trade": "🔄 Trade",
}


def staff_role_ids(settings: dict) -> list[int]:
    """Lista de roles staff (multi-rol), con fallback a staff_role_id."""
    import json
    raw = settings.get("staff_role_ids")
    if raw:
        try:
            return [int(x) for x in json.loads(raw)]
        except (ValueError, TypeError):
            pass
    rid = settings.get("staff_role_id")
    return [rid] if rid else []


def is_staff(member: discord.Member, settings: dict) -> bool:
    if member.id in config.OWNER_IDS:
        return True
    if member.guild_permissions.manage_guild or member.guild_permissions.administrator:
        return True
    ids = set(staff_role_ids(settings))
    return bool(ids) and any(r.id in ids for r in member.roles)


def is_vip(member: discord.Member, settings: dict) -> bool:
    rid = settings.get("vip_role_id")
    if rid:
        return any(r.id == rid for r in member.roles)
    role = discord.utils.get(member.guild.roles, name="VIP")
    return role is not None and role in member.roles


async def notify_user(bot, guild: discord.Guild, user_id: int,
                      fallback_channel_id: int | None, embed: discord.Embed):
    """Avisa al usuario por DM; si falla, por el canal donde se originó."""
    try:
        user = await bot.fetch_user(user_id)
        await user.send(embed=embed)
    except discord.HTTPException:
        if fallback_channel_id:
            channel = guild.get_channel(fallback_channel_id)
            if channel:
                try:
                    await channel.send(f"<@{user_id}>", embed=embed)
                except discord.HTTPException:
                    pass


async def submit_for_review(bot, guild: discord.Guild, user: discord.abc.User,
                            kind: str, ref_id: str, title: str,
                            description: str, proof_url: str | None,
                            payload: dict | None,
                            origin_channel_id: int) -> int | None:
    """Crea la solicitud y la publica en el canal de revisión correspondiente.

    Devuelve el id de la solicitud, o None si el canal no está configurado.
    """
    settings = await bot.db.get_settings(guild.id)
    channel = guild.get_channel(settings.get(KIND_CHANNEL_KEY[kind]) or 0)
    if channel is None:
        return None

    sub_id = await bot.db.create_submission(
        guild.id, user.id, kind, ref_id,
        json.dumps(payload) if payload else None,
        proof_url, origin_channel_id,
    )

    embed = discord.Embed(title=f"{KIND_LABEL[kind]} — {title}",
                          description=description, color=config.COLOR_WARNING,
                          timestamp=discord.utils.utcnow())
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="👤 Usuario", value=user.mention, inline=True)
    embed.add_field(name="🆔 ID", value=f"`{user.id}`", inline=True)
    embed.set_footer(text=f"SID:{sub_id}")
    if proof_url:
        embed.set_image(url=proof_url)

    msg = await channel.send(embed=embed, view=ReviewView(bot))
    await bot.db.set_submission(sub_id, "pending", review_message_id=msg.id)
    await send_log(bot, guild, "Nueva solicitud",
                   f"{KIND_LABEL[kind]} de {user.mention}: **{title}**",
                   config.COLOR_WARNING)
    return sub_id


# ---------- ejecución de efectos ----------

async def _find_or_create_role(guild: discord.Guild, name: str,
                               color: int | None = None) -> discord.Role | None:
    role = discord.utils.get(guild.roles, name=name)
    if role is None:
        try:
            role = await guild.create_role(
                name=name,
                colour=discord.Colour(color) if color else discord.Colour.default(),
                reason=f"{config.BOT_NAME}: rol de tienda/logro",
            )
        except discord.Forbidden:
            return None
    return role


async def _assign_role(member: discord.Member, role: discord.Role,
                       lang: str = "es") -> str | None:
    try:
        await member.add_roles(role, reason=f"{config.BOT_NAME}: compra/logro aprobado")
        return None
    except discord.Forbidden:
        return t(lang, "rev.role_fail", role=role.name)


async def execute_purchase(bot, guild: discord.Guild, member: discord.Member,
                           item: dict, payload: dict | None,
                           lang: str = "es") -> tuple[bool, str]:
    """Aplica el efecto del item. Devuelve (ok, detalle/error)."""
    typ = item["type"]

    if typ == "custom_role":
        name = (payload or {}).get("role_name", "Rol Personalizado")[:100]
        try:
            color = discord.Colour(int((payload or {}).get("role_color", "9B59B6"), 16))
        except (ValueError, TypeError):
            color = discord.Colour(config.EMBED_COLOR)
        try:
            role = await guild.create_role(
                name=name, colour=color,
                reason=f"{config.BOT_NAME}: rol personalizado de {member}",
            )
        except discord.Forbidden:
            return False, t(lang, "rev.custom_fail")
        err = await _assign_role(member, role, lang)
        if err:
            return False, err
        await bot.db.set_custom_role(guild.id, member.id, role.id)
        return True, t(lang, "rev.custom_ok", role=role.mention)

    if typ == "color_role":
        role = await _find_or_create_role(guild, item["name"], item["color"])
        if role is None:
            return False, t(lang, "rev.color_fail")
        to_remove = []
        for cid in config.COLOR_ITEM_IDS:
            other = discord.utils.get(guild.roles, name=config.SHOP_ITEMS[cid]["name"])
            if other and other in member.roles and other != role:
                to_remove.append(other)
        if to_remove:
            try:
                await member.remove_roles(*to_remove)
            except discord.HTTPException:
                pass
        err = await _assign_role(member, role, lang)
        if err:
            return False, err
        return True, t(lang, "rev.color_ok", role=role.mention)

    if typ == "vip_role":
        settings = await bot.db.get_settings(guild.id)
        role = guild.get_role(settings.get("vip_role_id") or 0)
        if role is None:
            role = await _find_or_create_role(guild, "VIP", config.EMBED_COLOR)
        if role is None:
            return False, t(lang, "rev.vip_fail")
        err = await _assign_role(member, role, lang)
        if err:
            return False, err
        return True, t(lang, "rev.vip_ok", role=role.mention)

    if typ == "temp_channel":
        settings = await bot.db.get_settings(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True,
                                                  manage_channels=True),
        }
        for rid in staff_role_ids(settings):
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)
        category = guild.get_channel(settings.get("temp_category_id") or 0)
        expires = discord.utils.utcnow() + timedelta(
            hours=config.TEMP_CHANNEL_HOURS)
        try:
            channel = await guild.create_text_channel(
                name=f"🔒・{member.display_name}"[:100],
                overwrites=overwrites, category=category,
                reason=f"{config.BOT_NAME}: canal temporal de {member}",
            )
        except discord.Forbidden:
            return False, t(lang, "rev.channel_fail")
        await bot.db.add_temp_channel(channel.id, guild.id, member.id,
                                      expires.isoformat())
        return True, t(lang, "rev.channel_ok", channel=channel.mention,
                       hours=config.TEMP_CHANNEL_HOURS)

    if typ == "chest":
        reward = random.randint(item["min_reward"], item["max_reward"])
        await bot.db.add_hearts(guild.id, member.id, reward)
        return True, t(lang, "rev.chest", reward=reward, heart=config.HEART,
                       price=item["price"])

    return False, t(lang, "rev.unknown_item")


async def grant_achievement_reward(bot, guild: discord.Guild,
                                   member: discord.Member,
                                   ach: dict, lang: str = "es") -> str:
    """Entrega hearts y/o rol del logro. Devuelve detalle para mensajes."""
    parts = []
    if ach.get("reward_hearts"):
        await bot.db.add_hearts(guild.id, member.id, ach["reward_hearts"])
        parts.append(f"**{ach['reward_hearts']} {config.HEART}**")
    role = None
    if ach.get("reward_role_id"):
        role = guild.get_role(ach["reward_role_id"])
    elif ach.get("role_name"):
        role = await _find_or_create_role(guild, ach["role_name"],
                                          ach.get("role_color"))
    if ach.get("reward_role_id") and role is None:
        parts.append(t(lang, "rev.role_missing"))
    elif ach.get("role_name") or ach.get("reward_role_id"):
        if role is None:
            parts.append(t(lang, "rev.role_perm"))
        else:
            err = await _assign_role(member, role, lang)
            parts.append(err or t(lang, "rev.role_part",
                                  role=role.mention))
    return " y ".join(parts) if parts else t(lang, "rev.delivered")


# ---------- vista persistente ----------

class ReviewView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def _submission_id(self, interaction: discord.Interaction) -> int | None:
        try:
            footer = interaction.message.embeds[0].footer.text or ""
            return int(footer.split("SID:")[1])
        except (IndexError, ValueError, AttributeError):
            return None

    async def _handle(self, interaction: discord.Interaction, approve: bool):
        sub_id = self._submission_id(interaction)
        sub = await self.bot.db.get_submission(sub_id) if sub_id else None
        if sub is None:
            return await interaction.response.send_message(
                "Solicitud no encontrada.", ephemeral=True)
        if sub["status"] != "pending":
            return await interaction.response.send_message(
                "Esta solicitud ya fue procesada.", ephemeral=True)

        settings = await self.bot.db.get_settings(interaction.guild.id)
        if not is_staff(interaction.user, settings):
            return await interaction.response.send_message(
                "Solo el staff puede revisar solicitudes.", ephemeral=True)

        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(sub["user_id"])
        if member is None:
            try:
                member = await guild.fetch_member(sub["user_id"])
            except discord.NotFound:
                await self.bot.db.set_submission(sub_id, "rejected")
                return await interaction.followup.send(
                    "El usuario ya no está en el servidor. Solicitud rechazada.",
                    ephemeral=True)

        # idioma del solicitante (preferencia o rol de idioma)
        u = await self.bot.db.get_user(guild.id, member.id)
        lang = member_lang(settings, member, u["lang"])

        if approve:
            ok, detail = await self._approve(guild, member, sub, lang)
            status = "approved" if ok else "rejected"
        else:
            ok, detail = False, t(lang, "rev.rejected_detail")
            status = "rejected"

        await self.bot.db.set_submission(sub_id, status)

        embed = interaction.message.embeds[0]
        verdict = discord.Embed.from_dict(embed.to_dict())
        verdict.color = config.COLOR_SUCCESS if ok else config.COLOR_ERROR
        verdict.title = f"{embed.title} — {'✅ Aprobada' if ok else '❌ Rechazada'}"
        verdict.add_field(name="🔍 Revisado por",
                          value=interaction.user.mention, inline=True)
        await interaction.message.edit(embed=verdict, view=None)

        titulo_limpio = embed.title.replace(
            KIND_LABEL[sub["kind"]] + " — ", "")
        user_embed = discord.Embed(
            title=t(lang, "rev.approved") if ok else t(lang, "rev.rejected"),
            description=f"**{titulo_limpio}**\n\n{detail}",
            color=config.COLOR_SUCCESS if ok else config.COLOR_ERROR)
        user_embed.set_footer(text=f"{config.BOT_NAME} • {config.BOT_TAGLINE}")
        await notify_user(self.bot, guild, sub["user_id"], sub["channel_id"],
                          user_embed)
        await send_log(
            self.bot, guild,
            "Solicitud aprobada" if ok else "Solicitud rechazada",
            f"{KIND_LABEL[sub['kind']]} #{sub_id} de <@{sub['user_id']}> — {detail}",
            config.COLOR_SUCCESS if ok else config.COLOR_ERROR,
            fields=[("Revisado por", interaction.user.mention)],
        )
        if not ok and approve:
            await interaction.followup.send(
                f"⚠️ Aprobación fallida: {detail}", ephemeral=True)

    async def _approve(self, guild, member, sub,
                       lang: str = "es") -> tuple[bool, str]:
        kind = sub["kind"]

        if kind == "purchase":
            item = config.get_item(sub["ref_id"])
            if item is None:
                return False, t(lang, "rev.item_gone")
            if not await self.bot.db.spend_hearts(guild.id, member.id,
                                                  item["price"]):
                return False, t(lang, "rev.no_funds", price=item["price"],
                                heart=config.HEART)
            payload = json.loads(sub["payload_json"]) if sub["payload_json"] else None
            ok, detail = await execute_purchase(self.bot, guild, member, item,
                                                payload, lang)
            if not ok:
                await self.bot.db.add_hearts(guild.id, member.id, item["price"])
                return False, detail
            await self.bot.db.bump_stat(guild.id, member.id, "items_bought")
            return True, detail

        if kind == "mission":
            mission = config.get_mission(sub["ref_id"])
            if mission is None:
                return False, t(lang, "rev.mis_gone")
            completed = await self.bot.db.bump_mission(
                guild.id, member.id, mission["id"], mission["required_count"])
            if completed:
                await self.bot.db.add_hearts(guild.id, member.id,
                                             mission["reward_hearts"])
                if mission.get("repeatable"):
                    await self.bot.db.reset_mission(guild.id, member.id,
                                                    mission["id"])
                return True, t(lang, "rev.mis_done", name=mission["name"],
                               hearts=mission["reward_hearts"],
                               heart=config.HEART)
            row = (await self.bot.db.get_mission_rows(
                guild.id, member.id))[mission["id"]]
            return True, t(lang, "rev.mis_progress", name=mission["name"],
                           p=row["progress"], n=mission["required_count"])

        if kind == "trade":
            is_v = is_vip(member, settings)
            reward = round(config.TRADE_REWARD * (config.VIP_HEARTS_MULT if is_v else 1.0))
            await self.bot.db.add_hearts(guild.id, member.id, reward)
            return True, t(lang, "rev.trade_done",
                           hearts=reward, heart=config.HEART,
                           vip=" 💎" if is_v else "")

        if kind == "achievement":
            ach = config.get_achievement(sub["ref_id"])
            if ach is None:
                return False, t(lang, "rev.ach_gone")
            await self.bot.db.claim_achievement(guild.id, member.id, ach["id"])
            detail = await grant_achievement_reward(self.bot, guild, member,
                                                    ach, lang)
            return True, t(lang, "rev.ach_done", name=ach["name"],
                           detail=detail)

        return False, t(lang, "rev.unknown_kind")

    @discord.ui.button(label="Aprobar", style=discord.ButtonStyle.success,
                       emoji="✅", custom_id="review:approve")
    async def approve(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        await self._handle(interaction, approve=True)

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.danger,
                       emoji="❌", custom_id="review:reject")
    async def reject(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        await self._handle(interaction, approve=False)


class ReviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(ReviewCog(bot))
