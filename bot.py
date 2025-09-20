import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Ambil token dari environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⚠️  Silakan set TELEGRAM_BOT_TOKEN di environment variables.")

# --- Fungsi Pembantu ---

def format_single_result(domain: str, result: dict) -> str:
    """Format hasil pengecekan satu domain."""
    if not result:
        return f"🌐 {domain}\n❌ Tidak dapat memeriksa domain ini.\n"

    blocked = result.get("blocked", False)
    status_icon = "🚫" if blocked else "✅"
    status_text = "Diblokir" if blocked else "Tidak Diblokir"
    return f"🌐 {domain}\n{status_icon} Status: {status_text}\n"

def format_bulk_results(domains: list, results: dict) -> str:
    """Format hasil pengecekan banyak domain."""
    output_lines = ["🤖 *Hasil Pengecekan Domain (Bulk)*\n"]
    
    success_count = 0
    blocked_count = 0
    error_domains = []

    for domain in domains:
        result = results.get(domain)
        if not result:
            error_domains.append(domain)
            output_lines.append(format_single_result(domain, {}))
        else:
            output_lines.append(format_single_result(domain, result))
            success_count += 1
            if result.get("blocked", False):
                blocked_count += 1

    # --- Ringkasan ---
    summary = f"\n📊 *Ringkasan:*\n"
    summary += f"✅ Berhasil: {success_count}\n"
    summary += f"🚫 Diblokir: {blocked_count}\n"
    if error_domains:
        summary += f"❌ Gagal: {len(error_domains)} ({', '.join(error_domains)})\n"
    
    output_lines.append(summary)
    return "\n".join(output_lines)

# --- Handler Bot ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *Halo! Selamat datang di Domain Status Checker Bot!*\n\n"
        "Saya dapat memeriksa apakah sebuah domain diblokir atau tidak.\n\n"
        "*Cara menggunakan:*\n"
        "🔹 Kirim satu domain: `example.com`\n"
        "🔹 Kirim banyak domain (pisahkan dengan koma): `google.com, yahoo.com, github.com`\n\n"
        "Perintah:\n"
        "/start - Mulai ulang bot\n"
        "/help - Bantuan penggunaan"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*❓ Bantuan Domain Status Checker*\n\n"
        "*Fitur:*\n"
        "• Cek status satu domain\n"
        "• Cek status banyak domain sekaligus\n\n"
        "*Cara Pakai:*\n"
        "1. Kirim satu domain:\n   `google.com`\n\n"
        "2. Kirim banyak domain (pisahkan dengan koma `,`):\n   `example.com, yahoo.com, github.com`\n\n"
        "*Catatan:*\n"
        "- Jangan gunakan spasi setelah koma.\n"
        "- Batas maksimal domain per permintaan adalah 10."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def check_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    if not user_input:
        await update.message.reply_text("❌ Silakan kirimkan nama domain yang ingin dicek.")
        return

    # --- Deteksi Bulk atau Single ---
    if ',' in user_input:
        # --- Mode Bulk ---
        domains_raw = [d.strip() for d in user_input.split(',')]
        # Batasi jumlah domain
        if len(domains_raw) > 10:
             await update.message.reply_text("⚠️ Maksimal 10 domain sekaligus. Silakan kurangi jumlah domain.")
             return
        domains = list(filter(None, domains_raw)) # Hapus string kosong
        if not domains:
            await update.message.reply_text("❌ Format tidak valid. Silakan kirim domain yang dipisahkan dengan koma (contoh: `example.com,google.com`).", parse_mode='Markdown')
            return
        is_bulk = True
    else:
        # --- Mode Single ---
        domains = [user_input]
        is_bulk = False

    try:
        # --- Panggil API Bulk ---
        domains_param = ",".join(domains)
        api_url = f"https://check.skiddle.id/?domains={domains_param}"
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        results_data = response.json()

        # --- Format Respons ---
        if is_bulk:
            formatted_response = format_bulk_results(domains, results_data)
        else:
            # Untuk single, tetap tampilkan format lama untuk konsistensi
            domain = domains[0]
            result = results_data.get(domain, {})
            if not result:
                 await update.message.reply_text(f"🌐 Domain: {domain}\n❌ Tidak dapat memeriksa domain ini.")
                 return
            blocked = result.get("blocked", False)
            status_icon = "🚫" if blocked else "✅"
            status_text = "Diblokir" if blocked else "Tidak Diblokir"
            formatted_response = f"🌐 Domain: {domain}\n{status_icon} Status: {status_text}"

        # Kirim respons
        await update.message.reply_text(formatted_response, parse_mode='Markdown')

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ Permintaan ke API terlalu lama. Silakan coba lagi.")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Gagal menghubungi API pengecekan domain.\nDetail: `{str(e)}`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat memproses permintaan.\nDetail: `{str(e)}`", parse_mode='Markdown')

# --- Setup dan Run Bot ---

if __name__ == "__main__":
    print("🚀 Bot Telegram sedang berjalan...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- Daftarkan Handler ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_domain))

    app.run_polling()
