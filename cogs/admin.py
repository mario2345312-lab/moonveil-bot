"""Comandos de staff: /hearts-admin + subida rápida de emojis/stickers."""

import asyncio
import io
import random
import re

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.review import is_staff
from logging_utils import send_log

EMOJI_NAME_RE = re.compile(r"^[A-Za-z0-9_]{2,32}$")
CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):(\d+)>")


def _auto_names(existing: set[str], prefix: str, count: int = 8) -> list[str]:
    """Genera nombres libres tipo emoji_482 / sticker_731."""
    cands = []
    for _ in range(count * 4):
        c = f"{prefix}_{random.randint(100, 999)}"
        if c not in existing and c not in cands:
            cands.append(c)
            if len(cands) == count:
                break
    return cands


class QuotaFullError(Exception):
    """El servidor ya no tiene espacio para más emojis/stickers."""


async def staff_check(interaction: discord.Interaction) -> bool:
    settings = await interaction.client.db.get_settings(interaction.guild.id)
    return is_staff(interaction.user, settings)


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    hearts_admin = app_commands.Group(
        name="hearts-admin",
        description="Gestiona el saldo de Hearts de un usuario (staff).",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    async def _apply(self, interaction: discord.Interaction,
                     usuario: discord.Member, cantidad: int,
                     accion: str) -> None:
        db = self.bot.db
        guild_id = interaction.guild.id

        if accion == "dar":
            await db.adjust_hearts(guild_id, usuario.id, abs(cantidad))
        elif accion == "quitar":
            await db.adjust_hearts(guild_id, usuario.id, -abs(cantidad))
        else:  # fijar
            await db.set_hearts(guild_id, usuario.id, cantidad)

        nuevo = await db.get_user(guild_id, usuario.id)
        accion_emoji = {"dar": "📥", "quitar": "📤", "fijar": "📌"}[accion]
        embed = discord.Embed(
            title=f"{accion_emoji} Saldo actualizado",
            description=f"{usuario.mention}\n"
                        f"# {nuevo['hearts']:,} {config.HEART}",
            color=config.COLOR_SUCCESS)
        embed.set_thumbnail(url=usuario.display_avatar.url)
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(
            self.bot, interaction.guild, "Saldo modificado por staff",
            f"{interaction.user.mention} → {accion} **{cantidad} "
            f"{config.HEART}** a {usuario.mention} "
            f"(nuevo saldo: {nuevo['hearts']}).")

    @hearts_admin.command(name="dar",
                          description="Suma Hearts al saldo de un usuario.")
    @app_commands.describe(usuario="Usuario", cantidad="Hearts a dar")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def dar(self, interaction: discord.Interaction,
                  usuario: discord.Member, cantidad: int):
        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self._apply(interaction, usuario, cantidad, "dar")

    @hearts_admin.command(name="quitar",
                          description="Resta Hearts del saldo de un usuario.")
    @app_commands.describe(usuario="Usuario", cantidad="Hearts a quitar")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def quitar(self, interaction: discord.Interaction,
                     usuario: discord.Member, cantidad: int):
        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self._apply(interaction, usuario, cantidad, "quitar")

    @hearts_admin.command(name="fijar",
                          description="Fija el saldo exacto de Hearts de un usuario.")
    @app_commands.describe(usuario="Usuario", cantidad="Saldo exacto")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def fijar(self, interaction: discord.Interaction,
                    usuario: discord.Member, cantidad: int):
        if cantidad < 0:
            return await interaction.response.send_message(
                "❌ El saldo no puede ser negativo.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self._apply(interaction, usuario, cantidad, "fijar")

    # ---------- emojis y stickers ----------

    @app_commands.command(name="emoji-add",
                          description="Sube una imagen como emoji al servidor (staff).")
    @app_commands.describe(imagen="Imagen PNG/JPG/GIF (máx. 256KB)",
                           nombre="Nombre del emoji (opcional)")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def emoji_add(self, interaction: discord.Interaction,
                        imagen: discord.Attachment, nombre: str | None = None):
        if nombre and not EMOJI_NAME_RE.match(nombre):
            return await interaction.response.send_message(
                "❌ Nombre inválido: usa 2-32 letras, números o `_`.",
                ephemeral=True)
        if not (imagen.content_type or "").startswith("image/"):
            return await interaction.response.send_message(
                "❌ El archivo debe ser una imagen.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            data = await imagen.read()
            existentes = {e.name for e in interaction.guild.emojis}
            candidatos = ([nombre] if nombre else
                          _auto_names(existentes, "emoji"))
            emoji = None
            for candidato in candidatos:
                if candidato in existentes:
                    continue
                try:
                    emoji = await interaction.guild.create_custom_emoji(
                        name=candidato, image=data,
                        reason=f"Subido por {interaction.user} vía bot")
                    break
                except discord.HTTPException:
                    if nombre:
                        raise
            if emoji is None:
                return await interaction.followup.send(
                    "❌ No pude crear el emoji (¿nombre repetido o cupo "
                    "lleno?).", ephemeral=True)
        except discord.HTTPException as e:
            return await interaction.followup.send(
                f"❌ No pude crear el emoji: {e.text}", ephemeral=True)

        await interaction.followup.send(
            f"✅ Emoji añadido: {emoji} `:{emoji.name}:`", ephemeral=True)
        await send_log(self.bot, interaction.guild, "Emoji añadido",
                       f"{interaction.user.mention} subió {emoji} "
                       f"`:{emoji.name}:`")

    @app_commands.command(
        name="emoji-tomar",
        description="Copia un emoji personalizado de otro servidor (staff).")
    @app_commands.describe(emoji="El emoji a copiar (pégalo aquí)",
                           nombre="Nombre con el que se guardará (opcional)")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def emoji_tomar(self, interaction: discord.Interaction, emoji: str,
                          nombre: str | None = None):
        m = CUSTOM_EMOJI_RE.search(emoji)
        if not m:
            return await interaction.response.send_message(
                "❌ Pega un **emoji personalizado** (ej: `:cat:` de otro "
                "servidor).", ephemeral=True)

        emoji_id = m.group(2)
        if nombre and not EMOJI_NAME_RE.match(nombre):
            return await interaction.response.send_message(
                f"❌ Nombre inválido: `{nombre}`. Indica otro con 2-32 "
                "letras, números o `_`.", ephemeral=True)

        animated = emoji.startswith("<a:")
        url = (f"https://cdn.discordapp.com/emojis/{emoji_id}"
               f".{'gif' if animated else 'png'}")

        await interaction.response.defer(ephemeral=True)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r:
                    if r.status != 200:
                        raise ValueError("no se pudo descargar el emoji")
                    data = await r.read()

            existentes = {e.name for e in interaction.guild.emojis}
            candidatos = ([nombre] if nombre else
                          _auto_names(existentes, "emoji"))
            nuevo = None
            for candidato in candidatos:
                if candidato in existentes:
                    continue
                try:
                    nuevo = await interaction.guild.create_custom_emoji(
                        name=candidato, image=data,
                        reason=f"Copiado por {interaction.user} vía bot")
                    break
                except discord.HTTPException:
                    if nombre:
                        raise
            if nuevo is None:
                return await interaction.followup.send(
                    "❌ No pude copiar el emoji (¿nombre repetido o cupo "
                    "lleno?).", ephemeral=True)
        except (ValueError, discord.HTTPException) as e:
            msg = getattr(e, "text", None) or str(e)
            return await interaction.followup.send(
                f"❌ No pude copiar el emoji: {msg}", ephemeral=True)

        await interaction.followup.send(
            f"✅ Emoji copiado: {nuevo} `:{nuevo.name}:`", ephemeral=True)
        await send_log(self.bot, interaction.guild, "Emoji copiado",
                       f"{interaction.user.mention} copió {nuevo} "
                       f"`:{nuevo.name}:` (id `{emoji_id}`)")

    @staticmethod
    def _resize_sticker(data: bytes) -> bytes:
        """Ajusta la imagen a 320x320 (requisito de Discord) manteniendo
        proporción sobre fondo transparente. Devuelve PNG."""
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        if getattr(img, "is_animated", False) or img.size == (320, 320):
            return data
        img = img.convert("RGBA")
        img.thumbnail((320, 320), Image.LANCZOS)
        canvas = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        canvas.paste(img, ((320 - img.width) // 2, (320 - img.height) // 2))
        out = io.BytesIO()
        canvas.save(out, "PNG")
        return out.getvalue()

    @app_commands.command(name="sticker-add",
                          description="Sube un sticker al servidor (staff).")
    @app_commands.describe(nombre="Nombre del sticker",
                           imagen="Imagen PNG/APNG (se ajusta a 320x320)",
                           emoji="Emoji relacionado (ej: 😂)")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def sticker_add(self, interaction: discord.Interaction, nombre: str,
                          imagen: discord.Attachment, emoji: str):
        if not (imagen.content_type or "").startswith("image/"):
            return await interaction.response.send_message(
                "❌ El archivo debe ser una imagen PNG/APNG.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            data = await asyncio.to_thread(
                self._resize_sticker, await imagen.read())
            file = discord.File(io.BytesIO(data), filename="sticker.png")
            sticker = await interaction.guild.create_sticker(
                name=nombre, description=nombre, emoji=emoji, file=file,
                reason=f"Subido por {interaction.user} vía bot")
        except discord.HTTPException as e:
            return await interaction.followup.send(
                f"❌ No pude crear el sticker: {e.text}", ephemeral=True)

        await interaction.followup.send(
            f"✅ Sticker añadido: **{sticker.name}**", ephemeral=True)
        await send_log(self.bot, interaction.guild, "Sticker añadido",
                       f"{interaction.user.mention} subió el sticker "
                       f"**{sticker.name}**")

    @app_commands.command(name="emoji-borrar",
                          description="Elimina un emoji del servidor (staff).")
    @app_commands.describe(emoji="Emoji a eliminar")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def emoji_borrar(self, interaction: discord.Interaction, emoji: str):
        await interaction.response.defer(ephemeral=True)
        m = CUSTOM_EMOJI_RE.search(emoji)
        encontrado = None
        if m:
            encontrado = interaction.guild.get_emoji(int(m.group(2)))
        else:
            encontrado = discord.utils.get(interaction.guild.emojis,
                                           name=emoji)
        if encontrado is None:
            return await interaction.followup.send(
                f"❌ No encontré un emoji llamado `{emoji}` en este "
                "servidor.", ephemeral=True)

        nombre = encontrado.name
        await encontrado.delete(
            reason=f"Borrado por {interaction.user} vía bot")
        await interaction.followup.send(
            f"🗑️ Emoji `:{nombre}:` eliminado.", ephemeral=True)
        await send_log(self.bot, interaction.guild, "Emoji borrado",
                       f"{interaction.user.mention} eliminó `:{nombre}:`")

    @emoji_borrar.autocomplete("emoji")
    async def emoji_borrar_ac(self, interaction: discord.Interaction,
                              current: str):
        return [
            app_commands.Choice(name=f"{e.name}", value=e.name)
            for e in interaction.guild.emojis
            if current.lower() in e.name.lower()
        ][:25]

    @app_commands.command(name="sticker-borrar",
                          description="Elimina un sticker del servidor (staff).")
    @app_commands.describe(sticker="Sticker a eliminar")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def sticker_borrar(self, interaction: discord.Interaction,
                             sticker: str):
        await interaction.response.defer(ephemeral=True)
        encontrado = discord.utils.get(interaction.guild.stickers,
                                       name=sticker)
        if encontrado is None:
            return await interaction.followup.send(
                f"❌ No encontré un sticker llamado `{sticker}` en este "
                "servidor.", ephemeral=True)

        await encontrado.delete(
            reason=f"Borrado por {interaction.user} vía bot")
        await interaction.followup.send(
            f"🗑️ Sticker **{sticker}** eliminado.", ephemeral=True)
        await send_log(self.bot, interaction.guild, "Sticker borrado",
                       f"{interaction.user.mention} eliminó el sticker "
                       f"**{sticker}**")

    @sticker_borrar.autocomplete("sticker")
    async def sticker_borrar_ac(self, interaction: discord.Interaction,
                                current: str):
        return [
            app_commands.Choice(name=s.name, value=s.name)
            for s in interaction.guild.stickers
            if current.lower() in s.name.lower()
        ][:25]

    # ---------- subida automática por canales ----------

    async def _create_emoji_auto(self, guild: discord.Guild, data: bytes,
                                 author: discord.Member):
        existentes = {e.name for e in guild.emojis}
        last_err = "sin nombres libres"
        for cand in _auto_names(existentes, "emoji"):
            try:
                return await guild.create_custom_emoji(
                    name=cand, image=data,
                    reason=f"Subido por {author} vía canal automático")
            except discord.HTTPException as e:
                if e.code in (30008, 30018):  # cupo de emojis lleno
                    raise QuotaFullError(
                        "cupo de emojis lleno — borra algunos con "
                        "`/emoji-borrar`")
                last_err = e.text
                existentes.add(cand)
        raise ValueError(last_err)

    async def _create_sticker_auto(self, guild: discord.Guild, data: bytes,
                                   author: discord.Member):
        data = await asyncio.to_thread(self._resize_sticker, data)
        existentes = {s.name for s in guild.stickers}
        last_err = "sin nombres libres"
        for cand in _auto_names(existentes, "sticker"):
            try:
                return await guild.create_sticker(
                    name=cand, description="Subido vía canal automático",
                    emoji="😀",
                    file=discord.File(io.BytesIO(data), filename="sticker.png"),
                    reason=f"Subido por {author} vía canal automático")
            except discord.HTTPException as e:
                if e.code == 30039:  # cupo de stickers lleno
                    raise QuotaFullError(
                        "cupo de stickers lleno — borra algunos con "
                        "`/sticker-borrar`")
                last_err = e.text
                existentes.add(cand)
        raise ValueError(last_err)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.attachments:
            return
        s = await self.bot.db.get_settings(message.guild.id)
        if message.channel.id == s.get("emoji_channel_id"):
            kind = "emoji"
        elif message.channel.id == s.get("sticker_channel_id"):
            kind = "sticker"
        else:
            return
        if not isinstance(message.author, discord.Member) or \
                not is_staff(message.author, s):
            return

        images = [a for a in message.attachments
                  if (a.content_type or "").startswith("image/")]
        if not images:
            try:
                await message.add_reaction("❌")
            except discord.HTTPException:
                pass
            return

        ok, fails = 0, []
        quota_full = False
        for i, att in enumerate(images):
            try:
                data = await att.read()
                if kind == "emoji":
                    await self._create_emoji_auto(message.guild, data,
                                                  message.author)
                else:
                    await self._create_sticker_auto(message.guild, data,
                                                    message.author)
                ok += 1
            except QuotaFullError as e:
                fails.append(str(e))
                quota_full = True
                break  # sin espacio: no seguir intentando el resto
            except Exception as e:
                fails.append(str(e)[:80])

        reaccion = "✅" if ok == len(images) else ("⚠️" if ok else "❌")
        try:
            await message.add_reaction(reaccion)
        except discord.HTTPException:
            pass

        if quota_full or fails:
            partes = [f"⚠️ **{ok}/{len(images)}** subidos"]
            if quota_full:
                sin_subir = len(images) - ok
                partes.append(
                    f"**{sin_subir} quedaron sin subir** — no hay espacio "
                    f"en el servidor.\nBorra algunos con "
                    f"`/{kind}-borrar` y vuelve a enviar las imágenes.")
            elif fails:
                partes.append("fallos: " + "; ".join(fails[:3]))
            await message.reply(" — ".join(partes), mention_author=False)
        if ok:
            await send_log(self.bot, message.guild,
                           f"Subida automática de {kind}s",
                           f"{message.author.mention} subió **{ok}** "
                           f"{kind}(s) en {message.channel.mention}")


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
