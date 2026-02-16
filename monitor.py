"""
Sistema principal de monitoramento multi-timeframe.
Verifica condições a cada 30 segundos e gera alertas.
Versão corrigida e otimizada para deploy em server.
"""

import ccxt
import pandas as pd
import time
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from config import Config  # Ajuste path se necessário
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
        self.exchange = ccxt.binance({
            'apiKey': self.config.API_KEY,  # Adicione no config!
            'secret': self.config.API_SECRET,
            'enableRateLimit': True,
            'sandbox': self.config.SANDBOX_MODE  # True para teste
        })
        self.telegram = TelegramAlerts()
        self.active_positions: Dict[str, bool] = {'long': False, 'short': False}
        self.entry_price: Dict[str, float] = {'long': 0.0, 'short': 0.0}
        logger.info(f"🚀 Monitor inicializado para {self.config.SYMBOL}")

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 150) -> pd.DataFrame:
        """Busca dados OHLCV com retry."""
        for attempt in range(3):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df.tail(limit)  # Garante tamanho
            except Exception as e:
                logger.error(f"Erro ao buscar {timeframe} (tentativa {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        return pd.DataFrame()

    def get_position_size(self, current_price: float, side: str) -> float:
        """Calcula tamanho da posição baseado em risco % do balance."""
        try:
            balance = self.exchange.fetch_balance()
            usdt_free = balance['USDT']['free']
            risk_usdt = usdt_free * self.config.RISK_PER_TRADE  # ex: 0.01 para 1%
            size = risk_usdt / current_price
            return round(size, 3)  # Ajuste precisão
        except Exception as e:
            logger.error(f"Erro ao calcular size: {e}")
            return 0.0

    def run(self):
        """Loop principal de monitoramento."""
        logger.info("🚀 Iniciando monitoramento contínuo...")
        logger.info(f"📈 Intervalo: {self.config.CHECK_INTERVAL}s | Símbolo: {self.config.SYMBOL}")

        while True:
            try:
                # Busca dados multi-timeframe
                data: Dict[str, pd.DataFrame] = {}
                for name, tf in self.config.TIMEFRAMES.items():
                    df = self.fetch_ohlcv(self.config.SYMBOL, tf)
                    if len(df) >= 50:  # Mínimo para indicadores
                        data[name] = enrich_dataframe(df, self.config)

                if len(data) != len(self.config.TIMEFRAMES):
                    logger.warning("⚠️ Dados incompletos. Aguardando...")
                    time.sleep(self.config.CHECK_INTERVAL)
                    continue

                current_price = data['fast']['close'].iloc[-1]
                current_time = datetime.now().strftime('%H:%M:%S')
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Verificação em {current_time} | Preço: {current_price:.4f} USDT")

                # Verifica entradas
                if not self.active_positions['long']:
                    is_long, msg = check_long_entry(data['fast'], data['medium'], data['slow'], self.config)
                    if is_long:
                        size = self.get_position_size(current_price, 'long')
                        if size > 0:
                            # TODO: self.exchange.create_market_buy_order(self.config.SYMBOL, size)
                            logger.info(f"🟢 LONG ENTRY | Size: {size} | {msg}")
                            self.telegram.send_alert(f"🟢 LONG {self.config.SYMBOL} | Preço: {current_price:.4f} | Size: {size}\n{msg}", "entry_long")
                            self.active_positions['long'] = True
                            self.entry_price['long'] = current_price

                if not self.active_positions['short']:
                    is_short, msg = check_short_entry(data['fast'], data['medium'], data['slow'], self.config)
                    if is_short:
                        size = self.get_position_size(current_price, 'short')
                        if size > 0:
                            # TODO: self.exchange.create_market_sell_order(self.config.SYMBOL, size)
                            logger.info(f"🔴 SHORT ENTRY | Size: {size} | {msg}")
                            self.telegram.send_alert(f"🔴 SHORT {self.config.SYMBOL} | Preço: {current_price:.4f} | Size: {size}\n{msg}", "entry_short")
                            self.active_positions['short'] = True
                            self.entry_price['short'] = current_price

                # Verifica saídas com SL/TP básico
                if self.active_positions['long']:
                    should_exit, msg = check_long_exit(data['medium'], self.config)
                    pnl_pct = (current_price - self.entry_price['long']) / self.entry_price['long'] * 100
                    if should_exit or pnl_pct <= -self.config.STOP_LOSS_PCT:
                        logger.info(f"🟡 LONG EXIT | PnL: {pnl_pct:.2f}% | {msg}")
                        self.telegram.send_alert(f"🟡 LONG EXIT {self.config.SYMBOL} | PnL: {pnl_pct:.2f}%", "exit_long")
                        self.active_positions['long'] = False

                if self.active_positions['short']:
                    should_exit, msg = check_short_exit(data['medium'], self.config)
                    pnl_pct = (self.entry_price['short'] - current_price) / self.entry_price['short'] * 100
                    if should_exit or pnl_pct <= -self.config.STOP_LOSS_PCT:
                        logger.info(f"🟡 SHORT EXIT | PnL: {pnl_pct:.2f}% | {msg}")
                        self.telegram.send_alert(f"🟡 SHORT EXIT {self.config.SYMBOL} | PnL: {pnl_pct:.2f}%", "exit_short")
                        self.active_positions['short'] = False

                # Resumo
                status_parts = []
                if self.active_positions['long']: status_parts.append("🟢 LONG")
                if self.active_positions['short']: status_parts.append("🔴 SHORT")
                status = " | ".join(status_parts) or "⚪ IDLE"
                logger.info(f"Estado: {status}")

                time.sleep(self.config.CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("\n🛑 Parado pelo usuário.")
                break
            except Exception as e:
                logger.error(f"❌ Erro crítico: {e}")
                time.sleep(60)

if __name__ == "__main__":
    monitor = TradingMonitor()
    monitor.run()
