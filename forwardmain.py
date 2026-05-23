#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════╗
║          🔥 GHOST FORWARDER BOT - PRODUCTION READY 🔥        ║
║              ✨ Made by @Virajjaint ✨                        ║
╚══════════════════════════════════════════════════════════════╝

Environment Variables Required:
    BOT_TOKEN   = 7826065412:AAGD9uz_LNpMiWN3uPgyMWt2NPI1hUmNrU0 <----- paste your Bot Token here (from @BotFather)
    API_ID      = 36421171 <----- paste your API ID here (from my.telegram.org)
    API_HASH    = 069627fa19eb45a775ce87939f1768c5 <----- paste your API Hash here (from my.telegram.org)

Requirements (requirements.txt):
    python-telegram-bot==20.7
    telethon==1.34.0
    python-dotenv==1.0.0
    aiohttp==3.9.1
    asyncio==3.4.3
"""

import os
import re
import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Optional, List, Tuple
from collections import defaultdict

# ─────────────────────────────────────────────
#  python-telegram-bot v20+ imports
# ─────────────────────────────────────────────
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ChatMember,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from telegram.error import (
    TelegramError,
    Forbidden,
    BadRequest,
    RetryAfter,
    NetworkError,
)
from telegram.constants import ParseMode, ChatAction

# ─────────────────────────────────────────────
#  Telethon imports for advanced forwarding
# ─────────────────────────────────────────────
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    ChatAdminRequiredError,
    ChannelPrivateError,
    MessageIdInvalidError,
    UserNotParticipantError,
)
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
)

# ─────────────────────────────────────────────
#  Environment Variables
#  PASTE YOUR CREDENTIALS BELOW ↓
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7826065412:AAGD9uz_LNpMiWN3uPgyMWt2NPI1hUmNrU0")
API_ID    = int(os.environ.get("API_ID",    "36421171"))        # <----- paste your API ID here
API_HASH  = os.environ.get("API_HASH",  "069627fa19eb45a775ce87939f1768c5")

# ─────────────────────────────────────────────
#  Required Channel (users MUST join this)
# ─────────────────────────────────────────────
REQUIRED_CHANNEL     = "Restrictedcontentforward_bot27"
REQUIRED_CHANNEL_URL = "https://t.me/Restrictedcontentforward_bot27"
WATERMARK            = "\n\n✨ *Made by @Virajjaint*"

# ─────────────────────────────────────────────
#  Conversation States
# ─────────────────────────────────────────────
WAITING_FOR_LINK  = 1
WAITING_FOR_RANGE = 2

# ─────────────────────────────────────────────
#  Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GhostForwarder")

# ─────────────────────────────────────────────
#  Stats Tracker
# ─────────────────────────────────────────────
user_stats = defaultdict(lambda: {"forwards": 0, "errors": 0, "last_active": None})

# ─────────────────────────────────────────────
#  Telethon Client (global)
# ─────────────────────────────────────────────
telethon_client: Optional[TelegramClient] = None

# ══════════════════════════════════════════════════════════════
#  🎨  HACKER-STYLE TEXT CONSTANTS
# ══════════════════════════════════════════════════════════════

HACKER_FONT = {
    "A": "Ａ", "B": "Ｂ", "C": "Ｃ", "D": "Ｄ", "E": "Ｅ",
    "F": "Ｆ", "G": "Ｇ", "H": "Ｈ", "I": "Ｉ", "J": "Ｊ",
    "K": "Ｋ", "L": "Ｌ", "M": "Ｍ", "N": "Ｎ", "O": "Ｏ",
    "P": "Ｐ", "Q": "Ｑ", "R": "Ｒ", "S": "Ｓ", "T": "Ｔ",
    "U": "Ｕ", "V": "Ｖ", "W": "Ｗ", "X": "Ｘ", "Y": "Ｙ",
    "Z": "Ｚ",
}

BOOT_FRAMES = [
    "```\n[ ░░░░░░░░░░ ]  0%  🔴\n⚡ INITIALIZING...\n```",
    "```\n[ ██░░░░░░░░ ] 20%  🟠\n⚡ LOADING MODULES...\n```",
    "```\n[ ████░░░░░░ ] 40%  🟡\n🔥 INJECTING PAYLOAD...\n```",
    "```\n[ ██████░░░░ ] 60%  🟢\n💀 BYPASSING FIREWALL...\n```",
    "```\n[ ████████░░ ] 80%  🔵\n🤖 ACTIVATING AI CORE...\n```",
    "```\n[ ██████████ ] 100% ✅\n🚀 GHOST MODE: ONLINE!\n```",
]

PROGRESS_FRAMES = [
    "▱▱▱▱▱▱▱▱▱▱",
    "▰▱▱▱▱▱▱▱▱▱",
    "▰▰▱▱▱▱▱▱▱▱",
    "▰▰▰▱▱▱▱▱▱▱",
    "▰▰▰▰▱▱▱▱▱▱",
    "▰▰▰▰▰▱▱▱▱▱",
    "▰▰▰▰▰▰▱▱▱▱",
    "▰▰▰▰▰▰▰▱▱▱",
    "▰▰▰▰▰▰▰▰▱▱",
    "▰▰▰▰▰▰▰▰▰▱",
    "▰▰▰▰▰▰▰▰▰▰",
]

LOADING_EMOJIS = ["⏳", "⌛", "🔄", "🌀", "💫", "✨", "⚡", "🔥", "💀", "🤖"]

HACKER_QUOTES = [
    "💀 *\"The quieter you become, the more you can hear...\"*",
    "⚡ *\"In cyberspace, no one can hear you scream...\"*",
    "🔥 *\"Data is the new oil, and I'm drilling...\"*",
    "🤖 *\"I am not a robot. I am a ghost in the machine...\"*",
    "💻 *\"Every system has a backdoor. This bot found yours...\"*",
    "🎭 *\"We are anonymous. We are legion. We do not forget...\"*",
    "🌐 *\"The internet never forgets, and neither do I...\"*",
    "🔮 *\"Information wants to be free...\"*",
]

ACCESS_DENIED_MSGS = [
    "💀 *Lmaooo u really thought?? Join the cult first bro* 😭",
    "☠️ *ACCESS DENIED — Bro really tried sneakin in 💀*",
    "🔒 *Nice try ngl but... the door is LOCKED king 💀*",
    "😂 *Sir this is a Wendy's... jk join the channel first bestie*",
    "💀 *You got ratio'd by a bot. Tragic. Just join the channel.*",
]

# ══════════════════════════════════════════════════════════════
#  🛠️  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════

def to_hacker_font(text: str) -> str:
    """Convert text to full-width hacker-style font."""
    return "".join(HACKER_FONT.get(c.upper(), c) for c in text)


def build_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Build an animated progress bar."""
    if total == 0:
        return PROGRESS_FRAMES[0]
    filled = int((current / total) * width)
    filled = min(filled, width)
    bar = "▰" * filled + "▱" * (width - filled)
    percent = int((current / total) * 100)
    return f"{bar} {percent}%"


