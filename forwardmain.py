#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          💀 GHOST FORWARDER BOT v2.0 💀                      ║
║          Built by: Senior Dev | Production Grade             ║
║          Style: Cyberpunk / Gen-Z / Hacker                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import asyncio
import logging
import html
import time
import random
from datetime import datetime
from typing import Optional

# ─── Telegram Bot (PTB v20+) ───────────────────────────────────
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMember,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, Forbidden, BadRequest

# ─── Telethon (MTProto for forwarding) ────────────────────────
from telethon import TelegramClient, errors
from telethon.tl.types import (
    InputPeerChannel,
    MessageMediaPhoto,
    MessageMediaDocument,
)
from telethon.errors import (
    FloodWaitError,
    ChatAdminRequiredError,
    ChannelPrivateError,
    UsernameNotOccupiedError,
)

# ─── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GhostForwarder")
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 ENVIRONMENT VARIABLES (NO HARDCODED SECRETS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
REQUIRED_CHANNEL = os.environ.get("REQUIRED_CHANNEL", "@your_channel")
ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

# ─── Validate env vars ─────────────────────────────────────────
if not BOT_TOKEN:
    raise EnvironmentError("❌ BOT_TOKEN not set in environment variables!")
if not API_ID or not API_HASH:
    raise EnvironmentError("❌ API_ID or API_HASH not set in environment variables!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 BOT STATS (In-Memory)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bot_stats = {
    "start_time": datetime.now(),
    "total_forwarded": 0,
    "total_users": set(),
    "total_sessions": 0,
    "errors_caught": 0,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎭 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(
    WAITING_SOURCE,
    WAITING_TARGET,
    WAITING_LIMIT,
    CONFIRM_FORWARD,
) = range(4)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 UI TEMPLATES - CYBERPUNK STYLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOOT_FRAMES = [
    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░░]  5%   ║
║  Initializing core...        ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓░░░░░░░░░░░░░]  25%  ║
║  Loading modules... ⚡       ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓░░░░░░░░░]  50%  ║
║  Connecting to matrix... 🔥  ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓▓▓▓▓░░░░░]  75%  ║
║  Bypassing firewall... 🤖    ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  100% ║
║  ✅ SYSTEM ONLINE            ║
╚══════════════════════════════╝
</pre>""",
]

DENIED_FRAMES = [
    "💀 <b>SCANNING ACCESS CREDENTIALS...</b>",
    "🔍 <b>CHECKING MEMBERSHIP STATUS...</b>",
    "⚠️ <b>INSUFFICIENT CLEARANCE LEVEL...</b>",
    "☠️ <b>ACCESS DENIED — UNAUTHORIZED!</b>",
]

MAIN_MENU_TEXT = """
<pre>
╔══════════════════════════════════╗
║   💀 GHOST FORWARDER v2.0 💀    ║
╠══════════════════════════════════╣
║  Status  : 🟢 ONLINE            ║
║  Engine  : ⚡ TELETHON MTProto  ║
║  Version : 2.0.0-cyberpunk      ║
╠══════════════════════════════════╣
║  💥 COMMANDS                    ║
║  /forward  → Start forwarding   ║
║  /stats    → Bot statistics     ║
║  /ping     → Check latency      ║
║  /help     → Full help guide    ║
╚══════════════════════════════════╝
</pre>
🔥 <b>yo bestie, pick ur weapon below 👇</b>
"""

HELP_TEXT = """
<pre>
╔══════════════════════════════════════╗
║      📖 GHOST FORWARDER HELP        ║
╠══════════════════════════════════════╣
║  /start    → Boot sequence + menu   ║
║  /forward  → Launch forward engine  ║
║  /stats    → View bot stats         ║
║  /ping     → Latency check          ║
║  /cancel   → Cancel any operation   ║
╠══════════════════════════════════════╣
║  📦 SUPPORTED MEDIA                 ║
║  ✅ Text messages                   ║
║  ✅ Photos                          ║
║  ✅ Videos                          ║
║  ✅ Documents                       ║
║  ✅ Audio files                     ║
╠══════════════════════════════════════╣
║  ⚙️ HOW IT WORKS                    ║
║  1. Enter SOURCE channel            ║
║  2. Enter TARGET channel            ║
║  3. Set message limit               ║
║  4. Confirm & LAUNCH 🚀             ║
╠══════════════════════════════════════╣
║  💡 TIPS                            ║
║  • Use @username or chat ID         ║
║  • Bot needs admin in target        ║
║  • FloodWait is auto-handled        ║
╚══════════════════════════════════════╝
</pre>
💀 <i>stay ghost, stay legendary fr fr no cap 💀</i>
"""


def make_progress_bar(current: int, total: int, width: int = 16) -> str:
    """Generate animated progress bar."""
    if total == 0:
        return "░" * width
    filled = int((current / total) * width)
    bar = "▓" * filled + "░" * (width - filled)
    pct = int((current / total) * 100)
    return f"[{bar}] {pct}%"


def get_uptime() -> str:
    """Calculate bot uptime."""
    delta = datetime.now() - bot_stats["start_time"]
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"


def random_hacker_quote() -> str:
    """Return a random Gen-Z hacker quote."""
    quotes = [
        "no cap this bot goes crazy hard 💀",
        "slay mode: ACTIVATED fr fr 🔥",
        "we do be ghosting the matrix tho ⚡",
        "bussin bussin on god 🫶🏻",
        "main character energy activated 😂",
        "lowkey slapping rn no cap 💀",
        "it's giving hacker vibes fr 🤖",
        "not me forwarding messages at 3am 💀",
    ]
    return random.choice(quotes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 MEMBERSHIP CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of the required channel."""
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        ]
    except (TelegramError, Exception) as e:
        logger.warning(f"Membership check failed for {user_id}: {e}")
        # If we can't check, allow access (graceful degradation)
        return True


async def show_access_denied(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show animated access denied screen."""
    query = update.callback_query
    msg = update.message

    # Send initial denied animation
    if query:
        target = query.message
        edit_fn = query.message.edit_text
    else:
        target = await msg.reply_text("💀")
        edit_fn = target.edit_text

    for frame in DENIED_FRAMES:
        try:
            await edit_fn(
                frame,
                parse_mode=ParseMode.HTML,
            )
            await asyncio.sleep(0.7)
        except Exception:
            pass

    # Final denied screen with join button
    denied_text = """
<pre>
╔══════════════════════════════════╗
║   ☠️  ACCESS DENIED ☠️           ║
╠══════════════════════════════════╣
║  ERROR CODE : 403_FORBIDDEN      ║
║  STATUS     : NOT A MEMBER       ║
║  CLEARANCE  : INSUFFICIENT       ║
╠══════════════════════════════════╣
║  🔐 JOIN REQUIRED CHANNEL        ║
║  to unlock full ghost mode       ║
╚══════════════════════════════════╝
</pre>
💀 <b>bestie u gotta join first lmao 😂</b>
<i>click the button below then verify 👇</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔗 JOIN CHANNEL ⚡",
            url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
        )],
        [InlineKeyboardButton(
            "✅ VERIFY MEMBERSHIP 🔍",
            callback_data="verify_membership"
        )],
    ])

    try:
        await edit_fn(
            denied_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Error showing denied screen: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 COMMAND HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start with animated boot sequence."""
    user = update.effective_user
    user_id = user.id
    bot_stats["total_users"].add(user_id)

    logger.info(f"User {user_id} ({user.username}) triggered /start")

    # Send first boot frame
    try:
        msg = await update.message.reply_text(
            BOOT_FRAMES[0],
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Failed to send boot frame: {e}")
        return

    # Animate boot sequence
    for i, frame in enumerate(BOOT_FRAMES[1:], 1):
        await asyncio.sleep(0.6)
        try:
            await msg.edit_text(frame, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Boot frame {i} edit failed: {e}")

    await asyncio.sleep(0.5)

    # Check membership
    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    # Show main menu
    welcome_text = f"""
{MAIN_MENU_TEXT}
👤 <b>Welcome back, <code>{html.escape(user.first_name)}</code>!</b>
💬 <i>{random_hacker_quote()}</i>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
            InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
        ],
        [
            InlineKeyboardButton("📖 HELP", callback_data="show_help"),
            InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
        ],
        [
            InlineKeyboardButton("🔥 JOIN OUR CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"),
        ],
    ])

    try:
        await msg.edit_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to show main menu: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user_id = update.effective_user.id

    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 START FORWARDING", callback_data="start_forward")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        await update.message.reply_text(
            HELP_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Help command error: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping with latency measurement."""
    start = time.monotonic()

    try:
        msg = await update.message.reply_text("🏓 <b>Pinging...</b>", parse_mode=ParseMode.HTML)
        latency = (time.monotonic() - start) * 1000

        ping_text = f"""
<pre>
╔══════════════════════════════╗
║   🏓 PING RESULTS            ║
╠══════════════════════════════╣
║  Latency  : {latency:.1f}ms          
║  Status   : {"🟢 EXCELLENT" if latency < 200 else "🟡 GOOD" if latency < 500 else "🔴 SLOW"}
║  Uptime   : {get_uptime()}  
║  Engine   : ⚡ Async PTB v20 ║
╚══════════════════════════════╝
</pre>
💀 <b>still faster than ur wifi bestie 😂</b>
"""
        await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ping error: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    await show_stats_message(update.message.reply_text)


async def show_stats_message(reply_fn):
    """Show bot statistics."""
    stats_text = f"""
