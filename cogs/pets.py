"""Moonveil — mini-juego de mascotas estilo Adopt Me.

/jugar abre un panel personal que SE ACTUALIZA con cada botón:
🥚 Adoptar | 🐾 Mis mascotas | 🗺️ Explorar | ✨ Neon
El panel queda ligado a quien lo abrió (owner en el footer del embed);
los botones principales son persistentes para sobrevivir reinicios.
"""

import asyncio
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow

import config
from i18n import t, user_lang
from logging_utils import send_log


# ---------- helpers ----------

def pet_emoji(pet) -> str:
    return config.PETS[pet["species"]][0]


def stage_label(pet) -> str:
    stages = config.NEON_STAGES if pet["neon"] else config.STAGES
    return stages[pet["stage"]][0]


def xp_bar(pet) -> str:
    stages = config.NEON_STAGES if pet["neon"] else config.STAGES
    idx = pet["stage"]
    if idx >= len(stages) - 1:
        return "🟩" * 8 + " ¡MAX!"
    lo, hi = stages[idx][1], stages[idx + 1][1]
    pct = (pet["xp"] - lo) / (hi - lo)
    fill = round(pct * 8)
    return "🟩" * fill + "⬜" * (8 - fill) + f"  {pet['xp']}/{hi} XP"


def _until(pet) -> datetime:
    return datetime.fromisoformat(pet["exploring_until"])


def hatch_species(egg: dict) -> tuple[str, str]:
    rarities = list(egg["odds"])
    weights = [egg["odds"][r] for r in rarities]
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    species = random.choice(
        [s for s, (_, r) in config.PETS.items() if r == rarity])
    return species, rarity


def pet_power(pet) -> int:
    """Poder de combate: rareza + etapa."""
    ri = config.RARITY_ORDER.index(pet["rarity"]) + 1
    return ri * 10 + pet["stage"] * 3 + (4 if pet["neon"] else 0) \
        + (2 if pet["shiny"] else 0)


def pet_tags(pet) -> str:
    tags = ""
    if pet["neon"]:
        tags += " ✨ NEON"
    if pet["shiny"]:
        tags += " 🌟 SHINY"
    return tags


def explore_rewards(pet) -> tuple[int, int, bool]:
    mult = config.RARITY_INFO[pet["rarity"]]["mult"]
    if pet["neon"]:
        mult *= config.NEON_MULT
    if pet["shiny"]:
        mult *= config.SHINY_MULT
    xp = round(random.randint(*config.EXPLORE_XP) * mult)
    hearts = round(random.randint(*config.EXPLORE_HEARTS) * mult)
    bonus = random.random() < config.EXPLORE_BONUS_CHANCE
    if bonus:
        hearts *= 3
    return xp, hearts, bonus


def main_embed(user: discord.abc.User, lang: str = "es") -> discord.Embed:
    embed = discord.Embed(
        title="🌙 Moonveil",
        description=t(lang, "mv.menu_desc", mins=config.EXPLORE_MINUTES),
        color=config.EMBED_COLOR)
    embed.set_author(name=user.display_name,
                     icon_url=user.display_avatar.url)
    embed.set_footer(text=f"Moonveil • owner:{user.id}")
    embed.timestamp = utcnow()
    return embed


def owner_id(interaction: discord.Interaction) -> int | None:
    try:
        footer = interaction.message.embeds[0].footer.text or ""
        return int(footer.split("owner:")[1].split()[0])
    except (IndexError, ValueError, AttributeError):
        return None


async def deny_if_not_owner(interaction: discord.Interaction) -> bool:
    """True si NO es el dueño (ya respondió con aviso efímero)."""
    oid = owner_id(interaction)
    if oid is not None and interaction.user.id != oid:
        lang = await user_lang(interaction.client, interaction)
        await interaction.response.send_message(
            t(lang, "mv.not_yours") + " 🌙", ephemeral=True)
        return True
    return False


