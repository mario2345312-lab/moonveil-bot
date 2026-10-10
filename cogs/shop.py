"""Tienda: /shop y /buy (con modal para custom_role y expiración de canales)."""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import utcnow

import config
from cogs.review import execute_purchase, submit_for_review
from i18n import t, user_lang
from logging_utils import send_log


class CustomRoleModal(discord.ui.Modal):
    def __init__(self, bot, item: dict, lang: str = "es"):
        super().__init__(title=t(lang, "shop.modal_title"))
        self.bot = bot
        self.item = item
        self.lang = lang
        self.role_name = discord.ui.TextInput(
            label=t(lang, "shop.modal_name"), placeholder="Ej: Los Panas",
            max_length=100, required=True)
        self.role_color = discord.ui.TextInput(
            label=t(lang, "shop.modal_color"), placeholder="Ej: FF5733",
            min_length=6, max_length=7, required=True)
        self.add_item(self.role_name)
        self.add_item(self.role_color)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        color = self.role_color.value.strip().lstrip("#")
        try:
            int(color, 16)
            assert len(color) == 6
        except (ValueError, AssertionError):
            return await interaction.response.send_message(
                t(lang, "shop.bad_color"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        sub_id = await submit_for_review(
            self.bot, interaction.guild, interaction.user,
            kind="purchase", ref_id="custom_role",
            title=self.item["name"],
            description=(f"Quiere comprar **{self.item['name']}** "
                         f"({self.item['price']} {config.HEART})\n"
                         f"• Nombre: `{self.role_name.value}`\n"
                         f"• Color: `#{color}`"),
            proof_url=None,
            payload={"role_name": self.role_name.value, "role_color": color},
            origin_channel_id=interaction.channel_id)
        await _after_submit(interaction, sub_id, self.item, lang)


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channel_cleanup.start()

    def cog_unload(self):
        self.temp_channel_cleanup.cancel()

    # ---------- comandos ----------

    @app_commands.command(name="shop",
                          description="Muestra el catálogo con los productos disponibles.")
    @app_commands.guild_only()
    async def shop(self, interaction: discord.Interaction):
        lang = await user_lang(self.bot, interaction)
        embed = discord.Embed(
            title=t(lang, "shop.title", heart=config.HEART),
            description=t(lang, "shop.desc"),
            color=config.EMBED_COLOR)

        groups = {
            t(lang, "shop.g_custom"): ["custom_role"],
            t(lang, "shop.g_colors"):
                ["color_pink", "color_purple", "color_gold"],
            t(lang, "shop.g_vip"): ["exclusive_role"],
            t(lang, "shop.g_channel"): ["temp_channel"],
            t(lang, "shop.g_chests"): ["flower_chest", "diamond_chest"],
        }
        for group_name, ids in groups.items():
            lines = []
            for iid in ids:
                it = config.SHOP_ITEMS[iid]
                lines.append(
                    f"{it['emoji']} **{it['name']}** — `{iid}`\n"
                    f"╰─ {it['price']} {config.HEART}  •  *{it['description']}*")
            embed.add_field(name=group_name, value="\n".join(lines),
                            inline=False)

        embed.set_footer(
            text=t(lang, "shop.footer", bot=config.BOT_NAME))
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.defer()
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="buy",
                          description="Compra un artículo de la tienda usando tus Hearts.")
    @app_commands.describe(item="Artículo a comprar (ej: custom_role)")
    @app_commands.guild_only()
    async def buy(self, interaction: discord.Interaction, item: str):
        lang = await user_lang(self.bot, interaction)
        it = config.get_item(item)
        if it is None:
            return await interaction.response.send_message(
                t(lang, "shop.not_found"), ephemeral=True)

        guild, user = interaction.guild, interaction.user
        db = self.bot.db
        u = await db.get_user(guild.id, user.id)

        faltan = discord.Embed(
            title=t(lang, "shop.faltan"),
            description=t(lang, "shop.faltan_desc", emoji=it["emoji"],
                          name=it["name"], price=it["price"],
                          heart=config.HEART, have=u["hearts"]),
            color=config.COLOR_ERROR)

        # custom_role abre un modal, que debe ser la primera respuesta
        if it["type"] == "custom_role":
            if u["hearts"] < it["price"]:
                return await interaction.response.send_message(
                    embed=faltan, ephemeral=True)
            if await db.has_pending(guild.id, user.id, "purchase", item):
                return await interaction.response.send_message(
                    t(lang, "shop.pending"), ephemeral=True)
            if u["custom_role_id"] and guild.get_role(u["custom_role_id"]):
                return await interaction.response.send_message(
                    t(lang, "shop.has_role"), ephemeral=True)
            return await interaction.response.send_modal(
                CustomRoleModal(self.bot, it, lang))

        await interaction.response.defer(ephemeral=True)

        if u["hearts"] < it["price"]:
            return await interaction.followup.send(embed=faltan,
                                                 ephemeral=True)
        if await db.has_pending(guild.id, user.id, "purchase", item):
            return await interaction.followup.send(
                t(lang, "shop.pending"), ephemeral=True)

        # validaciones por tipo antes de crear la solicitud
        typ = it["type"]
        if typ == "color_role":
            role = discord.utils.get(guild.roles, name=it["name"])
            if role and role in user.roles:
                return await interaction.followup.send(
                    t(lang, "shop.has_color", name=it["name"]),
                    ephemeral=True)

        if typ == "vip_role":
            s = await db.get_settings(guild.id)
            role = (guild.get_role(s.get("vip_role_id") or 0)
                    or discord.utils.get(guild.roles, name="VIP"))
            if role and role in user.roles:
                return await interaction.followup.send(
                    t(lang, "shop.has_vip"), ephemeral=True)

        if typ == "temp_channel":
            if await db.active_temp_channel(guild.id, user.id):
                return await interaction.followup.send(
                    t(lang, "shop.has_channel"), ephemeral=True)

        if it.get("requires_approval", True):
            sub_id = await submit_for_review(
                self.bot, guild, user,
                kind="purchase", ref_id=item,
                title=it["name"],
                description=f"Quiere comprar **{it['emoji']} {it['name']}** "
                            f"({it['price']} {config.HEART})",
                proof_url=None, payload=None,
                origin_channel_id=interaction.channel_id)
            await _after_submit(interaction, sub_id, it, lang)
        else:
            if not await db.spend_hearts(guild.id, user.id, it["price"]):
                return await interaction.followup.send(
                    t(lang, "shop.no_funds"), ephemeral=True)
            ok, detail = await execute_purchase(self.bot, guild, user, it, None)
            if not ok:
                await db.add_hearts(guild.id, user.id, it["price"])
                return await interaction.followup.send(
                    f"❌ {detail}", ephemeral=True)
            await db.bump_stat(guild.id, user.id, "items_bought")
            await interaction.followup.send(
                embed=discord.Embed(
                    title=t(lang, "shop.done", emoji=it["emoji"]),
                    description=f"**{it['name']}**\n\n{detail}",
                    color=config.COLOR_SUCCESS))
            await send_log(self.bot, guild, "Compra directa",
                           f"{user.mention} compró **{it['name']}** — {detail}",
                           config.COLOR_SUCCESS)

    @buy.autocomplete("item")
    async def buy_autocomplete(self, interaction: discord.Interaction,
                               current: str):
        return [
            app_commands.Choice(
                name=f"{it['emoji']} {it['name']} — {it['price']}♥",
                value=iid)
            for iid, it in config.SHOP_ITEMS.items()
            if current.lower() in iid or current.lower() in it["name"].lower()
        ][:25]

    # ---------- expiración de canales temporales ----------

    @tasks.loop(minutes=1)
    async def temp_channel_cleanup(self):
        for row in await self.bot.db.expired_temp_channels(utcnow().isoformat()):
            guild = self.bot.get_guild(row["guild_id"])
            channel = guild.get_channel(row["channel_id"]) if guild else None
            if channel:
                try:
                    await channel.delete(
                        reason=f"{config.BOT_NAME}: canal temporal expirado")
                except discord.HTTPException:
                    pass
            await self.bot.db.remove_temp_channel(row["channel_id"])
            if guild:
                await send_log(self.bot, guild, "Canal temporal expirado",
                               f"Canal de <@{row['owner_id']}> eliminado.")

    @temp_channel_cleanup.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


async def _after_submit(interaction: discord.Interaction,
                        sub_id: int | None, item: dict, lang: str = "es"):
    if sub_id is None:
        return await interaction.followup.send(
            t(lang, "shop.no_channel"), ephemeral=True)
    await interaction.followup.send(
        embed=discord.Embed(
            title=t(lang, "shop.sent"),
            description=t(lang, "shop.sent_desc", emoji=item["emoji"],
                          name=item["name"], price=item["price"],
                          heart=config.HEART),
            color=config.COLOR_WARNING),
        ephemeral=True)


async def setup(bot):
    await bot.add_cog(ShopCog(bot))