<pre>
╔══════════════════════════════════╗
║      📊 GHOST FORWARDER STATS   ║
╠══════════════════════════════════╣
║  ⚡ Messages Forwarded : {bot_stats['total_forwarded']:<7}║
║  👥 Total Users        : {len(bot_stats['total_users']):<7}║
║  🔄 Total Sessions     : {bot_stats['total_sessions']:<7}║
║  ⚠️  Errors Caught     : {bot_stats['errors_caught']:<7}║
╠══════════════════════════════════╣
║  ⏱️  Uptime : {get_uptime():<21}║
║  🗓️  Since  : {bot_stats['start_time'].strftime('%Y-%m-%d %H:%M'):<20}║
╠══════════════════════════════════╣
║  🟢 STATUS : FULLY OPERATIONAL  ║
╚══════════════════════════════════╝
</pre>
🔥 <i>{random_hacker_quote()}</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 REFRESH", callback_data="show_stats")],
        [InlineKeyboardButton("🏠 MENU", callback_data="main_menu")],
    ])

    try:
        await reply_fn(
            stats_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Stats display error: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📨 FORWARDING CONVERSATION HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the forwarding conversation."""
    user_id = update.effective_user.id
    bot_stats["total_users"].add(user_id)

    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return ConversationHandler.END

    # Initialize user data
    context.user_data.clear()

    prompt_text = """
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 1/3 : SOURCE CHANNEL      ║
╚══════════════════════════════════╝
</pre>
🔥 <b>aight bestie, drop the SOURCE channel below 👇</b>

<i>Accepted formats:</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code> (chat ID)
• <code>https://t.me/channelname</code>

💀 <i>make sure u have access to that channel fr</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                prompt_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                prompt_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Forward start error: {e}")
        return ConversationHandler.END

    return WAITING_SOURCE


async def receive_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive source channel from user."""
    source_input = update.message.text.strip()

    # Clean up the input
    source_input = source_input.replace("https://t.me/", "@")
    if source_input.startswith("t.me/"):
        source_input = "@" + source_input[5:]

    context.user_data["source"] = source_input

    prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 2/3 : TARGET CHANNEL      ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source_input[:20]+"..." if len(source_input)>20 else source_input):<20}║
╚══════════════════════════════════╝
</pre>
🎯 <b>now drop the TARGET channel bestie 👇</b>

<i>where u want messages to go?</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code>

⚠️ <i>bot needs ADMIN rights in target channel!</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Receive source error: {e}")
        return ConversationHandler.END

    return WAITING_TARGET


async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive target channel from user."""
    target_input = update.message.text.strip()

    target_input = target_input.replace("https://t.me/", "@")
    if target_input.startswith("t.me/"):
        target_input = "@" + target_input[5:]

    context.user_data["target"] = target_input

    prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 3/3 : MESSAGE LIMIT       ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(context.user_data['source'][:17]+"..." if len(context.user_data['source'])>17 else context.user_data['source']):<20}║
║  ✅ Target : {html.escape(target_input[:20]+"..." if len(target_input)>20 else target_input):<20}║
╚══════════════════════════════════╝
</pre>
🔢 <b>how many messages to forward? (1-10000)</b>

<i>Pro tip bestie:</i>
• <code>100</code> = first 100 messages
• <code>500</code> = first 500 messages  
• <code>0</code> = ALL messages (could take long tho 💀)

⚡ <i>auto batching enabled - no flood = no prob</i>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("100", callback_data="limit_100"),
            InlineKeyboardButton("500", callback_data="limit_500"),
            InlineKeyboardButton("1000", callback_data="limit_1000"),
        ],
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Receive target error: {e}")
        return ConversationHandler.END

    return WAITING_LIMIT


async def receive_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive message limit from user text."""
    try:
        limit = int(update.message.text.strip())
        if limit < 0:
            raise ValueError("Negative limit")
        if limit == 0:
            limit = 99999  # "All messages"
        if limit > 50000:
            limit = 50000  # Safety cap
    except ValueError:
        await update.message.reply_text(
            "⚠️ <b>bruh that's not a valid number 💀</b>\n"
            "Send a number like <code>100</code> or <code>500</code>",
            parse_mode=ParseMode.HTML,
        )
        return WAITING_LIMIT

    context.user_data["limit"] = limit
    return await show_confirmation(update, context)


async def receive_limit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive message limit from inline button."""
    query = update.callback_query
    await query.answer()

    limit_map = {"limit_100": 100, "limit_500": 500, "limit_1000": 1000}
    limit = limit_map.get(query.data, 100)
    context.user_data["limit"] = limit

    return await show_confirmation(update, context, from_callback=True)


async def show_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    from_callback: bool = False,
):
    """Show forwarding confirmation screen."""
    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    limit = context.user_data.get("limit", 100)

    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
║  ⏱️  Sleep   : 5-10s per batch  ║
╠══════════════════════════════════╣
║  ⚡ ENGINE  : TELETHON MTProto  ║
║  🛡️  FLOOD  : Auto protected    ║
╚══════════════════════════════════╝
</pre>
💀 <b>u sure bout this? no cap this is about to go crazy 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT FR FR", callback_data="confirm_forward"),
            InlineKeyboardButton("❌ NAH ABORT", callback_data="cancel_forward"),
        ],
    ])

    try:
        if from_callback and update.callback_query:
            await update.callback_query.message.edit_text(
                confirm_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                confirm_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Confirmation display error: {e}")
        return ConversationHandler.END

    return CONFIRM_FORWARD


async def confirm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and start the forwarding process."""
    query = update.callback_query
    await query.answer("🚀 Launching ghost engine...")

    source = context.user_data.get("source")
    target = context.user_data.get("target")
    limit = context.user_data.get("limit", 100)
    user_id = update.effective_user.id

    bot_stats["total_sessions"] += 1

    # Show launch animation
    launch_text = """
<pre>
╔══════════════════════════════════╗
║   🚀 GHOST ENGINE LAUNCHING...  ║
╠══════════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░]  5%        ║
║  Connecting to Telegram API...  ║
╚══════════════════════════════════╝
</pre>
⚡ <b>hold tight bestie, we cooking 🔥</b>
"""
    try:
        status_msg = await query.message.edit_text(
            launch_text, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Launch animation error: {e}")
        return ConversationHandler.END

    # Start forwarding in background task
    asyncio.create_task(
        run_forward_engine(
            status_msg,
            source,
            target,
            limit,
            user_id,
            context,
        )
    )

    return ConversationHandler.END


async def cancel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the forwarding operation."""
    query = update.callback_query
    if query:
        await query.answer("Operation cancelled!")

    cancel_text = """
<pre>
╔══════════════════════════════╗
║   ❌ MISSION ABORTED 💀      ║
╠══════════════════════════════╣
║  STATUS : CANCELLED          ║
║  Reason : User requested     ║
╚══════════════════════════════╝
</pre>
😂 <b>aight bet, mission cancelled bestie</b>
<i>use /forward to try again fr</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        if query:
            await query.message.edit_text(
                cancel_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                cancel_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Cancel error: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    context.user_data.clear()
    context.user_data["forward_cancelled"] = True

    try:
        await update.message.reply_text(
            "❌ <b>Operation cancelled! use /start to restart 💀</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Cancel command error: {e}")

    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚡ TELETHON FORWARDING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Global Telethon client
telethon_client: Optional[TelegramClient] = None


async def get_telethon_client() -> TelegramClient:
    """Get or create Telethon client."""
    global telethon_client

    if telethon_client is None or not telethon_client.is_connected():
        telethon_client = TelegramClient(
            "ghost_forwarder_session",
            API_ID,
            API_HASH,
        )
        await telethon_client.start(bot_token=BOT_TOKEN)
        logger.info("✅ Telethon client connected!")

    return telethon_client


async def run_forward_engine(
    status_msg,
    source: str,
    target: str,
    limit: int,
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Core forwarding engine using Telethon.
    Handles batching, flood wait, and progress updates.
    """
    forwarded = 0
    failed = 0
    batch_size = 100
    batch_num = 0
    start_time = time.monotonic()

    async def update_progress(current: int, total: int, status: str = ""):
        """Update progress message."""
        bar = make_progress_bar(current, total if total > 0 else current + 1)
        elapsed = time.monotonic() - start_time
        rate = current / elapsed if elapsed > 0 else 0

        progress_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ FORWARDING IN PROGRESS...  ║
