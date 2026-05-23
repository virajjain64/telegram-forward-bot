#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║     🔥 ULTRA FORWARD BOT - Production Ready 🔥          ║
║     ⚡ Built with python-telegram-bot v20+ async ⚡      ║
║     💀 Made by @Virajjaint 💀                           ║
╚══════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import random
import re
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union

from telegram import (
    Bot,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import (
    BadRequest,
    Forbidden,
    NetworkError,
    RetryAfter,
    TelegramError,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ═══════════════════════════════════════════════════════════
# 🔧 ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("069627fa19eb45a775ce87939f1768c5", "")
API_ID = os.environ.get("36421171", "")
API_HASH = os.environ.get("7826065412:AAGD9uz_LNpMiWN3uPgyMWt2NPI1hUmNrU0", "")
PORT = int(os.environ.get("PORT", 8080))

REQUIRED_CHANNEL = "@Restrictedcontentforward_bot27"
REQUIRED_CHANNEL_LINK = "https://t.me/Restrictedcontentforward_bot27"
WATERMARK = "\n\n✨ *Made by @Virajjaint*"

BATCH_SIZE = 100
BATCH_DELAY_MIN = 5
BATCH_DELAY_MAX = 10

# ═══════════════════════════════════════════════════════════
# 📊 LOGGING SETUP
# ═══════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("UltraForwardBot")

# Stats tracker
user_stats = defaultdict(lambda: {"forward_count": 0, "errors": 0, "last_seen": None})


def log_user_action(user_id: int, action: str, details: str = ""):
    user_stats[user_id]["last_seen"] = datetime.now().isoformat()
    logger.info(f"USER:{user_id} | ACTION:{action} | {details}")


def log_forward(user_id: int, count: int):
    user_stats[user_id]["forward_count"] += count
    logger.info(
        f"USER:{user_id} | FORWARDED:{count} | TOTAL:{user_stats[user_id]['forward_count']}"
    )


def log_error(user_id: int, error: str):
    user_stats[user_id]["errors"] += 1
    logger.error(f"USER:{user_id} | ERROR:{error}")


# ═══════════════════════════════════════════════════════════
# 🎨 UI STYLE CONSTANTS
# ═══════════════════════════════════════════════════════════

HACKER_FONT_MAP = {
    'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '$',
    'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '$',
}

LOADING_FRAMES = [
    "░░░░░░░░░░ 0%",
    "▓░░░░░░░░░ 10%",
    "▓▓░░░░░░░░ 20%",
    "▓▓▓░░░░░░░ 30%",
    "▓▓▓▓░░░░░░ 40%",
    "▓▓▓▓▓░░░░░ 50%",
    "▓▓▓▓▓▓░░░░ 60%",
    "▓▓▓▓▓▓▓░░░ 70%",
    "▓▓▓▓▓▓▓▓░░ 80%",
    "▓▓▓▓▓▓▓▓▓░ 90%",
    "▓▓▓▓▓▓▓▓▓▓ 100%",
]

ANIME_LOADING_STATES = [
    "⚡ Initializing neural uplink...",
    "💀 Hacking the mainframe...",
    "🔥 Bypassing firewall... jk lol",
    "🤖 Summoning digital demons...",
    "⚡ Overclocking processors...",
    "💀 Extracting quantum data...",
    "🔥 Almost there bestie...",
    "🎉 Finishing up...",
]

BLOCKED_MESSAGES = [
    "💀 *ACCESS DENIED* - Join the cult first bro",
    "☠️ *SYSTEM LOCKED* - We don't let randos in bestie",
    "🚫 *404: Permission Not Found* - You know what to do",
    "💀 *INTRUDER ALERT* - Join channel or skill issue lmaooo",
]


def get_progress_bar(current: int, total: int, width: int = 10) -> str:
    if total == 0:
        return "▓" * width + " 100%"
    percentage = min(current / total, 1.0)
    filled = int(width * percentage)
    bar = "▓" * filled + "░" * (width - filled)
    return f"{bar} {int(percentage * 100)}%"


def hacker_text(text: str) -> str:
    return "".join(HACKER_FONT_MAP.get(c, c) for c in text)


# ═══════════════════════════════════════════════════════════
# 🔒 MEMBERSHIP CHECK SYSTEM
# ═══════════════════════════════════════════════════════════

async def check_membership(bot: Bot, user_id: int) -> bool:
    """Check if user has joined the required channel."""
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]
    except Forbidden:
        logger.warning(f"Bot not in channel {REQUIRED_CHANNEL} or no admin rights")
        return False
    except BadRequest as e:
        logger.error(f"BadRequest checking membership: {e}")
        return False
    except TelegramError as e:
        logger.error(f"TelegramError checking membership: {e}")
        return False


async def require_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Gate function - returns True if user can proceed."""
    user = update.effective_user
    if not user:
        return False

    is_member = await check_membership(context.bot, user.id)

    if not is_member:
        blocked_msg = random.choice(BLOCKED_MESSAGES)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 JOIN THE CULT 🔥", url=REQUIRED_CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I Joined, Check Again", callback_data="check_membership")],
        ])

        deny_text = (
            f"{blocked_msg}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎭 *Bro really thought they could access this* 💀\n\n"
            f"📢 Step 1: Join → {REQUIRED_CHANNEL_LINK}\n"
            f"✅ Step 2: Come back and press check\n"
            f"⚡ Step 3: Enjoy the power bestie\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
            f"{WATERMARK}"
        )

        if update.callback_query:
            await update.callback_query.answer("💀 Not a member yet!", show_alert=True)
            await update.callback_query.edit_message_text(
                deny_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
        elif update.message:
            await update.message.reply_text(
                deny_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )

        log_user_action(user.id, "BLOCKED", "Not a channel member")
        return False

    return True


# ═══════════════════════════════════════════════════════════
# 🎬 ANIMATION SYSTEM
# ═══════════════════════════════════════════════════════════

async def animate_loading(message: Message, title: str = "Loading") -> None:
    """Anime-style loading animation on a single message."""
    try:
        for i, frame in enumerate(LOADING_FRAMES):
            state = ANIME_LOADING_STATES[min(i, len(ANIME_LOADING_STATES) - 1)]
            text = (
                f"```\n"
                f"╔══ {title.upper()} ══╗\n"
                f"║ {frame}\n"
                f"║ {state}\n"
                f"╚{'═' * (len(title) + 8)}╝\n"
                f"```"
            )
            await message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(0.3)
    except BadRequest:
        pass
    except TelegramError as e:
        logger.debug(f"Animation error (non-critical): {e}")


async def update_progress_message(
    message: Message,
    current: int,
    total: int,
    status: str = "Forwarding",
    extra_info: str = "",
) -> None:
    """Update progress message with anime-style UI."""
    try:
        bar = get_progress_bar(current, total)
        eta_state = random.choice([
            "⚡ Speed: MAXIMUM OVERDRIVE",
            "💀 Mode: ABSOLUTE DEMON",
            "🔥 Status: FULLY COOKED",
            "🤖 CPU: MELTING (jk)",
        ])

        text = (
            f"```\n"
            f"╔══════ FORWARD ENGINE ══════╗\n"
            f"║ 📊 {bar}\n"
            f"║ 📦 Messages: {current}/{total}\n"
            f"║ ⚡ Status: {status}\n"
            f"║ {eta_state}\n"
        )

        if extra_info:
            text += f"║ ℹ️  {extra_info}\n"

        text += (
            f"╚═══════════════════════════╝\n"
            f"```"
            f"{WATERMARK}"
        )

        await message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except BadRequest:
        pass
    except TelegramError as e:
        logger.debug(f"Progress update error (non-critical): {e}")


# ═══════════════════════════════════════════════════════════
# 🔗 LINK PARSER
# ═══════════════════════════════════════════════════════════

def parse_telegram_link(link: str) -> Optional[dict]:
    """
    Parse Telegram message links.
    Supports:
    - https://t.me/channel/123
    - https://t.me/c/123456789/123
    - https://t.me/channel/123?single
    Returns dict with chat_id/username and message_id(s)
    """
    link = link.strip()

    # Pattern: https://t.me/username/message_id
    public_pattern = re.compile(
        r'https?://t\.me/([a-zA-Z][a-zA-Z0-9_]{3,})/(\d+)(?:\?.*)?$'
    )

    # Pattern: https://t.me/c/chat_id/message_id (private supergroup)
    private_pattern = re.compile(
        r'https?://t\.me/c/(\d+)/(\d+)(?:\?.*)?$'
    )

    # Pattern with range: sometimes users pass start-end
    range_public = re.compile(
        r'https?://t\.me/([a-zA-Z][a-zA-Z0-9_]{3,})/(\d+)(?:\?.*)?.*?(\d+)?$'
    )

    match_private = private_pattern.match(link)
    if match_private:
        chat_id = int(f"-100{match_private.group(1)}")
        message_id = int(match_private.group(2))
        return {
            "type": "private",
            "chat_id": chat_id,
            "message_id": message_id,
            "username": None,
        }

    match_public = public_pattern.match(link)
    if match_public:
        username = match_public.group(1)
        message_id = int(match_public.group(2))
        return {
            "type": "public",
            "chat_id": None,
            "message_id": message_id,
            "username": f"@{username}",
        }

    return None


def parse_range_links(text: str) -> Optional[dict]:
    """
    Parse range forward request like:
    https://t.me/channel/100 to https://t.me/channel/200
    OR
    https://t.me/channel/100 200  (start message to end message id)
    """
    # Try "link1 to link2" pattern
    parts = re.split(r'\s+to\s+|\s+TO\s+', text.strip())

    if len(parts) == 2:
        start_info = parse_telegram_link(parts[0].strip())
        end_info = parse_telegram_link(parts[1].strip())

        if start_info and end_info:
            return {
                "start": start_info,
                "end": end_info,
                "is_range": True,
            }

    # Try "link end_id" pattern
    parts = text.strip().split()
    if len(parts) == 2:
        link_info = parse_telegram_link(parts[0])
        try:
            end_id = int(parts[1])
            if link_info:
                return {
                    "start": link_info,
                    "end_id": end_id,
                    "is_range": True,
                }
        except ValueError:
            pass

    # Single link
    single = parse_telegram_link(text.strip())
    if single:
        return {"start": single, "is_range": False}

    return None


# ═══════════════════════════════════════════════════════════
# 📨 FORWARD ENGINE
# ═══════════════════════════════════════════════════════════

async def safe_forward_message(
    bot: Bot,
    from_chat_id: Union[int, str],
    to_chat_id: int,
    message_id: int,
    retries: int = 3,
) -> bool:
    """Forward a single message with retry logic."""
    for attempt in range(retries):
        try:
            await bot.forward_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            return True

        except RetryAfter as e:
            wait_time = e.retry_after + 1
            logger.warning(f"FloodWait: sleeping {wait_time}s")
            await asyncio.sleep(wait_time)

        except BadRequest as e:
            error_msg = str(e).lower()
            if "message to forward not found" in error_msg:
                logger.debug(f"Message {message_id} not found in {from_chat_id}")
                return False
            elif "chat not found" in error_msg:
                logger.error(f"Chat {from_chat_id} not found")
                return False
            elif "message id invalid" in error_msg:
                logger.debug(f"Invalid message ID: {message_id}")
                return False
            else:
                logger.error(f"BadRequest forwarding msg {message_id}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)

        except Forbidden as e:
            logger.error(f"Forbidden: {e}")
            return False

        except NetworkError as e:
            logger.warning(f"NetworkError attempt {attempt + 1}: {e}")
            await asyncio.sleep(3)

        except TelegramError as e:
            logger.error(f"TelegramError forwarding msg {message_id}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)

    return False


async def bulk_forward_engine(
    bot: Bot,
    from_chat_id: Union[int, str],
    to_chat_id: int,
    start_id: int,
    end_id: int,
    progress_message: Message,
    user_id: int,
) -> dict:
    """
    Core bulk forward engine with:
    - Batch processing (100 msgs per batch)
    - Rate limiting
    - Progress updates
    - Error tracking
    """
    total = end_id - start_id + 1
    forwarded = 0
    failed = 0
    skipped = 0

    logger.info(f"Starting bulk forward: {from_chat_id} msgs {start_id}-{end_id} → {to_chat_id}")

    message_ids = list(range(start_id, end_id + 1))

    for batch_num, batch_start in enumerate(range(0, total, BATCH_SIZE)):
        batch = message_ids[batch_start: batch_start + BATCH_SIZE]
        batch_forwarded = 0
        batch_failed = 0

        for msg_id in batch:
            success = await safe_forward_message(
                bot=bot,
                from_chat_id=from_chat_id,
                to_chat_id=to_chat_id,
                message_id=msg_id,
            )

            if success:
                forwarded += 1
                batch_forwarded += 1
            else:
                failed += 1
                batch_failed += 1

            # Update progress every 10 messages
            if (forwarded + failed) % 10 == 0 or (forwarded + failed) == total:
                await update_progress_message(
                    message=progress_message,
                    current=forwarded + failed,
                    total=total,
                    status="FORWARDING",
                    extra_info=f"✅{forwarded} ❌{failed}",
                )

            # Small delay between messages to avoid flood
            await asyncio.sleep(0.1)

        # After each batch of 100
        log_forward(user_id, batch_forwarded)

        if batch_start + BATCH_SIZE < total:
            delay = random.uniform(BATCH_DELAY_MIN, BATCH_DELAY_MAX)
            logger.info(f"Batch {batch_num + 1} done. Waiting {delay:.1f}s before next batch.")

            await update_progress_message(
                message=progress_message,
                current=forwarded + failed,
                total=total,
                status=f"COOLDOWN {delay:.0f}s",
                extra_info=f"Batch {batch_num + 1} done | Next batch loading...",
            )

            await asyncio.sleep(delay)

    return {
        "total": total,
        "forwarded": forwarded,
        "failed": failed,
        "skipped": skipped,
    }


# ═══════════════════════════════════════════════════════════
# 🤖 BOT COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Animated start command with Gen Z vibes."""
    user = update.effective_user
    log_user_action(user.id, "START")

    # Send initial loading message
    loading_msg = await update.message.reply_text(
        "```\n⚡ BOOTING UP... ⚡\n```",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Animate loading
    await animate_loading(loading_msg, "INITIALIZING")

    # Check membership
    is_member = await check_membership(context.bot, user.id)

    if not is_member:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 JOIN THE CULT 🔥", url=REQUIRED_CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I Joined, Check Again", callback_data="check_membership")],
        ])

        blocked_msg = random.choice(BLOCKED_MESSAGES)
        await loading_msg.edit_text(
            f"{blocked_msg}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎭 *Bro really thought access was free* 💀\n\n"
            f"📢 Join → {REQUIRED_CHANNEL_LINK}\n"
            f"Then press the check button below bestie\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
            f"{WATERMARK}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Welcome animation frames
    frames = [
        "```\n██╗  ██╗███████╗██╗     ██╗      ██████╗ \n██║  ██║██╔════╝██║     ██║     ██╔═══██╗\n███████║█████╗  ██║     ██║     ██║   ██║\n██╔══██║██╔══╝  ██║     ██║     ██║   ██║\n██║  ██║███████╗███████╗███████╗╚██████╔╝\n```",
        "```\n⚡ ULTRA FORWARD BOT ⚡\n💀 By @Virajjaint 💀\n🔥 NO CAP JUST VIBES 🔥\n```",
        "```\n> Loading features...\n> Connecting to matrix...\n> Unlocking powers...\n> DONE ✓\n```",
    ]

    for frame in frames:
        await loading_msg.edit_text(frame, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(0.8)

    # Final welcome message
    welcome_text = (
        f"⚡ *W3LC0M3 T0 ULT R4 F0RW4RD B0T* ⚡\n\n"
        f"Sup `{user.first_name}` 👋🏻 you're in the right place fr\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *WHAT I CAN DO:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ `/forward <link>` - Forward single message\n"
        f"💀 `/bulk <link> to <link>` - Bulk forward range\n"
        f"📊 `/stats` - Your forward statistics\n"
        f"🤖 `/help` - Full command guide\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *FEATURES:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Photos, Videos, Docs, Text\n"
        f"✅ Bulk forward 100-1000+ messages\n"
        f"✅ Smart rate limiting (no ban risk)\n"
        f"✅ Anime-style progress bar UI\n"
        f"✅ Auto retry on errors\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *RULES (read or cry):*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• Bot must have access to source channel\n"
        f"• Only works on public/accessible channels\n"
        f"• No bypassing Telegram restrictions fr fr\n\n"
        f"{WATERMARK}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats"),
        ],
        [InlineKeyboardButton("🔥 Source Channel", url=REQUIRED_CHANNEL_LINK)],
    ])

    await loading_msg.edit_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command with full guide."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "HELP")

    help_text = (
        f"🤖 *ULTRA FORWARD BOT - MANUAL* 🤖\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *COMMANDS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"1️⃣ *Forward Single Message:*\n"
        f"```\n/forward https://t.me/channel/123\n```\n\n"
        f"2️⃣ *Bulk Forward (Range):*\n"
        f"```\n/bulk https://t.me/channel/100 to https://t.me/channel/200\n```\n\n"
        f"3️⃣ *Bulk Forward (Short form):*\n"
        f"```\n/bulk https://t.me/channel/100 200\n```\n"
        f"_(means forward msg 100 to 200)_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *SUPPORTED LINK FORMATS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ `https://t.me/username/123` (public)\n"
        f"✅ `https://t.me/c/1234567/123` (private*)\n\n"
        f"*Bot must be in private channel\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *HOW BULK WORKS:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• Forwards 100 msgs per batch\n"
        f"• Waits 5-10s between batches\n"
        f"• Shows live progress bar\n"
        f"• Auto-handles flood waits\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *IMPORTANT NOTES:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💀 Bot cannot bypass Telegram restrictions\n"
        f"💀 Messages in protected channels = no access\n"
        f"💀 Bot must have access to forward from source\n"
        f"{WATERMARK}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            help_text, parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user stats."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "STATS")

    stats = user_stats[user.id]
    total_users = len(user_stats)

    stats_text = (
        f"📊 *YOUR STATS BESTIE*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User ID: `{user.id}`\n"
        f"📨 Messages Forwarded: `{stats['forward_count']}`\n"
        f"❌ Errors Encountered: `{stats['errors']}`\n"
        f"🕐 Last Seen: `{stats['last_seen'] or 'Now'}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 Total Bot Users: `{total_users}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'🔥 You\'re a GOAT!' if stats['forward_count'] > 100 else '⚡ Keep going bestie!'}"
        f"{WATERMARK}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            stats_text, parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


async def forward_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward a single message from a Telegram link."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "FORWARD_CMD")

    if not context.args:
        await update.message.reply_text(
            f"⚡ *Usage:*\n"
            f"```\n/forward https://t.me/channel/123\n```\n\n"
            f"💀 Give me a link bestie, I can't read minds (yet)"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    link = " ".join(context.args)
    parsed = parse_telegram_link(link)

    if not parsed:
        await update.message.reply_text(
            f"❌ *Invalid Link Format*\n\n"
            f"Supported formats:\n"
            f"• `https://t.me/username/123`\n"
            f"• `https://t.me/c/chatid/123`\n\n"
            f"💀 That link looking sus no cap"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Loading message
    status_msg = await update.message.reply_text(
        "```\n⚡ ACTIVATING FORWARD PROTOCOL...\n```",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        chat_id = parsed["chat_id"] or parsed["username"]
        message_id = parsed["message_id"]

        await status_msg.edit_text(
            f"```\n💀 FORWARDING MSG #{message_id}...\n```",
            parse_mode=ParseMode.MARKDOWN,
        )

        success = await safe_forward_message(
            bot=context.bot,
            from_chat_id=chat_id,
            to_chat_id=update.effective_chat.id,
            message_id=message_id,
        )

        if success:
            log_forward(user.id, 1)
            await status_msg.edit_text(
                f"✅ *Message Forwarded Successfully!*\n\n"
                f"🔗 Source: `{link}`\n"
                f"📨 Message ID: `{message_id}`\n\n"
                f"🔥 Slay! That's how we do it bestie"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            log_error(user.id, f"Failed to forward {link}")
            await status_msg.edit_text(
                f"❌ *Forward Failed*\n\n"
                f"Possible reasons:\n"
                f"• Message doesn't exist\n"
                f"• Bot has no access to source\n"
                f"• Message was deleted\n"
                f"• Private channel (bot not member)\n\n"
                f"💀 It's giving 'no access' vibes ngl"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        log_error(user.id, str(e))
        logger.error(f"Forward error for {user.id}: {traceback.format_exc()}")
        await status_msg.edit_text(
            f"💥 *Unexpected Error*\n\n"
            f"```\n{str(e)[:200]}\n```\n\n"
            f"💀 The matrix glitched. Try again bestie."
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )


async def bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bulk forward messages from a range of Telegram links."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    log_user_action(user.id, "BULK_CMD")

    if not context.args:
        await update.message.reply_text(
            f"⚡ *Usage (pick your style):*\n\n"
            f"1️⃣ Range with two links:\n"
            f"```\n/bulk https://t.me/ch/100 to https://t.me/ch/200\n```\n\n"
            f"2️⃣ Range with end ID:\n"
            f"```\n/bulk https://t.me/ch/100 200\n```\n\n"
            f"💀 Can't bulk nothing bestie, give me the goods"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    full_text = " ".join(context.args)
    parsed = parse_range_links(full_text)

    if not parsed:
        await update.message.reply_text(
            f"❌ *Couldn't parse your links*\n\n"
            f"Make sure format is correct:\n"
            f"```\n/bulk https://t.me/ch/100 to https://t.me/ch/200\n```\n\n"
            f"💀 That input looking real cooked fr"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    start_info = parsed["start"]

    if parsed.get("is_range"):
        if "end" in parsed:
            end_info = parsed["end"]

            # Validate same channel
            start_chat = start_info.get("chat_id") or start_info.get("username")
            end_chat = end_info.get("chat_id") or end_info.get("username")

            if str(start_chat) != str(end_chat):
                await update.message.reply_text(
                    f"❌ *Both links must be from same channel!*\n\n"
                    f"💀 You can't forward from two different places bestie"
                    f"{WATERMARK}",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            start_id = start_info["message_id"]
            end_id = end_info["message_id"]

        elif "end_id" in parsed:
            start_id = start_info["message_id"]
            end_id = parsed["end_id"]
        else:
            start_id = end_id = start_info["message_id"]

    else:
        start_id = end_id = start_info["message_id"]

    if start_id > end_id:
        start_id, end_id = end_id, start_id

    total = end_id - start_id + 1

    if total > 1000:
        await update.message.reply_text(
            f"⚠️ *That's {total} messages!*\n\n"
            f"Max allowed: 1000 messages per bulk request\n"
            f"Split into smaller chunks bestie\n\n"
            f"💀 Even I have limits ngl"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    chat_id = start_info.get("chat_id") or start_info.get("username")

    # Confirm message
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ GO FOR IT",
                callback_data=f"confirm_bulk:{chat_id}:{start_id}:{end_id}:{user.id}",
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_bulk"),
        ]
    ])

    await update.message.reply_text(
        f"⚡ *BULK FORWARD CONFIRMATION*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Source: `{chat_id}`\n"
        f"🔢 From Message: `#{start_id}`\n"
        f"🔢 To Message: `#{end_id}`\n"
        f"📊 Total Messages: `{total}`\n"
        f"⏱️ Est. Time: `{total * 0.1 + (total // 100) * 7:.0f}s+`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔥 Ready to cook? Press GO\n"
        f"💀 No cap this might take a minute"
        f"{WATERMARK}",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    user = update.effective_user
    data = query.data

    if data == "check_membership":
        is_member = await check_membership(context.bot, user.id)
        if is_member:
            await query.answer("✅ Membership confirmed! Welcome to the cult!", show_alert=True)
            # Trigger start flow
            await query.message.delete()
            # Create fake update for start
            await start_command(update, context)
        else:
            await query.answer(
                "💀 Still not a member bro. Join first then check!",
                show_alert=True,
            )

    elif data == "help":
        await help_command(update, context)

    elif data == "stats":
        await stats_command(update, context)

    elif data == "cancel_bulk":
        await query.answer("❌ Cancelled!")
        await query.edit_message_text(
            f"❌ *Bulk forward cancelled*\n\n"
            f"💀 Changed your mind? No worries bestie"
            f"{WATERMARK}",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data.startswith("confirm_bulk:"):
        await query.answer("⚡ Starting bulk forward!")

        try:
            _, from_chat, start_id, end_id, req_user_id = data.split(":")
            start_id = int(start_id)
            end_id = int(end_id)
            req_user_id = int(req_user_id)

            # Security check
            if user.id != req_user_id:
                await query.answer("💀 This isn't your bulk request!", show_alert=True)
                return

            total = end_id - start_id + 1

            # Update message to progress tracker
            await query.edit_message_text(
                f"```\n"
                f"╔══════ FORWARD ENGINE ══════╗\n"
                f"║ {get_progress_bar(0, total)}\n"
                f"║ 📦 Messages: 0/{total}\n"
                f"║ ⚡ Status: STARTING\n"
                f"║ 🔥 Mode: ULTRA BULK\n"
                f"╚═══════════════════════════╝\n"
                f"```"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )

            # Try to parse from_chat back
            if from_chat.startswith("-100"):
                chat_identifier = int(from_chat)
            else:
                chat_identifier = from_chat

            # Run bulk forward
            result = await bulk_forward_engine(
                bot=context.bot,
                from_chat_id=chat_identifier,
                to_chat_id=update.effective_chat.id,
                start_id=start_id,
                end_id=end_id,
                progress_message=query.message,
                user_id=user.id,
            )

            # Final result
            success_rate = (
                (result["forwarded"] / result["total"] * 100)
                if result["total"] > 0
                else 0
            )

            final_text = (
                f"🎉 *BULK FORWARD COMPLETE!*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 {get_progress_bar(result['forwarded'], result['total'])}\n\n"
                f"✅ Successfully Forwarded: `{result['forwarded']}`\n"
                f"❌ Failed/Skipped: `{result['failed']}`\n"
                f"📦 Total Attempted: `{result['total']}`\n"
                f"📈 Success Rate: `{success_rate:.1f}%`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{'🔥 GOATED performance no cap!' if success_rate > 80 else '💀 Some failed but we move bestie'}"
                f"{WATERMARK}"
            )

            await query.edit_message_text(final_text, parse_mode=ParseMode.MARKDOWN)
            log_user_action(user.id, "BULK_COMPLETE", f"Forwarded:{result['forwarded']}/{result['total']}")

        except Exception as e:
            log_error(user.id, str(e))
            logger.error(f"Bulk callback error: {traceback.format_exc()}")
            await query.edit_message_text(
                f"💥 *Bulk Forward Error*\n\n"
                f"```\n{str(e)[:300]}\n```\n\n"
                f"💀 Something cooked wrong. Try again bestie."
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    if not await require_membership(update, context):
        return

    await update.message.reply_text(
        f"💀 *Unknown Command*\n\n"
        f"Use /help to see all commands bestie\n\n"
        f"🤖 Valid commands:\n"
        f"• `/start` - Start the bot\n"
        f"• `/forward <link>` - Forward message\n"
        f"• `/bulk <range>` - Bulk forward\n"
        f"• `/stats` - Your stats\n"
        f"• `/help` - This guide"
        f"{WATERMARK}",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_plain_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages - detect if they contain links."""
    if not await require_membership(update, context):
        return

    user = update.effective_user
    text = update.message.text or ""

    # Check if it's a telegram link
    if "t.me/" in text:
        parsed = parse_range_links(text)
        if parsed:
            await update.message.reply_text(
                f"🔗 *Detected Telegram Link!*\n\n"
                f"Use commands to forward:\n"
                f"• `/forward {text}` - Single message\n"
                f"• `/bulk {text}` - Bulk forward\n\n"
                f"⚡ Just add the command prefix bestie!"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    # Generic response
    responses = [
        f"🤖 I'm a forward bot bestie, not a chatbot lol\nUse /help to see what I can do!",
        f"💀 I speak in commands, not vibes\nTry /forward or /bulk",
        f"⚡ Wrong interface fam\nCheck /help for the real commands",
    ]

    await update.message.reply_text(
        random.choice(responses) + WATERMARK,
        parse_mode=ParseMode.MARKDOWN,
    )


# ═══════════════════════════════════════════════════════════
# 🚨 ERROR HANDLER
# ═══════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    error = context.error

    if isinstance(error, RetryAfter):
        wait_time = error.retry_after
        logger.warning(f"Global FloodWait: {wait_time}s")
        await asyncio.sleep(wait_time)

    elif isinstance(error, NetworkError):
        logger.error(f"NetworkError: {error}")

    elif isinstance(error, Forbidden):
        logger.error(f"Forbidden: {error}")

    elif isinstance(error, BadRequest):
        logger.error(f"BadRequest: {error}")

    else:
        logger.error(f"Unhandled error: {error}")
        logger.error(traceback.format_exc())

    # Try to notify user if possible
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"💥 *System Error*\n\n"
                f"Something crashed in the matrix bestie\n"
                f"Error: `{str(error)[:100]}`\n\n"
                f"💀 Try again or contact @Virajjaint"
                f"{WATERMARK}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# 🚀 APPLICATION BUILDER & MAIN
# ═══════════════════════════════════════════════════════════

def build_application() -> Application:
    """Build and configure the bot application."""

    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN not set! Add it to environment variables.")
        sys.exit(1)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("forward", forward_command))
    app.add_handler(CommandHandler("bulk", bulk_command))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    # Message handler for plain text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plain_message))

    # Unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Error handler
    app.add_error_handler(error_handler)

    return app


async def post_init(application: Application) -> None:
    """Actions to perform after bot initialization."""
    bot_info = await application.bot.get_me()
    logger.info(f"╔══════════════════════════════════════╗")
    logger.info(f"║  🤖 Bot: @{bot_info.username:<27}║")
    logger.info(f"║  ⚡ Status: ONLINE & READY            ║")
    logger.info(f"║  💀 Made by: @Virajjaint              ║")
    logger.info(f"╚══════════════════════════════════════╝")


def main() -> None:
    """Main entry point."""
    logger.info("🚀 Starting Ultra Forward Bot...")
    logger.info(f"📡 Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")

    app = build_application()
    app.post_init = post_init

    # Railway / production deployment
    webhook_url = os.environ.get("WEBHOOK_URL", "")

    if webhook_url:
        # Webhook mode (production/Railway)
        logger.info(f"🌐 Starting in Webhook mode on port {PORT}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}",
            drop_pending_updates=True,
        )
    else:
        # Polling mode (local dev)
        logger.info("🔄 Starting in Polling mode (local)")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════
# 📋 REQUIREMENTS (save as requirements.txt)
# ═══════════════════════════════════════════════════════════
# python-telegram-bot[job-queue]==20.7
# python-telegram-bot==20.7
# httpx==0.25.2
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# 🚂 RAILWAY DEPLOYMENT GUIDE
# ═══════════════════════════════════════════════════════════
#
# 1. Create a Railway project
# 2. Connect your GitHub repo or upload this file
#
# 3. Set Environment Variables in Railway:
#    BOT_TOKEN=7826065412:AAGD9uz_LNpMiWN3uPgyMWt2NPI1hUmNrU0
#    API_ID=36421171 (optional, for future Telethon features)
#    API_HASH=069627fa19eb45a775ce87939f1768c5 (optional)
#    WEBHOOK_URL=https://your-app.railway.app (for webhook mode)
#
# 4. requirements.txt content:
#    python-telegram-bot==20.7
#    httpx==0.25.2
#
# 5. Procfile (optional):
#    worker: python bot.py
#
# 6. Railway auto-assigns PORT env variable ✓
# ═══════════════════════════════════════════════════════════