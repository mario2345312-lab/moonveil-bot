"""Configuración global del bot: nombre, economía, tienda, logros y misiones.

Los canales/roles por servidor se configuran con /setup y se guardan en la DB.
"""

BOT_NAME = "Moonveil Bot"
BOT_TAGLINE = "Sistema interactivo"
EMBED_COLOR = 0x9B59B6          # morado (como la imagen)
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C

HEART = "💕"

# IDs de Discord con acceso total al bot (superusuarios).
# Pueden aprobar solicitudes y usar /hearts-admin aunque no tengan rol staff.
OWNER_IDS = {410535496641675265}

# Servidor donde se sincronizan los comandos al arrancar (sync instantáneo).
# Si es None, se sincronizan globalmente (tardan hasta 1h).
# También se puede sobreescribir con la variable de entorno GUILD_ID.
GUILD_ID = 1551339041482346607

# --- Economía ---
DAILY_BASE = 100                # hearts base del /daily
DAILY_STREAK_BONUS = 10         # hearts extra por cada día de racha
FLIP_MIN_BET = 10
WORK_REWARD = (80, 150)         # rango de hearts de /work
WORK_COOLDOWN_HOURS = 4
ROB_COOLDOWN_HOURS = 1
ROB_SUCCESS = 0.45              # probabilidad de robo exitoso
ROB_MIN_STEAL = 10              # mínimo robable
ROB_MAX_PCT = 0.15              # máximo % del saldo de la víctima
ROB_FAIL_LOSS = 0.10            # % del propio saldo que se pierde al fallar
LOTTERY_TICKET_PRICE = 25       # hearts por ticket de /loteria

# --- Canal privado temporal ---
TEMP_CHANNEL_HOURS = 24

# --- Tienda ---
# tipos: custom_role | color_role | vip_role | temp_channel | chest
SHOP_ITEMS = {
    "custom_role": {
        "name": "Rol Personalizado",
        "emoji": "🎨",
        "price": 500,
        "description": "Crea un rol con el nombre y color que elijas.",
        "type": "custom_role",
        "requires_approval": True,
    },
    "color_pink": {
        "name": "Soft Pink",
        "emoji": "🌸",
        "price": 200,
        "description": "Rol de color rosa exclusivo.",
        "type": "color_role",
        "color": 0xF8BBD0,
        "requires_approval": True,
    },
    "color_purple": {
        "name": "Mystic Purple",
        "emoji": "🔮",
        "price": 200,
        "description": "Rol de color morado místico.",
        "type": "color_role",
        "color": 0x9B59B6,
        "requires_approval": True,
    },
    "color_gold": {
        "name": "Golden Sparkle",
        "emoji": "✨",
        "price": 300,
        "description": "Rol de color dorado brillante.",
        "type": "color_role",
        "color": 0xF1C40F,
        "requires_approval": True,
    },
    "exclusive_role": {
        "name": "Acceso VIP",
        "emoji": "💎",
        "price": 1000,
        "description": "Rol VIP / exclusivo del servidor.",
        "type": "vip_role",
        "requires_approval": True,
    },
    "temp_channel": {
        "name": "Canal Privado Temporal",
        "emoji": "🔒",
        "price": 1500,
        "description": f"Canal privado solo para ti durante {TEMP_CHANNEL_HOURS}h.",
        "type": "temp_channel",
        "requires_approval": True,
    },
    "flower_chest": {
        "name": "Cofre Flor",
        "emoji": "🌷",
        "price": 300,
        "description": "Cofre misterioso con Hearts aleatorios (50-500).",
        "type": "chest",
        "min_reward": 50,
        "max_reward": 500,
        "requires_approval": True,
    },
    "diamond_chest": {
        "name": "Cofre Diamante",
        "emoji": "💠",
        "price": 800,
        "description": "Cofre misterioso con Hearts aleatorios (200-1500).",
        "type": "chest",
        "min_reward": 200,
        "max_reward": 1500,
        "requires_approval": True,
    },
}

