"""Capa de acceso a datos (SQLite async con aiosqlite)."""

import datetime
import json

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    guild_id        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    hearts          INTEGER NOT NULL DEFAULT 0,
    last_daily      TEXT,
    streak          INTEGER NOT NULL DEFAULT 0,
    best_streak     INTEGER NOT NULL DEFAULT 0,
    total_earned    INTEGER NOT NULL DEFAULT 0,
    total_spent     INTEGER NOT NULL DEFAULT 0,
    dailies_claimed INTEGER NOT NULL DEFAULT 0,
    flips_played    INTEGER NOT NULL DEFAULT 0,
    flips_won       INTEGER NOT NULL DEFAULT 0,
    items_bought    INTEGER NOT NULL DEFAULT 0,
    invites_count   INTEGER NOT NULL DEFAULT 0,
    custom_role_id  INTEGER,
    last_fish       TEXT,
    mv_login_date   TEXT,
    mv_login_streak INTEGER NOT NULL DEFAULT 0,
    fish_count      INTEGER NOT NULL DEFAULT 0,
    vip_since       TEXT,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id        INTEGER PRIMARY KEY,
    buy_channel_id  INTEGER,
    ach_channel_id  INTEGER,
    mis_channel_id  INTEGER,
    log_channel_id  INTEGER,
    staff_role_id   INTEGER,
    vip_role_id     INTEGER,
    temp_category_id INTEGER,
    emoji_channel_id   INTEGER,
    sticker_channel_id INTEGER,
    welcome_channel_id    INTEGER,
    suggestion_channel_id INTEGER,
    suggestion_channel_en_id INTEGER,
    lang_es_role_id    INTEGER,
    lang_en_role_id    INTEGER,
    staff_role_ids     TEXT,
    confession_channel_id INTEGER,
    qotd_channel_id    INTEGER,
    confession_count   INTEGER NOT NULL DEFAULT 0,
    qotd_index         INTEGER NOT NULL DEFAULT 0,
    qotd_last          TEXT,
    trade_channel_id   INTEGER
);

CREATE TABLE IF NOT EXISTS claimed_achievements (
    guild_id        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    achievement_id  TEXT NOT NULL,
    claimed_at      TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (guild_id, user_id, achievement_id)
);

