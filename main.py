import feedparser
import tweepy
import logging
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

# --- AYARLAR ---
# Bu değerleri Render'daki Environment Variables kısmından çekmek en güvenlisidir, 
# ancak buraya da yazabilirsin.
API_KEY = "NGgoVkbGFu8lk0Cj5VtZqlp1T"
API_SECRET = "AyCz0m1dJV8ezV8khgygX7hBtvT6KKlnCZBvzQiJkOI6x1kjwI"
ACCESS_TOKEN = "457483523-BqOwnURjjUnt4DgkV1gLEhYvgLOsfoFVppXoFgj7"
ACCESS_TOKEN_SECRET = "AINT6GsCQa7Ti14Qi531Amxxz4mSRuOguWQGlhgGLx9yU"

TELEGRAM_BOT_TOKEN = "8867562678:AAFEulJ8dGZs7NjBqSTHDFo5VCGZBzD9UQ8" 
YOUR_TELEGRAM_ID = "7512577586" 

news_cache = {}

# --- HABER TARAMA (7/24 ÇALIŞIR, X İLE İLETİŞİME GEÇMEZ) ---
def get_latest_news():
    news_list = []
    urls = ["https://tr.investing.com/rss/news.rss", "https://www.kap.org.tr/tr/api/dis-kaynak/rss", "https://www.bloomberght.com/rss"]
    for url in urls:
        feed = feedparser.parse(url)
        for i, entry in enumerate(feed.entries[:2]):
            news_id = f"n_{i}_{url.split('/')[2]}"
            news_cache[news_id] = {'title': entry.title, 'link': entry.link}
            news_list.append((news_id, entry.title, entry.link))
    return news_list

async def check_news(context):
    news = get_latest_news()
    for news_id, title, link in news:
        keyboard = [[InlineKeyboardButton("✅ Paylaş", callback_data=f"p_{news_id}"),
                     InlineKeyboardButton("❌ Sil", callback_data=f"s_{news_id}")]]
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=f"{title}\n{link}", reply_markup=InlineKeyboardMarkup(keyboard))

# --- BUTON TETİKLEME (SADECE SEN BASINCA X İLE İLETİŞİME GEÇER) ---
async def button_click(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    news_id = data[2:]
    
    if data.startswith("p_"):
        item = news_cache.get(news_id)
        if item:
            try:
                # X (Twitter) Bağlantısı SADECE burada kuruluyor
                client = tweepy.Client(
                    consumer_key=API_KEY,
                    consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN,
                    access_token_secret=ACCESS_TOKEN_SECRET
                )
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Başarıyla Tweetlendi:\n{item['title']}")
            except Exception as e:
                await query.edit_message_text(text=f"❌ X API Hatası: {str(e)}")
        else:
            await query.edit_message_text(text="❌ Haber bulunamadı.")
    elif data.startswith("s_"):
        await query.edit_message_text(text="❌ İşlem iptal edildi.")

# --- WEB SUNUCU (RENDER İÇİN GEREKLİ) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # Web sunucusunu başlat
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Telegram Botunu başlat
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("haber", check_news))
    
    # 6 saatte bir tarama yap
    application.job_queue.run_repeating(check_news, interval=21600, first=5)
    
    application.run_polling()
