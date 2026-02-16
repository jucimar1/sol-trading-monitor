import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SYMBOL = "SOLUSDT"  # Formato padrão API direta
    
    # API (Obrigatório para o futuro, mas o monitor roda público agora)
    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
    
    TIMEFRAMES = {
        'fast': '1m',    # Timing
        'medium': '5m',  # Confirmação
        'slow': '1h'     # Tendência
    }
    
    # Indicadores
    BB_LENGTH = 20
    BB_STD = 2.0
    RSI_LENGTH = 14
    RSI_OVERSOLD = 35
    RSI_OVERBOUGHT = 65
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