CREATE TABLE IF NOT EXISTS mission_progress (
    guild_id        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    mission_id      TEXT NOT NULL,
    progress        INTEGER NOT NULL DEFAULT 0,
    completed       INTEGER NOT NULL DEFAULT 0,
    completed_at    TEXT,
    PRIMARY KEY (guild_id, user_id, mission_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id         INTEGER NOT NULL,
    user_id          INTEGER NOT NULL,
    kind             TEXT NOT NULL,
    ref_id           TEXT NOT NULL,
    payload_json     TEXT,
    proof_url        TEXT,
    status           TEXT NOT NULL DEFAULT 'pending',
    review_message_id INTEGER,
    channel_id       INTEGER,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invited_members (
    guild_id   INTEGER NOT NULL,
    member_id  INTEGER NOT NULL,
    inviter_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS temp_channels (
    channel_id INTEGER PRIMARY KEY,
    guild_id   INTEGER NOT NULL,
    owner_id   INTEGER NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    species         TEXT NOT NULL,
    rarity          TEXT NOT NULL,
    stage           INTEGER NOT NULL DEFAULT 0,
    xp              INTEGER NOT NULL DEFAULT 0,
    neon            INTEGER NOT NULL DEFAULT 0,
    adopted_at      TEXT NOT NULL DEFAULT (datetime('now')),
    exploring_until TEXT
);

CREATE TABLE IF NOT EXISTS giveaways (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id       INTEGER NOT NULL,
    channel_id     INTEGER NOT NULL,
    message_id     INTEGER,
    prize_text     TEXT NOT NULL,
    prize_hearts   INTEGER NOT NULL DEFAULT 0,
    prize_role_id  INTEGER,
    winners_count  INTEGER NOT NULL DEFAULT 1,
    ends_at        TEXT NOT NULL,
    ended          INTEGER NOT NULL DEFAULT 0,
    host_id        INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS giveaway_entries (
    giveaway_id INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    PRIMARY KEY (giveaway_id, user_id)
);

CREATE TABLE IF NOT EXISTS reminders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    text       TEXT NOT NULL,
    remind_at  TEXT NOT NULL,
    kind       TEXT NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS lottery_tickets (
    guild_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    tickets  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS auctions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    message_id  INTEGER,
    item_text   TEXT NOT NULL,
    min_bid     INTEGER NOT NULL DEFAULT 0,
    current_bid INTEGER NOT NULL DEFAULT 0,
    bidder_id   INTEGER,
    ends_at     TEXT NOT NULL,
    ended       INTEGER NOT NULL DEFAULT 0,
    host_id     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS warnings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id     INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS birthdays (
    guild_id         INTEGER NOT NULL,
    user_id          INTEGER NOT NULL,
    month            INTEGER NOT NULL,
    day              INTEGER NOT NULL,
    last_wished_year INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS afk (
    guild_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    reason   TEXT NOT NULL,
    set_at   TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS custom_commands (
    guild_id   INTEGER NOT NULL,
    name       TEXT NOT NULL,
    response   TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    PRIMARY KEY (guild_id, name)
);

CREATE TABLE IF NOT EXISTS boss (
    guild_id   INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    hp         INTEGER NOT NULL,
    max_hp     INTEGER NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boss_damage (
    guild_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    damage   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
"""

USER_COLS = (
    "hearts, last_daily, streak, best_streak, total_earned, total_spent, "
    "dailies_claimed, flips_played, flips_won, items_bought, invites_count, "
    "custom_role_id, dream_pet, starter_claimed, last_work, last_rob, "
    "mv_explores, mv_battles, mv_battle_wins, mv_neons, lang, "
    "last_fish, mv_login_date, mv_login_streak, fish_count, vip_since"
)


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        # migraciones: columnas añadidas después de la creación inicial
        cur = await self.conn.execute("PRAGMA table_info(users)")
        cols = {r["name"] for r in await cur.fetchall()}
        if "dream_pet" not in cols:
            await self.conn.execute(
                "ALTER TABLE users ADD COLUMN dream_pet TEXT")
        if "starter_claimed" not in cols:
            await self.conn.execute(
                "ALTER TABLE users ADD COLUMN starter_claimed "
                "INTEGER NOT NULL DEFAULT 0")
        for col, ddl in {
            "last_work": "TEXT", "last_rob": "TEXT",
            "mv_explores": "INTEGER NOT NULL DEFAULT 0",
            "mv_battles": "INTEGER NOT NULL DEFAULT 0",
            "mv_battle_wins": "INTEGER NOT NULL DEFAULT 0",
            "mv_neons": "INTEGER NOT NULL DEFAULT 0",
            "lang": "TEXT",
            "last_fish": "TEXT",
            "mv_login_date": "TEXT",
            "mv_login_streak": "INTEGER NOT NULL DEFAULT 0",
            "fish_count": "INTEGER NOT NULL DEFAULT 0",
            "vip_since": "TEXT",
        }.items():
            if col not in cols:
                await self.conn.execute(
                    f"ALTER TABLE users ADD COLUMN {col} {ddl}")
        cur = await self.conn.execute("PRAGMA table_info(guild_settings)")
        gcols = {r["name"] for r in await cur.fetchall()}
        for col, ddl in {
            "emoji_channel_id": "INTEGER", "sticker_channel_id": "INTEGER",
            "welcome_channel_id": "INTEGER", "suggestion_channel_id": "INTEGER",
            "suggestion_channel_en_id": "INTEGER",
            "lang_es_role_id": "INTEGER", "lang_en_role_id": "INTEGER",
            "staff_role_ids": "TEXT",
            "confession_channel_id": "INTEGER",
            "qotd_channel_id": "INTEGER",
            "confession_count": "INTEGER NOT NULL DEFAULT 0",
            "qotd_index": "INTEGER NOT NULL DEFAULT 0",
            "qotd_last": "TEXT",
            "trade_channel_id": "INTEGER",
        }.items():
            if col not in gcols:
                await self.conn.execute(
                    f"ALTER TABLE guild_settings ADD COLUMN {col} {ddl}")
        # copiar el rol staff único a la lista si aún no migró
        await self.conn.execute(
            "UPDATE guild_settings SET staff_role_ids='[' || staff_role_id || ']'"
            " WHERE staff_role_ids IS NULL AND staff_role_id IS NOT NULL")
        cur = await self.conn.execute("PRAGMA table_info(pets)")
        pcols = {r["name"] for r in await cur.fetchall()}
        for col, ddl in {"shiny": "INTEGER NOT NULL DEFAULT 0",
                         "battle_until": "TEXT"}.items():
            if col not in pcols:
                await self.conn.execute(
                    f"ALTER TABLE pets ADD COLUMN {col} {ddl}")
        cur = await self.conn.execute("PRAGMA table_info(auctions)")
        acols = {r["name"] for r in await cur.fetchall()}
        if acols and "min_bid" not in acols:
            await self.conn.execute(
                "ALTER TABLE auctions ADD COLUMN min_bid "
                "INTEGER NOT NULL DEFAULT 0")
        cur = await self.conn.execute("PRAGMA table_info(reminders)")
        rcols = {r["name"] for r in await cur.fetchall()}
        if "kind" not in rcols:
            await self.conn.execute(
                "ALTER TABLE reminders ADD COLUMN kind "
                "TEXT NOT NULL DEFAULT 'user'")
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    # ---------- usuarios / economía ----------

    async def get_user(self, guild_id: int, user_id: int) -> aiosqlite.Row:
        cur = await self.conn.execute(
            f"SELECT {USER_COLS} FROM users WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        if row is None:
            await self.conn.execute(
                "INSERT INTO users (guild_id, user_id) VALUES (?, ?)",
                (guild_id, user_id),
            )
            await self.conn.commit()
            cur = await self.conn.execute(
                f"SELECT {USER_COLS} FROM users WHERE guild_id=? AND user_id=?",
                (guild_id, user_id),
            )
            row = await cur.fetchone()
        return row

    async def add_hearts(self, guild_id: int, user_id: int, amount: int):
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET hearts=hearts+?, total_earned=total_earned+? "
            "WHERE guild_id=? AND user_id=?",
            (amount, amount, guild_id, user_id),
        )
        await self.conn.commit()

    async def spend_hearts(self, guild_id: int, user_id: int, amount: int) -> bool:
        """Descuenta hearts si hay saldo. Devuelve True si se pudo."""
        await self.get_user(guild_id, user_id)
        cur = await self.conn.execute(
            "UPDATE users SET hearts=hearts-?, total_spent=total_spent+? "
            "WHERE guild_id=? AND user_id=? AND hearts>=?",
            (amount, amount, guild_id, user_id, amount),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def adjust_hearts(self, guild_id: int, user_id: int, amount: int):
        """Suma o resta hearts sin tocar stats (uso staff). Nunca baja de 0."""
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET hearts=MAX(0, hearts+?) WHERE guild_id=? AND user_id=?",
            (amount, guild_id, user_id),
        )
        await self.conn.commit()

    async def set_hearts(self, guild_id: int, user_id: int, amount: int):
        """Fija el saldo exacto (uso staff)."""
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET hearts=? WHERE guild_id=? AND user_id=?",
            (max(0, amount), guild_id, user_id),
        )
        await self.conn.commit()

    async def bump_stat(self, guild_id: int, user_id: int, column: str, amount: int = 1):
        assert column in {
            "dailies_claimed", "flips_played", "flips_won",
            "items_bought", "invites_count", "mv_explores", "mv_battles",
            "mv_battle_wins", "mv_neons",
        }
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            f"UPDATE users SET {column}={column}+? WHERE guild_id=? AND user_id=?",
            (amount, guild_id, user_id),
        )
        await self.conn.commit()

    async def claim_daily(self, guild_id: int, user_id: int, today: str,
                          yesterday: str, base: int, bonus: int,
                          mult: float = 1.0):
        """Devuelve (reward, streak) o None si ya reclamó hoy."""
        user = await self.get_user(guild_id, user_id)
        if user["last_daily"] == today:
            return None
        streak = user["streak"] + 1 if user["last_daily"] == yesterday else 1
        best = max(streak, user["best_streak"])
        reward = round((base + bonus * streak) * mult)
        await self.conn.execute(
            "UPDATE users SET hearts=hearts+?, total_earned=total_earned+?, "
            "last_daily=?, streak=?, best_streak=?, dailies_claimed=dailies_claimed+1 "
            "WHERE guild_id=? AND user_id=?",
            (reward, reward, today, streak, best, guild_id, user_id),
        )
        await self.conn.commit()
        return reward, streak

    async def leaderboard(self, guild_id: int, limit: int = 10):
        cur = await self.conn.execute(
            "SELECT user_id, hearts FROM users WHERE guild_id=? AND hearts>0 "
            "ORDER BY hearts DESC LIMIT ?",
            (guild_id, limit),
        )
        return await cur.fetchall()

    async def user_rank(self, guild_id: int, user_id: int):
        cur = await self.conn.execute(
            "SELECT COUNT(*)+1 AS rank FROM users WHERE guild_id=? AND hearts > "
            "(SELECT COALESCE((SELECT hearts FROM users WHERE guild_id=? AND user_id=?), 0))",
            (guild_id, guild_id, user_id),
        )
        row = await cur.fetchone()
        return row["rank"]

    async def set_custom_role(self, guild_id: int, user_id: int, role_id: int):
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET custom_role_id=? WHERE guild_id=? AND user_id=?",
            (role_id, guild_id, user_id),
        )
        await self.conn.commit()

    async def set_dream_pet(self, guild_id: int, user_id: int, pet: str):
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET dream_pet=? WHERE guild_id=? AND user_id=?",
            (pet, guild_id, user_id),
        )
        await self.conn.commit()

    async def set_lang(self, guild_id: int, user_id: int,
                       lang: str | None):
        """lang: 'es' | 'en' | None (None = autodetectar por rol)."""
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET lang=? WHERE guild_id=? AND user_id=?",
            (lang, guild_id, user_id),
        )
        await self.conn.commit()

    # ---------- guild_settings ----------

    async def get_settings(self, guild_id: int) -> dict:
        cur = await self.conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else {}

    async def set_setting(self, guild_id: int, key: str, value):
        assert key in {
            "buy_channel_id", "ach_channel_id", "mis_channel_id", "log_channel_id",
            "staff_role_id", "vip_role_id", "temp_category_id",
            "emoji_channel_id", "sticker_channel_id",
            "welcome_channel_id", "suggestion_channel_id",
            "suggestion_channel_en_id",
            "lang_es_role_id", "lang_en_role_id",
            "confession_channel_id", "qotd_channel_id", "qotd_last",
            "trade_channel_id",
        }
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id) VALUES (?) "
            "ON CONFLICT(guild_id) DO NOTHING",
            (guild_id,),
        )
        await self.conn.execute(
            f"UPDATE guild_settings SET {key}=? WHERE guild_id=?",
            (value, guild_id),
        )
        await self.conn.commit()

    # ---------- logros ----------

    async def claimed_achievement_ids(self, guild_id: int, user_id: int) -> set:
        cur = await self.conn.execute(
            "SELECT achievement_id FROM claimed_achievements WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        return {r["achievement_id"] for r in await cur.fetchall()}

    async def claim_achievement(self, guild_id: int, user_id: int, ach_id: str):
        await self.conn.execute(
            "INSERT OR IGNORE INTO claimed_achievements (guild_id, user_id, achievement_id) "
            "VALUES (?, ?, ?)",
            (guild_id, user_id, ach_id),
        )
        await self.conn.commit()

    # ---------- misiones ----------

    async def get_mission_rows(self, guild_id: int, user_id: int) -> dict:
        cur = await self.conn.execute(
            "SELECT mission_id, progress, completed FROM mission_progress "
            "WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        return {r["mission_id"]: r for r in await cur.fetchall()}

    async def bump_mission(self, guild_id: int, user_id: int, mission_id: str,
                           required: int) -> bool:
        """Suma progreso; si llega a required marca completed. Devuelve True si completó."""
        await self.conn.execute(
            "INSERT INTO mission_progress (guild_id, user_id, mission_id, progress) "
            "VALUES (?, ?, ?, 1) "
            "ON CONFLICT(guild_id, user_id, mission_id) "
            "DO UPDATE SET progress=progress+1",
            (guild_id, user_id, mission_id),
        )
        cur = await self.conn.execute(
            "SELECT progress FROM mission_progress "
            "WHERE guild_id=? AND user_id=? AND mission_id=?",
            (guild_id, user_id, mission_id),
        )
        progress = (await cur.fetchone())["progress"]
        completed = progress >= required
        if completed:
            await self.conn.execute(
                "UPDATE mission_progress SET completed=1, completed_at=datetime('now') "
                "WHERE guild_id=? AND user_id=? AND mission_id=?",
                (guild_id, user_id, mission_id),
            )
        await self.conn.commit()
        return completed

    async def reset_mission(self, guild_id: int, user_id: int, mission_id: str):
        """Reinicia una misión repetible tras completarla."""
        await self.conn.execute(
            "UPDATE mission_progress SET progress=0, completed=0, completed_at=NULL "
            "WHERE guild_id=? AND user_id=? AND mission_id=?",
            (guild_id, user_id, mission_id),
        )
        await self.conn.commit()

    # ---------- submissions ----------

    async def create_submission(self, guild_id: int, user_id: int, kind: str,
                                ref_id: str, payload_json: str | None,
                                proof_url: str | None, channel_id: int) -> int:
        cur = await self.conn.execute(
            "INSERT INTO submissions (guild_id, user_id, kind, ref_id, payload_json, "
            "proof_url, channel_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, kind, ref_id, payload_json, proof_url, channel_id),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_submission(self, sub_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM submissions WHERE id=?", (sub_id,)
        )
        return await cur.fetchone()

    async def has_pending(self, guild_id: int, user_id: int, kind: str,
                          ref_id: str) -> bool:
        cur = await self.conn.execute(
            "SELECT 1 FROM submissions WHERE guild_id=? AND user_id=? AND kind=? "
            "AND ref_id=? AND status='pending'",
            (guild_id, user_id, kind, ref_id),
        )
        return await cur.fetchone() is not None

    async def set_submission(self, sub_id: int, status: str,
                           review_message_id: int | None = None):
        if review_message_id is not None:
            await self.conn.execute(
                "UPDATE submissions SET status=?, review_message_id=? WHERE id=?",
                (status, review_message_id, sub_id),
            )
        else:
            await self.conn.execute(
                "UPDATE submissions SET status=? WHERE id=?", (status, sub_id)
            )
        await self.conn.commit()

    async def pending_submission_ids(self, guild_id: int, user_id: int,
                                     kind: str) -> set:
        cur = await self.conn.execute(
            "SELECT ref_id FROM submissions WHERE guild_id=? AND user_id=? "
            "AND kind=? AND status='pending'",
            (guild_id, user_id, kind),
        )
        return {r["ref_id"] for r in await cur.fetchall()}

    # ---------- invites ----------

    async def record_invite(self, guild_id: int, member_id: int,
                            inviter_id: int) -> bool:
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO invited_members (guild_id, member_id, inviter_id) "
            "VALUES (?, ?, ?)",
            (guild_id, member_id, inviter_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    # ---------- canales temporales ----------

    async def add_temp_channel(self, channel_id: int, guild_id: int,
                               owner_id: int, expires_at: str):
        await self.conn.execute(
            "INSERT INTO temp_channels (channel_id, guild_id, owner_id, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (channel_id, guild_id, owner_id, expires_at),
        )
        await self.conn.commit()

    async def remove_temp_channel(self, channel_id: int):
        await self.conn.execute(
            "DELETE FROM temp_channels WHERE channel_id=?", (channel_id,)
        )
        await self.conn.commit()

    async def expired_temp_channels(self, now_iso: str):
        cur = await self.conn.execute(
            "SELECT * FROM temp_channels WHERE expires_at <= ?", (now_iso,)
        )
        return await cur.fetchall()

    async def active_temp_channel(self, guild_id: int, owner_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM temp_channels WHERE guild_id=? AND owner_id=?",
            (guild_id, owner_id),
        )
        return await cur.fetchone()

    # ---------- mascotas (Moonveil) ----------

    async def claim_starter(self, guild_id: int, user_id: int) -> bool:
        """Marca el huevo inicial gratis. Devuelve True si era su primera vez."""
        await self.get_user(guild_id, user_id)
        cur = await self.conn.execute(
            "UPDATE users SET starter_claimed=1 "
            "WHERE guild_id=? AND user_id=? AND starter_claimed=0",
            (guild_id, user_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def get_pets(self, guild_id: int, user_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM pets WHERE guild_id=? AND user_id=? "
            "ORDER BY neon DESC, xp DESC, id",
            (guild_id, user_id),
        )
        return await cur.fetchall()

    async def top_pets(self, guild_id: int, limit: int = 10):
        cur = await self.conn.execute(
            "SELECT * FROM pets WHERE guild_id=? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit))
        return await cur.fetchall()

    async def get_pet(self, pet_id: int):
        cur = await self.conn.execute("SELECT * FROM pets WHERE id=?",
                                      (pet_id,))
        return await cur.fetchone()

    async def set_exploring(self, pet_id: int, until_iso: str):
        await self.conn.execute(
            "UPDATE pets SET exploring_until=? WHERE id=?",
            (until_iso, pet_id),
        )
        await self.conn.commit()

    async def finish_explore(self, pet_id: int, xp_gain: int,
                             stage: int):
        await self.conn.execute(
            "UPDATE pets SET xp=xp+?, stage=?, exploring_until=NULL "
            "WHERE id=?",
            (xp_gain, stage, pet_id),
        )
        await self.conn.commit()

    async def adult_pet_ids(self, guild_id: int, user_id: int,
                            species: str, stage: int, limit: int):
        cur = await self.conn.execute(
            "SELECT id FROM pets WHERE guild_id=? AND user_id=? AND species=? "
            "AND neon=0 AND shiny=0 AND stage=? ORDER BY id LIMIT ?",
            (guild_id, user_id, species, stage, limit),
        )
        return [r["id"] for r in await cur.fetchall()]

    async def neon_species(self, guild_id: int, user_id: int,
                           stage: int, required: int):
        """Especies con >= `required` adultas no-neon listas para combinar."""
        cur = await self.conn.execute(
            "SELECT species, COUNT(*) AS c FROM pets "
            "WHERE guild_id=? AND user_id=? AND neon=0 AND shiny=0 AND stage=? "
            "GROUP BY species HAVING c>=?",
            (guild_id, user_id, stage, required),
        )
        return await cur.fetchall()

    async def delete_pets(self, pet_ids: list[int]):
        marks = ",".join("?" * len(pet_ids))
        await self.conn.execute(
            f"DELETE FROM pets WHERE id IN ({marks})", pet_ids)
        await self.conn.commit()

    async def add_pet(self, guild_id: int, user_id: int, species: str,
                      rarity: str, neon: bool = False,
                      shiny: bool = False) -> int:
        cur = await self.conn.execute(
            "INSERT INTO pets (guild_id, user_id, species, rarity, neon, shiny) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, species, rarity, int(neon), int(shiny)),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def count_pets(self, guild_id: int, user_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM pets WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        return (await cur.fetchone())["c"]

    async def set_battle_until(self, pet_id: int, until_iso: str):
        await self.conn.execute(
            "UPDATE pets SET battle_until=? WHERE id=?",
            (until_iso, pet_id),
        )
        await self.conn.commit()

    async def add_pet_xp(self, pet_id: int, xp_gain: int, stage: int):
        await self.conn.execute(
            "UPDATE pets SET xp=xp+?, stage=? WHERE id=?",
            (xp_gain, stage, pet_id),
        )
        await self.conn.commit()

    # ---------- work / rob ----------

    async def claim_work(self, guild_id: int, user_id: int, now_iso: str,
                         reward: int) -> bool:
        """True si pasó el cooldown y reclamó. El chequeo lo hace el llamador."""
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET last_work=?, hearts=hearts+?, "
            "total_earned=total_earned+? WHERE guild_id=? AND user_id=?",
            (now_iso, reward, reward, guild_id, user_id),
        )
        await self.conn.commit()
        return True

    async def set_timestamp(self, guild_id: int, user_id: int,
                            column: str, value: str):
        assert column in {"last_work", "last_rob", "last_fish"}
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            f"UPDATE users SET {column}=? WHERE guild_id=? AND user_id=?",
            (value, guild_id, user_id),
        )
        await self.conn.commit()

    # ---------- sorteos ----------

    async def create_giveaway(self, guild_id: int, channel_id: int,
                              prize_text: str, prize_hearts: int,
                              prize_role_id: int | None, winners: int,
                              ends_at: str, host_id: int) -> int:
        cur = await self.conn.execute(
            "INSERT INTO giveaways (guild_id, channel_id, prize_text, "
            "prize_hearts, prize_role_id, winners_count, ends_at, host_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (guild_id, channel_id, prize_text, prize_hearts, prize_role_id,
             winners, ends_at, host_id),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def set_giveaway_message(self, giveaway_id: int, message_id: int):
        await self.conn.execute(
            "UPDATE giveaways SET message_id=? WHERE id=?",
            (message_id, giveaway_id),
        )
        await self.conn.commit()

    async def get_giveaway_by_message(self, message_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM giveaways WHERE message_id=?", (message_id,))
        return await cur.fetchone()

    async def get_giveaway(self, giveaway_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM giveaways WHERE id=?", (giveaway_id,))
        return await cur.fetchone()

    async def add_entry(self, giveaway_id: int, user_id: int) -> bool:
        """True si era nueva entrada."""
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO giveaway_entries (giveaway_id, user_id) "
            "VALUES (?, ?)", (giveaway_id, user_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def remove_entry(self, giveaway_id: int, user_id: int):
        await self.conn.execute(
            "DELETE FROM giveaway_entries WHERE giveaway_id=? AND user_id=?",
            (giveaway_id, user_id),
        )
        await self.conn.commit()

    async def giveaway_entries(self, giveaway_id: int) -> list[int]:
        cur = await self.conn.execute(
            "SELECT user_id FROM giveaway_entries WHERE giveaway_id=?",
            (giveaway_id,),
        )
        return [r["user_id"] for r in await cur.fetchall()]

    async def due_giveaways(self, now_iso: str):
        cur = await self.conn.execute(
            "SELECT * FROM giveaways WHERE ended=0 AND ends_at <= ?",
            (now_iso,))
        return await cur.fetchall()

    async def end_giveaway(self, giveaway_id: int):
        await self.conn.execute(
            "UPDATE giveaways SET ended=1 WHERE id=?", (giveaway_id,))
        await self.conn.commit()

    # ---------- recordatorios ----------

    async def add_reminder(self, guild_id: int, channel_id: int, user_id: int,
                           text: str, remind_at: str,
                           kind: str = "user") -> int:
        cur = await self.conn.execute(
            "INSERT INTO reminders (guild_id, channel_id, user_id, text, "
            "remind_at, kind) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, channel_id, user_id, text, remind_at, kind),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def due_reminders(self, now_iso: str):
        cur = await self.conn.execute(
            "SELECT * FROM reminders WHERE remind_at <= ?", (now_iso,))
        return await cur.fetchall()

    async def delete_reminder(self, reminder_id: int):
        await self.conn.execute(
            "DELETE FROM reminders WHERE id=?", (reminder_id,))
        await self.conn.commit()

    # ---------- lotería ----------

    async def add_lottery_tickets(self, guild_id: int, user_id: int,
                                  amount: int):
        await self.conn.execute(
            "INSERT INTO lottery_tickets (guild_id, user_id, tickets) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id, user_id) "
            "DO UPDATE SET tickets=tickets+excluded.tickets",
            (guild_id, user_id, amount),
        )
        await self.conn.commit()

    async def my_tickets(self, guild_id: int, user_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT tickets FROM lottery_tickets WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        row = await cur.fetchone()
        return row["tickets"] if row else 0

    async def lottery_pot(self, guild_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT COALESCE(SUM(tickets),0) AS t FROM lottery_tickets "
            "WHERE guild_id=?", (guild_id,))
        return (await cur.fetchone())["t"]

    async def lottery_entries(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT user_id, tickets FROM lottery_tickets WHERE guild_id=? "
            "AND tickets>0", (guild_id,))
        return await cur.fetchall()

    async def clear_lottery(self, guild_id: int):
        await self.conn.execute(
            "DELETE FROM lottery_tickets WHERE guild_id=?", (guild_id,))
        await self.conn.commit()

    # ---------- subastas ----------

    async def create_auction(self, guild_id: int, channel_id: int,
                             item_text: str, min_bid: int, ends_at: str,
                             host_id: int) -> int:
        cur = await self.conn.execute(
            "INSERT INTO auctions (guild_id, channel_id, item_text, min_bid, "
            "ends_at, host_id) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, channel_id, item_text, min_bid, ends_at, host_id),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_auction(self, auction_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM auctions WHERE id=?", (auction_id,))
        return await cur.fetchone()

    async def set_auction_message(self, auction_id: int, message_id: int):
        await self.conn.execute(
            "UPDATE auctions SET message_id=? WHERE id=?",
            (message_id, auction_id),
        )
        await self.conn.commit()

    async def get_auction_by_message(self, message_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM auctions WHERE message_id=?", (message_id,))
        return await cur.fetchone()

    async def place_bid(self, auction_id: int, amount: int, bidder_id: int):
        await self.conn.execute(
            "UPDATE auctions SET current_bid=?, bidder_id=? WHERE id=?",
            (amount, bidder_id, auction_id),
        )
        await self.conn.commit()

    async def due_auctions(self, now_iso: str):
        cur = await self.conn.execute(
            "SELECT * FROM auctions WHERE ended=0 AND ends_at <= ?",
            (now_iso,))
        return await cur.fetchall()

    async def end_auction(self, auction_id: int):
        await self.conn.execute(
            "UPDATE auctions SET ended=1 WHERE id=?", (auction_id,))
        await self.conn.commit()

    # ---------- staff (multi-rol) ----------

    async def get_staff_role_ids(self, guild_id: int) -> list[int]:
        s = await self.get_settings(guild_id)
        raw = s.get("staff_role_ids")
        if raw:
            try:
                return [int(x) for x in json.loads(raw)]
            except (ValueError, TypeError):
                pass
        rid = s.get("staff_role_id")
        return [rid] if rid else []

    async def add_staff_role(self, guild_id: int, role_id: int):
        ids = await self.get_staff_role_ids(guild_id)
        if role_id not in ids:
            ids.append(role_id)
        await self._set_staff_ids(guild_id, ids)

    async def remove_staff_role(self, guild_id: int, role_id: int):
        ids = await self.get_staff_role_ids(guild_id)
        await self._set_staff_ids(guild_id,
                                  [i for i in ids if i != role_id])

    async def _set_staff_ids(self, guild_id: int, ids: list[int]):
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id) VALUES (?) "
            "ON CONFLICT(guild_id) DO NOTHING", (guild_id,))
        await self.conn.execute(
            "UPDATE guild_settings SET staff_role_ids=? WHERE guild_id=?",
            (json.dumps(ids), guild_id))
        await self.conn.commit()

    # ---------- moderación ----------

    async def add_warning(self, guild_id: int, user_id: int,
                          moderator_id: int, reason: str):
        await self.conn.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) "
            "VALUES (?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason))
        await self.conn.commit()

    async def get_warnings(self, guild_id: int, user_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM warnings WHERE guild_id=? AND user_id=? "
            "ORDER BY id DESC", (guild_id, user_id))
        return await cur.fetchall()

    async def clear_warnings(self, guild_id: int, user_id: int):
        await self.conn.execute(
            "DELETE FROM warnings WHERE guild_id=? AND user_id=?",
            (guild_id, user_id))
        await self.conn.commit()

    # ---------- cumpleaños ----------

    async def set_birthday(self, guild_id: int, user_id: int,
                           month: int, day: int):
        await self.conn.execute(
            "INSERT INTO birthdays (guild_id, user_id, month, day) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET "
            "month=excluded.month, day=excluded.day, last_wished_year=0",
            (guild_id, user_id, month, day))
        await self.conn.commit()

    async def get_birthdays(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM birthdays WHERE guild_id=? ORDER BY month, day",
            (guild_id,))
        return await cur.fetchall()

    async def todays_birthdays(self, guild_id: int, month: int, day: int,
                               year: int):
        cur = await self.conn.execute(
            "SELECT * FROM birthdays WHERE guild_id=? AND month=? AND day=? "
            "AND last_wished_year<?", (guild_id, month, day, year))
        return await cur.fetchall()

    async def mark_birthday_wished(self, guild_id: int, user_id: int,
                                   year: int):
        await self.conn.execute(
            "UPDATE birthdays SET last_wished_year=? "
            "WHERE guild_id=? AND user_id=?",
            (year, guild_id, user_id))
        await self.conn.commit()

    # ---------- AFK ----------

    async def set_afk(self, guild_id: int, user_id: int, reason: str,
                      now_iso: str):
        await self.conn.execute(
            "INSERT INTO afk (guild_id, user_id, reason, set_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET "
            "reason=excluded.reason, set_at=excluded.set_at",
            (guild_id, user_id, reason, now_iso))
        await self.conn.commit()

    async def remove_afk(self, guild_id: int, user_id: int):
        await self.conn.execute(
            "DELETE FROM afk WHERE guild_id=? AND user_id=?",
            (guild_id, user_id))
        await self.conn.commit()

    async def get_afk(self, guild_id: int, user_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM afk WHERE guild_id=? AND user_id=?",
            (guild_id, user_id))
        return await cur.fetchone()

    # ---------- comandos personalizados ----------

    async def add_custom_command(self, guild_id: int, name: str,
                                 response: str, created_by: int):
        await self.conn.execute(
            "INSERT INTO custom_commands (guild_id, name, response, "
            "created_by) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(guild_id, name) DO UPDATE SET "
            "response=excluded.response, created_by=excluded.created_by",
            (guild_id, name, response, created_by))
        await self.conn.commit()

    async def remove_custom_command(self, guild_id: int, name: str):
        cur = await self.conn.execute(
            "DELETE FROM custom_commands WHERE guild_id=? AND name=?",
            (guild_id, name))
        await self.conn.commit()
        return cur.rowcount > 0

    async def get_custom_command(self, guild_id: int, name: str):
        cur = await self.conn.execute(
            "SELECT response FROM custom_commands "
            "WHERE guild_id=? AND name=?", (guild_id, name))
        return await cur.fetchone()

    async def get_custom_commands(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT name FROM custom_commands WHERE guild_id=? "
            "ORDER BY name", (guild_id,))
        return await cur.fetchall()

    # ---------- boss semanal ----------

    async def create_boss(self, guild_id: int, name: str, max_hp: int,
                          now_iso: str):
        await self.conn.execute(
            "INSERT INTO boss (guild_id, name, hp, max_hp, active, "
            "started_at) VALUES (?, ?, ?, ?, 1, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET name=excluded.name, "
            "hp=excluded.hp, max_hp=excluded.max_hp, active=1, "
            "started_at=excluded.started_at",
            (guild_id, name, max_hp, max_hp, now_iso))
        await self.conn.execute(
            "DELETE FROM boss_damage WHERE guild_id=?", (guild_id,))
        await self.conn.commit()

    async def get_boss(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM boss WHERE guild_id=? AND active=1", (guild_id,))
        return await cur.fetchone()

    async def latest_boss(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM boss WHERE guild_id=?", (guild_id,))
        return await cur.fetchone()

    async def all_boss_damage(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT user_id, damage FROM boss_damage WHERE guild_id=?",
            (guild_id,))
        return await cur.fetchall()

    async def add_boss_damage(self, guild_id: int, user_id: int,
                              damage: int) -> bool:
        """Suma daño; devuelve True si el boss murió con este golpe."""
        await self.conn.execute(
            "INSERT INTO boss_damage (guild_id, user_id, damage) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET "
            "damage=damage+excluded.damage",
            (guild_id, user_id, damage))
        await self.conn.execute(
            "UPDATE boss SET hp=MAX(0, hp-?) WHERE guild_id=? AND active=1",
            (damage, guild_id))
        cur = await self.conn.execute(
            "SELECT hp FROM boss WHERE guild_id=? AND active=1", (guild_id,))
        row = await cur.fetchone()
        dead = row is not None and row["hp"] <= 0
        if dead:
            await self.conn.execute(
                "UPDATE boss SET active=0 WHERE guild_id=?", (guild_id,))
        await self.conn.commit()
        return dead

    async def top_boss_damage(self, guild_id: int, limit: int = 5):
        cur = await self.conn.execute(
            "SELECT user_id, damage FROM boss_damage WHERE guild_id=? "
            "ORDER BY damage DESC LIMIT ?", (guild_id, limit))
        return await cur.fetchall()

    async def total_boss_damage(self, guild_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT COALESCE(SUM(damage),0) AS d FROM boss_damage "
            "WHERE guild_id=?", (guild_id,))
        return (await cur.fetchone())["d"]

    # ---------- confesiones / QOTD ----------

    async def bump_confession(self, guild_id: int) -> int:
        """Incrementa el contador y devuelve el número de la confesión."""
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id) VALUES (?) "
            "ON CONFLICT(guild_id) DO NOTHING", (guild_id,))
        await self.conn.execute(
            "UPDATE guild_settings SET "
            "confession_count=confession_count+1 WHERE guild_id=?",
            (guild_id,))
        await self.conn.commit()
        cur = await self.conn.execute(
            "SELECT confession_count FROM guild_settings WHERE guild_id=?",
            (guild_id,))
        return (await cur.fetchone())["confession_count"]

    async def qotd_next_index(self, guild_id: int, total: int) -> int:
        """Avanza el índice de preguntas (cíclico) y lo devuelve."""
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id) VALUES (?) "
            "ON CONFLICT(guild_id) DO NOTHING", (guild_id,))
        cur = await self.conn.execute(
            "SELECT qotd_index FROM guild_settings WHERE guild_id=?",
            (guild_id,))
        idx = ((await cur.fetchone())["qotd_index"] or 0) + 1
        await self.conn.execute(
            "UPDATE guild_settings SET qotd_index=? WHERE guild_id=?",
            (idx, guild_id))
        await self.conn.commit()
        return idx % total

    # ---------- misc: pescar / racha login ----------

    async def set_last_fish(self, guild_id: int, user_id: int, now_iso: str):
        await self.set_timestamp(guild_id, user_id, "last_fish", now_iso)

    async def get_fish_count(self, guild_id: int, user_id: int) -> int:
        u = await self.get_user(guild_id, user_id)
        today = datetime.date.today().isoformat()
        # last_fish formato YYYY-MM-DD con hora, extraemos solo la fecha
        last_date = (u["last_fish"] or "")[:10] if u["last_fish"] else ""
        if last_date != today:
            await self.conn.execute(
                "UPDATE users SET fish_count=0 WHERE guild_id=? AND user_id=?",
                (guild_id, user_id))
            await self.conn.commit()
            return 0
        return u["fish_count"]

    async def bump_fish_count(self, guild_id: int, user_id: int) -> int:
        await self.conn.execute(
            "UPDATE users SET fish_count=fish_count+1 WHERE guild_id=? AND user_id=?",
            (guild_id, user_id))
        await self.conn.commit()
        return await self.get_fish_count(guild_id, user_id)

    async def set_vip_since(self, guild_id: int, user_id: int,
                           iso: str):
        """Set vip_since solo si no está ya definido."""
        u = await self.get_user(guild_id, user_id)
        if not u["vip_since"]:
            await self.conn.execute(
                "UPDATE users SET vip_since=? WHERE guild_id=? AND user_id=?",
                (iso, guild_id, user_id))
            await self.conn.commit()

    async def bump_login_streak(self, guild_id: int, user_id: int,
                                today_iso: str) -> int:
        """Devuelve la racha actualizada (1 si es reset o primer día)."""
        u = await self.get_user(guild_id, user_id)
        last = u["mv_login_date"]
        if last == today_iso:
            return u["mv_login_streak"]
        yesterday = (datetime.date.fromisoformat(today_iso)
                     - datetime.timedelta(days=1)).isoformat()
        streak = u["mv_login_streak"] + 1 if last == yesterday else 1
        await self.conn.execute(
            "UPDATE users SET mv_login_date=?, mv_login_streak=? "
            "WHERE guild_id=? AND user_id=?",
            (today_iso, streak, guild_id, user_id))
        await self.conn.commit()
        return streak
