"""
Configurações do sistema de monitoramento.
⚠️ NUNCA commite chaves reais no GitHub!
Use .env para armazenar chaves sensíveis.
"""

import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

class Config:
    # Símbolo e exchange (foco SOL volátil)
    SYMBOL = "SOL/USDT"
    EXCHANGE = "binance"
    
    # API Keys (obrigatórias para ordens/balance)
    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    SANDBOX_MODE = os.getenv("SANDBOX_MODE", "false").lower() == "true"  # Testnet
    
    # Timeframes otimizados para SOL (rápido + confirmação)
    TIMEFRAMES: Dict[str, str] = {
        'fast': '1m',      # Entradas precisas
        'medium': '5m',    # Confirmação (melhor que 15m para scalping)
        'slow': '1h'       # Tendência macro
    }
    
    # Indicadores (tune para SOL: EMA agressiva)
    BB_LENGTH = 20
    BB_STD = 2.0
    EMA_SHORT = 9        # Mais responsivo que 6
    EMA_LONG = 21        # Padrão rápido
    RSI_LENGTH = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # Risco (por trade e global)
    RISK_PER_TRADE = 0.01      # 1% do balance por posição
    STOP_LOSS_PCT = 2.0        # SL 2% por posição
    TAKE_PROFIT_PCT = 4.0      # TP 4:1 RR
    MAX_DRAWDOWN = -0.10       # Pare se -10% total
    MAX_POSITIONS = 1          # Evita hedging (long OU short)
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Monitoramento
    CHECK_INTERVAL = 30        # Segundos
    MIN_DATA_BARS = 100        # Barras mínimas para indicadores
    
    @staticmethod
    def is_api_enabled() -> bool:
        """Verifica API keys."""
        return bool(Config.API_KEY and Config.API_SECRET)
    
    @staticmethod
    def is_telegram_enabled() -> bool:
        """Verifica Telegram."""
        return bool(Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID)
    
    @staticmethod
    def validate():
        """Valida config no init."""
        errors = []
        if not Config.is_api_enabled():
            errors.append("Falta BINANCE_API_KEY e/ou API_SECRET no .env")
        if not Config.SYMBOL:
            errors.append("SYMBOL não definido")
        if errors:
            raise ValueError(f"Config inválida: {errors}")
        print("✅ Config validada!")

# Validação automática
if __name__ == "__main__":
    Config.validate()
