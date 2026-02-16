import pandas as pd

def enrich_dataframe(df: pd.DataFrame, config) -> pd.DataFrame:
    """Calcula indicadores usando apenas Pandas nativo."""
    df_out = df.copy()
    
    # Bollinger Bands
    df_out['BBM'] = df_out['close'].rolling(window=config.BB_LENGTH).mean()
    std = df_out['close'].rolling(window=config.BB_LENGTH).std()
    df_out['BBU'] = df_out['BBM'] + (config.BB_STD * std)
    df_out['BBL'] = df_out['BBM'] - (config.BB_STD * std)
    df_out['BBP'] = (df_out['close'] - df_out['BBL']) / (df_out['BBU'] - df_out['BBL'])
    
    # EMAs
    df_out['EMA_6'] = df_out['close'].ewm(span=6, adjust=False).mean()
    df_out['EMA_99'] = df_out['close'].ewm(span=99, adjust=False).mean()
    
    # MACD
    ema_fast = df_out['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
    ema_slow = df_out['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
    df_out['MACD'] = ema_fast - ema_slow
    df_out['MACD_signal'] = df_out['MACD'].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
    df_out['MACD_hist'] = df_out['MACD'] - df_out['MACD_signal']
    
    # RSI
    delta = df_out['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_LENGTH).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_LENGTH).mean()
    rs = gain / loss
    df_out['RSI'] = 100 - (100 / (1 + rs))
    
    return df_out.ffill().bfill().tail(100)
