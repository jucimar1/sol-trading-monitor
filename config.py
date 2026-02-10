"""
Configurações do sistema de monitoramento.
⚠️ NUNCA commite chaves reais no GitHub!
Use .env para armazenar chaves sensíveis.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (não commitado)
load_dotenv()

class Config:
    # Símbolo e exchange
    SYMBOL = "SOL/USDT"
    EXCHANGE = "binance"
    
    # Timeframes para análise multi-timeframe
    TIMEFRAMES = {
        'fast': '1m',    # Timing preciso de entrada
        'medium': '15m', # Confirmação da tendência
        'slow': '1h'     # Contexto geral do mercado
    }
    
    # Parâmetros dos indicadores
    BB_LENGTH = 20      # Período das Bollinger Bands
    BB_STD = 2.0        # Desvio padrão (2 = 95% de confiança)
    EMA_SHORT = 6       # EMA rápida (canal dinâmico)
    EMA_LONG = 99       # EMA lenta (tendência geral)
    RSI_LENGTH = 14     # Período do RSI
    
    # Configurações de risco
    MAX_DRAWDOWN = -0.10  # Stop loss máximo em USDT
    
    # Telegram (opcional)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Intervalo de verificação (segundos)
    CHECK_INTERVAL = 30
    
    @staticmethod
    def is_telegram_enabled():
        """Verifica se Telegram está configurado"""
        return bool(Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID)
