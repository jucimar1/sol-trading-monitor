"""
Configurações do sistema de monitoramento SOL/USDT.
⚠️ NUNCA commite chaves reais! Use .env
"""
import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

class Config:
    # Trading
    SYMBOL = "SOL/USDT"
    EXCHANGE = "binance"
    
    # API (obrigatório para ordens)
    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
    
    # Timeframes otimizados SOL
    TIMEFRAMES: Dict[str, str] = {
        'fast': '1m',    # Timing entrada
        'medium': '5m',  # Confirmação
        'slow': '1h'     # Contexto
    }
    
    # Indicadores
    BB_LENGTH = 20
    BB_STD = 2.0
    EMA_SHORT = 6
    EMA_LONG = 99
    RSI_LENGTH = 14
    RSI_OVERSOLD = 35
    RSI_OVERBOUGHT = 65
    
    # MACD
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # Risco
    RISK_PER_TRADE = 0.01  # 1% balance
    STOP_LOSS_PCT = 2.0
    TAKE_PROFIT_PCT = 4.0
    MAX_POSITIONS = 1
    
    # Monitor
    CHECK_INTERVAL = 30
    MIN_DATA_BARS = 100
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    @staticmethod
    def is_api_enabled() -> bool:
        return bool(Config.API_KEY and Config.API_SECRET)
    
    @staticmethod
    def is_telegram_enabled() -> bool:
        return bool(Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID)
    
    @staticmethod
    def validate():
        errors = []
        if not Config.is_api_enabled():
            errors.append("BINANCE_API_KEY/API_SECRET faltando")
        print("✅ Config OK!" if not errors else f"❌ Erros: {errors}")

if __name__ == "__main__":
    Config.validate()