╠══════════════════════════════════╣
║  {bar:<32}║
╠══════════════════════════════════╣
║  ✅ Forwarded : {str(current):<16} ║
║  ❌ Failed    : {str(failed):<16} ║
║  📦 Batch     : #{str(batch_num):<15} ║
║  ⚡ Rate      : {f"{rate:.1f} msg/s":<16} ║
╠══════════════════════════════════╣
║  {html.escape(status[:32]) if status else "Processing messages...":<32}║
╚══════════════════════════════════╝
</pre>
🔥 <b>we going crazy rn no cap 💀</b>
"""
        try:
            await status_msg.edit_text(progress_text, parse_mode=ParseMode.HTML)
        except Exception:
            pass  # Silently ignore edit failures (too many requests etc)

    try:
        # Connect Telethon
        await update_progress(0, limit, "🔌 Connecting to Telegram API...")
        client = await get_telethon_client()

        await update_progress(0, limit, "🔍 Resolving channels...")

        # Resolve source entity
        try:
            source_entity = await client.get_entity(source)
        except (UsernameNotOccupiedError, ValueError) as e:
            await show_error(status_msg, f"Source channel not found: {html.escape(str(e))}")
            bot_stats["errors_caught"] += 1
            return
        except ChannelPrivateError:
            await show_error(status_msg, "Source channel is private — bot has no access 💀")
            bot_stats["errors_caught"] += 1
            return
        except Exception as e:
            await show_error(status_msg, f"Source error: {html.escape(str(e)[:100])}")
            bot_stats["errors_caught"] += 1
            return

        # Resolve target entity
        try:
            target_entity = await client.get_entity(target)
        except (UsernameNotOccupiedError, ValueError) as e:
            await show_error(status_msg, f"Target channel not found: {html.escape(str(e))}")
            bot_stats["errors_caught"] += 1
            return
        except ChannelPrivateError:
            await show_error(status_msg, "Target channel is private — bot has no access 💀")
            bot_stats["errors_caught"] += 1
            return
        except Exception as e:
            await show_error(status_msg, f"Target error: {html.escape(str(e)[:100])}")
            bot_stats["errors_caught"] += 1
            return

        await update_progress(0, limit, "📡 Fetching messages...")

        # Collect messages in batches
        offset_id = 0
        all_message_ids = []

        # First pass: collect message IDs
        async for message in client.iter_messages(
            source_entity,
            limit=limit if limit < 99999 else None,
        ):
            if message and message.id:
                all_message_ids.append(message.id)

        total_messages = len(all_message_ids)
        logger.info(f"Found {total_messages} messages in {source}")

        if total_messages == 0:
            await show_error(status_msg, "No messages found in source channel 😭")
            return

        await update_progress(0, total_messages, f"📦 Found {total_messages} messages!")
        await asyncio.sleep(1)

        # Process in batches of 100
        message_ids_reversed = list(reversed(all_message_ids))

        for batch_start in range(0, total_messages, batch_size):
            # Check if cancelled
            if context.user_data.get("forward_cancelled"):
                logger.info(f"Forwarding cancelled by user {user_id}")
                break

            batch_num += 1
            batch = message_ids_reversed[batch_start: batch_start + batch_size]

            await update_progress(
                forwarded,
                total_messages,
                f"🔄 Processing batch #{batch_num}...",
            )

            # Forward each message in batch
            for msg_id in batch:
                # Check cancelled again
                if context.user_data.get("forward_cancelled"):
                    break

                try:
                    await client.forward_messages(
                        entity=target_entity,
                        messages=msg_id,
                        from_peer=source_entity,
                    )
                    forwarded += 1
                    bot_stats["total_forwarded"] += 1

                    # Update progress every 10 messages
                    if forwarded % 10 == 0:
                        await update_progress(
                            forwarded,
                            total_messages,
                            f"⚡ Forwarding batch #{batch_num}...",
                        )

                    # Small delay between messages to avoid flood
                    await asyncio.sleep(0.3)

                except FloodWaitError as e:
                    wait_time = e.seconds
                    logger.warning(f"FloodWait: sleeping {wait_time}s")

                    for remaining in range(wait_time, 0, -5):
                        await update_progress(
                            forwarded,
                            total_messages,
                            f"⏳ FloodWait: {remaining}s remaining...",
                        )
                        await asyncio.sleep(min(5, remaining))

                except ChatAdminRequiredError:
                    await show_error(
                        status_msg,
                        "Bot needs admin rights in target channel! 💀"
                    )
                    bot_stats["errors_caught"] += 1
                    return

                except Exception as e:
                    failed += 1
                    bot_stats["errors_caught"] += 1
                    logger.warning(f"Forward error for msg {msg_id}: {e}")
                    await asyncio.sleep(0.5)

            # Batch complete - sleep between batches
            if batch_start + batch_size < total_messages:
                sleep_time = random.randint(5, 10)
                for remaining in range(sleep_time, 0, -1):
                    await update_progress(
                        forwarded,
                        total_messages,
                        f"😴 Batch #{batch_num} done! Next in {remaining}s...",
                    )
                    await asyncio.sleep(1)

        # ─── DONE! Show final result ─────────────────────────
        elapsed = time.monotonic() - start_time
        rate = forwarded / elapsed if elapsed > 0 else 0

        final_text = f"""
<pre>
╔══════════════════════════════════╗
║   ✅ MISSION COMPLETE! 💀       ║
╠══════════════════════════════════╣
║  {make_progress_bar(forwarded, total_messages):<32}║
╠══════════════════════════════════╣
║  ✅ Forwarded : {str(forwarded):<16} ║
║  ❌ Failed    : {str(failed):<16} ║
║  📦 Batches   : {str(batch_num):<16} ║
║  ⏱️  Time      : {f"{elapsed:.1f}s":<16} ║
║  ⚡ Speed     : {f"{rate:.1f} msg/s":<16} ║
╠══════════════════════════════════╣
║  🏆 STATUS : FULLY COMPLETE     ║
╚══════════════════════════════════╝
</pre>
🔥 <b>SLAY! we did it bestie 🫶🏻 {random_hacker_quote()}</b>
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 FORWARD AGAIN", callback_data="start_forward")],
            [InlineKeyboardButton("📊 VIEW STATS", callback_data="show_stats")],
            [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
        ])

        try:
            await status_msg.edit_text(
                final_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Final message edit error: {e}")

        logger.info(
            f"Forwarding complete: {forwarded}/{total_messages} messages "
            f"in {elapsed:.1f}s by user {user_id}"
        )

    except Exception as e:
        logger.error(f"Forward engine critical error: {e}", exc_info=True)
        bot_stats["errors_caught"] += 1
        await show_error(status_msg, f"Critical error: {html.escape(str(e)[:150])}")


async def show_error(status_msg, error_text: str):
    """Show styled error message."""
    error_display = f"""
<pre>
╔══════════════════════════════════╗
║   ⚠️  ERROR DETECTED 💀         ║
╠══════════════════════════════════╣
║  Status : OPERATION FAILED       ║
╚══════════════════════════════════╝
</pre>
❌ <b>bruh something went wrong fr:</b>

<code>{html.escape(error_text)}</code>

💡 <i>try again bestie, or check ur channel settings</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 TRY AGAIN", callback_data="start_forward")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        await status_msg.edit_text(
            error_display,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Error display failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎛️ CALLBACK QUERY HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central callback query router."""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    await query.answer()

    logger.info(f"Callback: {data} from user {user_id}")

    try:
        if data == "verify_membership":
            is_member = await check_membership(user_id, context)
            if is_member:
                # Show boot sequence again
                await query.message.edit_text(
                    BOOT_FRAMES[4], parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(0.5)

                welcome = f"""
{MAIN_MENU_TEXT}
👤 <b>Welcome, <code>{html.escape(update.effective_user.first_name)}</code>!</b>
✅ <i>Membership verified! Access granted fr 💀</i>
"""
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
                        InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
                    ],
                    [
                        InlineKeyboardButton("📖 HELP", callback_data="show_help"),
                        InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
                    ],
                ])
                await query.message.edit_text(
                    welcome,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            else:
                await show_access_denied(update, context)

        elif data == "main_menu":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
                    InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
                ],
                [
                    InlineKeyboardButton("📖 HELP", callback_data="show_help"),
                    InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
                ],
                [
                    InlineKeyboardButton(
                        "🔥 JOIN CHANNEL",
                        url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
                    ),
                ],
            ])
            await query.message.edit_text(
                MAIN_MENU_TEXT,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "show_stats":
            await show_stats_message(query.message.edit_text)

        elif data == "show_help":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 START FORWARDING", callback_data="start_forward")],
                [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
            ])
            await query.message.edit_text(
                HELP_TEXT,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "do_ping":
            start = time.monotonic()
            await query.message.edit_text(
                "🏓 <b>Calculating latency...</b>",
                parse_mode=ParseMode.HTML,
            )
            latency = (time.monotonic() - start) * 1000

            ping_text = f"""
<pre>
╔══════════════════════════════╗
║   🏓 PING RESULTS            ║
╠══════════════════════════════╣
║  Latency : {latency:.1f}ms           
║  Status  : {"🟢 EXCELLENT" if latency < 200 else "🟡 GOOD" if latency < 500 else "🔴 SLOW"}
║  Uptime  : {get_uptime()}   
╚══════════════════════════════╝
</pre>
💀 <b>still faster than ur ex texting back 😂</b>
"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
            ])
            await query.message.edit_text(
                ping_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "start_forward":
            # Trigger forward conversation
            is_member = await check_membership(user_id, context)
            if not is_member:
                await show_access_denied(update, context)
                return

            context.user_data.clear()
            prompt_text = """
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 1/3 : SOURCE CHANNEL      ║
╚══════════════════════════════════╝
</pre>
🔥 <b>drop the SOURCE channel below 👇</b>

<i>Accepted formats:</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code>
• <code>https://t.me/channelname</code>
"""
            await query.message.edit_text(
                prompt_text, parse_mode=ParseMode.HTML
            )
            # Store state in user_data for next message
            context.user_data["awaiting"] = "source"

    except Exception as e:
        logger.error(f"Callback handler error [{data}]: {e}", exc_info=True)
        bot_stats["errors_caught"] += 1
        try:
            await query.message.edit_text(
                f"⚠️ <b>Something went wrong fr:</b>\n<code>{html.escape(str(e)[:200])}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 GENERAL MESSAGE HANDLER (for conversation state via callbacks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages for conversation state from callbacks."""
    awaiting = context.user_data.get("awaiting")

    if not awaiting:
        # Default response for unhandled messages
        await update.message.reply_text(
            "💀 <b>use /start to boot up the ghost engine bestie</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    user_input = update.message.text.strip() if update.message.text else ""

    if awaiting == "source":
        source_input = user_input.replace("https://t.me/", "@")
        if source_input.startswith("t.me/"):
            source_input = "@" + source_input[5:]

        context.user_data["source"] = source_input
        context.user_data["awaiting"] = "target"

        prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 2/3 : TARGET CHANNEL      ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source_input[:20]+"..." if len(source_input)>20 else source_input):<20}║
