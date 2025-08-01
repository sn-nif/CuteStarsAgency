import os
import requests

def send_application_to_telegram(data, photo_urls=[]):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    message = f"📥 *New Application Received*\n\n" \
              f"👤 *Name:* {data.get('name')}\n" \
              f"🎂 *Age:* {data.get('age')}\n" \
              f"📧 *Email:* {data.get('email')}\n" \
              f"📱 *Phone:* {data.get('contact')}\n" \
              f"🌍 *Nationality:* {data.get('country')}\n"

    if data.get('instagram'):
        message += f"📸 *Instagram:* {data.get('instagram')}\n"
    if data.get('tiktok'):
        message += f"🎵 *TikTok:* {data.get('tiktok')}\n"
    if data.get('telegram'):
        message += f"📬 *Telegram:* @{data.get('telegram')}\n"

    if photo_urls:
        message += "\n🖼️ *Photos:*\n"
        for i, url in enumerate(photo_urls):
            message += f"🔗 [Photo {i+1}]({url})\n"

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    )