# Roles de color que se quitan al comprar otro color
COLOR_ITEM_IDS = ["color_pink", "color_purple", "color_gold"]

# --- Logros ---
# verify: "auto" (el bot comprueba el stat) | "proof" (captura -> staff)
ACHIEVEMENTS = [
    {
        "id": "neon_market",
        "name": "Neon Market",
        "emoji": "🛍️",
        "description": "Compra tu primer artículo en la tienda.",
        "verify": "auto",
        "stat": "items_bought",
        "threshold": 1,
        "reward_hearts": 300,
    },
    {
        "id": "mega_market",
        "name": "Mega Market",
        "emoji": "🏪",
        "description": "Compra 10 artículos en la tienda.",
        "verify": "auto",
        "stat": "items_bought",
        "threshold": 10,
        "reward_hearts": 300,
    },
    {
        "id": "arquitecto",
        "name": "Arquitecto",
        "emoji": "🏗️",
        "description": "Alcanza una racha de 7 días.",
        "verify": "auto",
        "stat": "best_streak",
        "threshold": 7,
        "reward_hearts": 0,
        "role_name": "Constructor",   # find-or-create si no hay role_id
        "role_color": 0xE67E22,
    },
    {
        "id": "trade",
        "name": "Trade",
        "emoji": "🔄",
        "description": "Completa un trade en Adopt Me (adjunta captura).",
        "verify": "proof",
        "reward_hearts": 250,
    },
    {
        "id": "invitador",
        "name": "Invitador",
        "emoji": "📨",
        "description": "Invita a 5 personas al servidor.",
        "verify": "auto",
        "stat": "invites_count",
        "threshold": 5,
        "reward_hearts": 500,
    },
]

# --- Misiones (se verifican con captura -> staff) ---
MISSIONS = [
    {
        "id": "adopt_trade",
        "name": "Hacer un Trade en Adopt Me",
        "emoji": "🔁",
        "description": "Completa cualquier intercambio con otro jugador.",
        "reward_hearts": 75,
        "required_count": 1,
        "repeatable": True,
    },
    {
        "id": "screenshot",
        "name": "Publicar una captura de Adopt Me",
        "emoji": "📸",
        "description": "Comparte una captura de tu juego.",
        "reward_hearts": 50,
        "required_count": 1,
        "repeatable": True,
    },
    {
        "id": "mega_events",
        "name": "Mega Misión: Participar en 3 eventos",
        "emoji": "🎪",
        "description": "Participa en 3 eventos de Moonveil.",
        "reward_hearts": 350,
        "required_count": 3,
        "repeatable": False,
    },
    {
        "id": "max_pet",
        "name": "Subir una mascota a su edad máxima",
        "emoji": "🐾",
        "description": "Lleva una mascota de Adopt Me hasta su edad máxima.",
        "reward_hearts": 200,
        "required_count": 1,
        "repeatable": False,
    },
]


# --- Moonveil (mini-juego de mascotas) ---
EXPLORE_MINUTES = 60               # duración de la exploración
EXPLORE_XP = (30, 60)              # XP base min-max
EXPLORE_HEARTS = (10, 30)          # Hearts base min-max
EXPLORE_BONUS_CHANCE = 0.10        # probabilidad de bonus x3

RARITY_INFO = {
    "comun":       {"name": "Común",       "emoji": "⚪", "mult": 1.0},
    "poco_comun":  {"name": "Poco Común",  "emoji": "🟢", "mult": 1.25},
    "rara":        {"name": "Rara",        "emoji": "🔵", "mult": 1.5},
    "ultra_rara":  {"name": "Ultra-Rara",  "emoji": "🟣", "mult": 2.0},
    "legendaria":  {"name": "Legendaria",  "emoji": "🟡", "mult": 3.0},
}
RARITY_ORDER = list(RARITY_INFO)