╚══════════════════════════════════╝
</pre>
🎯 <b>now drop the TARGET channel 👇</b>
⚠️ <i>bot needs ADMIN in target channel!</i>
"""
        await update.message.reply_text(prompt_text, parse_mode=ParseMode.HTML)

    elif awaiting == "target":
        target_input = user_input.replace("https://t.me/", "@")
        if target_input.startswith("t.me/"):
            target_input = "@" + target_input[5:]

        context.user_data["target"] = target_input
        context.user_data["awaiting"] = "limit"

        source = context.user_data.get("source", "")
        prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 3/3 : MESSAGE LIMIT       ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source[:20]):<20}║
║  ✅ Target : {html.escape(target_input[:20]):<20}║
╚══════════════════════════════════╝
</pre>
🔢 <b>how many messages? (enter a number)</b>
"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("100", callback_data="cb_limit_100"),
                InlineKeyboardButton("500", callback_data="cb_limit_500"),
                InlineKeyboardButton("1000", callback_data="cb_limit_1000"),
            ],
        ])
        await update.message.reply_text(
            prompt_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )

    elif awaiting == "limit":
        try:
            limit = int(user_input)
            if limit <= 0:
                limit = 99999
            if limit > 50000:
                limit = 50000
        except ValueError:
            await update.message.reply_text(
                "⚠️ <b>that ain't a number bestie 💀</b> try again",
                parse_mode=ParseMode.HTML,
            )
            return

        context.user_data["limit"] = limit
        context.user_data["awaiting"] = None
        await show_confirmation_message(update, context)


async def show_confirmation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation via regular message."""
    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    limit = context.user_data.get("limit", 100)
    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
╚══════════════════════════════════╝
</pre>
💀 <b>ready to go full ghost mode? 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT!", callback_data="cb_confirm_forward"),
            InlineKeyboardButton("❌ ABORT", callback_data="cb_cancel"),
        ],
    ])
    await update.message.reply_text(
        confirm_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


async def handle_cb_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick limit selection callbacks from message flow."""
    query = update.callback_query
    await query.answer()
    data = query.data

    limit_map = {
        "cb_limit_100": 100,
        "cb_limit_500": 500,
        "cb_limit_1000": 1000,
    }

    limit = limit_map.get(data, 100)
    context.user_data["limit"] = limit
    context.user_data["awaiting"] = None

    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
╚══════════════════════════════════╝
</pre>
💀 <b>ready to go full ghost mode? 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT!", callback_data="cb_confirm_forward"),
            InlineKeyboardButton("❌ ABORT", callback_data="cb_cancel"),
        ],
    ])
    await query.message.edit_text(
        confirm_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


async def handle_cb_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forward confirmation from message flow."""
    query = update.callback_query
    await query.answer("🚀 Launching...")

    source = context.user_data.get("source")
    target = context.user_data.get("target")
    limit = context.user_data.get("limit", 100)
    user_id = update.effective_user.id

    if not source or not target:
        await query.message.edit_text(
            "⚠️ <b>Mission data lost! Use /forward to restart</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    bot_stats["total_sessions"] += 1

    launch_text = """
<pre>
╔══════════════════════════════════╗
║   🚀 GHOST ENGINE LAUNCHING...  ║
╠══════════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░]  5%        ║
║  Connecting to Telegram API...  ║
╚══════════════════════════════════╝
</pre>
⚡ <b>hold tight, we cooking rn 🔥</b>
"""
    try:
        status_msg = await query.message.edit_text(
            launch_text, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Launch message error: {e}")
        return

    asyncio.create_task(
        run_forward_engine(status_msg, source, target, limit, user_id, context)
    )


async def handle_cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel from message flow."""
    query = update.callback_query
    await query.answer("Cancelled!")
    context.user_data.clear()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])
    await query.message.edit_text(
        "❌ <b>Mission aborted! bestie took the L 😂</b>\n<i>use /forward to try again</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ERROR HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler - bot must NEVER crash."""
    bot_stats["errors_caught"] += 1
    error = context.error

    logger.error(f"Global error handler caught: {error}", exc_info=True)

    # Specific error handling
    if isinstance(error, Forbidden):
        logger.warning("Bot was blocked by user or lacks permissions")
        return

    if isinstance(error, BadRequest):
        logger.warning(f"Bad request: {error}")
        return

    if isinstance(error, TelegramError):
        logger.warning(f"Telegram error: {error}")
        return

    # Try to notify user about unknown errors
    try:
        if update and hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(
                f"""
<pre>
╔══════════════════════════════╗
║  ⚠️  SYSTEM ERROR 💀         ║
╚══════════════════════════════╝
</pre>
❌ <b>something glitched fr:</b>
<code>{html.escape(str(error)[:200])}</code>

💡 <i>try /start to reset the system bestie</i>
""",
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.error(f"Error handler notification failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏗️ APPLICATION SETUP & MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_application() -> Application:
    """Build and configure the PTB application."""

    app = Application.builder().token(BOT_TOKEN).build()

    # ─── Conversation Handler for /forward ────────────────────
    forward_conv = ConversationHandler(
        entry_points=[
            CommandHandler("forward", cmd_forward),
        ],
        states={
            WAITING_SOURCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_source),
            ],
            WAITING_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target),
            ],
            WAITING_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_limit),
                CallbackQueryHandler(receive_limit_callback, pattern="^limit_"),
            ],
            CONFIRM_FORWARD: [
                CallbackQueryHandler(confirm_forward, pattern="^confirm_forward$"),
                CallbackQueryHandler(cancel_forward, pattern="^cancel_forward$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(cancel_forward, pattern="^cancel_forward$"),
        ],
        allow_reentry=True,
    )

    # ─── Register Handlers ─────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # Conversation handler
    app.add_handler(forward_conv)

    # Callback handlers for message-flow forwarding
    app.add_handler(
        CallbackQueryHandler(handle_cb_limit, pattern="^cb_limit_")
    )
    app.add_handler(
        CallbackQueryHandler(handle_cb_confirm, pattern="^cb_confirm_forward$")
    )
    app.add_handler(
        CallbackQueryHandler(handle_cb_cancel, pattern="^cb_cancel$")
    )

    # General callback handler
    app.add_handler(
        CallbackQueryHandler(handle_callbacks)
    )

    # General message handler
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Global error handler
    app.add_error_handler(error_handler)

    return app


async def startup_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║          💀 GHOST FORWARDER BOT v2.0 💀                      ║
║          Production Grade | Cyberpunk Style                  ║
╠══════════════════════════════════════════════════════════════╣
║  ⚡ Engine    : python-telegram-bot v20+ + Telethon          ║
║  🔐 Auth      : Environment Variables Only                   ║
║  🛡️  Security  : FloodWait Protection Enabled                ║
║  📦 Batching  : 100 msgs/batch with 5-10s sleep              ║
╠══════════════════════════════════════════════════════════════╣
║  📡 Status    : INITIALIZING...                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logger.info("Ghost Forwarder Bot starting up...")
    logger.info(f"Required channel: {REQUIRED_CHANNEL}")
    logger.info(f"Admin IDs: {ADMIN_IDS}")


def main():
    """Main entry point."""
    asyncio.get_event_loop().run_until_complete(startup_banner())

    app = build_application()

    logger.info("✅ Bot is online! Polling for updates...")
    print("\n💀 GHOST FORWARDER BOT IS ONLINE! SLAY MODE ACTIVATED 🔥\n")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          💀 GHOST FORWARDER BOT v2.0 💀                      ║
║          Built by: Senior Dev | Production Grade             ║
║          Style: Cyberpunk / Gen-Z / Hacker                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import asyncio
import logging
import html
import time
import random
from datetime import datetime
from typing import Optional

# ─── Telegram Bot (PTB v20+) ───────────────────────────────────
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMember,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, Forbidden, BadRequest

# ─── Telethon (MTProto for forwarding) ────────────────────────
from telethon import TelegramClient, errors
from telethon.tl.types import (
    InputPeerChannel,
    MessageMediaPhoto,
    MessageMediaDocument,
)
from telethon.errors import (
    FloodWaitError,
    ChatAdminRequiredError,
    ChannelPrivateError,
    UsernameNotOccupiedError,
)

# ─── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GhostForwarder")
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 ENVIRONMENT VARIABLES (NO HARDCODED SECRETS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
REQUIRED_CHANNEL = os.environ.get("REQUIRED_CHANNEL", "@your_channel")
ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

# ─── Validate env vars ─────────────────────────────────────────
if not BOT_TOKEN:
    raise EnvironmentError("❌ BOT_TOKEN not set in environment variables!")
if not API_ID or not API_HASH:
    raise EnvironmentError("❌ API_ID or API_HASH not set in environment variables!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 BOT STATS (In-Memory)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bot_stats = {
    "start_time": datetime.now(),
    "total_forwarded": 0,
    "total_users": set(),
    "total_sessions": 0,
    "errors_caught": 0,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎭 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(
    WAITING_SOURCE,
    WAITING_TARGET,
    WAITING_LIMIT,
    CONFIRM_FORWARD,
) = range(4)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 UI TEMPLATES - CYBERPUNK STYLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOOT_FRAMES = [
    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░░]  5%   ║
║  Initializing core...        ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓░░░░░░░░░░░░░]  25%  ║
║  Loading modules... ⚡       ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓░░░░░░░░░]  50%  ║
║  Connecting to matrix... 🔥  ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓▓▓▓▓░░░░░]  75%  ║
║  Bypassing firewall... 🤖    ║
╚══════════════════════════════╝
</pre>""",

    """
