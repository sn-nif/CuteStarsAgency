const axios = require("axios");

async function sendApplicationToTelegram(application, photoUrls = []) {
  const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
  const CHAT_ID = process.env.TELEGRAM_CHAT_ID;

  let message = `📥 *New Application Received*\n\n` +
    `👤 *Name:* ${application.name}\n` +
    `🎂 *Age:* ${application.age}\n` +
    `📧 *Email:* ${application.email}\n` +
    `📱 *Phone:* ${application.contact}\n` +
    `🌍 *Nationality:* ${application.country}\n`;

  if (application.instagram) message += `📸 *Instagram:* ${application.instagram}\n`;
  if (application.tiktok) message += `🎵 *TikTok:* ${application.tiktok}\n`;
  if (application.telegram) message += `📬 *Telegram:* @${application.telegram}\n`;

  if (photoUrls.length > 0) {
    message += `\n🖼️ *Photos:*\n`;
    photoUrls.forEach((url, i) => {
      message += `🔗 [Photo ${i + 1}](${url})\n`;
    });
  }

  await axios.post(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    chat_id: CHAT_ID,
    text: message,
    parse_mode: "Markdown"
  });
}

module.exports = { sendApplicationToTelegram };
