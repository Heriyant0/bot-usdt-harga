from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
import requests
import os
from datetime import datetime

# ============ KONFIGURASI ============
PORT = int(os.environ.get("PORT", 8443))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# ============ FUNGSI AMBIL HARGA ============

def get_indodax():
    try:
        r = requests.get("https://indodax.com/api/ticker/usdtidr", timeout=10)
        return float(r.json()['ticker']['last'])
    except:
        return None

def get_tokocrypto():
    try:
        r = requests.get(
            "https://api.tokocrypto.com/api/v3/ticker/price",
            params={"symbol": "USDTIDR"}, timeout=10
        )
        return float(r.json()['price'])
    except:
        return None

def get_binance_p2p():
    try:
        r = requests.post(
            "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
            json={"asset":"USDT","fiat":"IDR","page":1,"rows":5,"tradeType":"BUY"},
            timeout=10
        )
        return float(r.json()['data'][0]['adv']['price'])
    except:
        return None

def get_okx_p2p():
    try:
        r = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "USDT-IDR"}, timeout=10
        )
        return float(r.json()['data'][0]['last'])
    except:
        return None

def get_bybit_p2p():
    try:
        r = requests.post(
            "https://api2.bybit.com/fiat/otc/item/online",
            json={
                "userId": "",
                "tokenId": "USDT",
                "currencyId": "IDR",
                "payment": [],
                "side": "1",
                "size": "10",
                "page": "1"
            },
            timeout=10
        )
        return float(r.json()['result']['items'][0]['price'])
    except:
        return None

# ============ FUNGSI FORMAT PESAN ============

def format_pesan(judul, data_harga):
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pesan = f"💰 *{judul}*\n_{waktu}_\n\n"
    
    valid_prices = []
    for platform, harga in data_harga.items():
        if harga:
            pesan += f"• {platform}: `Rp {harga:,.0f}`\n"
            valid_prices.append(harga)
        else:
            pesan += f"• {platform}: ❌ Tidak tersedia\n"
    
    if len(valid_prices) >= 2:
        min_p = min(valid_prices)
        max_p = max(valid_prices)
        spread = max_p - min_p
        spread_pct = (spread / min_p) * 100
        pesan += f"\n📊 *Spread:* Rp {spread:,.0f} ({spread_pct:.2f}%)"
    
    return pesan

# ============ KEYBOARD MENU ============

def menu_utama():
    keyboard = [
        [InlineKeyboardButton("🏠 Exchange Lokal", callback_data="menu_lokal")],
        [InlineKeyboardButton("🌏 Exchange Global", callback_data="menu_global")],
        [InlineKeyboardButton("📊 Semua Harga", callback_data="menu_semua")],
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_kembali():
    keyboard = [
        [InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="menu_utama")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============ HANDLER ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "👋 *Selamat datang di Bot Pemantau Harga USDT/IDR!*\n\n"
        "Saya bisa membantu kamu memantau harga USDT dari berbagai exchange.\n\n"
        "Pilih menu di bawah ini:"
    )
    await update.message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=menu_utama()
    )

async def tombol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_utama":
        pesan = "👋 *Menu Utama*\n\nPilih menu di bawah ini:"
        await query.edit_message_text(
            pesan,
            parse_mode="Markdown",
            reply_markup=menu_utama()
        )
    
    elif data == "menu_lokal":
        await query.edit_message_text("⏳ Mengambil harga dari exchange lokal...")
        
        hasil = {
            "Indodax": get_indodax(),
            "Tokocrypto": get_tokocrypto(),
        }
        
        pesan = format_pesan("🏠 Harga USDT - Exchange Lokal", hasil)
        
        await query.edit_message_text(
            pesan,
            parse_mode="Markdown",
            reply_markup=menu_kembali()
        )
    
    elif data == "menu_global":
        await query.edit_message_text("⏳ Mengambil harga dari exchange global...")
        
        hasil = {
            "Binance P2P": get_binance_p2p(),
            "OKX P2P": get_okx_p2p(),
            "Bybit P2P": get_bybit_p2p(),
        }
        
        pesan = format_pesan("🌏 Harga USDT - Exchange Global (P2P)", hasil)
        
        await query.edit_message_text(
            pesan,
            parse_mode="Markdown",
            reply_markup=menu_kembali()
        )
    
    elif data == "menu_semua":
        await query.edit_message_text("⏳ Mengambil semua harga...")
        
        hasil = {
            "Indodax": get_indodax(),
            "Tokocrypto": get_tokocrypto(),
            "Binance P2P": get_binance_p2p(),
            "OKX P2P": get_okx_p2p(),
            "Bybit P2P": get_bybit_p2p(),
        }
        
        pesan = format_pesan("📊 Semua Harga USDT/IDR", hasil)
        
        await query.edit_message_text(
            pesan,
            parse_mode="Markdown",
            reply_markup=menu_kembali()
        )

async def cek_harga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pilih menu:",
        reply_markup=menu_utama()
    )

# ============ MAIN ============

def main():
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN belum di-set!")
        return
    
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("harga", cek_harga_command))
    app.add_handler(CallbackQueryHandler(tombol_handler))
    
    if RENDER_EXTERNAL_URL:
        print(f"Running in webhook mode at {RENDER_EXTERNAL_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}"
        )
    else:
        print("Running in polling mode...")
        app.run_polling()

if __name__ == "__main__":
    main()
