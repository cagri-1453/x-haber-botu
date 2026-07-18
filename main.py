import os
import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

# Render Environment'tan bilgileri al
TELEGRAM_BOT_TOKEN = os.environ.get("8867562678:AAFEulJ8dGZs7NjBqSTHDFo5VCGZBzD9UQ8")
YOUR_TELEGRAM_ID = os.environ.get("7512577586")
API_KEY = os.environ.get("cn6zvjYROGLnKFOYgYWQo0GF4")
API_SECRET = os.environ.get("EryNYsgIu4P9Gl9RAWC04cB9L6cFbbI2yEqa9HND0qPP6rVJbb")
ACCESS_TOKEN = os.environ.get("457483523-hsBomhqHfpdqeWlJYiFOmBIjTjgOgvW8pN9FFevk")
ACCESS_TOKEN_SECRET = os.environ.get("xlc2xEb7HfmuyCnDkjUyhiREsCF0uNqXHFmfKjMN40nt0")

news_cache = {}

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
        keyboard = [
            [InlineKeyboardButton("✅ Paylaş", callback_data=f"p_{news_id}"),
             InlineKeyboardButton("❌ Sil", callback_data=f"s_{news_id}")]
        ]
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=f"{title}\n{link}", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_news(update, context):
    await check_news(context)

async def button_click(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    news_id = data[2:]
    
    if data.startswith("p_"):
        item = news_cache.get(news_id)
        if item:
            try:
                client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, 
                                       access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
            except Exception as e:
                await query.edit_message_text(text=f"❌ API Hatası: {str(e)}")
        else:
            await query.edit_message_text(text="❌ Haber hafızadan silinmiş.")
    elif data.startswith("s_"):
        await query.edit_message_text(text="❌ Haber silindi.")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # Flask sunucusunu başlat
    Thread(target=run_flask).start()
    
    # Telegram botunu oluştur ve başlat
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("haber", start_news))
    
    # İş zamanlayıcıyı başlat
    application.job_queue.run_repeating(check_news, interval=21600, first=5)
    
    # BOTA KOMUT GELMESİNİ ZORLA (Polling'i başlat)
    print("Bot dinlemeye başladı...")
    application.run_polling(drop_pending_updates=True)
