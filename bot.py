import os
from dotenv import load_dotenv
import logging
import asyncio
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
load_dotenv()

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(level=logging.INFO)

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))

# MongoDB Atlas URI: keep credentials out of source control.
MONGO_URI = os.environ.get("MONGO_URI", "")

# Source Chat & Message IDs
SOURCE_CHAT_ID = 5785924075
WELCOME_MSG_ID = 31      # Text Welcome
VIDEO_MSG_ID = 33        # Tutorial Video
AUDIO_MSG_ID = 35        # Audio Note
APK_MSG_ID = 37          # VIP Hack File

TEST_BUTTON_URL = os.environ.get("TEST_BUTTON_URL", "https://6club77.com/#/register?invitationCode=134575773989")
REGISTRATION_LINK = os.environ.get("REGISTRATION_LINK", TEST_BUTTON_URL)

# Test mode: all four buttons intentionally use the same destination.
VIP_CHANNEL_URL = os.environ.get("VIP_CHANNEL_URL", TEST_BUTTON_URL)
FREE_GIFTCODE_URL = os.environ.get("FREE_GIFTCODE_URL", TEST_BUTTON_URL)
PROFIT_TOOL_URL = os.environ.get("PROFIT_TOOL_URL", TEST_BUTTON_URL)

# Two supplied custom emoji IDs, alternating across the four buttons.
EMOJI_JOIN = os.environ.get("EMOJI_JOIN", "5271604874419647061")
EMOJI_TOOL = os.environ.get("EMOJI_TOOL", "5255934767844567828")
# =======================================================

# --- MONGODB SETUP ---
mongo_client = MongoClient(MONGO_URI) if MONGO_URI else None
db = mongo_client["telegram_bot_db"] if mongo_client is not None else None
users_collection = db["users"] if db is not None else None

def styled_button(text, *, style, icon_custom_emoji_id=None, url=None, callback_data=None):
    """Build a Bot API 9.4 styled button with a graceful older-PTB fallback.

    `style` is one of primary/success/danger. Custom emoji IDs are optional.
    The fallback keeps ordinary buttons working if python-telegram-bot is older
    than the Bot API fields.
    """
    action = {"url": url} if url else {"callback_data": callback_data or "noop"}
    modern = {"text": text, **action, "style": style}
    if icon_custom_emoji_id:
        modern["icon_custom_emoji_id"] = icon_custom_emoji_id

    try:
        return InlineKeyboardButton(**modern)
    except TypeError:
        # Recent PTB releases may expose new Bot API fields through api_kwargs.
        api_kwargs = {"style": style}
        if icon_custom_emoji_id:
            api_kwargs["icon_custom_emoji_id"] = icon_custom_emoji_id
        try:
            return InlineKeyboardButton(text=text, api_kwargs=api_kwargs, **action)
        except TypeError:
            logging.warning("PTB does not support styled buttons; using plain fallback")
            return InlineKeyboardButton(text=text, **action)


def build_welcome_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("JOIN VIP CHANNEL", style="primary", icon_custom_emoji_id=EMOJI_JOIN,
                       url=VIP_CHANNEL_URL or None, callback_data="vip_channel")],
        [styled_button("GET NUMBER SURESHOT", style="success", icon_custom_emoji_id=EMOJI_SURESHOT,
                       url=TEST_BUTTON_URL)],
        [styled_button("FREE GIFTCODE", style="primary", icon_custom_emoji_id=EMOJI_GIFT,
                       url=FREE_GIFTCODE_URL or None, callback_data="free_giftcode")],
        [styled_button("GET PROFIT TOOL APK", style="danger", icon_custom_emoji_id=EMOJI_TOOL,
                       url=PROFIT_TOOL_URL or TEST_BUTTON_URL)],
    ])


def save_user_to_mongo(user_id, first_name, username):
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "first_name": first_name,
                    "username": username
                }
            },
            upsert=True
        )
    except Exception as e:
        logging.error(f"MongoDB Error: {e}")

# --- KEEP-ALIVE WEB SERVER (FIXED FOR UPTIMEROBOT 501 ERROR) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Live and MongoDB Connected!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- WELCOME MESSAGES SENDER FUNCTION ---
async def send_welcome_content(context: ContextTypes.DEFAULT_TYPE, user_id: int, first_name: str):
    try:
        welcome_text = (
            f"Welcome {first_name} ❤️‍🔥\n\n"
            f"Yrr aapne colour trading me aaj tak kitna bhi loss kia ho no problem sab recover ho jayega\n\n"
            f"100%\n\n"
            f"Niche ka video pura dekho or paisa chapo💸\n"
            f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
        )
        await context.bot.send_message(chat_id=user_id, text=welcome_text)

        reply_markup = build_welcome_keyboard()

        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=VIDEO_MSG_ID,
            reply_markup=reply_markup
        )

        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=AUDIO_MSG_ID
        )
    except Exception as e:
        logging.error(f"Could not send welcome content to user {user_id}: {e}")

