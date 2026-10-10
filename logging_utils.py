"""Envío de logs al canal configurado con /setup canal-logs."""

import discord

import config


async def send_log(bot, guild: discord.Guild, title: str,
                   description: str | None = None,
                   color: int = config.EMBED_COLOR,
                   fields: list[tuple[str, str]] | None = None):
    """Envía un embed de log al canal de logs del servidor. Silencioso si no está configurado."""
    settings = await bot.db.get_settings(guild.id)
    channel_id = settings.get("log_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    embed = discord.Embed(title=f"📋 {title}", description=description,
                          color=color, timestamp=discord.utils.utcnow())
    for name, value in (fields or []):
        embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text=f"{config.BOT_NAME} • Logs")
    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass
