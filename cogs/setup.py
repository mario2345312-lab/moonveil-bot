"""Comando /setup: configuración por servidor guardada en la DB."""

import discord
from discord import app_commands
from discord.ext import commands

import config


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup = app_commands.Group(
        name="setup",
        description="Configura el bot en este servidor (solo admins).",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    async def _set_channel(self, interaction, key: str,
                           channel: discord.TextChannel, label: str):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id, key, channel.id)
        await interaction.followup.send(
            f"✅ {label} configurado: {channel.mention}", ephemeral=True)

    @setup.command(name="canal-compras",
                   description="Canal donde llegan las solicitudes de compra.")
    async def canal_compras(self, interaction: discord.Interaction,
                            canal: discord.TextChannel):
        await self._set_channel(interaction, "buy_channel_id", canal,
                                "Canal de compras")

    @setup.command(name="canal-logros",
                   description="Canal donde llegan los reclamos de logros.")
    async def canal_logros(self, interaction: discord.Interaction,
                           canal: discord.TextChannel):
        await self._set_channel(interaction, "ach_channel_id", canal,
                                "Canal de logros")

    @setup.command(name="canal-misiones",
                   description="Canal donde llegan los reclamos de misiones.")
    async def canal_misiones(self, interaction: discord.Interaction,
                             canal: discord.TextChannel):
        await self._set_channel(interaction, "mis_channel_id", canal,
                                "Canal de misiones")

    @setup.command(name="canal-logs",
                   description="Canal donde el bot registra sus acciones.")
    async def canal_logs(self, interaction: discord.Interaction,
                         canal: discord.TextChannel):
        await self._set_channel(interaction, "log_channel_id", canal,
                                "Canal de logs")

    @setup.command(name="rol-staff",
                   description="Rol que puede aprobar/rechazar solicitudes.")
    async def rol_staff(self, interaction: discord.Interaction,
                        rol: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id, "staff_role_id",
                                      rol.id)
        await interaction.followup.send(
            f"✅ Rol de staff configurado: {rol.mention}", ephemeral=True)

    @setup.command(name="rol-vip",
                   description="Rol que entrega el item 'Acceso VIP'.")
    async def rol_vip(self, interaction: discord.Interaction,
                      rol: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id, "vip_role_id",
                                      rol.id)
        await interaction.followup.send(
            f"✅ Rol VIP configurado: {rol.mention}", ephemeral=True)

    @setup.command(name="rol-espanol",
                   description="Rol de miembros que hablan español (idioma del bot).")
    async def rol_espanol(self, interaction: discord.Interaction,
                          rol: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id, "lang_es_role_id",
                                      rol.id)
        await interaction.followup.send(
            f"✅ Rol de español configurado: {rol.mention}", ephemeral=True)

    @setup.command(name="rol-ingles",
                   description="Rol de miembros que hablan inglés (idioma del bot).")
    async def rol_ingles(self, interaction: discord.Interaction,
                         rol: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id, "lang_en_role_id",
                                      rol.id)
        await interaction.followup.send(
            f"✅ Rol de inglés configurado: {rol.mention}", ephemeral=True)

    async def _create_upload_channel(self, interaction: discord.Interaction,
                                     key: str, channel_name: str,
                                     label: str, topic: str):
        """Crea un canal privado para staff y lo guarda en settings."""
        await interaction.response.defer(ephemeral=True)
        g = interaction.guild
        s = await self.bot.db.get_settings(g.id)

        existente = g.get_channel(s.get(key) or 0)
        if existente:
            return await interaction.followup.send(
                f"ℹ️ Ya está configurado: {existente.mention}\n"
                "▫️ Si quieres otro canal, bórralo y vuelve a usar este comando.",
                ephemeral=True)

        overwrites = {
            g.default_role: discord.PermissionOverwrite(view_channel=False),
            g.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                manage_messages=True, add_reactions=True),
        }
        staff_role = g.get_role(s.get("staff_role_id") or 0)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, attach_files=True)

        try:
            canal = await g.create_text_channel(
                name=channel_name, overwrites=overwrites, topic=topic,
                reason=f"Canal de {label} creado por {interaction.user} "
                       "vía /setup")
        except discord.HTTPException as e:
            return await interaction.followup.send(
                f"❌ No pude crear el canal: {e.text}", ephemeral=True)

        await self.bot.db.set_setting(g.id, key, canal.id)
        await interaction.followup.send(
            f"✅ Canal de {label} creado: {canal.mention}\n"
            "▫️ Solo el staff puede verlo y subir imágenes ahí.",
            ephemeral=True)

    @setup.command(name="canal-emojis",
                   description="Crea el canal donde el staff sube imágenes y el "
                               "bot las convierte en emojis automáticamente.")
    async def canal_emojis(self, interaction: discord.Interaction):
        await self._create_upload_channel(
            interaction, "emoji_channel_id", "emojis-auto", "emojis",
            "Sube imágenes aquí y el bot las convierte en emojis ✅")

    @setup.command(name="canal-stickers",
                   description="Crea el canal donde el staff sube imágenes y el "
                               "bot las convierte en stickers automáticamente.")
    async def canal_stickers(self, interaction: discord.Interaction):
        await self._create_upload_channel(
            interaction, "sticker_channel_id", "stickers-auto", "stickers",
            "Sube imágenes aquí y el bot las convierte en stickers ✅")

    @setup.command(name="canal-bienvenida",
                   description="Canal donde el bot saluda a los nuevos miembros.")
    async def canal_bienvenida(self, interaction: discord.Interaction,
                               canal: discord.TextChannel):
        await self._set_channel(interaction, "welcome_channel_id", canal,
                                "Canal de bienvenida")

    @setup.command(name="canal-sugerencias",
                   description="Canal de sugerencias en español (los mensajes se convierten en votables).")
    async def canal_sugerencias(self, interaction: discord.Interaction,
                                canal: discord.TextChannel):
        await self._set_channel(interaction, "suggestion_channel_id", canal,
                                "Canal de sugerencias (español)")

    @setup.command(name="canal-sugerencias-en",
                   description="Canal de sugerencias en inglés (los mensajes se convierten en votables).")
    async def canal_sugerencias_en(self, interaction: discord.Interaction,
                                   canal: discord.TextChannel):
        await self._set_channel(interaction, "suggestion_channel_en_id", canal,
                                "Canal de sugerencias (inglés)")

    @setup.command(name="categoria-canales",
                   description="Categoría donde se crean los canales privados temporales.")
    async def categoria_canales(self, interaction: discord.Interaction,
                                categoria: discord.CategoryChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.set_setting(interaction.guild.id,
                                      "temp_category_id", categoria.id)
        await interaction.followup.send(
            f"✅ Categoría de canales temporales: **{categoria.name}**",
            ephemeral=True)

    @setup.command(name="estado",
                   description="Muestra la configuración actual del servidor.")
    async def estado(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        s = await self.bot.db.get_settings(interaction.guild.id)
        g = interaction.guild

        def ch(key):
            cid = s.get(key)
            return g.get_channel(cid).mention if cid and g.get_channel(cid) else "❌ sin configurar"

        def rl(key):
            rid = s.get(key)
            role = g.get_role(rid) if rid else None
            return role.mention if role else ("❌ sin configurar" if rid else "↩️ automático")

        embed = discord.Embed(
            title=f"⚙️ Panel de configuración",
            description=f"Estado actual de **{g.name}**:",
            color=config.EMBED_COLOR)
        embed.set_thumbnail(url=g.icon.url if g.icon else None)
        embed.add_field(
            name="📋 Canales del staff",
            value=(
                f"🛒 Compras: {ch('buy_channel_id')}\n"
                f"🏆 Logros: {ch('ach_channel_id')}\n"
                f"📜 Misiones: {ch('mis_channel_id')}\n"
                f"📋 Logs: {ch('log_channel_id')}"
            ), inline=False)
        embed.add_field(
            name="🎉 Comunidad",
            value=(
                f"👋 Bienvenida: {ch('welcome_channel_id')}\n"
                f"💡 Sugerencias 🇪🇸: {ch('suggestion_channel_id')}\n"
                f"💡 Suggestions 🇺🇸: {ch('suggestion_channel_en_id')}"
            ), inline=False)
        embed.add_field(
            name="🎨 Subida automática",
            value=(
                f"Emojis: {ch('emoji_channel_id')}\n"
                f"Stickers: {ch('sticker_channel_id')}\n"
                "╰─ Crea los canales con `/setup canal-emojis` y "
                "`/setup canal-stickers`"
            ), inline=False)
        embed.add_field(
            name="🛡️ Roles",
            value=(
                f"Staff: {rl('staff_role_id')}\n"
                f"💎 VIP: {rl('vip_role_id')}\n"
                f"🇪🇸 Español: {rl('lang_es_role_id')}\n"
                f"🇺🇸 English: {rl('lang_en_role_id')}"
            ), inline=True)

        cat = g.get_channel(s.get("temp_category_id") or 0)
        embed.add_field(
            name="📁 Canales temporales",
            value=cat.name if cat else "↩️ sin categoría",
            inline=True)

        me = g.me
        perms = me.guild_permissions
        checks = [
            ("Gestionar Roles", perms.manage_roles),
            ("Gestionar Canales", perms.manage_channels),
            ("Gestionar Servidor (invites)", perms.manage_guild),
            ("Gestionar Emojis y Stickers", perms.manage_emojis),
        ]
        embed.add_field(
            name="🔐 Permisos del bot",
            value="\n".join(f"{'✅' if ok else '⚠️'} {n}" for n, ok in checks),
            inline=False)
        embed.set_footer(text="Usa los subcomandos de /setup para completar los ❌")
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCog(bot))
