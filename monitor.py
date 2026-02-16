"""
Monitor SOL/USDT completo - copie e rode!
"""
import ccxt
import pandas as pd
import time
import logging
from datetime import datetime
from config import Config
from indicators import enrich_dataframe
from strategy import check_long_entry, check_short_entry, check_long_exit, check_short_exit
from telegram_alerts import TelegramAlerts

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

class TradingMonitor:
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        self.exchange = ccxt.binance({
            'apiKey': self.config.API_KEY,
            'secret': self.config.API_SECRET,
            'enableRateLimit': True,
            'sandbox': self.config.SANDBOX_MODE
        })
        
        self.telegram = TelegramAlerts()
        self.positions = {'long': False, 'short': False}
        logger.info(f"🚀 Monitor {self.config.SYMBOL} INICIADO")

    def fetch_ohlcv(self, timeframe, limit=150):
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.config.SYMBOL, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp','o','h','l','c','v'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df
        except Exception as e:
            logger.error(f"❌ Fetch {timeframe}: {e}")
            return pd.DataFrame()

    def run(self):
        logger.info("🔄 Loop iniciado...")
        while True:
            try:
                # Fetch dados
                data = {}
                for name, tf in self.config.TIMEFRAMES.items():
                    df = self.fetch_ohlcv(tf)
                    if len(df) >= 50:
                        data[name] = enrich_dataframe(df, self.config)

                if len(data) != 3:
                    logger.warning("⚠️ Dados incompletos")
                    time.sleep(self.config.CHECK_INTERVAL)
                    continue

                price = data['fast']['close'].iloc[-1]
                logger.info(f"📊 {datetime.now().strftime('%H:%M:%S')} | {self.config.SYMBOL}: ${price:.4f}")

                # ENTRADAS
                if not self.positions['long']:
                    ok, msg = check_long_entry(data['fast'], data['medium'], data['slow'], self.config)
                    if ok:
                        self.positions['long'] = True
                        self.telegram.send_alert(msg, "entry_long")

                if not self.positions['short']:
                    ok, msg = check_short_entry(data['fast'], data['medium'], data['slow'], self.config)
                    if ok:
                        self.positions['short'] = True
                        self.telegram.send_alert(msg, "entry_short")

                # SAÍDAS
                if self.positions['long']:
                    ok, msg = check_long_exit(data['medium'], self.config)
                    if ok:
                        self.positions['long'] = False
                        self.telegram.send_alert(msg, "exit")

                if self.positions['short']:
                    ok, msg = check_short_exit(data['medium'], self.config)
                    if ok:
                        self.positions['short'] = False
                        self.telegram.send_alert(msg, "exit")

                status = "🟢L" if self.positions['long'] else ""
                status += "🔴S" if self.positions['short'] else ""
                logger.info(f"Estado: {status or '⚪'}")
                
                time.sleep(self.config.CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("🛑 Interrompido")
                break
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                time.sleep(60)

if __name__ == "__main__":
    TradingMonitor().run()
