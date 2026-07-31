import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8996402477:AAEt8FF2NAnWNrTyIRwGgJJcWEZoJIn2u8c"  # Yahan apna BotFather se mila Token daalein
ADMIN_ID = 5785924075  # Aapki User ID set kar di hai!
# =======================================================

async def get_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sirf Admin jab koi bhi message/media bhejega tabhi ID milegi
    if update.effective_user.id == ADMIN_ID:
        chat_id = update.effective_chat.id
        msg_id = update.message.message_id
        
        reply_text = (
            f"✅ **Message Saved in Bot History!**\n\n"
            f"🆔 **CHAT_ID:** `{chat_id}`\n"
            f"📩 **MSG_ID:** `{msg_id}`\n\n"
            f"👉 Is MSG_ID ko yaad rakhna, hum direct welcome message me use karenge!"
        )
        await update.message.reply_text(reply_text, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_ids))
    print("ID Extractor Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
  