def parse_telegram_link(link: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse a Telegram message link.
    Returns: (chat_identifier, message_id, thread_id)
    Supports:
        https://t.me/username/123
        https://t.me/c/1234567890/123
        https://t.me/username/456/789  (topic thread)
    """
    link = link.strip()

    # Pattern: private channel  t.me/c/CHAT_ID/MSG_ID
    private_pattern = r"(?:https?://)?t\.me/c/(-?\d+)/(\d+)"
    # Pattern: public channel   t.me/USERNAME/MSG_ID
    public_pattern  = r"(?:https?://)?t\.me/([a-zA-Z0-9_]+)/(\d+)(?:/(\d+))?"

    m = re.match(private_pattern, link)
    if m:
        chat_id = int("-100" + m.group(1))
        msg_id  = int(m.group(2))
        return str(chat_id), msg_id, None

    m = re.match(public_pattern, link)
    if m:
        username  = m.group(1)
        id_part_1 = int(m.group(2))
        id_part_2 = int(m.group(3)) if m.group(3) else None
        if id_part_2:
            # username/thread_id/msg_id
            return username, id_part_2, id_part_1
        return username, id_part_1, None

    return None, None, None


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.1f} GB"


def log_user_action(user_id: int, action: str, details: str = ""):
    """Log user actions with stats tracking."""
    user_stats[user_id]["last_active"] = datetime.now().isoformat()
    logger.info(f"USER:{user_id} | ACTION:{action} | {details}")


# ══════════════════════════════════════════════════════════════
#  🔐  MEMBERSHIP CHECK
# ══════════════════════════════════════════════════════════════

async def check_membership(bot, user_id: int) -> bool:
    """Check if user has joined the required channel."""
    try:
        member: ChatMember = await bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id,
        )
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        ]
    except Forbidden:
        logger.warning(f"Bot not in channel @{REQUIRED_CHANNEL}")
        return False
    except BadRequest as e:
        logger.error(f"Membership check error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected membership check error: {e}")
        return False


async def require_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Decorator-style helper: checks membership and sends
    the blocked message if user hasn't joined.
    Returns True if user is a member, False otherwise.
    """
    user = update.effective_user
    is_member = await check_membership(context.bot, user.id)

    if not is_member:
        denial_msg = random.choice(ACCESS_DENIED_MSGS)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 JOIN THE CULT NOW 🔥", url=REQUIRED_CHANNEL_URL)],
            [InlineKeyboardButton("✅ I Joined, Let Me In!", callback_data="check_membership")],
        ])
        blocked_text = (
            f"╔══════════════════════════╗\n"
            f"║   💀 A C C E S S   D E N I E D  ☠️   ║\n"
            f"╚══════════════════════════╝\n\n"
            f"{denial_msg}\n\n"
            f"🔒 *This bot is member-exclusive, bestie.*\n\n"
            f"📢 You gotta join:\n"
            f"👉 [Restricted Content Forward]({REQUIRED_CHANNEL_URL})\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Bot Status:* `LOCKED 🔐`\n"
            f"💀 *Your Status:* `OUTSIDER`\n"
            f"⚡ *Required:* `JOIN THE CHANNEL`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{WATERMARK}"
        )
        await update.effective_message.reply_text(
            blocked_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        log_user_action(user.id, "ACCESS_DENIED", f"username={user.username}")
        return False

    return True


# ══════════════════════════════════════════════════════════════
#  🎬  ANIMATION ENGINE
# ══════════════════════════════════════════════════════════════

async def animate_boot_sequence(message: Message) -> None:
    """Play the animated boot sequence on a message."""
    for frame in BOOT_FRAMES:
        try:
            await message.edit_text(frame, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(0.6)
        except Exception:
            pass


async def animate_progress(
    message: Message,
    current: int,
    total: int,
    label: str = "Processing",
    extra_info: str = "",
) -> None:
    """Update a message with an animated progress bar."""
    bar = build_progress_bar(current, total)
    emoji = random.choice(LOADING_EMOJIS)
    percent = int((current / total) * 100) if total > 0 else 0

    status_lines = [
        "⠀",
        f"```",
        f"┌─────────────────────────┐",
        f"│  {emoji} {label.upper()[:20]:<20} │",
        f"│  {bar} │",
        f"│  Progress: {current}/{total} ({percent}%)  │",
        f"└─────────────────────────┘",
        f"```",
    ]
    if extra_info:
        status_lines.append(f"\n💬 `{extra_info}`")
    status_lines.append(WATERMARK)

    try:
        await message.edit_text(
            "\n".join(status_lines),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest:
        pass  # Message not modified


async def animate_thinking(message: Message, steps: int = 5) -> None:
    """Animate a thinking/processing sequence."""
    thinking_frames = [
        "🤔 `Thinking...`",
        "💭 `Processing neural pathways...`",
        "🧠 `Analyzing data streams...`",
        "⚡ `Charging laser beams...`",
        "🔮 `Consulting the dark web...`",
        "💀 `Hacking the mainframe...`",
        "🌐 `Connecting to ghost server...`",
        "🚀 `Almost there...`",
    ]
    for i in range(min(steps, len(thinking_frames))):
        try:
            await message.edit_text(
                f"{thinking_frames[i]}\n{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await asyncio.sleep(0.7)
        except Exception:
            pass


async def animate_typing_text(message: Message, final_text: str, delay: float = 0.05) -> None:
    """Simulate typing animation by progressively revealing text."""
    words = final_text.split()
    current = ""
    for i, word in enumerate(words):
        current += ("" if i == 0 else " ") + word
        if i % 3 == 0 or i == len(words) - 1:
            try:
                await message.edit_text(
                    current + " ▌",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                await asyncio.sleep(delay)
            except Exception:
                pass
    try:
        await message.edit_text(
            final_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
#  📨  /START COMMAND
# ══════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start with full animated boot sequence."""
    user   = update.effective_user
    chat   = update.effective_chat

    log_user_action(user.id, "START", f"username={user.username}")

    # ── Phase 1: Boot animation ──────────────────────────────
    boot_msg = await update.message.reply_text(
        "```\n[ ░░░░░░░░░░ ]  0%  🔴\n⚡ INITIALIZING...\n```",
        parse_mode=ParseMode.MARKDOWN,
    )
    await animate_boot_sequence(boot_msg)
    await asyncio.sleep(0.3)

    # ── Phase 2: Check membership ────────────────────────────
    is_member = await check_membership(context.bot, user.id)

    if not is_member:
        denial_msg = random.choice(ACCESS_DENIED_MSGS)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 JOIN THE CULT NOW 🔥", url=REQUIRED_CHANNEL_URL)],
            [InlineKeyboardButton("✅ Already Joined — Let Me IN!", callback_data="check_membership")],
        ])
        blocked = (
            f"```\n"
            f"╔══════════════════════════════╗\n"
            f"║   💀  ACCESS  DENIED  ☠️   ║\n"
            f"║   ERROR CODE: 403_OUTSIDER   ║\n"
            f"╚══════════════════════════════╝\n"
            f"```\n\n"
            f"{denial_msg}\n\n"
            f"🔒 *Yo, this bot is exclusive, bestie.*\n"
            f"You gotta join the channel to unlock the ghost powers 👻\n\n"
            f"📢 Required Channel:\n"
            f"👉 [Restricted Content Forward]({REQUIRED_CHANNEL_URL})\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 Status  : `SYSTEM LOCKED 🔐`\n"
            f"💀 Access  : `DENIED ❌`\n"
            f"⚡ Action  : `JOIN → UNLOCK`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{WATERMARK}"
        )
        await boot_msg.edit_text(
            blocked,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        return

    # ── Phase 3: Welcome animation ───────────────────────────
    hacker_name = to_hacker_font(user.first_name[:10] if user.first_name else "USER")
    quote = random.choice(HACKER_QUOTES)

    welcome_text = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║  ⚡ G H O S T   F O R W A R D E R  ⚡  ║\n"
        f"║        💀 S Y S T E M  O N L I N E  💀  ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"```\n\n"
        f"👾 *Ｗｅｌｃｏｍｅ，* `{hacker_name}` 🫶🏻\n\n"
        f"{quote}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *SYSTEM CAPABILITIES UNLOCKED:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ `/forward` — Ghost-forward any message\n"
        f"   ↳ 📸 Photos  📹 Videos  📄 Docs  💬 Text\n\n"
        f"🔥 `/bulk` — Mass forward engine (100/batch)\n"
        f"   ↳ 🚀 Up to 1000 messages per session\n\n"
        f"💀 `/stats` — Your ghost activity report\n"
        f"   ↳ 📊 Forward count, errors, last active\n\n"
        f"🤖 `/help` — Full command manual\n"
        f"   ↳ 📖 All tricks and hacks listed\n\n"
        f"🌐 `/ping` — Check if ghost is alive\n"
        f"   ↳ 💓 Heartbeat monitor\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"```\n"
        f"[SYSTEM] User authenticated ✅\n"
        f"[SYSTEM] Ghost mode: ACTIVE 👻\n"
        f"[SYSTEM] Rate limit: MANAGED 🛡️\n"
        f"[SYSTEM] Encryption: ENABLED 🔐\n"
        f"```\n\n"
        f"💀 *Stay in the shadows, king.* ⚡\n\n"
        f"{WATERMARK}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Forward Message", callback_data="cmd_forward"),
            InlineKeyboardButton("🔥 Bulk Forward", callback_data="cmd_bulk"),
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="cmd_stats"),
            InlineKeyboardButton("📖 Help", callback_data="cmd_help"),
        ],
        [
            InlineKeyboardButton("🌐 Join Channel", url=REQUIRED_CHANNEL_URL),
        ],
    ])

    await boot_msg.edit_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


