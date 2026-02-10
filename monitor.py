"""
Sistema principal de monitoramento multi-timeframe.
Verifica condições a cada 30 segundos e gera alertas.
"""

import ccxt
import pandas as pd
import time
import logging
from datetime import datetime
from config import Config
from indicators import enrich_dataframe
from strategy import (
    check_long_entry, check_short_entry,
    check_long_exit, check_short_exit
)
from telegram_alerts import TelegramAlerts

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TradingMonitor:
    def __init__(self):
        self.config = Config()
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.telegram = TelegramAlerts()
        self.active_positions = {
            'long': False,
            'short': False
        }
        logger.info(f"Intialized monitor for {self.config.SYMBOL}")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=150):
        """Busca dados OHLCV do exchange."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar dados {timeframe}: {e}")
            return pd.DataFrame()
    
    def run(self):
        """Loop principal de monitoramento."""
        logger.info("🚀 Iniciando monitoramento contínuo...")
        logger.info(f".Intervalo: {self.config.CHECK_INTERVAL}s | Símbolo: {self.config.SYMBOL}")
        
        while True:
            try:
                # Busca dados para todos os timeframes
                data = {}
                for name, tf in self.config.TIMEFRAMES.items():
                    df = self.fetch_ohlcv(self.config.SYMBOL, tf)
                    if not df.empty:
                        data[name] = enrich_dataframe(df, self.config)
                
                # Verifica se temos dados suficientes
                if len(data) != len(self.config.TIMEFRAMES):
                    logger.warning("⚠️ Dados incompletos. Aguardando próxima iteração...")
                    time.sleep(self.config.CHECK_INTERVAL)
                    continue
                
                current_time = datetime.now().strftime('%H:%M:%S')
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Verificação em {current_time}")
                logger.info(f"Preço atual: {data['fast']['close'].iloc[-1]:.4f} USDT")
                
                # ============ VERIFICA ENTRADAS ============
                if not self.active_positions['long']:
                    is_long, msg = check_long_entry(
                        data['fast'], data['medium'], data['slow'], self.config
                    )
                    if is_long:
                        logger.info(msg)
                        self.telegram.send_alert(msg, "entry_long")
                        self.active_positions['long'] = True
                
                if not self.active_positions['short']:
                    is_short, msg = check_short_entry(
                        data['fast'], data['medium'], data['slow'], self.config
                    )
                    if is_short:
                        logger.info(msg)
                        self.telegram.send_alert(msg, "entry_short")
                        self.active_positions['short'] = True
                
                # ============ VERIFICA SAÍDAS ============
                if self.active_positions['long']:
                    should_exit, msg = check_long_exit(data['medium'], self.config)
                    if should_exit:
                        logger.info(msg)
                        self.telegram.send_alert(msg, "exit")
                        self.active_positions['long'] = False
                
                if self.active_positions['short']:
                    should_exit, msg = check_short_exit(data['medium'], self.config)
                    if should_exit:
                        logger.info(msg)
                        self.telegram.send_alert(msg, "exit")
                        self.active_positions['short'] = False
                
                # ============ RESUMO DO ESTADO ============
                status = "🟢 LONG ATIVO" if self.active_positions['long'] else ""
                status += " 🔴 SHORT ATIVO" if self.active_positions['short'] else ""
                status = status.strip() or "⚪ NENHUMA POSIÇÃO"
                logger.info(f"Estado atual: {status}")
                
                time.sleep(self.config.CHECK_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("\n🛑 Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                time.sleep(60)  # Espera 1 minuto antes de tentar novamente

if __name__ == "__main__":
    monitor = TradingMonitor()
    monitor.run()
