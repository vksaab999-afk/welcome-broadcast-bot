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
BOT_TOKEN = "8996402477:AAEK_pRrL1w8MXyuJXY4y7QInnNfiTlJOaw" 
ADMIN_CHAT_ID = 5785924075

# MongoDB Atlas URI
MONGO_URI = "mongodb+srv://kiroriwalsaab76_db_user:Vijay786482@cluster0.5isln6k.mongodb.net/?appName=Cluster0"

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

# --- KEEP-ALIVE WEB SERVER ---
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
        welcome_text = (
            f"Welcome {first_name} ❤️‍🔥\n\n"
            f"Yrr aapne colour trading me aaj tak kitna bhi loss kia ho no problem sab recover ho jayega\n\n"
            f"100%\n\n"
            f"Niche ka video pura dekho or paisa chapo💸\n"
            f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
        )
        await context.bot.send_message(chat_id=user_id, text=welcome_text)

        keyboard = [
            [InlineKeyboardButton("Download Vip Hack 📥", callback_data="download_hack")],
            [InlineKeyboardButton("Registration Link 🔗", url=REGISTRATION_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Doosra message (Tutorial Video + Buttons) jo bheja ja raha hai
        sent_video_msg = await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=VIDEO_MSG_ID,
            reply_markup=reply_markup
        )

        # Sirf is doosre video wale message ko turant automatic pin karna
        try:
            await context.bot.pin_chat_message(
                chat_id=user_id,
                message_id=sent_video_msg.message_id
            )
        except Exception as pin_err:
            logging.error(f"Could not pin message for user {user_id}: {pin_err}")

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
    
    # User ko database me save karna
    save_user_to_mongo(user.id, user.first_name, user.username)
    
    # Welcome content bhejna aur video wale message ko pin karna
    await send_welcome_content(context, user.id, user.first_name)
    
    try:
        await request.approve()
    except Exception:
        pass

# --- MAIN FUNCTION (Bot Setup & Starting Server) ---
def main():
    # Web server thread start kar rahe hain Render ke liye
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    # Telegram Application Build
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers add karna
    application.add_handler(ChatJoinRequestHandler(handle_join_request))

    # Bot Start karo
    logging.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