<pre>
╔══════════════════════════════╗
║  💀 GHOST FORWARDER v2.0    ║
╠══════════════════════════════╣
║  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  100% ║
║  ✅ SYSTEM ONLINE            ║
╚══════════════════════════════╝
</pre>""",
]

DENIED_FRAMES = [
    "💀 <b>SCANNING ACCESS CREDENTIALS...</b>",
    "🔍 <b>CHECKING MEMBERSHIP STATUS...</b>",
    "⚠️ <b>INSUFFICIENT CLEARANCE LEVEL...</b>",
    "☠️ <b>ACCESS DENIED — UNAUTHORIZED!</b>",
]

MAIN_MENU_TEXT = """
<pre>
╔══════════════════════════════════╗
║   💀 GHOST FORWARDER v2.0 💀    ║
╠══════════════════════════════════╣
║  Status  : 🟢 ONLINE            ║
║  Engine  : ⚡ TELETHON MTProto  ║
║  Version : 2.0.0-cyberpunk      ║
╠══════════════════════════════════╣
║  💥 COMMANDS                    ║
║  /forward  → Start forwarding   ║
║  /stats    → Bot statistics     ║
║  /ping     → Check latency      ║
║  /help     → Full help guide    ║
╚══════════════════════════════════╝
</pre>
🔥 <b>yo bestie, pick ur weapon below 👇</b>
"""

HELP_TEXT = """
<pre>
╔══════════════════════════════════════╗
║      📖 GHOST FORWARDER HELP        ║
╠══════════════════════════════════════╣
║  /start    → Boot sequence + menu   ║
║  /forward  → Launch forward engine  ║
║  /stats    → View bot stats         ║
║  /ping     → Latency check          ║
║  /cancel   → Cancel any operation   ║
╠══════════════════════════════════════╣
║  📦 SUPPORTED MEDIA                 ║
║  ✅ Text messages                   ║
║  ✅ Photos                          ║
║  ✅ Videos                          ║
║  ✅ Documents                       ║
║  ✅ Audio files                     ║
╠══════════════════════════════════════╣
║  ⚙️ HOW IT WORKS                    ║
║  1. Enter SOURCE channel            ║
║  2. Enter TARGET channel            ║
║  3. Set message limit               ║
║  4. Confirm & LAUNCH 🚀             ║
╠══════════════════════════════════════╣
║  💡 TIPS                            ║
║  • Use @username or chat ID         ║
║  • Bot needs admin in target        ║
║  • FloodWait is auto-handled        ║
╚══════════════════════════════════════╝
</pre>
💀 <i>stay ghost, stay legendary fr fr no cap 💀</i>
"""


def make_progress_bar(current: int, total: int, width: int = 16) -> str:
    """Generate animated progress bar."""
    if total == 0:
        return "░" * width
    filled = int((current / total) * width)
    bar = "▓" * filled + "░" * (width - filled)
    pct = int((current / total) * 100)
    return f"[{bar}] {pct}%"


def get_uptime() -> str:
    """Calculate bot uptime."""
    delta = datetime.now() - bot_stats["start_time"]
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"


def random_hacker_quote() -> str:
    """Return a random Gen-Z hacker quote."""
    quotes = [
        "no cap this bot goes crazy hard 💀",
        "slay mode: ACTIVATED fr fr 🔥",
        "we do be ghosting the matrix tho ⚡",
        "bussin bussin on god 🫶🏻",
        "main character energy activated 😂",
        "lowkey slapping rn no cap 💀",
        "it's giving hacker vibes fr 🤖",
        "not me forwarding messages at 3am 💀",
    ]
    return random.choice(quotes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 MEMBERSHIP CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of the required channel."""
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        ]
    except (TelegramError, Exception) as e:
        logger.warning(f"Membership check failed for {user_id}: {e}")
        # If we can't check, allow access (graceful degradation)
        return True


async def show_access_denied(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show animated access denied screen."""
    query = update.callback_query
    msg = update.message

    # Send initial denied animation
    if query:
        target = query.message
        edit_fn = query.message.edit_text
    else:
        target = await msg.reply_text("💀")
        edit_fn = target.edit_text

    for frame in DENIED_FRAMES:
        try:
            await edit_fn(
                frame,
                parse_mode=ParseMode.HTML,
            )
            await asyncio.sleep(0.7)
        except Exception:
            pass

    # Final denied screen with join button
    denied_text = """
<pre>
╔══════════════════════════════════╗
║   ☠️  ACCESS DENIED ☠️           ║
╠══════════════════════════════════╣
║  ERROR CODE : 403_FORBIDDEN      ║
║  STATUS     : NOT A MEMBER       ║
║  CLEARANCE  : INSUFFICIENT       ║
╠══════════════════════════════════╣
║  🔐 JOIN REQUIRED CHANNEL        ║
║  to unlock full ghost mode       ║
╚══════════════════════════════════╝
</pre>
💀 <b>bestie u gotta join first lmao 😂</b>
<i>click the button below then verify 👇</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔗 JOIN CHANNEL ⚡",
            url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
        )],
        [InlineKeyboardButton(
            "✅ VERIFY MEMBERSHIP 🔍",
            callback_data="verify_membership"
        )],
    ])

    try:
        await edit_fn(
            denied_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Error showing denied screen: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 COMMAND HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start with animated boot sequence."""
    user = update.effective_user
    user_id = user.id
    bot_stats["total_users"].add(user_id)

    logger.info(f"User {user_id} ({user.username}) triggered /start")

    # Send first boot frame
    try:
        msg = await update.message.reply_text(
            BOOT_FRAMES[0],
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Failed to send boot frame: {e}")
        return

    # Animate boot sequence
    for i, frame in enumerate(BOOT_FRAMES[1:], 1):
        await asyncio.sleep(0.6)
        try:
            await msg.edit_text(frame, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Boot frame {i} edit failed: {e}")

    await asyncio.sleep(0.5)

    # Check membership
    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    # Show main menu
    welcome_text = f"""
{MAIN_MENU_TEXT}
👤 <b>Welcome back, <code>{html.escape(user.first_name)}</code>!</b>
💬 <i>{random_hacker_quote()}</i>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
            InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
        ],
        [
            InlineKeyboardButton("📖 HELP", callback_data="show_help"),
            InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
        ],
        [
            InlineKeyboardButton("🔥 JOIN OUR CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"),
        ],
    ])

    try:
        await msg.edit_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to show main menu: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user_id = update.effective_user.id

    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 START FORWARDING", callback_data="start_forward")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        await update.message.reply_text(
            HELP_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Help command error: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping with latency measurement."""
    start = time.monotonic()

    try:
        msg = await update.message.reply_text("🏓 <b>Pinging...</b>", parse_mode=ParseMode.HTML)
        latency = (time.monotonic() - start) * 1000

        ping_text = f"""
<pre>
╔══════════════════════════════╗
║   🏓 PING RESULTS            ║
╠══════════════════════════════╣
║  Latency  : {latency:.1f}ms          
║  Status   : {"🟢 EXCELLENT" if latency < 200 else "🟡 GOOD" if latency < 500 else "🔴 SLOW"}
║  Uptime   : {get_uptime()}  
║  Engine   : ⚡ Async PTB v20 ║
╚══════════════════════════════╝
</pre>
💀 <b>still faster than ur wifi bestie 😂</b>
"""
        await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ping error: {e}")
        bot_stats["errors_caught"] += 1


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return

    await show_stats_message(update.message.reply_text)


async def show_stats_message(reply_fn):
    """Show bot statistics."""
    stats_text = f"""