# ══════════════════════════════════════════════════════════════
#  📖  /HELP COMMAND
# ══════════════════════════════════════════════════════════════

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show full help manual in hacker style."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "HELP")

    help_text = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║   🤖  GHOST FORWARDER — MANUAL  🤖   ║\n"
        f"║      💀 READ CAREFULLY KING 💀       ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"```\n\n"
        f"⚡ *COMMAND REFERENCE:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 `/start`\n"
        f"   ↳ Boot the ghost system\n"
        f"   ↳ Animated startup sequence\n\n"
        f"🔹 `/forward <link>`\n"
        f"   ↳ Forward a single message\n"
        f"   ↳ Supports: photos, videos, docs, text\n"
        f"   ↳ Example: `/forward https://t.me/channel/123`\n\n"
        f"🔹 `/bulk`\n"
        f"   ↳ Bulk forward mode (interactive)\n"
        f"   ↳ Step 1: Send source link\n"
        f"   ↳ Step 2: Send range (e.g. `1-500`)\n"
        f"   ↳ Auto-batches 100 msgs at a time\n"
        f"   ↳ Built-in flood protection\n\n"
        f"🔹 `/stats`\n"
        f"   ↳ Your personal usage stats\n"
        f"   ↳ Total forwards, errors, activity\n\n"
        f"🔹 `/ping`\n"
        f"   ↳ Check bot heartbeat\n"
        f"   ↳ See response latency\n\n"
        f"🔹 `/cancel`\n"
        f"   ↳ Cancel any active operation\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📎 *SUPPORTED LINK FORMATS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ `https://t.me/username/123`\n"
        f"✅ `https://t.me/c/1234567890/456`\n"
        f"✅ `t.me/username/789`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *IMPORTANT RULES:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💀 Bot only accesses what it has permission to\n"
        f"🔒 No private channel bypassing\n"
        f"⚡ Rate limiting prevents Telegram bans\n"
        f"🛡️ FloodWait handled automatically\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{WATERMARK}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Forward", callback_data="cmd_forward"),
            InlineKeyboardButton("🔥 Bulk", callback_data="cmd_bulk"),
        ],
        [InlineKeyboardButton("🏠 Back to Start", callback_data="cmd_start")],
    ])

    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ══════════════════════════════════════════════════════════════
#  📊  /STATS COMMAND
# ══════════════════════════════════════════════════════════════

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user stats in hacker dashboard style."""
    if not await require_membership(update, context):
        return

    user    = update.effective_user
    stats   = user_stats[user.id]
    log_user_action(user.id, "STATS")

    global_total = sum(s["forwards"] for s in user_stats.values())
    global_users = len(user_stats)

    last_active = stats.get("last_active") or "Never"
    if last_active != "Never":
        try:
            dt = datetime.fromisoformat(last_active)
            last_active = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    stats_text = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║   📊  GHOST ACTIVITY REPORT  📊      ║\n"
        f"║       💀 YOUR DARK PROFILE 💀        ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"```\n\n"
        f"👤 *USER PROFILE:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID        : `{user.id}`\n"
        f"👾 Username  : `@{user.username or 'N/A'}`\n"
        f"📛 Name      : `{user.first_name}`\n"
        f"⏰ Last Seen : `{last_active}`\n\n"
        f"📈 *YOUR STATS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Forwards  : `{stats['forwards']}`\n"
        f"❌ Errors    : `{stats['errors']}`\n"
        f"💯 Success % : `{_success_rate(stats)}%`\n\n"
        f"🌐 *GLOBAL STATS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users    : `{global_users}`\n"
        f"📨 Total Forwards : `{global_total}`\n\n"
        f"```\n"
        f"[STATUS] Ghost: OPERATIONAL ✅\n"
        f"[STATUS] Rank: {'ELITE 💀' if stats['forwards'] > 100 else 'ROOKIE 🌱'}\n"
        f"```\n\n"
        f"{WATERMARK}"
    )

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


def _success_rate(stats: dict) -> int:
    total = stats["forwards"] + stats["errors"]
    if total == 0:
        return 100
    return int((stats["forwards"] / total) * 100)


# ══════════════════════════════════════════════════════════════
#  💓  /PING COMMAND
# ══════════════════════════════════════════════════════════════

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping the bot and show latency."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "PING")

    start_time = time.time()
    msg = await update.message.reply_text(
        "```\n[PING] Sending pulse to ghost server...\n```",
        parse_mode=ParseMode.MARKDOWN,
    )
    latency_ms = int((time.time() - start_time) * 1000)

    quality = "🟢 EXCELLENT" if latency_ms < 200 else ("🟡 GOOD" if latency_ms < 500 else "🔴 POOR")

    ping_text = (
        f"```\n"
        f"╔═══════════════════════════╗\n"
        f"║   💓  HEARTBEAT CHECK  💓  ║\n"
        f"╚═══════════════════════════╝\n"
        f"\n"
        f"[PING]  → Ghost Server\n"
        f"[PONG]  ← Response received\n"
        f"\n"
        f"Latency : {latency_ms}ms\n"
        f"Quality : {quality}\n"
        f"Status  : ONLINE ✅\n"
        f"Ghost   : ACTIVE 👻\n"
        f"```\n\n"
        f"⚡ *Response time:* `{latency_ms}ms`\n"
        f"{WATERMARK}"
    )

    await msg.edit_text(ping_text, parse_mode=ParseMode.MARKDOWN)


# ══════════════════════════════════════════════════════════════
#  ⚡  /FORWARD COMMAND  (Single message)
# ══════════════════════════════════════════════════════════════

async def forward_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the forward conversation."""
    if not await require_membership(update, context):
        return ConversationHandler.END

    user = update.effective_user
    log_user_action(user.id, "FORWARD_START")

    # If link provided inline: /forward https://t.me/...
    if context.args:
        link = context.args[0]
        context.user_data["forward_link"] = link
        await _process_single_forward(update, context, link)
        return ConversationHandler.END

    prompt = (
        f"```\n"
        f"╔══════════════════════════════════╗\n"
        f"║   ⚡  GHOST FORWARD ENGINE  ⚡   ║\n"
        f"║      💀 SINGLE FIRE MODE 💀      ║\n"
        f"╚══════════════════════════════════╝\n"
        f"```\n\n"
        f"🔗 *Send me the Telegram message link*\n\n"
        f"📎 *Accepted formats:*\n"
        f"↳ `https://t.me/username/123`\n"
        f"↳ `https://t.me/c/1234567890/456`\n"
        f"↳ `t.me/channel/789`\n\n"
        f"⚠️ *Note:* Bot must have access to the source\n\n"
        f"💀 Send the link or /cancel to abort\n\n"
        f"{WATERMARK}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Operation", callback_data="cancel")],
    ])

    await update.message.reply_text(
        prompt,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )
    return WAITING_FOR_LINK


