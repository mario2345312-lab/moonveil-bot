"""Punto de entrada del bot.

Uso:
    pip install -r requirements.txt
    # rellenar .env con DISCORD_TOKEN (y opcionalmente GUILD_ID)
    python bot.py
"""

import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from database import Database
from cogs.review import ReviewView
from cogs.pets import MoonveilView
from cogs.community import GiveawayJoinView, AuctionBidView

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

COGS = [
    "cogs.setup",
    "cogs.admin",
    "cogs.economy",
    "cogs.shop",
    "cogs.games",
    "cogs.progression",
    "cogs.pets",
    "cogs.review",
    "cogs.help",
    "cogs.invites",
    "cogs.lottery",
    "cogs.community",
    "cogs.utility",
]


class MoonveilBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # para el logro "Invitador"
        intents.message_content = True  # para leer adjuntos en canales auto
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database(str(DATA_DIR / "bot.db"))

    async def setup_hook(self):
        await self.db.connect()
        self.add_view(ReviewView(self))   # botones de revisión persistentes
        self.add_view(MoonveilView(self)) # panel Moonveil persistente
        self.add_view(GiveawayJoinView(self))  # botón Participar persistente
        self.add_view(AuctionBidView(self))    # botón Pujar persistente
        for cog in COGS:
            await self.load_extension(cog)

        guild_id = os.getenv("GUILD_ID") or config.GUILD_ID
        guild_id = int(guild_id) if guild_id else None
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Comandos sincronizados en el servidor {guild_id}")
        else:
            await self.tree.sync()
            print("Comandos sincronizados globalmente "
                  "(pueden tardar hasta 1h en aparecer)")

    async def on_ready(self):
        print(f"{config.BOT_NAME} conectado como {self.user} "
              f"({self.user.id}) en {len(self.guilds)} servidor(es)")

    async def close(self):
        await self.db.close()
        await super().close()


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "pega_tu_token_aqui":
        raise SystemExit(
            "Falta DISCORD_TOKEN: edita el archivo .env con el token de tu bot.")
    MoonveilBot().run(token)


if __name__ == "__main__":
    main()
