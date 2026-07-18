import os
import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# Sadece gerekli değişkenler
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = os.environ.get("YOUR_TELEGRAM_ID")

# Twitter API anahtarları (Sadece tweet fonksiyonu içinde kullanılacak)
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")

news_cache = {}

def get_latest_news():
    news_list = []
    urls = ["https://tr.investing.com/rss/news.rss", "https://www.kap.org.tr/tr/api/dis-kaynak/rss", "https://www.bloomberght.com/rss"]
    for url in urls:
        feed = feedparser.parse(url)
        for i, entry in enumerate(feed.entries[:2]):
            news_id = f"n_{url.split('/')[2]}_{i}"
            news_cache[news_id] = {'title': entry.title, 'link': entry.link}
            news_list.append((news_id, entry.title, entry.link))
    return news_list

async def check_news(context):
    news = get_latest_news() # Burası tamamen ücretsiz RSS sorgusu
    for news_id, title, link in news:
        keyboard = [
            [InlineKeyboardButton("✅ Paylaş", callback_data=f"p_{news_id}"),
             InlineKeyboardButton("❌ Sil", callback_data=f"s_{news_id}")]
        ]
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=f"{title}\n{link}", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update, context):
    query = update.callback_query
    data = query.data
    news_id = data[2:]
    
    if data.startswith("p_"): # PAYLAŞ - API KREDİSİ BURADA HARCANIR
        item = news_cache.get(news_id)
        if item:
            try:
                # API istemcisini burada kuruyoruz (Sadece paylaştığında)
                client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, 
                                       access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
            except Exception as e:
                await query.edit_message_text(text=f"❌ API Hatası: {str(e)}")
        else:
            await query.edit_message_text(text="❌ Haber hafızadan silinmiş.")
            
    elif data.startswith("s_"): # SİL - API KREDİSİ HARCANMAZ
        await query.edit_message_text(text="❌ Haber silindi.")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot haberleri getiriyor!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_click))
    # Buradaki interval (saniye) senin tercihine göre ayarlanabilir, RSS sorgusu ücretsizdir.
    application.job_queue.run_repeating(check_news, interval=3600, first=10) 
    application.run_polling()
