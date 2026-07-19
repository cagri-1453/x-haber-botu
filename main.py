import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
import os
import requests
import time
import logging

# --- LOG AYARLARI ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- AYARLAR ---
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = os.environ.get("YOUR_TELEGRAM_ID")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") # Render'ın otomatik atadığı URL

# --- KONTROL ---
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, TELEGRAM_BOT_TOKEN, YOUR_TELEGRAM_ID]):
    print("HATA: Ortam değişkenleri eksik!")
    exit(1)

news_cache = {}

# --- KENDİNİ UYANDIRMA (KEEP ALIVE) ---
def keep_alive():
    while True:
        try:
            if RENDER_URL:
                requests.get(RENDER_URL)
        except:
            pass
        time.sleep(300) # 5 dakikada bir ping at

# --- TARAMA ---
def get_latest_news():
    news_list = []
    urls = ["https://tr.investing.com/rss/news.rss", "https://www.kap.org.tr/tr/api/dis-kaynak/rss", "https://www.bloomberght.com/rss"]
    for url in urls:
        feed = feedparser.parse(url)
        for i, entry in enumerate(feed.entries[:2]):
            news_id = f"n_{i}_{url.split('/')[2].replace('.', '_')}"
            news_cache[news_id] = {'title': entry.title, 'link': entry.link}
            news_list.append((news_id, entry.title, entry.link))
    return news_list

async def check_news(update_or_context, context=None):
    # Komut gelirse update, JobQueue gelirse context üzerinden işlem yap
    ctx = context if context else update_or_context
    news = get_latest_news()
    for news_id, title, link in news:
        keyboard = [[InlineKeyboardButton("✅ Paylaş", callback_data=f"p_{news_id}"),
                     InlineKeyboardButton("❌ Sil", callback_data=f"s_{news_id}")]]
        await ctx.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=f"{title}\n{link}", reply_markup=InlineKeyboardMarkup(keyboard))

# --- PAYLAŞIM ---
async def button_click(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    news_id = data[2:]
    
    if data.startswith("p_"):
        item = news_cache.get(news_id)
        if item:
            try:
                client = tweepy.Client(
                    consumer_key=API_KEY, consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
                )
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
            except Exception as e:
                error_msg = str(e)
                if "402" in error_msg or "403" in error_msg:
                    await query.edit_message_text(text="❌ X API Hatası: Krediniz bitti. Ödeme planınızı kontrol edin.")
                else:
                    await query.edit_message_text(text=f"❌ X API Hatası: {error_msg}")
        else:
            await query.edit_message_text(text="❌ Haber bulunamadı veya süre aşımı oldu.")
    elif data.startswith("s_"):
        await query.edit_message_text(text="❌ İşlem iptal edildi.")

# --- WEB SUNUCU ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot 7/24 Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    # Flask sunucusunu başlat
    Thread(target=run_flask, daemon=True).start()
    # Keep alive döngüsünü başlat
    Thread(target=keep_alive, daemon=True).start()
    
    # Telegram botunu başlat
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("haber", check_news))
    
    # 6 saatte bir (21600 sn) otomatik kontrol
    application.job_queue.run_repeating(check_news, interval=21600, first=5)
    application.run_polling()
