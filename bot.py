import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Ambil token dari environment variable Railway
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⚠️  Silakan set TELEGRAM_BOT_TOKEN di Railway environment variables.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Halo! Kirimkan nama domain untuk dicek statusnya.\nContoh: google.com")

async def check_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    domain = update.message.text.strip()
    
    if not domain:
        await update.message.reply_text("❌ Silakan kirimkan nama domain yang ingin dicek.")
        return

    try:
        response = requests.get(f"https://check.skiddle.id/?domain={domain}", timeout=10)
        response.raise_for_status()
        data = response.json()
        result = data.get(domain, {})
        blocked = result.get("blocked", False)
        
        status = "🚫 Diblokir" if blocked else "✅ Tidak Diblokir"
        await update.message.reply_text(f"🌐 Domain: {domain}\n📊 Status: {status}")
    except requests.exceptions.RequestException:
        await update.message.reply_text("❌ Gagal menghubungi API pengecekan domain.")
    except Exception as e:
        await update.message.reply_text("❌ Terjadi kesalahan saat memeriksa domain.")

# Setup bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_domain))

# Jalankan bot
if __name__ == "__main__":
    print("🚀 Bot Telegram sedang berjalan...")
    app.run_polling()
