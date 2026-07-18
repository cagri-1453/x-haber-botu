import os
import feedparser
import tweepy
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# Render Environment Variables (Kasa) üzerinden al
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = os.environ.get("YOUR_TELEGRAM_ID")

# X (Twitter) Client
client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Haber Kaynakları
RSS_URLS = [
    "https://tr.investing.com/rss/news.rss",
    "https://www.kap.org.tr/tr/api/dis-kaynak/rss",
    "https://www.bloomberght.com/rss"
]

# Haberleri Çekme
def get_latest_news():
    news_list = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news_list.append({'title': entry.title, 'link': entry.link})
    return news_list

# Haberleri gönder ve hafızaya al
async def check_news(context: ContextTypes.DEFAULT_TYPE):
    news = get_latest_news()
    for i, item in enumerate(news):
        # Buton verisini kısalt (sadece index)
        keyboard = [[InlineKeyboardButton("Tweetle", callback_data=f"tweet_{i}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, 
                                       text=f"{item['title']}\n{item['link']}", 
                                       reply_markup=reply_markup)
        # Haberi botun hafızasında (context) tut
        context.chat_data[f"haber_{i}"] = item

# Tweetleme işleyişi
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("tweet_"):
        idx = query.data.split("_")[1]
        item = context.chat_data.get(f"haber_{idx}")
        
        if item:
            tweet_text = f"{item['title']}\n\nDetaylar: {item['link']}"
            client.create_tweet(text=tweet_text)
            await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
        else:
            await query.edit_message_text(text="❌ Haber bulunamadı veya süre aşımı.")

# Flask (Render'ın portu açık tutması için)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"

def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # Flask'ı arkada başlat
    Thread(target=run_flask).start()
    
    # Botu başlat
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: c.bot.send_message(u.effective_chat.id, "Bot hazır!")))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # Haber kontrolü (her 10 dakikada bir)
    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=600, first=10)
    
    application.run_polling()