# especie: (emoji, rareza) — mascotas reales de Adopt Me
PETS = {
    "Cat": ("🐱", "comun"), "Dog": ("🐶", "comun"), "Otter": ("🦦", "comun"),
    "Buffalo": ("🐃", "comun"), "Chick": ("🐤", "comun"),
    "Penguin": ("🐧", "poco_comun"), "Fennec Fox": ("🦊", "poco_comun"),
    "Snow Cat": ("❄️", "poco_comun"), "Chocolate Labrador": ("🍫", "poco_comun"),
    "Red Squirrel": ("🐿️", "poco_comun"),
    "Beaver": ("🦫", "rara"), "Bunny": ("🐰", "rara"), "Elephant": ("🐘", "rara"),
    "Pig": ("🐷", "rara"), "Polar Bear": ("🐻‍❄️", "rara"),
    "Shiba Inu": ("🐕", "rara"), "Reindeer": ("🦌", "rara"),
    "Red Panda": ("🐼", "ultra_rara"), "Crocodile": ("🐊", "ultra_rara"),
    "Dalmatian": ("🐕", "ultra_rara"), "Hedgehog": ("🦔", "ultra_rara"),
    "Koala": ("🐨", "ultra_rara"), "Panda": ("🐼", "ultra_rara"),
    "Sloth": ("🦥", "ultra_rara"), "Turtle": ("🐢", "ultra_rara"),
    "Flamingo": ("🦩", "ultra_rara"), "Llama": ("🦙", "ultra_rara"),
    "Dragon": ("🐉", "legendaria"), "Unicorn": ("🦄", "legendaria"),
    "Griffin": ("🦅", "legendaria"), "Kitsune": ("🦊", "legendaria"),
    "Frost Dragon": ("🧊", "legendaria"), "Shadow Dragon": ("🖤", "legendaria"),
    "Bat Dragon": ("🦇", "legendaria"), "Giraffe": ("🦒", "legendaria"),
    "Owl": ("🦉", "legendaria"), "Parrot": ("🦜", "legendaria"),
    "Crow": ("🐦‍⬛", "legendaria"), "Evil Unicorn": ("😈", "legendaria"),
}

EGGS = {
    "cracked": {
        "name": "Cracked Egg", "emoji": "🥚", "price": 300,
        "odds": {"comun": 45, "poco_comun": 30, "rara": 16,
                 "ultra_rara": 7, "legendaria": 2},
    },
    "pet": {
        "name": "Pet Egg", "emoji": "🥚", "price": 600,
        "odds": {"comun": 25, "poco_comun": 30, "rara": 25,
                 "ultra_rara": 14, "legendaria": 6},
    },
    "royal": {
        "name": "Royal Egg", "emoji": "👑", "price": 1200,
        "odds": {"comun": 10, "poco_comun": 20, "rara": 30,
                 "ultra_rara": 27, "legendaria": 13},
    },
}

# etapas de edad reales de Adopt Me (nombre, xp mínima)
STAGES = [
    ("🐣 Recién Nacida", 0), ("🐾 Junior", 100), ("🧒 Pre-Adolescente", 300),
    ("🧑 Adolescente", 600), ("🎓 Post-Adolescente", 1000), ("🐕 Adulta", 1500),
]
NEON_STAGES = [
    ("✨ Reborn", 0), ("💫 Twinkle", 100), ("⭐ Sparkle", 300),
    ("🔥 Flare", 600), ("☀️ Sunshine", 1000), ("🌟 Luminous", 1500),
]
NEON_REQUIRED = 4            # adultas iguales para crear un Neon
NEON_MULT = 2.0              # multiplicador extra de recompensas
SHINY_CHANCE = 0.05          # probabilidad de mascota shiny al eclosionar
SHINY_MULT = 1.5             # multiplicador de recompensas de shiny
BATTLE_COOLDOWN_MIN = 30     # minutos entre batallas por mascota
BATTLE_HEARTS = (15, 40)     # hearts min-max por ganar una batalla

