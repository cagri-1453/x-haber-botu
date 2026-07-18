import os
import feedparser
import tweepy
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# Değişkenleri al
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = os.environ.get("YOUR_TELEGRAM_ID")

client = tweepy.Client(
    consumer_key=API_KEY, consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
)

# Haberleri geçici olarak tutacak sözlük
news_cache = {}

def get_latest_news():
    news_list = []
    for url in ["https://tr.investing.com/rss/news.rss", "https://www.kap.org.tr/tr/api/dis-kaynak/rss", "https://www.bloomberght.com/rss"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news_list.append({'title': entry.title, 'link': entry.link})
    return news_list

async def check_news(context: ContextTypes.DEFAULT_TYPE):
    news = get_latest_news()
    for i, item in enumerate(news):
        news_id = f"news_{i}"
        news_cache[news_id] = item # Haberi sözlüğe kaydet
        
        # Sadece ID gönderiyoruz (Limit sorunu bitti)
        keyboard = [[InlineKeyboardButton("Tweetle", callback_data=news_id)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=f"{item['title']}\n{item['link']}", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    news_id = query.data
    item = news_cache.get(news_id)
    
    if item:
        try:
            tweet_text = f"{item['title']}\n\nDetaylar: {item['link']}"
            client.create_tweet(text=tweet_text[:280]) # Twitter 280 karakter sınırı
            await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
        except Exception as e:
            await query.edit_message_text(text=f"❌ Hata: {str(e)}")
    else:
        await query.edit_message_text(text="❌ Haber hafızadan silinmiş.")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: c.bot.send_message(u.effective_chat.id, "Bot hazır!")))
    application.add_handler(CallbackQueryHandler(button_click))
    application.job_queue.run_repeating(check_news, interval=600, first=10)
    application.run_polling()
