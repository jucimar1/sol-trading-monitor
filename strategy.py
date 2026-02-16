def is_uptrend(df_slow):
    if len(df_slow) < 2: return False
    return (df_slow['close'].iloc[-1] > df_slow['EMA_99'].iloc[-1] and
            df_slow['MACD_hist'].iloc[-1] >= 0)

def is_downtrend(df_slow):
    if len(df_slow) < 2: return False
    return (df_slow['close'].iloc[-1] < df_slow['EMA_99'].iloc[-1] and
            df_slow['MACD_hist'].iloc[-1] <= 0)

def check_long_entry(df_fast, df_medium, df_slow, config):
    price = df_fast['close'].iloc[-1]
    if not is_uptrend(df_slow): return False, "❌ Sem trend 1h"
    if df_medium['close'].iloc[-1] < df_medium['EMA_6'].iloc[-1]: return False, "❌ < EMA6 5m"
    
    rsi = df_medium['RSI'].iloc[-1]
    if rsi < config.RSI_OVERSOLD: return False, f"❌ RSI {rsi:.1f}"
    
    ema6 = df_fast['EMA_6'].iloc[-1]
    if abs(price - ema6) > ema6 * 0.002: return False, "❌ Longe EMA6"
    
    # Volume crescente nas últimas 3 velas
    vol = df_fast['volume'].iloc[-3:].values
    if not (vol[0] < vol[1] < vol[2]): return False, "❌ Volume"
    
    if df_medium['BBP'].iloc[-1] > 0.95: return False, "❌ BB alta"
    return True, f"🟢 LONG em {price}"

def check_short_entry(df_fast, df_medium, df_slow, config):
    price = df_fast['close'].iloc[-1]
    if not is_downtrend(df_slow): return False, "❌ Sem trend 1h"
    if df_medium['close'].iloc[-1] > df_medium['EMA_6'].iloc[-1]: return False, "❌ > EMA6 5m"
    
    rsi = df_medium['RSI'].iloc[-1]
    if rsi > config.RSI_OVERBOUGHT: return False, f"❌ RSI {rsi:.1f}"
    
    ema6 = df_fast['EMA_6'].iloc[-1]
    if abs(price - ema6) > ema6 * 0.002: return False, "❌ Longe EMA6"
    
    vol = df_fast['volume'].iloc[-3:].values
    if not (vol[0] < vol[1] < vol[2]): return False, "❌ Volume"
    
    if df_medium['BBP'].iloc[-1] < 0.05: return False, "❌ BB baixa"
    return True, f"🔴 SHORT em {price}"