# misiones internas de Moonveil (stat de users, umbral, recompensa)
MV_MISSIONS = [
    {"id": "explore1", "name": "Primera expedición", "emoji": "🗺️",
     "description": "Completa tu primera exploración.",
     "stat": "mv_explores", "threshold": 1, "reward_hearts": 50},
    {"id": "explore5", "name": "Explorador novato", "emoji": "🧭",
     "description": "Completa 5 exploraciones.",
     "stat": "mv_explores", "threshold": 5, "reward_hearts": 150},
    {"id": "explore15", "name": "Explorador experto", "emoji": "🏔️",
     "description": "Completa 15 exploraciones.",
     "stat": "mv_explores", "threshold": 15, "reward_hearts": 300},
    {"id": "battle1", "name": "Primera victoria", "emoji": "⚔️",
     "description": "Gana tu primera batalla.",
     "stat": "mv_battle_wins", "threshold": 1, "reward_hearts": 100},
    {"id": "battle5", "name": "Guerrera", "emoji": "🛡️",
     "description": "Gana 5 batallas.",
     "stat": "mv_battle_wins", "threshold": 5, "reward_hearts": 250},
    {"id": "neon1", "name": "Brillo Neón", "emoji": "✨",
     "description": "Crea tu primera mascota Neon.",
     "stat": "mv_neons", "threshold": 1, "reward_hearts": 500},
    {"id": "pets5", "name": "Coleccionista", "emoji": "📦",
     "description": "Ten 5 mascotas en tu colección.",
     "stat": "mv_pets", "threshold": 5, "reward_hearts": 200},
    {"id": "pets15", "name": "Gran colección", "emoji": "🏆",
     "description": "Ten 15 mascotas en tu colección.",
     "stat": "mv_pets", "threshold": 15, "reward_hearts": 500},
]

# --- Trivia de Adopt Me (pregunta, opciones, índice correcta) ---
TRIVIA = [
    {"q": "¿En qué juego de Roblox se basa Moonveil?",
     "o": ["Brookhaven", "Adopt Me", "Bloxburg", "Pet Simulator"], "a": 1},
    {"q": "¿Cuántas mascotas iguales adultas necesitas para hacer una Neon?",
     "o": ["2", "3", "4", "6"], "a": 2},
    {"q": "¿Cuál es la etapa máxima de una mascota normal?",
     "o": ["Adolescente", "Junior", "Adulta", "Luminous"], "a": 2},
    {"q": "¿Qué mascota legendaria es un dragón de hielo?",
     "o": ["Bat Dragon", "Frost Dragon", "Shadow Dragon", "Dragon"], "a": 1},
    {"q": "¿Cuántas Neons Luminous se necesitan para una Mega Neon?",
     "o": ["2", "4", "6", "8"], "a": 1},
    {"q": "¿Cuál de estas mascotas NO existe en Adopt Me?",
     "o": ["Kitsune", "Pikachu", "Griffin", "Owlbear"], "a": 1},
    {"q": "¿Qué huevo tiene mejor probabilidad de legendario?",
     "o": ["Cracked Egg", "Pet Egg", "Royal Egg", "Todos igual"], "a": 2},
    {"q": "¿Cuál es la rareza más alta en Adopt Me?",
     "o": ["Rara", "Ultra-Rara", "Legendaria", "Épica"], "a": 2},
    {"q": "¿Qué mascota común es un ave?",
     "o": ["Cat", "Chick", "Buffalo", "Otter"], "a": 1},
    {"q": "¿Cuál es la primera etapa de una Neon?",
     "o": ["Sparkle", "Reborn", "Twinkle", "Junior"], "a": 1},
    {"q": "¿Qué mascota legendaria parece un murciélago?",
     "o": ["Bat Dragon", "Owl", "Crow", "Evil Unicorn"], "a": 0},
    {"q": "¿Cuántas etapas de edad tiene una mascota normal?",
     "o": ["4", "5", "6", "7"], "a": 2},
    {"q": "¿Qué mascota ultra-rara es un oso perezoso?",
     "o": ["Koala", "Sloth", "Panda", "Red Panda"], "a": 1},
    {"q": "¿La jirafa de Adopt Me es de rareza...?",
     "o": ["Rara", "Ultra-Rara", "Legendaria", "Común"], "a": 2},
    {"q": "¿Qué hace una mascota al explorar en Moonveil?",
     "o": ["Gana XP y Hearts", "Solo duerme", "Pierde Hearts", "Nada"], "a": 0},
]


