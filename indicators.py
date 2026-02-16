import pandas as pd
import logging

logger = logging.getLogger(__name__)

def enrich_dataframe(df: pd.DataFrame, config) -> pd.DataFrame:
    """Enriquece DF com indicadores usando cálculos nativos do Pandas."""
    df_out = df.copy()
    
    # 1. Bollinger Bands
    df_out['BBM'] = df_out['close'].rolling(window=config.BB_LENGTH).mean()
    std = df_out['close'].rolling(window=config.BB_LENGTH).std()
    df_out['BBU'] = df_out['BBM'] + (config.BB_STD * std)
    df_out['BBL'] = df_out['BBM'] - (config.BB_STD * std)
    # %B (BBP)
    df_out['BBP'] = (df_out['close'] - df_out['BBL']) / (df_out['BBU'] - df_out['BBL'])
    
    # 2. EMAs
    df_out['EMA_6'] = df_out['close'].ewm(span=6, adjust=False).mean()
    df_out['EMA_99'] = df_out['close'].ewm(span=99, adjust=False).mean()
    
    # 3. MACD
    ema_fast = df_out['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
    ema_slow = df_out['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
    df_out['MACD'] = ema_fast - ema_slow
    df_out['MACD_signal'] = df_out['MACD'].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
    df_out['MACD_hist'] = df_out['MACD'] - df_out['MACD_signal']
    
    # 4. RSI (Cálculo clássico)
    delta = df_out['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_LENGTH).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_LENGTH).mean()
    rs = gain / loss
    df_out['RSI'] = 100 - (100 / (1 + rs))
    
    # Limpa NaN (usando ffill/bfill compatível com Pandas novos)
    df_out = df_out.ffill().bfill()
    
    return df_out.tail(100)
