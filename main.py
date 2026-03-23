import requests
import json
from datetime import datetime, timezone
import pytz
import schedule
import time

TELEGRAM_TOKEN = "8736551836:AAFlGWnVIkNjplTA3LGgUhIaK3cGWvAwUgo"
TELEGRAM_CHANNEL = "@yourxtrend"
TURKEY_TZ = pytz.timezone("Europe/Istanbul")

NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us",
]

def get_trending_turkey():
    """Türkiye trendlerini çek"""
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/search?q=lang%3Atr&f=tweets&since_id=0"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return parse_tweets(r.text, "tr")
        except:
            continue
    return get_twitter_trending_turkey_fallback()

def get_twitter_trending_turkey_fallback():
    """Yedek yöntem: Woeid ile Türkiye trendleri"""
    try:
        # trends24.in sitesinden Türkiye trendlerini çek
        url = "https://trends24.in/turkey/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            trends = []
            trend_items = soup.select(".trend-card__list li a")[:10]
            for item in trend_items:
                trends.append({
                    "text": item.get_text(strip=True),
                    "url": f"https://x.com/search?q={requests.utils.quote(item.get_text(strip=True))}&src=trend_click&lang=tr",
                    "engagement": "Trend"
                })
            return trends
    except Exception as e:
        print(f"Fallback hata: {e}")
    return []

def get_trending_global():
    """Global trendleri çek"""
    try:
        url = "https://trends24.in/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            trends = []
            trend_items = soup.select(".trend-card__list li a")[:10]
            for item in trend_items:
                trends.append({
                    "text": item.get_text(strip=True),
                    "url": f"https://x.com/search?q={requests.utils.quote(item.get_text(strip=True))}&src=trend_click",
                    "engagement": "Trend"
                })
            return trends
    except Exception as e:
        print(f"Global trend hata: {e}")
    return []

def parse_tweets(html, lang):
    """HTML'den tweet parse et"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        tweets = []
        for tweet in soup.select(".timeline-item")[:5]:
            try:
                content = tweet.select_one(".tweet-content")
                stats = tweet.select(".tweet-stat")
                link = tweet.select_one(".tweet-link")
                if content:
                    engagement = {}
                    for stat in stats:
                        val = stat.get_text(strip=True)
                        if "retweet" in str(stat).lower():
                            engagement["rt"] = val
                        elif "like" in str(stat).lower() or "heart" in str(stat).lower():
                            engagement["like"] = val
                    tweets.append({
                        "text": content.get_text(strip=True)[:200],
                        "url": link["href"] if link else "#",
                        "engagement": engagement
                    })
            except:
                continue
        return tweets
    except:
        return []

def format_daily_message(turkey_trends, global_trends):
    now = datetime.now(TURKEY_TZ)
    date_str = now.strftime("%d %B %Y")
    
    msg = f"🔥 *GÜNLÜK TREND — {date_str}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "🇹🇷 *TÜRKİYE TRENDLERİ*\n\n"
    if turkey_trends:
        for i, t in enumerate(turkey_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "🌍 *GLOBAL TRENDLER*\n\n"
    if global_trends:
        for i, t in enumerate(global_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 _@yourxtrend_"
    return msg

def format_weekly_message(turkey_trends, global_trends):
    now = datetime.now(TURKEY_TZ)
    date_str = now.strftime("%d %B %Y")
    
    msg = f"📅 *HAFTALIK TREND — {date_str}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "🇹🇷 *TÜRKİYE — HAFTALIK EN ÇOK ETKİLEŞİM*\n\n"
    if turkey_trends:
        for i, t in enumerate(turkey_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "🌍 *GLOBAL — HAFTALIK EN ÇOK ETKİLEŞİM*\n\n"
    if global_trends:
        for i, t in enumerate(global_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 _@yourxtrend_"
    return msg

def format_monthly_message(turkey_trends, global_trends):
    now = datetime.now(TURKEY_TZ)
    date_str = now.strftime("%B %Y")
    
    msg = f"🗓️ *AYLIK TREND — {date_str}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "🇹🇷 *TÜRKİYE — AYLIK EN ÇOK ETKİLEŞİM*\n\n"
    if turkey_trends:
        for i, t in enumerate(turkey_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "🌍 *GLOBAL — AYLIK EN ÇOK ETKİLEŞİM*\n\n"
    if global_trends:
        for i, t in enumerate(global_trends[:5], 1):
            msg += f"{i}. [{t['text']}]({t['url']})\n"
    else:
        msg += "⚠️ Veri alınamadı\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 _@yourxtrend_"
    return msg

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=data, timeout=15)
        result = r.json()
        if result.get("ok"):
            print(f"✅ Mesaj gönderildi: {datetime.now(TURKEY_TZ)}")
        else:
            print(f"❌ Hata: {result}")
    except Exception as e:
        print(f"❌ Telegram hatası: {e}")

def daily_job():
    print(f"🔄 Günlük görev başladı: {datetime.now(TURKEY_TZ)}")
    turkey = get_trending_turkey()
    global_t = get_trending_global()
    msg = format_daily_message(turkey, global_t)
    send_telegram(msg)

def weekly_job():
    now = datetime.now(TURKEY_TZ)
    if now.weekday() == 6:  # Pazar
        print(f"🔄 Haftalık görev başladı: {now}")
        turkey = get_trending_turkey()
        global_t = get_trending_global()
        msg = format_weekly_message(turkey, global_t)
        send_telegram(msg)

def monthly_job():
    import calendar
    now = datetime.now(TURKEY_TZ)
    last_day = calendar.monthrange(now.year, now.month)[1]
    if now.day == last_day:
        print(f"🔄 Aylık görev başladı: {now}")
        turkey = get_trending_turkey()
        global_t = get_trending_global()
        msg = format_monthly_message(turkey, global_t)
        send_telegram(msg)

def run_all():
    """Tüm görevleri birden çalıştır (test için)"""
    daily_job()

# Zamanlama — Türkiye saati 20:00
schedule.every().day.at("17:00").do(daily_job)   # UTC 17:00 = TR 20:00
schedule.every().day.at("17:00").do(weekly_job)  # Pazar günleri haftalık
schedule.every().day.at("17:00").do(monthly_job) # Ayın son günü aylık

print("🤖 XTrend Bot başladı!")
print(f"⏰ Her gün 20:00'da (TR saati) çalışacak")

# İlk çalıştırmada test mesajı gönder
send_telegram("🤖 *XTrend Bot aktif!*\nHer gün akşam 20:00'da trend paylaşımları başlıyor. 🚀")

while True:
    schedule.run_pending()
    time.sleep(60)