<pre>
╔══════════════════════════════════╗
║      📊 GHOST FORWARDER STATS   ║
╠══════════════════════════════════╣
║  ⚡ Messages Forwarded : {bot_stats['total_forwarded']:<7}║
║  👥 Total Users        : {len(bot_stats['total_users']):<7}║
║  🔄 Total Sessions     : {bot_stats['total_sessions']:<7}║
║  ⚠️  Errors Caught     : {bot_stats['errors_caught']:<7}║
╠══════════════════════════════════╣
║  ⏱️  Uptime : {get_uptime():<21}║
║  🗓️  Since  : {bot_stats['start_time'].strftime('%Y-%m-%d %H:%M'):<20}║
╠══════════════════════════════════╣
║  🟢 STATUS : FULLY OPERATIONAL  ║
╚══════════════════════════════════╝
</pre>
🔥 <i>{random_hacker_quote()}</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 REFRESH", callback_data="show_stats")],
        [InlineKeyboardButton("🏠 MENU", callback_data="main_menu")],
    ])

    try:
        await reply_fn(
            stats_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Stats display error: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📨 FORWARDING CONVERSATION HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the forwarding conversation."""
    user_id = update.effective_user.id
    bot_stats["total_users"].add(user_id)

    is_member = await check_membership(user_id, context)
    if not is_member:
        await show_access_denied(update, context)
        return ConversationHandler.END

    # Initialize user data
    context.user_data.clear()

    prompt_text = """
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 1/3 : SOURCE CHANNEL      ║
╚══════════════════════════════════╝
</pre>
🔥 <b>aight bestie, drop the SOURCE channel below 👇</b>

<i>Accepted formats:</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code> (chat ID)
• <code>https://t.me/channelname</code>

💀 <i>make sure u have access to that channel fr</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                prompt_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                prompt_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Forward start error: {e}")
        return ConversationHandler.END

    return WAITING_SOURCE


async def receive_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive source channel from user."""
    source_input = update.message.text.strip()

    # Clean up the input
    source_input = source_input.replace("https://t.me/", "@")
    if source_input.startswith("t.me/"):
        source_input = "@" + source_input[5:]

    context.user_data["source"] = source_input

    prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 2/3 : TARGET CHANNEL      ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source_input[:20]+"..." if len(source_input)>20 else source_input):<20}║
╚══════════════════════════════════╝
</pre>
🎯 <b>now drop the TARGET channel bestie 👇</b>

<i>where u want messages to go?</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code>

⚠️ <i>bot needs ADMIN rights in target channel!</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Receive source error: {e}")
        return ConversationHandler.END

    return WAITING_TARGET


async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive target channel from user."""
    target_input = update.message.text.strip()

    target_input = target_input.replace("https://t.me/", "@")
    if target_input.startswith("t.me/"):
        target_input = "@" + target_input[5:]

    context.user_data["target"] = target_input

    prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 3/3 : MESSAGE LIMIT       ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(context.user_data['source'][:17]+"..." if len(context.user_data['source'])>17 else context.user_data['source']):<20}║
║  ✅ Target : {html.escape(target_input[:20]+"..." if len(target_input)>20 else target_input):<20}║
╚══════════════════════════════════╝
</pre>
🔢 <b>how many messages to forward? (1-10000)</b>

<i>Pro tip bestie:</i>
• <code>100</code> = first 100 messages
• <code>500</code> = first 500 messages  
• <code>0</code> = ALL messages (could take long tho 💀)

⚡ <i>auto batching enabled - no flood = no prob</i>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("100", callback_data="limit_100"),
            InlineKeyboardButton("500", callback_data="limit_500"),
            InlineKeyboardButton("1000", callback_data="limit_1000"),
        ],
        [InlineKeyboardButton("❌ CANCEL MISSION", callback_data="cancel_forward")],
    ])

    try:
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Receive target error: {e}")
        return ConversationHandler.END

    return WAITING_LIMIT


async def receive_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive message limit from user text."""
    try:
        limit = int(update.message.text.strip())
        if limit < 0:
            raise ValueError("Negative limit")
        if limit == 0:
            limit = 99999  # "All messages"
        if limit > 50000:
            limit = 50000  # Safety cap
    except ValueError:
        await update.message.reply_text(
            "⚠️ <b>bruh that's not a valid number 💀</b>\n"
            "Send a number like <code>100</code> or <code>500</code>",
            parse_mode=ParseMode.HTML,
        )
        return WAITING_LIMIT

    context.user_data["limit"] = limit
    return await show_confirmation(update, context)


async def receive_limit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive message limit from inline button."""
    query = update.callback_query
    await query.answer()

    limit_map = {"limit_100": 100, "limit_500": 500, "limit_1000": 1000}
    limit = limit_map.get(query.data, 100)
    context.user_data["limit"] = limit

    return await show_confirmation(update, context, from_callback=True)


async def show_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    from_callback: bool = False,
):
    """Show forwarding confirmation screen."""
    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    limit = context.user_data.get("limit", 100)

    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
║  ⏱️  Sleep   : 5-10s per batch  ║
╠══════════════════════════════════╣
║  ⚡ ENGINE  : TELETHON MTProto  ║
║  🛡️  FLOOD  : Auto protected    ║
╚══════════════════════════════════╝
</pre>
💀 <b>u sure bout this? no cap this is about to go crazy 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT FR FR", callback_data="confirm_forward"),
            InlineKeyboardButton("❌ NAH ABORT", callback_data="cancel_forward"),
        ],
    ])

    try:
        if from_callback and update.callback_query:
            await update.callback_query.message.edit_text(
                confirm_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                confirm_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Confirmation display error: {e}")
        return ConversationHandler.END

    return CONFIRM_FORWARD


async def confirm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and start the forwarding process."""
    query = update.callback_query
    await query.answer("🚀 Launching ghost engine...")

    source = context.user_data.get("source")
    target = context.user_data.get("target")
    limit = context.user_data.get("limit", 100)
    user_id = update.effective_user.id

    bot_stats["total_sessions"] += 1

    # Show launch animation
    launch_text = """
<pre>
╔══════════════════════════════════╗
║   🚀 GHOST ENGINE LAUNCHING...  ║
╠══════════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░]  5%        ║
║  Connecting to Telegram API...  ║
╚══════════════════════════════════╝
</pre>
⚡ <b>hold tight bestie, we cooking 🔥</b>
"""
    try:
        status_msg = await query.message.edit_text(
            launch_text, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Launch animation error: {e}")
        return ConversationHandler.END

    # Start forwarding in background task
    asyncio.create_task(
        run_forward_engine(
            status_msg,
            source,
            target,
            limit,
            user_id,
            context,
        )
    )

    return ConversationHandler.END


async def cancel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the forwarding operation."""
    query = update.callback_query
    if query:
        await query.answer("Operation cancelled!")

    cancel_text = """
<pre>
╔══════════════════════════════╗
║   ❌ MISSION ABORTED 💀      ║
╠══════════════════════════════╣
║  STATUS : CANCELLED          ║
║  Reason : User requested     ║
╚══════════════════════════════╝
</pre>
😂 <b>aight bet, mission cancelled bestie</b>
<i>use /forward to try again fr</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        if query:
            await query.message.edit_text(
                cancel_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                cancel_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Cancel error: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    context.user_data.clear()
    context.user_data["forward_cancelled"] = True

    try:
        await update.message.reply_text(
            "❌ <b>Operation cancelled! use /start to restart 💀</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Cancel command error: {e}")

    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚡ TELETHON FORWARDING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Global Telethon client
telethon_client: Optional[TelegramClient] = None


async def get_telethon_client() -> TelegramClient:
    """Get or create Telethon client."""
    global telethon_client

    if telethon_client is None or not telethon_client.is_connected():
        telethon_client = TelegramClient(
            "ghost_forwarder_session",
            API_ID,
            API_HASH,
        )
        await telethon_client.start(bot_token=BOT_TOKEN)
        logger.info("✅ Telethon client connected!")

    return telethon_client


async def run_forward_engine(
    status_msg,
    source: str,
    target: str,
    limit: int,
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Core forwarding engine using Telethon.
    Handles batching, flood wait, and progress updates.
    """
    forwarded = 0
    failed = 0
    batch_size = 100
    batch_num = 0
    start_time = time.monotonic()

    async def update_progress(current: int, total: int, status: str = ""):
        """Update progress message."""
        bar = make_progress_bar(current, total if total > 0 else current + 1)
        elapsed = time.monotonic() - start_time
        rate = current / elapsed if elapsed > 0 else 0

        progress_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ FORWARDING IN PROGRESS...  ║
