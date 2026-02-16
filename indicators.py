"""
Indicadores técnicos com pandas_ta + limpeza NaN.
Nomes padronizados para strategy.py.
"""
import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)

def enrich_dataframe(df: pd.DataFrame, config) -> pd.DataFrame:
    """Enriquece DF com todos indicadores."""
    df_out = df.copy()
    
    # Bollinger Bands
    bb = df.ta.bbands(length=config.BB_LENGTH, std=config.BB_STD)
    bb.columns = ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']
    df_out = pd.concat([df_out, bb], axis=1)
    
    # EMAs
    df_out['EMA_6'] = df_out['close'].ta.ema(6)
    df_out['EMA_99'] = df_out['close'].ta.ema(99)
    
    # MACD
    macd = df.ta.macd(fast=config.MACD_FAST, slow=config.MACD_SLOW, signal=config.MACD_SIGNAL)
    macd.columns = ['MACD', 'MACD_signal', 'MACD_hist']
    df_out = pd.concat([df_out, macd], axis=1)
    
    # RSI
    df_out['RSI'] = df_out['close'].ta.rsi(config.RSI_LENGTH)
    
    # Limpa NaN
    df_out = df_out.fillna(method='ffill').fillna(method='bfill')
    df_out = df_out.dropna()
    
    return df_out.tail(100)

def test_indicators():
    """Teste standalone."""
    import ccxt
    config = Config()
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(config.SYMBOL, '5m', limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    df_enriched = enrich_dataframe(df, config)
    print(df_enriched[['close', 'RSI', 'BBP', 'MACD_hist']].tail())
