"""
Integração com Telegram para envio de alertas.
"""

import logging
from config import Config

logger = logging.getLogger(__name__)

class TelegramAlerts:
    def __init__(self):
        self.enabled = Config.is_telegram_enabled()
        if self.enabled:
            try:
                from telegram import Bot
                self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
                logger.info("✅ Telegram configurado com sucesso")
            except ImportError:
                logger.error("❌ Módulo 'python-telegram-bot' não instalado")
                self.enabled = False
        else:
            logger.info("ℹ️ Telegram desativado (chaves não configuradas)")
    
    def send_alert(self, message, alert_type="info"):
        """
        Envia alerta para o Telegram.
        alert_type: "entry_long", "entry_short", "exit", "info"
        """
        if not self.enabled:
            logger.info(f"[ALERTA] {message}")
            return
        
        try:
            # Adiciona emoji conforme tipo de alerta
            emoji = "ℹ️"
            if alert_type == "entry_long":
                emoji = "🟢"
            elif alert_type == "entry_short":
                emoji = "🔴"
            elif alert_type == "exit":
                emoji = "⚠️"
            
            full_message = f"{emoji} {message}"
            self.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=full_message,
                parse_mode="HTML"
            )
            logger.info(f"✅ Alerta enviado ao Telegram: {message[:50]}...")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta Telegram: {e}")
