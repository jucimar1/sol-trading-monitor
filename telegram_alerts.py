"""
Telegram SYNC simples (requests) - sem asyncio complexo.
"""
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class TelegramAlerts:
    def __init__(self):
        self.enabled = Config.is_telegram_enabled()
        self.base_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        if not self.enabled:
            logger.info("ℹ️ Telegram OFF")
    
    def send_alert(self, message, alert_type="info"):
        if not self.enabled:
            emoji = {"entry_long": "🟢", "entry_short": "🔴", "exit": "🟡"}.get(alert_type, "ℹ️")
            logger.info(f"{emoji} {message}")
            return
        
        emoji = {"entry_long": "🟢🚀", "entry_short": "🔴📉", "exit": "🟡💰"}.get(alert_type, "📊")
        full_msg = f"{emoji} <b>SOL Monitor</b>\n{escape_html(message)}"
        
        try:
            requests.post(self.base_url, json={
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': full_msg,
                'parse_mode': 'HTML',
                'disable_notification': alert_type not in ['entry_long', 'entry_short']
            }).raise_for_status()
            logger.info(f"✅ Telegram: {alert_type}")
        except Exception as e:
            logger.error(f"❌ Telegram: {e}")

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
