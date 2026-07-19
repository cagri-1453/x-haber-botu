import feedparser
import tweepy
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
import os

API_KEY = os.environ.get("xb3kHJ9fOiEoCNvBXfmVSrJL7")
API_SECRET = os.environ.get("Hf07yOy40fskGbH469l82VB6Xyh1E5SpAEHU2Cm2HQIswiqEhC")
ACCESS_TOKEN = os.environ.get("457483523-rbR3J7xwOJmsHALQWQAbxEJRbt0f0YzWv4kUkCFH")
ACCESS_TOKEN_SECRET = os.environ.get("ajHhAfl5UjRvUUFgc2wspsPsrtb6X0vl2GvpzUJe8hqPi")
TELEGRAM_BOT_TOKEN = os.environ.get("8867562678:AAEDfyaYaLdCvPWgSUM594DJdG9M1-iesiI")
YOUR_TELEGRAM_ID = os.environ.get("7512577586")

# --- TEST ADIMI: DEĞİŞKENLERİ LOGLAYALIM ---
print(f"DEBUG: API_KEY durumu: {API_KEY}")
print(f"DEBUG: API_SECRET durumu: {API_SECRET}")
print(f"DEBUG: TELEGRAM_BOT_TOKEN durumu: {TELEGRAM_BOT_TOKEN}")

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, TELEGRAM_BOT_TOKEN, YOUR_TELEGRAM_ID]):
    print("HATA: Aşağıdaki değişkenlerden biri veya birkaçı boş geldi:")
    print(f"API_KEY: {API_KEY}, API_SECRET: {API_SECRET}, ACCESS_TOKEN: {ACCESS_TOKEN}, ACCESS_TOKEN_SECRET: {ACCESS_TOKEN_SECRET}, TELEGRAM: {TELEGRAM_BOT_TOKEN}, ID: {YOUR_TELEGRAM_ID}")
    exit(1)
news_cache = {}

# --- TARAMA (X İLE İLETİŞİM YOK - SADECE RSS OKUR) ---
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

# --- TETİKLEMELİ PAYLAŞIM (X İLE İLETİŞİM SADECE BURADA) ---
async def button_click(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    news_id = data[2:]
    
    if data.startswith("p_"):
        item = news_cache.get(news_id)
        if item:
            try:
                # X bağlantısı sadece butona basıldığında kurulur
                client = tweepy.Client(
                    consumer_key=API_KEY,
                    consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN,
                    access_token_secret=ACCESS_TOKEN_SECRET
                )
                client.create_tweet(text=f"{item['title']}\n{item['link']}")
                await query.edit_message_text(text=f"✅ Tweetlendi: {item['title']}")
            except Exception as e:
                # 402 veya 403 hatalarını burada yakalıyoruz
                await query.edit_message_text(text=f"❌ X API Hatası: {str(e)}")
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
    
    # 6 saatte bir tarama yap
    application.job_queue.run_repeating(check_news, interval=21600, first=5)
    
    application.run_polling()
