import os
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
# Telegram BotFather se NAYA Valid Token yahan daalo
BOT_TOKEN = "8996402477:AAEK_pRrL1w8MXyuJXY4y7QInnNfiTlJOaw" 
ADMIN_CHAT_ID = 5785924075

# MongoDB Atlas URI
MONGO_URI = "mongodb+srv://kiror1walsaab76_db_user:2pv87iabNqubraPX@cluster0.5isln6k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Source Chat & Message IDs
SOURCE_CHAT_ID = 5785924075
WELCOME_MSG_ID = 31      # Text Welcome
VIDEO_MSG_ID = 33        # Tutorial Video
AUDIO_MSG_ID = 35        # Audio Note
APK_MSG_ID = 37          # VIP Hack File

REGISTRATION_LINK = "https://6club77.com/#/register?invitationCode=134575773989"
# =======================================================

# --- MONGODB SETUP ---
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot_db"]
users_collection = db["users"]

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

# --- KEEP-ALIVE WEB SERVER FOR RENDER & UPTIMEROBOT ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Live and MongoDB Connected!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- WELCOME MESSAGES SENDER FUNCTION ---
async def send_welcome_content(context: ContextTypes.DEFAULT_TYPE, user_id: int, first_name: str):
    try:
        # 1. Welcome Text with Name
        welcome_text = (
            f"Welcome {first_name}  ❤️‍🔥\n\n"
            f"Yrr aapne colour trading me aaj tak kitna bhi loss kia ho no problem sab recover ho jayega\n\n"
            f"100%\n\n"
            f"Niche ka video pura dekho or paisa chapo 💸\n"
            f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
        )
        await context.bot.send_message(chat_id=user_id, text=welcome_text)

        # 2. Video Post with Buttons
        keyboard = [
            [InlineKeyboardButton("Download Vip Hack 📥", callback_data="download_hack")],
            [InlineKeyboardButton("Registration Link 🔗", url=REGISTRATION_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=VIDEO_MSG_ID,
            reply_markup=reply_markup
        )

        # 3. Audio Post
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
    
    # 1. Save user details to MongoDB
    save_user_to_mongo(user.id, user.first_name, user.username)

    # 2. Send Welcome Content in DM immediately
    await send_welcome_content(context, user.id, user.first_name)

# --- START COMMAND (Fallback) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    await send_welcome_content(context, user.id, user.first_name)

# --- BUTTON HANDLER FOR VIP HACK FILE ---
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download_hack":
        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=APK_MSG_ID
        )

# --- DIRECT ADMIN BROADCAST HANDLER (FIXED) ---
async def admin_auto_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only Admin can trigger this
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    msg = update.message

    # Skip if it's a command
    if msg.text and msg.text.startswith("/"):
        return

    users = list(users_collection.find({}, {"user_id": 1}))
    total_users = len(users)
    
    if total_users == 0:
        await msg.reply_text("⚠️ **Database me abhi koi user nahi hai.**", parse_mode="Markdown")
        return

    status_msg = await msg.reply_text(f"🚀 **Broadcasting to {total_users} users...**", parse_mode="Markdown")
    
    success_count = 0
    failed_count = 0

    for user in users:
        u_id = user["user_id"]
        try:
            # Fixed: Properly copying message from Admin chat to each user
            await context.bot.copy_message(
                chat_id=u_id,
                from_chat_id=ADMIN_CHAT_ID,
                message_id=msg.message_id
            )
            success_count += 1
            await asyncio.sleep(0.05)  # Telegram Rate Limit protection
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to send broadcast to {u_id}: {e}")

    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"✔️ Delivered: `{success_count}`\n"
        f"❌ Failed: `{failed_count}`",
        parse_mode="Markdown"
    )

# --- ADMIN STATS COMMAND ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_CHAT_ID:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 **Total Registered Users in MongoDB:** `{total_users}`", parse_mode="Markdown")

def main():
    # Start Keep-Alive Web Server Thread
    Thread(target=run_web_server, daemon=True).start()

    # Asyncio Event Loop Fix
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Telegram Bot App
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    # Direct Auto Broadcast Handler for Admin
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, admin_auto_broadcast))

    print("Bot is running...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
        
