"""Lotería del servidor: /loteria con tickets de Hearts y pozo acumulado."""

import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.admin import staff_check
from i18n import t, user_lang
from logging_utils import send_log


class LotteryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    loteria = app_commands.Group(
        name="loteria",
        description="Lotería de Hearts del servidor.")

    @loteria.command(name="estado",
                     description="Muestra el pozo actual y tus tickets.")
    @app_commands.guild_only()
    async def estado(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        pot = await db.lottery_pot(interaction.guild.id)
        mios = await db.my_tickets(interaction.guild.id,
                                   interaction.user.id)
        total_premio = pot * config.LOTTERY_TICKET_PRICE
        embed = discord.Embed(
            title=t(lang, "lottery.title"),
            description=(
                t(lang, "lottery.pot", pot=total_premio,
                  heart=config.HEART) + "\n"
                + t(lang, "lottery.sold", n=pot) + "\n"
                + t(lang, "lottery.yours", n=mios)
                + (t(lang, "lottery.chance", pct=f"{mios / pot:.0%}")
                   if pot else "")
            ),
            color=config.EMBED_COLOR)
        embed.set_footer(
            text=t(lang, "lottery.footer",
                   price=config.LOTTERY_TICKET_PRICE, heart=config.HEART))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    @loteria.command(name="comprar",
                     description="Compra tickets para la lotería.")
    @app_commands.describe(tickets="Cantidad de tickets a comprar")
    @app_commands.guild_only()
    async def comprar(self, interaction: discord.Interaction, tickets: int):
        await interaction.response.defer(ephemeral=True)
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        gid, uid = interaction.guild.id, interaction.user.id
        if tickets <= 0:
            return await interaction.followup.send(
                t(lang, "lottery.min_one"), ephemeral=True)
        costo = tickets * config.LOTTERY_TICKET_PRICE
        if not await db.spend_hearts(gid, uid, costo):
            u = await db.get_user(gid, uid)
            return await interaction.followup.send(
                t(lang, "lottery.cant_afford", n=tickets, cost=costo,
                  heart=config.HEART, have=u["hearts"]), ephemeral=True)
        await db.add_lottery_tickets(gid, uid, tickets)
        pot = await db.lottery_pot(gid)
        await interaction.followup.send(
            t(lang, "lottery.bought", n=tickets, cost=costo,
              heart=config.HEART,
              pot=pot * config.LOTTERY_TICKET_PRICE), ephemeral=True)

    @loteria.command(name="sortear",
                     description="Sortea el pozo entre los tickets (staff).")
    @app_commands.check(staff_check)
    @app_commands.guild_only()
    async def sortear(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        db = self.bot.db
        gid = interaction.guild.id
        entries = await db.lottery_entries(gid)
        if not entries:
            return await interaction.followup.send(
                t(lang, "lottery.no_tickets"), ephemeral=True)

        pool = [r["user_id"] for r in entries for _ in range(r["tickets"])]
        ganador_id = random.choice(pool)
        premio = sum(r["tickets"] for r in entries) * \
            config.LOTTERY_TICKET_PRICE
        await db.clear_lottery(gid)
        await db.add_hearts(gid, ganador_id, premio)

        embed = discord.Embed(
            title=t(lang, "lottery.winner_title"),
            description=t(lang, "lottery.winner_desc",
                          user=f"<@{ganador_id}>", pot=premio,
                          heart=config.HEART),
            color=config.COLOR_SUCCESS)
        embed.set_footer(
            text=t(lang, "lottery.drawn_by",
                   name=interaction.user.display_name))
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)
        await send_log(self.bot, interaction.guild, "Lotería sorteada",
                       f"<@{ganador_id}> ganó **{premio} {config.HEART}** "
                       f"(sorteado por {interaction.user.mention})")


async def setup(bot):
    await bot.add_cog(LotteryCog(bot))