def stage_index(xp: int) -> int:
    idx = 0
    for i, (_, min_xp) in enumerate(STAGES):
        if xp >= min_xp:
            idx = i
    return idx


def get_item(item_id: str):
    return SHOP_ITEMS.get(item_id)


def get_achievement(ach_id: str):
    return next((a for a in ACHIEVEMENTS if a["id"] == ach_id), None)


def get_mission(mis_id: str):
    return next((m for m in MISSIONS if m["id"] == mis_id), None)


# ---------- automod ----------

BAD_WORDS = [
    "puta", "puto", "mierda", "cabron", "pendejo", "imbecil",
    "fuck", "shit", "bitch", "asshole", "retard", "nigga", "whore",
]
SPAM_MESSAGES = 6          # mensajes en la ventana
SPAM_WINDOW_SECONDS = 5    # ventana de tiempo para spam
CAPS_RATIO = 0.7           # ratio de mayúsculas para activar automod
CAPS_MIN_LEN = 10          # longitud mínima del mensaje
AUTOMOD_TIMEOUT_MIN = 5    # timeout por spam

# ---------- pescar ----------

FISH_COOLDOWN_MIN = 60
FISH_REWARDS = [
    {"name_es": "Nada... solo agua", "name_en": "Nothing... just water",
     "hearts": (0, 5), "chance": 20},
    {"name_es": "Pez común", "name_en": "Common fish",
     "hearts": (15, 30), "chance": 35},
    {"name_es": "Pez raro", "name_en": "Rare fish",
     "hearts": (40, 70), "chance": 20},
    {"name_es": "Pulpo", "name_en": "Octopus",
     "hearts": (80, 120), "chance": 12},
    {"name_es": "Cofre del tesoro", "name_en": "Treasure chest",
     "hearts": (150, 250), "chance": 8},
    {"name_es": "Pez dorado", "name_en": "Golden fish",
     "hearts": (300, 400), "chance": 5},
]

# ---------- boss semanal ----------

BOSS_HP = 5000
BOSS_REWARD_POOL = 5000
BOSS_DAMAGE_FACTOR = 1       # hearts ganados = hearts * factor
BOSS_NAMES = {
    "es": "El Guardián Lunar", "en": "The Lunar Guardian"}
LOGIN_STREAK_REWARDS = {1: 25, 2: 50, 3: 75, 4: 100, 5: 150, 6: 200, 7: 300}

# ---------- QOTD (es, en) ----------

QOTD = [
    ("¿Cuál es tu mascota favorita de Adopt Me?",
     "What is your favorite Adopt Me pet?"),
    ("Si pudieras viajar a cualquier lugar, ¿a dónde irías?",
     "If you could travel anywhere, where would you go?"),
    ("¿Qué superpoder elegirías y por qué?",
     "What superpower would you choose and why?"),
    ("¿Cuál fue el último juego que jugaste?",
     "What was the last game you played?"),
    ("¿Pizza o tacos?",
     "Pizza or tacos?"),
    ("¿Qué emoji usas más?",
     "Which emoji do you use the most?"),
    ("¿Cuál es tu comida favorita?",
     "What is your favorite food?"),
    ("¿Perros o gatos?",
     "Dogs or cats?"),
    ("¿Qué serie o película recomendarías?",
     "What show or movie would you recommend?"),
    ("¿Cuál es tu meta para esta semana?",
     "What is your goal for this week?"),
    ("¿Qué harías con un millón de Hearts?",
     "What would you do with a million Hearts?"),
    ("¿Cuál es tu canción favorita ahora mismo?",
     "What is your favorite song right now?"),
    ("¿Qué mascota legendaria te falta?",
     "Which legendary pet are you missing?"),
    ("¿Madrugador o noctámbulo?",
     "Early bird or night owl?"),
]

# ---------- trades ----------

TRADE_REWARD = 100           # Hearts por trade aprobado por el staff
