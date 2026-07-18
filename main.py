import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

# --- TOKENLAR ---
TELEGRAM_BOT_TOKEN = "8867562678:AAFEulJ8dGZs7NjBqSTHDFo5VCGZBzD9UQ8" # Telegram Token
YOUR_TELEGRAM_ID = "7512577586"    # Telegram ID
# Twitter OAuth 2.0 Bilgileri
CLIENT_ID = "cGpuVUFOTDVXRTExclF1ZTZpNWs6MTpjaQ"           # Twitter Client ID
CLIENT_SECRET = "u_I621Icn-9XVRWQHbKU53Oo9QPbRBy_4XtCJRuzpZWa99F-Jt"       # Twitter Client Secret
ACCESS_TOKEN = "c200and4LWVCN1JOWWFVczRqQU1pSVRSUmpKdkhKOVZNbUZDY2lHVF9KeXJjOjE3ODQ0MTU0NzI0MzI6MToxOmF0OjE"        # Oluşturduğun OAuth 2.0 Access Token
REFRESH_TOKEN = "MWk3aEx4dURBR3MxaUpvbXMycFFGX2x6YnBncUE3UVVkOFctemJPUWR4d3Q3OjE3ODQ0MTU0NzI0MzI6MToxOnJ0OjE"       # Oluşturduğun OAuth 2.0 Refresh Token

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
        if YOUR_TELEGRAM_ID:
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
                # OAuth 2.0 ile Client başlatma
                client = tweepy.Client(
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                    access_token=ACCESS_TOKEN,
                    access_token_secret=REFRESH_TOKEN,
                    wait_on_rate_limit=True
                )
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
    print("--- BOT BAŞLATILIYOR ---")
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    if TELEGRAM_BOT_TOKEN:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(CommandHandler("haber", start_news))
        application.job_queue.run_repeating(check_news, interval=21600, first=5)
        
        print("--- POLLİNG BAŞLIYOR ---")
        application.run_polling()
    else:
        print("HATA: Token eksik, bot başlatılamadı.")