def back_button(bot) -> discord.ui.Button:
    btn = discord.ui.Button(label="Menú", emoji="🏠",
                            style=discord.ButtonStyle.secondary,
                            custom_id="moonveil:home", row=4)

    async def cb(interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(bot, interaction)
        await interaction.edit_original_response(
            embed=main_embed(interaction.user, lang),
            view=MoonveilView(bot, lang))

    btn.callback = cb
    return btn


def pet_card(pet, lang: str = "es") -> discord.Embed:
    emoji, _ = config.PETS[pet["species"]]
    rarity = config.RARITY_INFO[pet["rarity"]]
    embed = discord.Embed(title=f"{emoji} {pet['species']}{pet_tags(pet)}",
                          color=config.EMBED_COLOR)
    embed.add_field(name=t(lang, "mv.rarity"),
                    value=f"{rarity['emoji']} {rarity['name']}", inline=True)
    embed.add_field(name=t(lang, "mv.stage"), value=stage_label(pet),
                    inline=True)
    embed.add_field(name=t(lang, "mv.progress"), value=xp_bar(pet),
                    inline=False)
    if pet["exploring_until"]:
        ts = int(_until(pet).timestamp())
        estado = (t(lang, "mv.status_exploring", ts=ts)
                  if _until(pet) > utcnow()
                  else t(lang, "mv.status_returned"))
    else:
        estado = t(lang, "mv.status_ready")
    embed.add_field(name=t(lang, "mv.status"), value=estado, inline=False)
    return embed


def pet_options(pets, *, for_explore: bool = False, lang: str = "es"):
    """Opciones de select para una lista de mascotas."""
    now = utcnow()
    options = []
    for p in pets[:25]:
        emoji, _ = config.PETS[p["species"]]
        neon = " ✨" if p["neon"] else ""
        if p["shiny"]:
            neon += " 🌟"
        if for_explore:
            if p["exploring_until"] and _until(p) > now:
                ts = int(_until(p).timestamp())
                desc = t(lang, "mv.status_exploring", ts=ts)
            elif p["exploring_until"]:
                desc = t(lang, "mv.opt_returned")
            else:
                desc = t(lang, "mv.opt_ready")
        else:
            desc = stage_label(p)
        options.append(discord.SelectOption(
            label=f"{p['species']}{neon}"[:100], value=str(p["id"]),
            description=desc[:100], emoji=emoji))
    return options


# ---------- vista principal persistente ----------

class MoonveilView(discord.ui.View):
    def __init__(self, bot, lang: str = "es"):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        self.adopt.label = t(lang, "mv.btn_adopt")
        self.pets.label = t(lang, "mv.btn_pets")
        self.explore.label = t(lang, "mv.btn_explore")
        self.battle.label = t(lang, "mv.btn_battle")
        self.mv_missions.label = t(lang, "mv.btn_missions")
        self.home.label = t(lang, "mv.btn_menu")

    async def _guard(self, interaction: discord.Interaction) -> bool:
        return await deny_if_not_owner(interaction)

    @discord.ui.button(label="Adoptar", emoji="🥚",
                       style=discord.ButtonStyle.success,
                       custom_id="moonveil:adopt")
    async def adopt(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        u = await self.bot.db.get_user(interaction.guild.id,
                                       interaction.user.id)
        free = not u["starter_claimed"]
        desc = (f"{t(lang, 'mv.first_free')}\n\n" if free else "")
        desc += t(lang, "mv.choose_egg_hint")
        embed = discord.Embed(title=t(lang, "mv.adopt_title"),
                              description=desc, color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=EggView(self.bot, free, lang))

    @discord.ui.button(label="Mis mascotas", emoji="🐾",
                       style=discord.ButtonStyle.primary,
                       custom_id="moonveil:pets")
    async def pets(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        pets = await self.bot.db.get_pets(interaction.guild.id,
                                          interaction.user.id)
        if not pets:
            embed = discord.Embed(
                title=t(lang, "mv.btn_pets"),
                description=t(lang, "mv.no_pets"),
                color=config.EMBED_COLOR)
            embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))
        embed = discord.Embed(
            title=t(lang, "mv.your_pets", n=len(pets)),
            description=t(lang, "mv.choose_pet"),
            color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=PetSelectView(self.bot, pets, lang))

    @discord.ui.button(label="Explorar", emoji="🗺️",
                       style=discord.ButtonStyle.primary,
                       custom_id="moonveil:explore")
    async def explore(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        pets = await self.bot.db.get_pets(interaction.guild.id,
                                          interaction.user.id)
        if not pets:
            embed = discord.Embed(
                title=t(lang, "mv.explore_title"),
                description=t(lang, "mv.explore_need_pet"),
                color=config.EMBED_COLOR)
            embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))
        embed = discord.Embed(
            title=t(lang, "mv.explore_title"),
            description=t(lang, "mv.explore_desc",
                          mins=config.EXPLORE_MINUTES),
            color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=ExploreView(self.bot, pets, lang))

    @discord.ui.button(label="Neon", emoji="✨",
                       style=discord.ButtonStyle.secondary,
                       custom_id="moonveil:neon")
    async def neon(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        adult_stage = len(config.STAGES) - 1
        rows = await self.bot.db.neon_species(
            interaction.guild.id, interaction.user.id,
            adult_stage, config.NEON_REQUIRED)
        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        if not rows:
            embed.title = t(lang, "mv.neon_title")
            embed.description = t(lang, "mv.neon_desc_none",
                                  n=config.NEON_REQUIRED)
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))
        embed.title = t(lang, "mv.neon_title")
        embed.description = t(lang, "mv.neon_choose")
        await interaction.edit_original_response(
            embed=embed, view=NeonView(self.bot, rows, lang))

    @discord.ui.button(label="Batalla", emoji="⚔️",
                       style=discord.ButtonStyle.danger,
                       custom_id="moonveil:battle", row=1)
    async def battle(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        pets = await self.bot.db.get_pets(interaction.guild.id,
                                          interaction.user.id)
        listas = [p for p in pets
                  if not (p["exploring_until"] and _until(p) > utcnow())]
        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        if not pets:
            embed.title = t(lang, "mv.battle_title")
            embed.description = t(lang, "mv.explore_need_pet")
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))
        if not listas:
            embed.title = t(lang, "mv.battle_title")
            embed.description = t(lang, "mv.all_exploring")
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))
        embed.title = t(lang, "mv.battle_title")
        embed.description = t(lang, "mv.battle_desc",
                              mins=config.BATTLE_COOLDOWN_MIN)
        await interaction.edit_original_response(
            embed=embed, view=BattleView(self.bot, listas, lang))

    @discord.ui.button(label="Misiones", emoji="📜",
                       style=discord.ButtonStyle.secondary,
                       custom_id="moonveil:missions", row=1)
    async def mv_missions(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        embed, view = await missions_panel(self.bot, interaction, lang)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(label="Menú", emoji="🏠",
                       style=discord.ButtonStyle.secondary,
                       custom_id="moonveil:home", row=1)
    async def home(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        """Restaura el panel principal (también tras reinicios)."""
        if await self._guard(interaction):
            return
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        await interaction.edit_original_response(
            embed=main_embed(interaction.user, lang),
            view=MoonveilView(self.bot, lang))


class BackOnlyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(back_button(bot))


# ---------- Adoptar ----------

class EggView(discord.ui.View):
    def __init__(self, bot, free: bool, lang: str = "es"):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        if free:
            btn = discord.ui.Button(
                label=t(lang, "mv.starter_free"), emoji="🎁",
                style=discord.ButtonStyle.success)
            btn.callback = self._starter
            self.add_item(btn)
        for egg_id, egg in config.EGGS.items():
            btn = discord.ui.Button(
                label=f"{egg['name']} — {egg['price']}💕",
                emoji=egg["emoji"], style=discord.ButtonStyle.primary)
            btn.callback = self._make_hatch(egg_id)
            self.add_item(btn)
        self.add_item(back_button(bot))

    async def _starter(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        if not await self.bot.db.claim_starter(interaction.guild.id,
                                               interaction.user.id):
            return await interaction.followup.send(
                t(self.lang, "mv.starter_used"), ephemeral=True)
        await self._hatch(interaction, config.EGGS["cracked"])

    def _make_hatch(self, egg_id: str):
        async def cb(interaction: discord.Interaction):
            if await deny_if_not_owner(interaction):
                return
            await interaction.response.defer()
            egg = config.EGGS[egg_id]
            if not await self.bot.db.spend_hearts(
                    interaction.guild.id, interaction.user.id, egg["price"]):
                u = await self.bot.db.get_user(interaction.guild.id,
                                               interaction.user.id)
                return await interaction.followup.send(
                    t(self.lang, "mv.no_hearts_egg", have=u["hearts"],
                      egg=egg["name"], price=egg["price"],
                      heart=config.HEART), ephemeral=True)
            await self._hatch(interaction, egg)
        return cb

    async def _hatch(self, interaction: discord.Interaction, egg: dict):
        """La interacción ya está deferida; edita el mensaje original."""
        lang = self.lang
        embed = discord.Embed(
            title=t(lang, "mv.hatching", emoji=egg["emoji"]),
            description=t(lang, "mv.crack"),
            color=config.COLOR_WARNING)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(embed=embed, view=None)
        await asyncio.sleep(1.5)

        species, rarity = hatch_species(egg)
        shiny = random.random() < config.SHINY_CHANCE
        pet_id = await self.bot.db.add_pet(
            interaction.guild.id, interaction.user.id, species, rarity,
            shiny=shiny)
        emoji = config.PETS[species][0]
        rinfo = config.RARITY_INFO[rarity]

        titulo = t(lang, "mv.hatch_shiny" if shiny else "mv.hatch_normal")
        result = discord.Embed(
            title=titulo,
            description=f"# {emoji} {species}{' 🌟' if shiny else ''}\n"
                        f"{rinfo['emoji']} **{rinfo['name']}**"
                        + (t(lang, "mv.shiny_note") if shiny else ""),
            color=(0xFFD700 if rarity == "legendaria" or shiny
                   else config.COLOR_SUCCESS))
        result.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=result, view=AfterHatchView(self.bot, lang))

        if rarity in ("ultra_rara", "legendaria"):
            await send_log(
                self.bot, interaction.guild, "Mascota rara eclosionada",
                f"{interaction.user.mention} obtuvo **{emoji} {species}** "
                f"({rinfo['name']}) de un {egg['name']}.")


class AfterHatchView(discord.ui.View):
    """Tras eclosionar: adoptar otro huevo o volver al menú."""
    def __init__(self, bot, lang: str = "es"):
        super().__init__(timeout=None)
        btn = discord.ui.Button(label=t(lang, "mv.adopt_another"), emoji="🥚",
                                style=discord.ButtonStyle.success)

        async def again(interaction: discord.Interaction):
            if await deny_if_not_owner(interaction):
                return
            await interaction.response.defer()
            embed = discord.Embed(title=t(lang, "mv.adopt_title"),
                                  description=t(lang, "mv.choose_egg"),
                                  color=config.EMBED_COLOR)
            embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
            await interaction.edit_original_response(
                embed=embed, view=EggView(bot, free=False, lang=lang))
        btn.callback = again
        self.add_item(btn)
        self.add_item(back_button(bot))


# ---------- Mis mascotas ----------

class PetSelect(discord.ui.Select):
    def __init__(self, bot, pets, lang: str = "es"):
        self.bot = bot
        self.lang = lang
        super().__init__(placeholder=t(lang, "mv.pick_pet"),
                         options=pet_options(pets, lang=lang),
                         min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        pet = await self.bot.db.get_pet(int(self.values[0]))
        if pet is None or pet["user_id"] != interaction.user.id:
            return await interaction.followup.send(
                t(self.lang, "mv.pet_gone"), ephemeral=True)
        embed = pet_card(pet, self.lang)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=PetCardView(self.bot, self.lang))


class PetCardView(discord.ui.View):
    def __init__(self, bot, lang: str = "es"):
        super().__init__(timeout=None)
        self.bot = bot
        btn = discord.ui.Button(label=t(lang, "mv.btn_pets"), emoji="🐾",
                                style=discord.ButtonStyle.primary)

        async def back(interaction: discord.Interaction):
            if await deny_if_not_owner(interaction):
                return
            await interaction.response.defer()
            pets = await bot.db.get_pets(interaction.guild.id,
                                         interaction.user.id)
            embed = discord.Embed(
                title=t(lang, "mv.your_pets", n=len(pets)),
                description=t(lang, "mv.choose_pet"),
                color=config.EMBED_COLOR)
            embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
            await interaction.edit_original_response(
                embed=embed, view=PetSelectView(bot, pets, lang))
        btn.callback = back
        self.add_item(btn)
        self.add_item(back_button(bot))


class PetSelectView(discord.ui.View):
    def __init__(self, bot, pets, lang: str = "es"):
        super().__init__(timeout=None)
        self.add_item(PetSelect(bot, pets, lang))
        self.add_item(back_button(bot))


# ---------- Explorar ----------

class ExploreSelect(discord.ui.Select):
    def __init__(self, bot, pets, lang: str = "es"):
        self.bot = bot
        self.lang = lang
        super().__init__(placeholder=t(lang, "mv.pick_explorer"),
                         options=pet_options(pets, for_explore=True,
                                             lang=lang),
                         min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        lang = self.lang
        db = self.bot.db
        pet = await db.get_pet(int(self.values[0]))
        if pet is None or pet["user_id"] != interaction.user.id:
            return await interaction.followup.send(
                t(lang, "mv.pet_gone"), ephemeral=True)

        now = utcnow()
        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")

        if pet["exploring_until"]:
            until = _until(pet)
            if until > now:
                ts = int(until.timestamp())
                embed.title = t(lang, "mv.still_exploring")
                embed.description = t(lang, "mv.back_at",
                                      emoji=pet_emoji(pet),
                                      pet=pet["species"], ts=ts)
                embed.color = config.COLOR_WARNING
                return await interaction.edit_original_response(
                    embed=embed, view=BackOnlyView(self.bot))

            xp, hearts, bonus = explore_rewards(pet)
            new_xp = pet["xp"] + xp
            new_stage = config.stage_index(new_xp)
            await db.finish_explore(pet["id"], xp, new_stage)
            await db.add_hearts(interaction.guild.id, interaction.user.id,
                                hearts)
            await db.bump_stat(interaction.guild.id, interaction.user.id,
                               "mv_explores")

            leveled = new_stage > pet["stage"]
            stages = config.NEON_STAGES if pet["neon"] else config.STAGES
            embed.title = t(lang, "mv.explore_done")
            embed.description = t(
                lang, "mv.explore_done_desc", emoji=pet_emoji(pet),
                pet=pet["species"], xp=xp, hearts=hearts,
                heart=config.HEART,
                bonus=t(lang, "mv.bonus_x3") if bonus else "")
            if leveled:
                embed.description += t(lang, "mv.level_up",
                                       stage=stages[new_stage][0])
            embed.color = config.COLOR_SUCCESS
            return await interaction.edit_original_response(
                embed=embed, view=BackOnlyView(self.bot))

        until = now + timedelta(minutes=config.EXPLORE_MINUTES)
        await db.set_exploring(pet["id"], until.isoformat())
        ts = int(until.timestamp())
        embed.title = t(lang, "mv.explore_start")
        embed.description = t(lang, "mv.explore_sent", emoji=pet_emoji(pet),
                              pet=pet["species"], ts=ts)
        await interaction.edit_original_response(
            embed=embed, view=BackOnlyView(self.bot))


class ExploreView(discord.ui.View):
    def __init__(self, bot, pets, lang: str = "es"):
        super().__init__(timeout=None)
        self.add_item(ExploreSelect(bot, pets, lang))
        self.add_item(back_button(bot))


# ---------- Neon ----------

class NeonSelect(discord.ui.Select):
    def __init__(self, bot, species_rows, lang: str = "es"):
        self.bot = bot
        self.lang = lang
        options = []
        for r in species_rows[:25]:
            emoji, _ = config.PETS[r["species"]]
            options.append(discord.SelectOption(
                label=r["species"][:100], value=r["species"],
                description=t(lang, "mv.have_adults", n=r["c"]), emoji=emoji))
        super().__init__(placeholder=t(lang, "mv.pick_species"),
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        species = self.values[0]
        emoji, _ = config.PETS[species]
        await interaction.response.defer()
        embed = discord.Embed(
            title=t(self.lang, "mv.neon_confirm_title", species=species),
            description=t(self.lang, "mv.neon_confirm_desc",
                          n=config.NEON_REQUIRED, species=species),
            color=config.EMBED_COLOR)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=NeonConfirmView(self.bot, species, self.lang))


class NeonConfirmView(discord.ui.View):
    def __init__(self, bot, species, lang: str = "es"):
        super().__init__(timeout=None)
        self.bot = bot
        self.species = species
        self.lang = lang
        self.confirm.label = t(lang, "mv.btn_fuse")
        self.add_item(back_button(bot))

    @discord.ui.button(label="Combinar en Neon", emoji="✨",
                       style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        db = self.bot.db
        guild_id, user_id = interaction.guild.id, interaction.user.id
        adult_stage = len(config.STAGES) - 1
        ids = await db.adult_pet_ids(guild_id, user_id, self.species,
                                     adult_stage, config.NEON_REQUIRED)
        if len(ids) < config.NEON_REQUIRED:
            return await interaction.followup.send(
                t(self.lang, "mv.neon_few"), ephemeral=True)
        await db.delete_pets(ids)
        emoji, rarity = config.PETS[self.species]
        pet_id = await db.add_pet(guild_id, user_id, self.species, rarity,
                                  neon=True)
        await db.bump_stat(guild_id, user_id, "mv_neons")
        embed = discord.Embed(
            title=t(self.lang, "mv.neon_done"),
            description=(f"# {emoji} Neon {self.species}\n"
                         + t(self.lang, "mv.neon_done_desc2")),
            color=0xFFD700)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(
            embed=embed, view=BackOnlyView(self.bot))
        await send_log(
            self.bot, interaction.guild, "Neon creado",
            f"{interaction.user.mention} combinó una **{emoji} {self.species} "
            f"Neon**.")


class NeonView(discord.ui.View):
    def __init__(self, bot, species_rows, lang: str = "es"):
        super().__init__(timeout=None)
        self.add_item(NeonSelect(bot, species_rows, lang))
        self.add_item(back_button(bot))


# ---------- Batalla ----------

class BattleSelect(discord.ui.Select):
    def __init__(self, bot, pets, lang: str = "es"):
        self.bot = bot
        self.lang = lang
        now = utcnow()
        options = []
        for p in pets[:25]:
            emoji, _ = config.PETS[p["species"]]
            label = f"{p['species']}{'✨' if p['neon'] else ''}" \
                    f"{'🌟' if p['shiny'] else ''}"
            if p["battle_until"]:
                bu = datetime.fromisoformat(p["battle_until"])
                if bu > now:
                    desc = t(lang, "mv.status_resting",
                             ts=int(bu.timestamp()))
                else:
                    desc = stage_label(p)
            else:
                desc = stage_label(p)
            options.append(discord.SelectOption(
                label=label[:100], value=str(p["id"]), description=desc[:100],
                emoji=emoji))
        super().__init__(placeholder=t(lang, "mv.pick_fighter"),
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        lang = self.lang
        db = self.bot.db
        pet = await db.get_pet(int(self.values[0]))
        if pet is None or pet["user_id"] != interaction.user.id:
            return await interaction.followup.send(
                t(lang, "mv.pet_gone"), ephemeral=True)

        now = utcnow()
        if pet["battle_until"]:
            bu = datetime.fromisoformat(pet["battle_until"])
            if bu > now:
                return await interaction.followup.send(
                    t(lang, "mv.battle_rest", pet=pet["species"],
                      ts=int(bu.timestamp())), ephemeral=True)
        if pet["exploring_until"] and _until(pet) > now:
            return await interaction.followup.send(
                t(lang, "mv.battle_exploring", pet=pet["species"]),
                ephemeral=True)

        # rival salvaje escalado al poder del jugador
        species = random.choice(list(config.PETS))
        e_rival, r_rival = config.PETS[species]
        p_stage = max(0, min(len(config.STAGES) - 1,
                             pet["stage"] + random.randint(-1, 1)))
        rival = {"species": species, "emoji": e_rival,
                 "rarity": r_rival, "stage": p_stage,
                 "neon": 0, "shiny": 0}
        p_pow = pet_power(pet) * random.uniform(0.8, 1.25)
        r_pow = pet_power(rival) * random.uniform(0.8, 1.25)
        gana = p_pow >= r_pow

        stages = config.NEON_STAGES if pet["neon"] else config.STAGES
        xp = random.randint(30, 60) if gana else random.randint(10, 20)
        new_xp = pet["xp"] + xp
        await db.add_pet_xp(pet["id"], xp, config.stage_index(new_xp))
        await db.set_battle_until(
            pet["id"],
            (now + timedelta(minutes=config.BATTLE_COOLDOWN_MIN)).isoformat())
        await db.bump_stat(interaction.guild.id, interaction.user.id,
                           "mv_battles")

        e_pet, _ = config.PETS[pet["species"]]
        embed = discord.Embed(
            title=t(lang, "mv.battle_title"),
            description=f"{e_pet} **{pet['species']}** "
                        f"vs {e_rival} **{species}**\n\n"
                        + t(lang, "mv.battle_fighting"),
            color=config.COLOR_WARNING)
        embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
        await interaction.edit_original_response(embed=embed, view=None)
        await asyncio.sleep(1.5)

        if gana:
            await db.bump_stat(interaction.guild.id, interaction.user.id,
                               "mv_battle_wins")
            mult = config.RARITY_INFO[pet["rarity"]]["mult"]
            if pet["neon"]:
                mult *= config.NEON_MULT
            if pet["shiny"]:
                mult *= config.SHINY_MULT
            hearts = round(random.randint(*config.BATTLE_HEARTS) * mult)
            await db.add_hearts(interaction.guild.id, interaction.user.id,
                                hearts)
            new_stage = config.stage_index(new_xp)
            leveled = new_stage > pet["stage"]
            embed.title = t(lang, "mv.battle_win")
            embed.description = t(
                lang, "mv.battle_win_desc", e_pet=e_pet, pet=pet["species"],
                e_rival=e_rival, rival=species, xp=xp, hearts=hearts,
                heart=config.HEART)
            if leveled:
                embed.description += t(lang, "mv.level_up",
                                       stage=stages[new_stage][0])
            embed.color = config.COLOR_SUCCESS
        else:
            embed.title = t(lang, "mv.battle_lose")
            embed.description = t(
                lang, "mv.battle_lose_desc", e_rival=e_rival, rival=species,
                xp=xp, mins=config.BATTLE_COOLDOWN_MIN)
            embed.color = config.COLOR_ERROR
        await interaction.edit_original_response(
            embed=embed, view=BackOnlyView(self.bot))


class BattleView(discord.ui.View):
    def __init__(self, bot, pets, lang: str = "es"):
        super().__init__(timeout=None)
        self.add_item(BattleSelect(bot, pets, lang))
        self.add_item(back_button(bot))


# ---------- Misiones Moonveil ----------

async def missions_panel(bot, interaction, lang: str = "es"):
    """Embed + vista del panel de misiones internas de Moonveil."""
    db = bot.db
    gid, uid = interaction.guild.id, interaction.user.id
    u = await db.get_user(gid, uid)
    claimed = await db.claimed_achievement_ids(gid, uid)
    stats = dict(u)
    stats["mv_pets"] = await db.count_pets(gid, uid)

    lines, claimable = [], []
    for m in config.MV_MISSIONS:
        mid = "mv_" + m["id"]
        name = t(lang, f"mvm.{m['id']}.name")
        desc_m = t(lang, f"mvm.{m['id']}.desc")
        if mid in claimed:
            estado = t(lang, "mv.mission_claimed")
        elif stats[m["stat"]] >= m["threshold"]:
            estado = t(lang, "mv.mission_ready")
            claimable.append(m)
        else:
            estado = f"🔒 {stats[m['stat']]}/{m['threshold']}"
        lines.append(f"{m['emoji']} **{name}** — "
                     f"**{m['reward_hearts']} {config.HEART}**\n"
                     f"╰─ *{desc_m}* — {estado}")

    embed = discord.Embed(title=t(lang, "mv.missions_title"),
                          description="\n\n".join(lines),
                          color=config.EMBED_COLOR)
    embed.set_footer(text=f"Moonveil • owner:{interaction.user.id}")
    view = MissionsView(bot, claimable, lang) if claimable \
        else BackOnlyView(bot)
    return embed, view


class MissionClaimSelect(discord.ui.Select):
    def __init__(self, bot, claimable, lang: str = "es"):
        self.bot = bot
        self.lang = lang
        options = [
            discord.SelectOption(
                label=t(lang, f"mvm.{m['id']}.name")[:100], value=m["id"],
                emoji=m["emoji"],
                description=f"+{m['reward_hearts']} Hearts")
            for m in claimable[:25]
        ]
        super().__init__(placeholder=t(lang, "mv.pick_mission"),
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if await deny_if_not_owner(interaction):
            return
        await interaction.response.defer()
        lang = self.lang
        db = self.bot.db
        gid, uid = interaction.guild.id, interaction.user.id
        m = next((x for x in config.MV_MISSIONS if x["id"] == self.values[0]),
                 None)
        mid = "mv_" + self.values[0]
        claimed = await db.claimed_achievement_ids(gid, uid)
        if m is None or mid in claimed:
            embed, view = await missions_panel(self.bot, interaction, lang)
            return await interaction.edit_original_response(
                embed=embed, view=view)
        await db.claim_achievement(gid, uid, mid)
        await db.add_hearts(gid, uid, m["reward_hearts"])
        await send_log(self.bot, interaction.guild,
                       "Misión Moonveil completada",
                       f"{interaction.user.mention} completó "
                       f"**{m['name']}** (+{m['reward_hearts']} "
                       f"{config.HEART})")
        embed, view = await missions_panel(self.bot, interaction, lang)
        embed.title = t(lang, "mv.mission_done",
                        name=t(lang, f"mvm.{m['id']}.name"),
                        hearts=m["reward_hearts"], heart=config.HEART)
        await interaction.edit_original_response(embed=embed, view=view)


class MissionsView(discord.ui.View):
    def __init__(self, bot, claimable, lang: str = "es"):
        super().__init__(timeout=None)
        self.add_item(MissionClaimSelect(bot, claimable, lang))
        self.add_item(back_button(bot))


# ---------- cog ----------

class PetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="jugar",
        description="Abre Moonveil: adopta mascotas, explóralas y haz Neon.")
    @app_commands.guild_only()
    async def jugar(self, interaction: discord.Interaction):
        await interaction.response.defer()
        lang = await user_lang(self.bot, interaction)
        await interaction.edit_original_response(
            embed=main_embed(interaction.user, lang),
            view=MoonveilView(self.bot, lang))


async def setup(bot):
    await bot.add_cog(PetsCog(bot))