╠══════════════════════════════════╣
║  {bar:<32}║
╠══════════════════════════════════╣
║  ✅ Forwarded : {str(current):<16} ║
║  ❌ Failed    : {str(failed):<16} ║
║  📦 Batch     : #{str(batch_num):<15} ║
║  ⚡ Rate      : {f"{rate:.1f} msg/s":<16} ║
╠══════════════════════════════════╣
║  {html.escape(status[:32]) if status else "Processing messages...":<32}║
╚══════════════════════════════════╝
</pre>
🔥 <b>we going crazy rn no cap 💀</b>
"""
        try:
            await status_msg.edit_text(progress_text, parse_mode=ParseMode.HTML)
        except Exception:
            pass  # Silently ignore edit failures (too many requests etc)

    try:
        # Connect Telethon
        await update_progress(0, limit, "🔌 Connecting to Telegram API...")
        client = await get_telethon_client()

        await update_progress(0, limit, "🔍 Resolving channels...")

        # Resolve source entity
        try:
            source_entity = await client.get_entity(source)
        except (UsernameNotOccupiedError, ValueError) as e:
            await show_error(status_msg, f"Source channel not found: {html.escape(str(e))}")
            bot_stats["errors_caught"] += 1
            return
        except ChannelPrivateError:
            await show_error(status_msg, "Source channel is private — bot has no access 💀")
            bot_stats["errors_caught"] += 1
            return
        except Exception as e:
            await show_error(status_msg, f"Source error: {html.escape(str(e)[:100])}")
            bot_stats["errors_caught"] += 1
            return

        # Resolve target entity
        try:
            target_entity = await client.get_entity(target)
        except (UsernameNotOccupiedError, ValueError) as e:
            await show_error(status_msg, f"Target channel not found: {html.escape(str(e))}")
            bot_stats["errors_caught"] += 1
            return
        except ChannelPrivateError:
            await show_error(status_msg, "Target channel is private — bot has no access 💀")
            bot_stats["errors_caught"] += 1
            return
        except Exception as e:
            await show_error(status_msg, f"Target error: {html.escape(str(e)[:100])}")
            bot_stats["errors_caught"] += 1
            return

        await update_progress(0, limit, "📡 Fetching messages...")

        # Collect messages in batches
        offset_id = 0
        all_message_ids = []

        # First pass: collect message IDs
        async for message in client.iter_messages(
            source_entity,
            limit=limit if limit < 99999 else None,
        ):
            if message and message.id:
                all_message_ids.append(message.id)

        total_messages = len(all_message_ids)
        logger.info(f"Found {total_messages} messages in {source}")

        if total_messages == 0:
            await show_error(status_msg, "No messages found in source channel 😭")
            return

        await update_progress(0, total_messages, f"📦 Found {total_messages} messages!")
        await asyncio.sleep(1)

        # Process in batches of 100
        message_ids_reversed = list(reversed(all_message_ids))

        for batch_start in range(0, total_messages, batch_size):
            # Check if cancelled
            if context.user_data.get("forward_cancelled"):
                logger.info(f"Forwarding cancelled by user {user_id}")
                break

            batch_num += 1
            batch = message_ids_reversed[batch_start: batch_start + batch_size]

            await update_progress(
                forwarded,
                total_messages,
                f"🔄 Processing batch #{batch_num}...",
            )

            # Forward each message in batch
            for msg_id in batch:
                # Check cancelled again
                if context.user_data.get("forward_cancelled"):
                    break

                try:
                    await client.forward_messages(
                        entity=target_entity,
                        messages=msg_id,
                        from_peer=source_entity,
                    )
                    forwarded += 1
                    bot_stats["total_forwarded"] += 1

                    # Update progress every 10 messages
                    if forwarded % 10 == 0:
                        await update_progress(
                            forwarded,
                            total_messages,
                            f"⚡ Forwarding batch #{batch_num}...",
                        )

                    # Small delay between messages to avoid flood
                    await asyncio.sleep(0.3)

                except FloodWaitError as e:
                    wait_time = e.seconds
                    logger.warning(f"FloodWait: sleeping {wait_time}s")

                    for remaining in range(wait_time, 0, -5):
                        await update_progress(
                            forwarded,
                            total_messages,
                            f"⏳ FloodWait: {remaining}s remaining...",
                        )
                        await asyncio.sleep(min(5, remaining))

                except ChatAdminRequiredError:
                    await show_error(
                        status_msg,
                        "Bot needs admin rights in target channel! 💀"
                    )
                    bot_stats["errors_caught"] += 1
                    return

                except Exception as e:
                    failed += 1
                    bot_stats["errors_caught"] += 1
                    logger.warning(f"Forward error for msg {msg_id}: {e}")
                    await asyncio.sleep(0.5)

            # Batch complete - sleep between batches
            if batch_start + batch_size < total_messages:
                sleep_time = random.randint(5, 10)
                for remaining in range(sleep_time, 0, -1):
                    await update_progress(
                        forwarded,
                        total_messages,
                        f"😴 Batch #{batch_num} done! Next in {remaining}s...",
                    )
                    await asyncio.sleep(1)

        # ─── DONE! Show final result ─────────────────────────
        elapsed = time.monotonic() - start_time
        rate = forwarded / elapsed if elapsed > 0 else 0

        final_text = f"""
<pre>
╔══════════════════════════════════╗
║   ✅ MISSION COMPLETE! 💀       ║
╠══════════════════════════════════╣
║  {make_progress_bar(forwarded, total_messages):<32}║
╠══════════════════════════════════╣
║  ✅ Forwarded : {str(forwarded):<16} ║
║  ❌ Failed    : {str(failed):<16} ║
║  📦 Batches   : {str(batch_num):<16} ║
║  ⏱️  Time      : {f"{elapsed:.1f}s":<16} ║
║  ⚡ Speed     : {f"{rate:.1f} msg/s":<16} ║
╠══════════════════════════════════╣
║  🏆 STATUS : FULLY COMPLETE     ║
╚══════════════════════════════════╝
</pre>
🔥 <b>SLAY! we did it bestie 🫶🏻 {random_hacker_quote()}</b>
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 FORWARD AGAIN", callback_data="start_forward")],
            [InlineKeyboardButton("📊 VIEW STATS", callback_data="show_stats")],
            [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
        ])

        try:
            await status_msg.edit_text(
                final_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Final message edit error: {e}")

        logger.info(
            f"Forwarding complete: {forwarded}/{total_messages} messages "
            f"in {elapsed:.1f}s by user {user_id}"
        )

    except Exception as e:
        logger.error(f"Forward engine critical error: {e}", exc_info=True)
        bot_stats["errors_caught"] += 1
        await show_error(status_msg, f"Critical error: {html.escape(str(e)[:150])}")


async def show_error(status_msg, error_text: str):
    """Show styled error message."""
    error_display = f"""
<pre>
╔══════════════════════════════════╗
║   ⚠️  ERROR DETECTED 💀         ║
╠══════════════════════════════════╣
║  Status : OPERATION FAILED       ║
╚══════════════════════════════════╝
</pre>
❌ <b>bruh something went wrong fr:</b>

<code>{html.escape(error_text)}</code>

💡 <i>try again bestie, or check ur channel settings</i>
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 TRY AGAIN", callback_data="start_forward")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])

    try:
        await status_msg.edit_text(
            error_display,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Error display failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎛️ CALLBACK QUERY HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central callback query router."""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    await query.answer()

    logger.info(f"Callback: {data} from user {user_id}")

    try:
        if data == "verify_membership":
            is_member = await check_membership(user_id, context)
            if is_member:
                # Show boot sequence again
                await query.message.edit_text(
                    BOOT_FRAMES[4], parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(0.5)

                welcome = f"""
{MAIN_MENU_TEXT}
👤 <b>Welcome, <code>{html.escape(update.effective_user.first_name)}</code>!</b>
✅ <i>Membership verified! Access granted fr 💀</i>
"""
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
                        InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
                    ],
                    [
                        InlineKeyboardButton("📖 HELP", callback_data="show_help"),
                        InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
                    ],
                ])
                await query.message.edit_text(
                    welcome,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            else:
                await show_access_denied(update, context)

        elif data == "main_menu":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚡ FORWARD ENGINE", callback_data="start_forward"),
                    InlineKeyboardButton("📊 STATS", callback_data="show_stats"),
                ],
                [
                    InlineKeyboardButton("📖 HELP", callback_data="show_help"),
                    InlineKeyboardButton("🏓 PING", callback_data="do_ping"),
                ],
                [
                    InlineKeyboardButton(
                        "🔥 JOIN CHANNEL",
                        url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
                    ),
                ],
            ])
            await query.message.edit_text(
                MAIN_MENU_TEXT,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "show_stats":
            await show_stats_message(query.message.edit_text)

        elif data == "show_help":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 START FORWARDING", callback_data="start_forward")],
                [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
            ])
            await query.message.edit_text(
                HELP_TEXT,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "do_ping":
            start = time.monotonic()
            await query.message.edit_text(
                "🏓 <b>Calculating latency...</b>",
                parse_mode=ParseMode.HTML,
            )
            latency = (time.monotonic() - start) * 1000

            ping_text = f"""
<pre>
╔══════════════════════════════╗
║   🏓 PING RESULTS            ║
╠══════════════════════════════╣
║  Latency : {latency:.1f}ms           
║  Status  : {"🟢 EXCELLENT" if latency < 200 else "🟡 GOOD" if latency < 500 else "🔴 SLOW"}
║  Uptime  : {get_uptime()}   
╚══════════════════════════════╝
</pre>
💀 <b>still faster than ur ex texting back 😂</b>
"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
            ])
            await query.message.edit_text(
                ping_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        elif data == "start_forward":
            # Trigger forward conversation
            is_member = await check_membership(user_id, context)
            if not is_member:
                await show_access_denied(update, context)
                return

            context.user_data.clear()
            prompt_text = """
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 1/3 : SOURCE CHANNEL      ║
╚══════════════════════════════════╝
</pre>
🔥 <b>drop the SOURCE channel below 👇</b>

<i>Accepted formats:</i>
• <code>@channelname</code>
• <code>-100xxxxxxxxxx</code>
• <code>https://t.me/channelname</code>
"""
            await query.message.edit_text(
                prompt_text, parse_mode=ParseMode.HTML
            )
            # Store state in user_data for next message
            context.user_data["awaiting"] = "source"

    except Exception as e:
        logger.error(f"Callback handler error [{data}]: {e}", exc_info=True)
        bot_stats["errors_caught"] += 1
        try:
            await query.message.edit_text(
                f"⚠️ <b>Something went wrong fr:</b>\n<code>{html.escape(str(e)[:200])}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 GENERAL MESSAGE HANDLER (for conversation state via callbacks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages for conversation state from callbacks."""
    awaiting = context.user_data.get("awaiting")

    if not awaiting:
        # Default response for unhandled messages
        await update.message.reply_text(
            "💀 <b>use /start to boot up the ghost engine bestie</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    user_input = update.message.text.strip() if update.message.text else ""

    if awaiting == "source":
        source_input = user_input.replace("https://t.me/", "@")
        if source_input.startswith("t.me/"):
            source_input = "@" + source_input[5:]

        context.user_data["source"] = source_input
        context.user_data["awaiting"] = "target"

        prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 2/3 : TARGET CHANNEL      ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source_input[:20]+"..." if len(source_input)>20 else source_input):<20}║