async def receive_forward_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and process the forwarded link."""
    if not await require_membership(update, context):
        return ConversationHandler.END

    link = update.message.text.strip()
    await _process_single_forward(update, context, link)
    return ConversationHandler.END


async def _process_single_forward(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    link: str,
) -> None:
    """Core logic for single message forwarding."""
    user     = update.effective_user
    chat_id  = update.effective_chat.id

    status_msg = await update.effective_message.reply_text(
        "```\n[GHOST] Initializing forward sequence...\n⚡ Parsing link...\n```",
        parse_mode=ParseMode.MARKDOWN,
    )

    await animate_thinking(status_msg, steps=4)

    # Parse link
    chat_identifier, msg_id, _ = parse_telegram_link(link)

    if not chat_identifier or not msg_id:
        await status_msg.edit_text(
            f"```\n"
            f"╔═══════════════════════╗\n"
            f"║  ❌  INVALID LINK  ❌  ║\n"
            f"╚═══════════════════════╝\n"
            f"```\n\n"
            f"💀 *That link is totally cooked bro*\n\n"
            f"🔗 *Accepted formats:*\n"
            f"↳ `https://t.me/username/123`\n"
            f"↳ `https://t.me/c/1234567890/456`\n\n"
            f"Try again with `/forward`\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        user_stats[user.id]["errors"] += 1
        return

    log_user_action(user.id, "FORWARD_LINK", f"chat={chat_identifier} msg={msg_id}")

    # Attempt forward via Telethon
    await status_msg.edit_text(
        f"```\n"
        f"[GHOST] Link parsed ✅\n"
        f"[GHOST] Target: {chat_identifier}\n"
        f"[GHOST] Message ID: {msg_id}\n"
        f"[GHOST] Connecting to ghost server...\n"
        f"```",
        parse_mode=ParseMode.MARKDOWN,
    )

    success = await _telethon_forward_single(
        user_tg_id=user.id,
        chat_identifier=chat_identifier,
        msg_id=msg_id,
        dest_chat_id=chat_id,
        status_msg=status_msg,
        context=context,
    )

    if success:
        user_stats[user.id]["forwards"] += 1
        await status_msg.edit_text(
            f"```\n"
            f"╔═══════════════════════════════╗\n"
            f"║  ✅  FORWARD COMPLETE  ✅     ║\n"
            f"║     💀 GHOST DELIVERED 👻     ║\n"
            f"╚═══════════════════════════════╝\n"
            f"```\n\n"
            f"⚡ *Message forwarded successfully!*\n"
            f"📨 Source: `{chat_identifier}/{msg_id}`\n"
            f"💀 Ghost status: `MISSION COMPLETE`\n\n"
            f"🔥 Total forwards: `{user_stats[user.id]['forwards']}`\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        user_stats[user.id]["errors"] += 1


# ══════════════════════════════════════════════════════════════
#  🔥  /BULK COMMAND  (Bulk forwarding engine)
# ══════════════════════════════════════════════════════════════

async def bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bulk forward conversation."""
    if not await require_membership(update, context):
        return ConversationHandler.END

    user = update.effective_user
    log_user_action(user.id, "BULK_START")

    prompt = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║  🔥  GHOST BULK FORWARD ENGINE  🔥   ║\n"
        f"║    💀 MASS OPERATION MODE 💀          ║\n"
        f"║    ⚡ 100 msgs/batch | auto-delay ⚡  ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"```\n\n"
        f"🚀 *STEP 1 of 2:* Send the source channel link\n\n"
        f"📎 *Format:*\n"
        f"↳ `https://t.me/username/FIRST_MSG_ID`\n"
        f"↳ The bot fetches from that message onwards\n\n"
        f"⚠️ *Requirements:*\n"
        f"↳ Bot must be a member of source channel\n"
        f"↳ Or channel must be public\n\n"
        f"💀 Send the link or /cancel to abort\n\n"
        f"{WATERMARK}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Operation", callback_data="cancel")],
    ])

    await update.message.reply_text(
        prompt,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )
    return WAITING_FOR_LINK