# --- JOIN REQUEST HANDLER ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    await send_welcome_content(context, user.id, user.first_name)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    await send_welcome_content(context, user.id, user.first_name)

# --- BUTTON HANDLER ---
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in {"download_hack", "free_giftcode"}:
        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=APK_MSG_ID
        )
    elif query.data == "vip_channel":
        await query.message.reply_text("VIP channel link is not configured yet.")

# --- BULLET-PROOF BROADCAST LOGIC (FOR 50k+ USERS) ---
async def execute_broadcast(message_to_broadcast, context, admin_chat_id):
    users = list(users_collection.find({}, {"user_id": 1}))
    total_users = len(users)

    if total_users == 0:
        await context.bot.send_message(chat_id=admin_chat_id, text="⚠️ Database me koi user nahi hai!")
        return

    success = 0
    failed = 0

    progress_msg = await context.bot.send_message(
        chat_id=admin_chat_id, 
        text=f"🚀 **Broadcast Started!**\nTotal Users: `{total_users}`\nPlease wait..."
    )

    for index, u in enumerate(users):
        u_id = u["user_id"]
        try:
            if message_to_broadcast.text:
                await context.bot.send_message(chat_id=u_id, text=message_to_broadcast.text, entities=message_to_broadcast.entities)
            elif message_to_broadcast.photo:
                await context.bot.send_photo(chat_id=u_id, photo=message_to_broadcast.photo[-1].file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.video:
                await context.bot.send_video(chat_id=u_id, video=message_to_broadcast.video.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.audio:
                await context.bot.send_audio(chat_id=u_id, audio=message_to_broadcast.audio.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.voice:
                await context.bot.send_voice(chat_id=u_id, voice=message_to_broadcast.voice.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.document:
                await context.bot.send_document(chat_id=u_id, document=message_to_broadcast.document.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            
            success += 1
        except Exception as e:
            failed += 1
            logging.error(f"Error sending to {u_id}: {e}")

        # Telegram limit protect karne ke liye delay (Har 30 messages ke baad thoda extra rest taaki FloodWait na aaye)
        await asyncio.sleep(0.05)
        if index > 0 and index % 30 == 0:
            await asyncio.sleep(1.0)

    try:
        await context.bot.edit_message_text(
            chat_id=admin_chat_id, 
            message_id=progress_msg.message_id,
            text=f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", 
            parse_mode="Markdown"
        )
    except:
        await context.bot.send_message(
            chat_id=admin_chat_id, 
            text=f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", 
            parse_mode="Markdown"
        )

# --- 1. DIRECT AUTOMATIC BROADCAST ---
async def auto_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    if msg.text and msg.text.startswith("/"):
        return
    await execute_broadcast(msg, context, ADMIN_CHAT_ID)

# --- 2. COMMAND BASED BROADCAST ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if msg.reply_to_message:
        await execute_broadcast(msg.reply_to_message, context, ADMIN_CHAT_ID)
    else:
        text_after_command = msg.text.replace("/broadcast", "").strip()
        if text_after_command:
            users = list(users_collection.find({}, {"user_id": 1}))
            total_users = len(users)
            success = 0
            failed = 0
            
            progress_msg = await msg.reply_text(f"🚀 Broadcast started for {total_users} users...")
            
            for index, u in enumerate(users):
                try:
                    await context.bot.send_message(chat_id=u["user_id"], text=text_after_command)
                    success += 1
                except:
                    failed += 1
                await asyncio.sleep(0.05)
                if index > 0 and index % 30 == 0:
                    await asyncio.sleep(1.0)
                    
            await progress_msg.edit_text(f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", parse_mode="Markdown")
        else:
            await msg.reply_text("⚠️ Kripya message ke sath /broadcast likhein ya kisi message par reply karke /broadcast bhejein.")

# --- STATS COMMAND ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_CHAT_ID:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 **Total Users:** `{total_users}`", parse_mode="Markdown")

def main():
    if not BOT_TOKEN or not MONGO_URI or not ADMIN_CHAT_ID or users_collection is None:
        raise RuntimeError("Set BOT_TOKEN, MONGO_URI, and ADMIN_CHAT_ID environment variables")
    Thread(target=run_web_server, daemon=True).start()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    # Direct Message Handler
    app.add_handler(MessageHandler(filters.Chat(ADMIN_CHAT_ID) & ~filters.COMMAND, auto_broadcast))

    print("Bot is running...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
