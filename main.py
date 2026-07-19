import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
import os

# Kod içerisine anahtar YAZILMAZ, bu değişken isimleri Render panelindeki 'Key' kısmı ile eşleşir.
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = os.environ.get("YOUR_TELEGRAM_ID")

# --- HATA KONTROLÜ ---
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, TELEGRAM_BOT_TOKEN, YOUR_TELEGRAM_ID]):
    print("HATA: Ortam değişkenleri Render'da bulunamadı!")
    exit(1)

news_cache = {}

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
                    consumer_key=API_KEY,
                    consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN,
                    access_token_secret=ACCESS_TOKEN_SECRET
                )
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
            except Exception as e:
                error_msg = str(e)
                if "402" in error_msg:
                    await query.edit_message_text(text="❌ X API Hatası: Krediniz bitti. Twitter Developer portalından ödeme planınızı kontrol edin.")
                else:
                    await query.edit_message_text(text=f"❌ X API Hatası: {error_msg}")
        else:
            await query.edit_message_text(text="❌ Haber bulunamadı.")
    elif data.startswith("s_"):
        await query.edit_message_text(text="❌ İşlem iptal edildi.")

# --- WEB SUNUCU ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("haber", check_news))
    
    application.job_queue.run_repeating(check_news, interval=21600, first=5)
    application.run_polling()
