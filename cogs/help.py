"""Comando /help — menú de ayuda estilo Moonveil Bot."""

import discord
from discord import app_commands
from discord.ext import commands

import config
from i18n import t, user_lang


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help",
                          description="Muestra el menú de ayuda del bot.")
    @app_commands.guild_only()
    async def help(self, interaction: discord.Interaction):
        lang = await user_lang(self.bot, interaction)
        embed = discord.Embed(
            title=t(lang, "help.title", bot=config.BOT_NAME),
            description=t(lang, "help.desc"),
            color=config.EMBED_COLOR)

        for name_key, cmds_key in (
                ("help.shop", "help.shop_cmds"),
                ("help.economy", "help.economy_cmds"),
                ("help.games", "help.games_cmds"),
                ("help.community", "help.community_cmds"),
                ("help.progress", "help.progress_cmds"),
                ("help.info", "help.info_cmds")):
            embed.add_field(name=t(lang, name_key),
                            value=t(lang, cmds_key), inline=False)

        embed.set_footer(
            text=f"{config.BOT_NAME} • {config.BOT_TAGLINE}")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