async def bulk_receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the source link for bulk forwarding."""
    if not await require_membership(update, context):
        return ConversationHandler.END

    link = update.message.text.strip()
    chat_identifier, start_id, _ = parse_telegram_link(link)

    if not chat_identifier or not start_id:
        await update.message.reply_text(
            f"❌ *Invalid link!* Try again or /cancel\n\n"
            f"Format: `https://t.me/username/123`\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return WAITING_FOR_LINK

    context.user_data["bulk_chat"]     = chat_identifier
    context.user_data["bulk_start_id"] = start_id

    await update.message.reply_text(
        f"```\n"
        f"[GHOST] Source: {chat_identifier}\n"
        f"[GHOST] Start ID: {start_id}\n"
        f"[GHOST] Link parsed ✅\n"
        f"```\n\n"
        f"🎯 *STEP 2 of 2:* How many messages?\n\n"
        f"📏 *Send a range or count:*\n"
        f"↳ Single count: `500` (forward 500 msgs)\n"
        f"↳ Range: `100-600` (IDs 100 to 600)\n"
        f"↳ Max recommended: `1000`\n\n"
        f"⚡ *Auto-batching:* 100 msgs/batch with delays\n"
        f"🛡️ *Flood protection:* Fully managed\n\n"
        f"💀 Send count/range or /cancel\n\n"
        f"{WATERMARK}",
        parse_mode=ParseMode.MARKDOWN,
    )
    return WAITING_FOR_RANGE


async def bulk_receive_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the range and start bulk forwarding."""
    if not await require_membership(update, context):
        return ConversationHandler.END

    user      = update.effective_user
    chat_id   = update.effective_chat.id
    text      = update.message.text.strip()

    chat_identifier = context.user_data.get("bulk_chat")
    start_id        = context.user_data.get("bulk_start_id")

    # Parse range
    range_pattern = r"^(\d+)(?:-(\d+))?$"
    m = re.match(range_pattern, text)
    if not m:
        await update.message.reply_text(
            f"❌ *Invalid range!*\n\nSend like: `500` or `100-600`\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return WAITING_FOR_RANGE

    if m.group(2):  # Range format: START-END
        range_start = int(m.group(1))
        range_end   = int(m.group(2))
    else:  # Count format: just a number
        count       = int(m.group(1))
        range_start = start_id
        range_end   = start_id + count - 1

    if range_end < range_start:
        range_start, range_end = range_end, range_start

    total_msgs = range_end - range_start + 1

    log_user_action(user.id, "BULK_FORWARD", f"chat={chat_identifier} range={range_start}-{range_end}")

    status_msg = await update.message.reply_text(
        f"```\n"
        f"╔══════════════════════════════════╗\n"
        f"║  🚀  BULK FORWARD INITIATED  🚀  ║\n"
        f"╚══════════════════════════════════╝\n"
        f"\n"
        f"[CONFIG] Source : {chat_identifier}\n"
        f"[CONFIG] Range  : {range_start} → {range_end}\n"
        f"[CONFIG] Total  : {total_msgs} messages\n"
        f"[CONFIG] Batch  : 100 msgs/batch\n"
        f"[CONFIG] Delay  : 5-10s/batch\n"
        f"\n"
        f"[STATUS] Initializing ghost protocol...\n"
        f"```",
        parse_mode=ParseMode.MARKDOWN,
    )

    await asyncio.sleep(1)

    # Run bulk forward
    await _bulk_forward_engine(
        user_id         = user.id,
        chat_identifier = chat_identifier,
        range_start     = range_start,
        range_end       = range_end,
        dest_chat_id    = chat_id,
        status_msg      = status_msg,
        context         = context,
    )

    return ConversationHandler.END


async def _bulk_forward_engine(
    user_id: int,
    chat_identifier: str,
    range_start: int,
    range_end: int,
    dest_chat_id: int,
    status_msg: Message,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Core bulk forwarding engine.
    Processes messages in batches of 100 with rate limiting.
    """
    global telethon_client

    if telethon_client is None or not telethon_client.is_connected():
        await status_msg.edit_text(
            f"❌ *Ghost server offline!*\n\n"
            f"Telethon client not connected. Contact admin.\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    BATCH_SIZE  = 100
    total       = range_end - range_start + 1
    forwarded   = 0
    errors      = 0
    batch_count = 0
    start_time  = time.time()

    all_ids = list(range(range_start, range_end + 1))

    try:
        entity = await telethon_client.get_entity(chat_identifier)
    except Exception as e:
        await status_msg.edit_text(
            f"```\n"
            f"╔═══════════════════════╗\n"
            f"║  ❌  ACCESS DENIED  ❌ ║\n"
            f"╚═══════════════════════╝\n"
            f"```\n\n"
            f"💀 *Can't reach that channel bro*\n\n"
            f"Error: `{str(e)[:100]}`\n\n"
            f"Make sure the bot/account has access!\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        user_stats[user_id]["errors"] += 1
        return

    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch_ids   = all_ids[batch_start : batch_start + BATCH_SIZE]
        batch_count += 1
        batch_num    = (batch_start // BATCH_SIZE) + 1
        total_batches= (total + BATCH_SIZE - 1) // BATCH_SIZE

        # ── Fetch messages ───────────────────────────────────
        await status_msg.edit_text(
            f"```\n"
            f"╔══════════════════════════════════╗\n"
            f"║   ⚡  GHOST BULK ENGINE  ⚡       ║\n"
            f"╚══════════════════════════════════╝\n"
            f"\n"
            f"[BATCH] {batch_num}/{total_batches}\n"
            f"[FETCH] IDs {batch_ids[0]} → {batch_ids[-1]}\n"
            f"[PROG]  {build_progress_bar(forwarded, total)} {forwarded}/{total}\n"
            f"[SPEED] {_calc_speed(forwarded, start_time)}\n"
            f"[ETA]   {_calc_eta(forwarded, total, start_time)}\n"
            f"```",
            parse_mode=ParseMode.MARKDOWN,
        )

        try:
            messages = await telethon_client.get_messages(entity, ids=batch_ids)
        except FloodWaitError as e:
            wait_time = e.seconds + 5
            logger.warning(f"FloodWait: sleeping {wait_time}s")
            await _flood_wait_animation(status_msg, wait_time)
            try:
                messages = await telethon_client.get_messages(entity, ids=batch_ids)
            except Exception as retry_err:
                logger.error(f"Retry failed: {retry_err}")
                errors += len(batch_ids)
                continue
        except ChannelPrivateError:
            await status_msg.edit_text(
                f"❌ *Private channel — no access!*\n\n"
                f"The bot doesn't have permission to read this channel.\n{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            errors += len(batch_ids)
            continue

        # ── Forward messages in batch ────────────────────────
        batch_forwarded = 0
        for idx, msg in enumerate(messages):
            if msg is None:
                errors += 1
                continue

            success = await _forward_single_telethon_msg(
                msg         = msg,
                dest_chat_id= dest_chat_id,
                context     = context,
            )

            if success:
                forwarded       += 1
                batch_forwarded += 1
                user_stats[user_id]["forwards"] += 1
            else:
                errors += 1
                user_stats[user_id]["errors"] += 1

            # Update progress every 10 messages
            if idx % 10 == 0:
                await animate_progress(
                    message     = status_msg,
                    current     = forwarded,
                    total       = total,
                    label       = "BULK FORWARDING",
                    extra_info  = f"Batch {batch_num}/{total_batches} | ✅{forwarded} ❌{errors}",
                )
                await asyncio.sleep(0.1)

            # Small delay between individual forwards
            await asyncio.sleep(random.uniform(0.3, 0.8))

        # ── Inter-batch delay with animation ────────────────
        if batch_start + BATCH_SIZE < total:
            delay = random.randint(5, 10)
            logger.info(f"Batch {batch_num} done. Sleeping {delay}s before next batch.")

            await status_msg.edit_text(
                f"```\n"
                f"╔══════════════════════════════════╗\n"
                f"║   🛡️  RATE LIMIT PROTECTION  🛡️  ║\n"
                f"╚══════════════════════════════════╝\n"
                f"\n"
                f"[BATCH {batch_num}] Complete ✅\n"
                f"[BATCH {batch_num}] Forwarded: {batch_forwarded}\n"
                f"[TOTAL]  ✅ {forwarded} / ❌ {errors}\n"
                f"[PROG]   {build_progress_bar(forwarded, total)}\n"
                f"[PAUSE]  Cooling down {delay}s to avoid flood...\n"
                f"[NEXT]   Batch {batch_num + 1}/{total_batches} incoming\n"
                f"```",
                parse_mode=ParseMode.MARKDOWN,
            )

            # Countdown animation
            for remaining in range(delay, 0, -1):
                await asyncio.sleep(1)
                bar = "⬜" * remaining + "⬛" * (delay - remaining)
                try:
                    await status_msg.edit_text(
                        f"```\n"
                        f"[COOLDOWN] {bar}\n"
                        f"[WAIT]     {remaining}s remaining...\n"
                        f"[STATUS]   Preventing flood ban 🛡️\n"
                        f"```\n\n"
                        f"💀 *Ghost is cooling down between batches...*\n"
                        f"⚡ Progress: `{forwarded}/{total}`\n{WATERMARK}",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

    # ── Final report ─────────────────────────────────────────
    elapsed     = int(time.time() - start_time)
    success_pct = int((forwarded / max(total, 1)) * 100)

    final_text = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║   🎉  BULK FORWARD COMPLETE  🎉      ║\n"
        f"║      💀 GHOST MISSION DONE 💀         ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"\n"
        f"[RESULT] Total Requested : {total}\n"
        f"[RESULT] Forwarded       : {forwarded} ✅\n"
        f"[RESULT] Failed          : {errors} ❌\n"
        f"[RESULT] Success Rate    : {success_pct}%\n"
        f"[RESULT] Time Elapsed    : {elapsed}s\n"
        f"[RESULT] Batches Done    : {batch_count}\n"
        f"```\n\n"
        f"🎊 *All done king!* Ghost delivered the goods 👻\n\n"
        f"💀 Total your forwards: `{user_stats[user_id]['forwards']}`\n\n"
        f"{WATERMARK}"
    )

    await status_msg.edit_text(final_text, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"Bulk forward complete: user={user_id} forwarded={forwarded} errors={errors}")


def _calc_speed(forwarded: int, start_time: float) -> str:
    """Calculate forwarding speed."""
    elapsed = time.time() - start_time
    if elapsed < 1 or forwarded == 0:
        return "Calculating..."
    speed = forwarded / elapsed
    return f"{speed:.1f} msgs/s"


def _calc_eta(forwarded: int, total: int, start_time: float) -> str:
    """Calculate estimated time remaining."""
    elapsed = time.time() - start_time
    if elapsed < 1 or forwarded == 0:
        return "Calculating..."
    speed = forwarded / elapsed
    remaining = total - forwarded
    if speed <= 0:
        return "Unknown"
    eta_seconds = int(remaining / speed)
    if eta_seconds < 60:
        return f"{eta_seconds}s"
    elif eta_seconds < 3600:
        return f"{eta_seconds // 60}m {eta_seconds % 60}s"
    else:
        return f"{eta_seconds // 3600}h {(eta_seconds % 3600) // 60}m"


async def _flood_wait_animation(message: Message, wait_seconds: int) -> None:
    """Animate flood wait countdown."""
    for remaining in range(wait_seconds, 0, -1):
        try:
            await message.edit_text(
                f"```\n"
                f"╔════════════════════════════╗\n"
                f"║  ⚠️  FLOOD WAIT DETECTED  ⚠️ ║\n"
                f"╚════════════════════════════╝\n"
                f"\n"
                f"[TELEGRAM] Rate limit hit!\n"
                f"[WAIT]     {remaining}s remaining\n"
                f"[STATUS]   Auto-resume after wait\n"
                f"[REASON]   Too many requests\n"
                f"```\n\n"
                f"🛡️ *Telegram said slow down bruh*\n"
                f"⏳ Resuming in `{remaining}s`...\n{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(1)


# ══════════════════════════════════════════════════════════════
#  🔧  TELETHON FORWARDING HELPERS
# ══════════════════════════════════════════════════════════════

async def _telethon_forward_single(
    user_tg_id: int,
    chat_identifier: str,
    msg_id: int,
    dest_chat_id: int,
    status_msg: Message,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Forward a single message via Telethon."""
    global telethon_client

    if telethon_client is None or not telethon_client.is_connected():
        await status_msg.edit_text(
            f"❌ *Ghost server offline!*\n\nContact admin.\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False

    try:
        entity  = await telethon_client.get_entity(chat_identifier)
        message = await telethon_client.get_messages(entity, ids=msg_id)

        if message is None:
            await status_msg.edit_text(
                f"```\n"
                f"╔════════════════════════╗\n"
                f"║  ❌  NOT FOUND  ❌     ║\n"
                f"╚════════════════════════╝\n"
                f"```\n\n"
                f"💀 *Message not found!*\n\n"
                f"The message might be deleted or ID is wrong.\n{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return False

        await status_msg.edit_text(
            f"```\n"
            f"[GHOST] Message found ✅\n"
            f"[GHOST] Type: {_get_msg_type(message)}\n"
            f"[GHOST] Forwarding to you...\n"
            f"```",
            parse_mode=ParseMode.MARKDOWN,
        )

        await _forward_single_telethon_msg(message, dest_chat_id, context)
        return True

    except FloodWaitError as e:
        wait = e.seconds + 5
        logger.warning(f"FloodWait {wait}s for user {user_tg_id}")
        await _flood_wait_animation(status_msg, wait)
        return await _telethon_forward_single(
            user_tg_id, chat_identifier, msg_id, dest_chat_id, status_msg, context
        )
    except MessageIdInvalidError:
        await status_msg.edit_text(
            f"❌ *Invalid message ID!*\n\nDouble-check the link.\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False
    except ChannelPrivateError:
        await status_msg.edit_text(
            f"🔒 *Private channel!*\n\nBot doesn't have access.\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False
    except ChatAdminRequiredError:
        await status_msg.edit_text(
            f"👮 *Admin required!*\n\nBot needs admin rights there.\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False
    except Exception as e:
        logger.error(f"Forward error: {e}")
        await status_msg.edit_text(
            f"```\n"
            f"╔═══════════════════════╗\n"
            f"║  💥  ERROR  💥        ║\n"
            f"╚═══════════════════════╝\n"
            f"```\n\n"
            f"❌ *Something broke:*\n`{str(e)[:200]}`\n\n"
            f"Try again or contact @Virajjaint\n{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False


async def _forward_single_telethon_msg(
    msg,
    dest_chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Forward a single Telethon message object to a destination chat."""
    try:
        bot = context.bot

        # ── Forward based on media type ──────────────────────
        if msg.media is None:
            # Plain text message
            text = msg.message or ""
            if text:
                await bot.send_message(
                    chat_id    = dest_chat_id,
                    text       = f"{text}\n{WATERMARK}",
                    parse_mode = ParseMode.MARKDOWN,
                )
            return True

        elif isinstance(msg.media, MessageMediaPhoto):
            # Photo
            photo_bytes = await telethon_client.download_media(msg, bytes)
            caption     = (msg.message or "") + WATERMARK
            await bot.send_photo(
                chat_id = dest_chat_id,
                photo   = photo_bytes,
                caption = caption,
                parse_mode = ParseMode.MARKDOWN,
            )
            return True

        elif isinstance(msg.media, MessageMediaDocument):
            # Document / Video / Audio / etc.
            doc         = msg.media.document
            file_bytes  = await telethon_client.download_media(msg, bytes)
            caption     = (msg.message or "") + WATERMARK
            mime_type   = doc.mime_type if doc else ""

            if "video" in mime_type:
                await bot.send_video(
                    chat_id    = dest_chat_id,
                    video      = file_bytes,
                    caption    = caption,
                    parse_mode = ParseMode.MARKDOWN,
                )
            elif "audio" in mime_type:
                await bot.send_audio(
                    chat_id    = dest_chat_id,
                    audio      = file_bytes,
                    caption    = caption,
                    parse_mode = ParseMode.MARKDOWN,
                )
            elif "image" in mime_type:
                await bot.send_photo(
                    chat_id    = dest_chat_id,
                    photo      = file_bytes,
                    caption    = caption,
                    parse_mode = ParseMode.MARKDOWN,
                )
            else:
                await bot.send_document(
                    chat_id    = dest_chat_id,
                    document   = file_bytes,
                    caption    = caption,
                    parse_mode = ParseMode.MARKDOWN,
                )
            return True

        elif isinstance(msg.media, MessageMediaWebPage):
            # Webpage preview — send as text
            text = msg.message or ""
            if text:
                await bot.send_message(
                    chat_id    = dest_chat_id,
                    text       = f"{text}\n{WATERMARK}",
                    parse_mode = ParseMode.MARKDOWN,
                    disable_web_page_preview = False,
                )
            return True

        else:
            # Unsupported — send text if available
            text = msg.message or ""
            if text:
                await bot.send_message(
                    chat_id    = dest_chat_id,
                    text       = f"{text}\n{WATERMARK}",
                    parse_mode = ParseMode.MARKDOWN,
                )
            return bool(text)

    except RetryAfter as e:
        logger.warning(f"RetryAfter: sleeping {e.retry_after}s")
        await asyncio.sleep(e.retry_after + 1)
        return await _forward_single_telethon_msg(msg, dest_chat_id, context)
    except FloodWaitError as e:
        logger.warning(f"Telethon FloodWait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds + 2)
        return await _forward_single_telethon_msg(msg, dest_chat_id, context)
    except Exception as e:
        logger.error(f"Forward single msg error: {e}")
        return False


def _get_msg_type(msg) -> str:
    """Return a human-readable message type."""
    if msg.media is None:
        return "TEXT 💬"
    elif isinstance(msg.media, MessageMediaPhoto):
        return "PHOTO 📸"
    elif isinstance(msg.media, MessageMediaDocument):
        doc  = msg.media.document
        mime = doc.mime_type if doc else ""
        if "video" in mime:
            return "VIDEO 📹"
        elif "audio" in mime:
            return "AUDIO 🎵"
        elif "image" in mime:
            return "IMAGE 🖼️"
        else:
            return "DOCUMENT 📄"
    elif isinstance(msg.media, MessageMediaWebPage):
        return "WEBPAGE 🌐"
    return "UNKNOWN ❓"


# ══════════════════════════════════════════════════════════════
#  🔘  CALLBACK QUERY HANDLERS
# ══════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    data = query.data

    log_user_action(user.id, "CALLBACK", f"data={data}")

    if data == "check_membership":
        is_member = await check_membership(context.bot, user.id)
        if is_member:
            await query.edit_message_text(
                f"```\n"
                f"╔═══════════════════════════╗\n"
                f"║  ✅  ACCESS GRANTED  ✅   ║\n"
                f"║   👻 GHOST MODE: ON 👻    ║\n"
                f"╚═══════════════════════════╝\n"
                f"```\n\n"
                f"🎉 *YO you're in king!!*\n\n"
                f"⚡ Type /start to boot the ghost system!\n"
                f"💀 Time to do some ghosting... 👻\n\n"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            denial = random.choice(ACCESS_DENIED_MSGS)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 JOIN NOW 🔥", url=REQUIRED_CHANNEL_URL)],
                [InlineKeyboardButton("✅ Check Again", callback_data="check_membership")],
            ])
            await query.edit_message_text(
                f"☠️ *Still not in bro...*\n\n"
                f"{denial}\n\n"
                f"👉 Join: {REQUIRED_CHANNEL_URL}\n\n"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )

    elif data == "cmd_forward":
        await query.edit_message_text(
            f"⚡ *Use the command:*\n\n"
            f"`/forward https://t.me/channel/123`\n\n"
            f"Or just type `/forward` and I'll ask for the link!\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "cmd_bulk":
        await query.edit_message_text(
            f"🔥 *Use the command:*\n\n"
            f"`/bulk`\n\n"
            f"I'll guide you step by step through bulk forwarding!\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "cmd_stats":
        stats = user_stats[user.id]
        await query.edit_message_text(
            f"📊 *Your Quick Stats:*\n\n"
            f"✅ Forwards : `{stats['forwards']}`\n"
            f"❌ Errors   : `{stats['errors']}`\n"
            f"💯 Success  : `{_success_rate(stats)}%`\n\n"
            f"Use `/stats` for full dashboard!\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "cmd_help":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="cmd_start")],
        ])
        await query.edit_message_text(
            f"📖 *Commands:*\n\n"
            f"⚡ `/forward` — Forward a message\n"
            f"🔥 `/bulk` — Bulk forward engine\n"
            f"📊 `/stats` — Your stats\n"
            f"💓 `/ping` — Bot health check\n"
            f"❓ `/help` — Full manual\n\n"
            f"Use `/help` for the full hacker-style guide!\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

    elif data == "cmd_start":
        # Reinvoke start
        is_member = await check_membership(context.bot, user.id)
        if not is_member:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 JOIN NOW 🔥", url=REQUIRED_CHANNEL_URL)],
                [InlineKeyboardButton("✅ Check Again", callback_data="check_membership")],
            ])
            await query.edit_message_text(
                f"💀 *Join the channel first bro*\n\n"
                f"{REQUIRED_CHANNEL_URL}\n\n{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚡ Forward", callback_data="cmd_forward"),
                    InlineKeyboardButton("🔥 Bulk", callback_data="cmd_bulk"),
                ],
                [
                    InlineKeyboardButton("📊 Stats", callback_data="cmd_stats"),
                    InlineKeyboardButton("📖 Help", callback_data="cmd_help"),
                ],
            ])
            await query.edit_message_text(
                f"👻 *Ghost System Online!*\n\n"
                f"What do you want to do, king? 💀\n\n"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )

    elif data == "cancel":
        await query.edit_message_text(
            f"❌ *Operation cancelled.*\n\n"
            f"Ghost went back to sleep 👻\n\n"
            f"Use /start to wake it up again!\n\n"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )


# ══════════════════════════════════════════════════════════════
#  ❌  CANCEL COMMAND
# ══════════════════════════════════════════════════════════════

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any active conversation."""
    user = update.effective_user
    log_user_action(user.id, "CANCEL")

    await update.message.reply_text(
        f"```\n"
        f"╔═══════════════════════════╗\n"
        f"║  ❌  OPERATION CANCELLED  ║\n"
        f"║   👻 Ghost went to sleep  ║\n"
        f"╚═══════════════════════════╝\n"
        f"```\n\n"
        f"💀 *Aight, operation aborted king*\n\n"
        f"Ghost mode: `STANDBY 💤`\n\n"
        f"Use /start to boot back up! 🚀\n\n"
        f"{WATERMARK}",
        parse_mode=ParseMode.MARKDOWN,
    )
    context.user_data.clear()
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════
#  🌀  UNKNOWN COMMAND HANDLER
# ══════════════════════════════════════════════════════════════

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    user = update.effective_user
    log_user_action(user.id, "UNKNOWN_CMD", f"text={update.message.text[:50]}")

    await update.message.reply_text(
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║  🤖  COMMAND NOT FOUND  🤖   ║\n"
        f"╚══════════════════════════════╝\n"
        f"```\n\n"
        f"💀 *Bro what was that command??* 😭\n\n"
        f"🔍 I don't recognize: `{update.message.text[:30]}`\n\n"
        f"📖 Use /help to see all valid commands\n"
        f"🏠 Or /start to boot the system\n\n"
        f"{WATERMARK}",
        parse_mode=ParseMode.MARKDOWN,
    )


# ══════════════════════════════════════════════════════════════
#  🌐  ERROR HANDLER
# ══════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    logger.error(f"Exception: {context.error}", exc_info=context.error)

    err = context.error

    if isinstance(err, RetryAfter):
        logger.warning(f"RetryAfter: {err.retry_after}s")
        await asyncio.sleep(err.retry_after + 1)

    elif isinstance(err, NetworkError):
        logger.warning("Network error, will retry on next update")

    elif isinstance(err, Forbidden):
        logger.warning("Bot was blocked by a user")

    elif isinstance(err, BadRequest):
        logger.error(f"BadRequest: {err}")

    else:
        logger.error(f"Unhandled error: {err}")

    # Try to notify user
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"```\n"
                f"╔═══════════════════════════╗\n"
                f"║  💥  SYSTEM ERROR  💥     ║\n"
                f"╚═══════════════════════════╝\n"
                f"```\n\n"
                f"😭 *Ghost crashed bro, not gonna lie*\n\n"
                f"Error: `{str(err)[:150]}`\n\n"
                f"🔄 Try again or contact @Virajjaint\n\n"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
#  🚀  APPLICATION SETUP & MAIN
# ══════════════════════════════════════════════════════════════

async def post_init(application: Application) -> None:
    """Initialize Telethon client after bot starts."""
    global telethon_client

    logger.info("Initializing Telethon client...")
    try:
        telethon_client = TelegramClient(
            session       = "ghost_session",
            api_id        = API_ID,
            api_hash      = API_HASH,
            connection_retries = 5,
            retry_delay   = 1,
        )
        await telethon_client.start(bot_token=BOT_TOKEN)
        logger.info("✅ Telethon client connected successfully!")
    except Exception as e:
        logger.error(f"❌ Telethon client failed to start: {e}")
        telethon_client = None


async def post_shutdown(application: Application) -> None:
    """Cleanup Telethon on shutdown."""
    global telethon_client
    if telethon_client and telethon_client.is_connected():
        await telethon_client.disconnect()
        logger.info("Telethon client disconnected.")


def build_application() -> Application:
    """Build and configure the PTB Application."""

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── ConversationHandler for /forward ────────────────────
    forward_conv = ConversationHandler(
        entry_points = [CommandHandler("forward", forward_command)],
        states       = {
            WAITING_FOR_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_forward_link)
            ],
        },
        fallbacks    = [CommandHandler("cancel", cancel_command)],
        allow_reentry= True,
    )

    # ── ConversationHandler for /bulk ────────────────────────
    bulk_conv = ConversationHandler(
        entry_points = [CommandHandler("bulk", bulk_command)],
        states       = {
            WAITING_FOR_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_receive_link)
            ],
            WAITING_FOR_RANGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_receive_range)
            ],
        },
        fallbacks    = [CommandHandler("cancel", cancel_command)],
        allow_reentry= True,
    )

    # ── Register handlers ────────────────────────────────────
    app.add_handler(CommandHandler("start",  start_command))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("stats",  stats_command))
    app.add_handler(CommandHandler("ping",   ping_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(forward_conv)
    app.add_handler(bulk_conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # ── Global error handler ─────────────────────────────────
    app.add_error_handler(error_handler)

    return app


def main() -> None:
    """Entry point."""
    logger.info("=" * 60)
    logger.info("  💀 GHOST FORWARDER BOT — STARTING UP 💀")
    logger.info("  ✨ Made by @Virajjaint ✨")
    logger.info("=" * 60)

    # Validate credentials
    if BOT_TOKEN == "7826065412:AAGD9uz_LNpMiWN3uPgyMWt2NPI1hUmNrU0":
        logger.critical("❌ BOT_TOKEN not set! Set the BOT_TOKEN environment variable.")
        return
    if API_ID == 36421171:
        logger.critical("❌ API_ID not set! Set the API_ID environment variable.")
        return
    if API_HASH == "069627fa19eb45a775ce87939f1768c5":
        logger.critical("❌ API_HASH not set! Set the API_HASH environment variable.")
        return

    logger.info(f"✅ Bot Token: {BOT_TOKEN[:8]}...")
    logger.info(f"✅ API ID   : {API_ID}")
    logger.info(f"✅ API Hash : {API_HASH[:8]}...")
    logger.info(f"✅ Channel  : @{REQUIRED_CHANNEL}")

    app = build_application()

    # Railway / production port handling
    PORT = int(os.environ.get("PORT", 0))
    if PORT:
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
        if WEBHOOK_URL:
            logger.info(f"🌐 Starting webhook on port {PORT}")
            app.run_webhook(
                listen       = "0.0.0.0",
                port         = PORT,
                webhook_url  = WEBHOOK_URL,
                drop_pending_updates = True,
            )
        else:
            logger.info(f"🔄 PORT set but no WEBHOOK_URL — falling back to polling")
            app.run_polling(
                drop_pending_updates = True,
                allowed_updates      = Update.ALL_TYPES,
            )
    else:
        logger.info("🔄 Starting in long-polling mode")
        app.run_polling(
            drop_pending_updates = True,
            allowed_updates      = Update.ALL_TYPES,
        )


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════
# 📦  REQUIREMENTS.TXT (save as requirements.txt)
# ══════════════════════════════════════════════════════════════
#
# python-telegram-bot==20.7
# telethon==1.34.0
# python-dotenv==1.0.0
# aiohttp==3.9.1
#
# ══════════════════════════════════════════════════════════════
# 🚂  RAILWAY DEPLOYMENT GUIDE
# ══════════════════════════════════════════════════════════════
#
# 1. Push this file to GitHub repo
# 2. Connect repo to Railway.app
# 3. Set Environment Variables in Railway dashboard:
#       BOT_TOKEN  = your_bot_token_here        ← from @BotFather
#       API_ID     = your_api_id_here           ← from my.telegram.org
#       API_HASH   = your_api_hash_here         ← from my.telegram.org
#
# 4. Railway auto-deploys on push ✅
#
# 🌐 For webhook mode (optional, better for production):
#       PORT        = 8443  (Railway sets this automatically)
#       WEBHOOK_URL = https://your-app.railway.app/
#
# ✨ Made by @Virajjaint ✨
# ══════════════════════════════════════════════════════════════