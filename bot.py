import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Render Port Keep-Alive Web Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8996402477:AAEXpsC0GrRVlJnnw5CRcuWHGLoibrEgRdw"
# =======================================================

async def get_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.effective_chat.id
        msg_id = update.message.message_id
        
        reply_text = (
            f"✅ **Message ID Extracted!**\n\n"
            f"🆔 **CHAT_ID:** `{chat_id}`\n"
            f"📩 **MSG_ID:** `{msg_id}`"
        )
        await update.message.reply_text(reply_text, parse_mode="Markdown")

def main():
    # Background me web server start hoga Render ke liye
    Thread(target=run_web_server, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_ids))
    print("Bot is active and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