╚══════════════════════════════════╝
</pre>
🎯 <b>now drop the TARGET channel 👇</b>
⚠️ <i>bot needs ADMIN in target channel!</i>
"""
        await update.message.reply_text(prompt_text, parse_mode=ParseMode.HTML)

    elif awaiting == "target":
        target_input = user_input.replace("https://t.me/", "@")
        if target_input.startswith("t.me/"):
            target_input = "@" + target_input[5:]

        context.user_data["target"] = target_input
        context.user_data["awaiting"] = "limit"

        source = context.user_data.get("source", "")
        prompt_text = f"""
<pre>
╔══════════════════════════════════╗
║   ⚡ GHOST FORWARD ENGINE 💀    ║
╠══════════════════════════════════╣
║  STEP 3/3 : MESSAGE LIMIT       ║
╠══════════════════════════════════╣
║  ✅ Source : {html.escape(source[:20]):<20}║
║  ✅ Target : {html.escape(target_input[:20]):<20}║
╚══════════════════════════════════╝
</pre>
🔢 <b>how many messages? (enter a number)</b>
"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("100", callback_data="cb_limit_100"),
                InlineKeyboardButton("500", callback_data="cb_limit_500"),
                InlineKeyboardButton("1000", callback_data="cb_limit_1000"),
            ],
        ])
        await update.message.reply_text(
            prompt_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )

    elif awaiting == "limit":
        try:
            limit = int(user_input)
            if limit <= 0:
                limit = 99999
            if limit > 50000:
                limit = 50000
        except ValueError:
            await update.message.reply_text(
                "⚠️ <b>that ain't a number bestie 💀</b> try again",
                parse_mode=ParseMode.HTML,
            )
            return

        context.user_data["limit"] = limit
        context.user_data["awaiting"] = None
        await show_confirmation_message(update, context)


async def show_confirmation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation via regular message."""
    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    limit = context.user_data.get("limit", 100)
    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
╚══════════════════════════════════╝
</pre>
💀 <b>ready to go full ghost mode? 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT!", callback_data="cb_confirm_forward"),
            InlineKeyboardButton("❌ ABORT", callback_data="cb_cancel"),
        ],
    ])
    await update.message.reply_text(
        confirm_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


async def handle_cb_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick limit selection callbacks from message flow."""
    query = update.callback_query
    await query.answer()
    data = query.data

    limit_map = {
        "cb_limit_100": 100,
        "cb_limit_500": 500,
        "cb_limit_1000": 1000,
    }

    limit = limit_map.get(data, 100)
    context.user_data["limit"] = limit
    context.user_data["awaiting"] = None

    source = context.user_data.get("source", "Unknown")
    target = context.user_data.get("target", "Unknown")
    batch_count = (limit // 100) + (1 if limit % 100 else 0)

    confirm_text = f"""
<pre>
╔══════════════════════════════════╗
║   🚀 MISSION BRIEFING 💀        ║
╠══════════════════════════════════╣
║  ✅ Source  : {html.escape(source[:18]):<18} ║
║  🎯 Target  : {html.escape(target[:18]):<18} ║
║  📦 Limit   : {str(limit):<18} ║
║  🔄 Batches : ~{str(batch_count)+" batches":<16} ║
╚══════════════════════════════════╝
</pre>
💀 <b>ready to go full ghost mode? 🔥</b>
"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 LAUNCH IT!", callback_data="cb_confirm_forward"),
            InlineKeyboardButton("❌ ABORT", callback_data="cb_cancel"),
        ],
    ])
    await query.message.edit_text(
        confirm_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


async def handle_cb_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forward confirmation from message flow."""
    query = update.callback_query
    await query.answer("🚀 Launching...")

    source = context.user_data.get("source")
    target = context.user_data.get("target")
    limit = context.user_data.get("limit", 100)
    user_id = update.effective_user.id

    if not source or not target:
        await query.message.edit_text(
            "⚠️ <b>Mission data lost! Use /forward to restart</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    bot_stats["total_sessions"] += 1

    launch_text = """
<pre>
╔══════════════════════════════════╗
║   🚀 GHOST ENGINE LAUNCHING...  ║
╠══════════════════════════════════╣
║  [▓░░░░░░░░░░░░░░░░]  5%        ║
║  Connecting to Telegram API...  ║
╚══════════════════════════════════╝
</pre>
⚡ <b>hold tight, we cooking rn 🔥</b>
"""
    try:
        status_msg = await query.message.edit_text(
            launch_text, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Launch message error: {e}")
        return

    asyncio.create_task(
        run_forward_engine(status_msg, source, target, limit, user_id, context)
    )


async def handle_cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel from message flow."""
    query = update.callback_query
    await query.answer("Cancelled!")
    context.user_data.clear()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")],
    ])
    await query.message.edit_text(
        "❌ <b>Mission aborted! bestie took the L 😂</b>\n<i>use /forward to try again</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ERROR HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler - bot must NEVER crash."""
    bot_stats["errors_caught"] += 1
    error = context.error

    logger.error(f"Global error handler caught: {error}", exc_info=True)

    # Specific error handling
    if isinstance(error, Forbidden):
        logger.warning("Bot was blocked by user or lacks permissions")
        return

    if isinstance(error, BadRequest):
        logger.warning(f"Bad request: {error}")
        return

    if isinstance(error, TelegramError):
        logger.warning(f"Telegram error: {error}")
        return

    # Try to notify user about unknown errors
    try:
        if update and hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(
                f"""
<pre>
╔══════════════════════════════╗
║  ⚠️  SYSTEM ERROR 💀         ║
╚══════════════════════════════╝
</pre>
❌ <b>something glitched fr:</b>
<code>{html.escape(str(error)[:200])}</code>

💡 <i>try /start to reset the system bestie</i>
""",
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.error(f"Error handler notification failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏗️ APPLICATION SETUP & MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_application() -> Application:
    """Build and configure the PTB application."""

    app = Application.builder().token(BOT_TOKEN).build()

    # ─── Conversation Handler for /forward ────────────────────
    forward_conv = ConversationHandler(
        entry_points=[
            CommandHandler("forward", cmd_forward),
        ],
        states={
            WAITING_SOURCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_source),
            ],
            WAITING_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target),
            ],
            WAITING_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_limit),
                CallbackQueryHandler(receive_limit_callback, pattern="^limit_"),
            ],
            CONFIRM_FORWARD: [
                CallbackQueryHandler(confirm_forward, pattern="^confirm_forward$"),
                CallbackQueryHandler(cancel_forward, pattern="^cancel_forward$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(cancel_forward, pattern="^cancel_forward$"),
        ],
        allow_reentry=True,
    )

    # ─── Register Handlers ─────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # Conversation handler
    app.add_handler(forward_conv)

    # Callback handlers for message-flow forwarding
    app.add_handler(
        CallbackQueryHandler(handle_cb_limit, pattern="^cb_limit_")
    )
    app.add_handler(
        CallbackQueryHandler(handle_cb_confirm, pattern="^cb_confirm_forward$")
    )
    app.add_handler(
        CallbackQueryHandler(handle_cb_cancel, pattern="^cb_cancel$")
    )

    # General callback handler
    app.add_handler(
        CallbackQueryHandler(handle_callbacks)
    )

    # General message handler
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Global error handler
    app.add_error_handler(error_handler)

    return app


async def startup_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║          💀 GHOST FORWARDER BOT v2.0 💀                      ║
║          Production Grade | Cyberpunk Style                  ║
╠══════════════════════════════════════════════════════════════╣
║  ⚡ Engine    : python-telegram-bot v20+ + Telethon          ║
║  🔐 Auth      : Environment Variables Only                   ║
║  🛡️  Security  : FloodWait Protection Enabled                ║
║  📦 Batching  : 100 msgs/batch with 5-10s sleep              ║
╠══════════════════════════════════════════════════════════════╣
║  📡 Status    : INITIALIZING...                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logger.info("Ghost Forwarder Bot starting up...")
    logger.info(f"Required channel: {REQUIRED_CHANNEL}")
    logger.info(f"Admin IDs: {ADMIN_IDS}")


def main():
    """Main entry point."""
    asyncio.get_event_loop().run_until_complete(startup_banner())

    app = build_application()

    logger.info("✅ Bot is online! Polling for updates...")
    print("\n💀 GHOST FORWARDER BOT IS ONLINE! SLAY MODE ACTIVATED 🔥\n")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()
