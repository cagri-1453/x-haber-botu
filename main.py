import feedparser
import tweepy
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import config

# X (Twitter) API Kurulumu
auth = tweepy.OAuthHandler(config.API_KEY, config.API_SECRET)
auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=config.API_KEY,
    consumer_secret=config.API_SECRET,
    access_token=config.ACCESS_TOKEN,
    access_token_secret=config.ACCESS_TOKEN_SECRET
)

# Haber Kaynakları Listesi
RSS_URLS = [
    "https://tr.investing.com/rss/news.rss",
    "https://www.kap.org.tr/tr/api/dis-kaynak/rss",
    "https://www.bloomberght.com/rss"
]

# Haberleri çekme fonksiyonu
def get_latest_news():
    news_list = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # Her kaynaktan son 3 haber
            news_list.append({'title': entry.title, 'link': entry.link})
    return news_list

# Telegram Başlangıç
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot aktif! Haberler izleniyor...")

# Haberleri Telegram'a gönder ve buton ekle
async def # Haberleri Telegram'a gönder
async def check_news(context: ContextTypes.DEFAULT_TYPE):
    news = get_latest_news()
    for i, item in enumerate(news):
        # Sadece indeks gönderiyoruz, metinler kodun içinde eşleşecek
        keyboard = [[InlineKeyboardButton("Tweetle", callback_data=f"tweet_{i}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Haberleri bir listeye kaydedip sonra erişmemiz lazım (Şimdilik başlığı gönderiyoruz)
        await context.bot.send_message(chat_id=config.YOUR_TELEGRAM_ID, 
                                       text=f"{item['title']}\n{item['link']}", 
                                       reply_markup=reply_markup)
        context.user_data[f"haber_{i}"] = item # Haberi hafızaya al
# Tweetleme işleyişi
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("tweet"):
        _, title, link = query.data.split("|", 2)
        tweet_text = f"{title}\n\nDetaylar için: {link}"
        client.create_tweet(text=tweet_text)
        await query.edit_message_text(text=f"✅ Tweetlendi: {title}")

# Botu çalıştır
if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).job_queue(None).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # Haber kontrolü (Örn: 10 dakikada bir)
    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=600, first=10)
    
    application.run_polling()
