"""
Estratégia EMA6 canal + multi-timeframe + volume.
Compatível com indicators.py nomes.
"""
import logging

logger = logging.getLogger(__name__)

def is_uptrend(df_slow, config):
    """Tendência alta 1h."""
    if len(df_slow) < 2: return False
    return (df_slow['close'].iloc[-1] > df_slow['EMA_99'].iloc[-1] and
            df_slow['MACD_hist'].iloc[-1] >= 0)

def is_downtrend(df_slow, config):
    """Tendência baixa 1h."""
    if len(df_slow) < 2: return False
    return (df_slow['close'].iloc[-1] < df_slow['EMA_99'].iloc[-1] and
            df_slow['MACD_hist'].iloc[-1] <= 0)

def check_long_entry(df_fast, df_medium, df_slow, config):
    """LONG: 6 filtros."""
    price = df_fast['close'].iloc[-1]
    
    # 1. Contexto 1h
    if not is_uptrend(df_slow, config):
        return False, "❌ Sem trend 1h"
    
    # 2. EMA6 medium
    if df_medium['close'].iloc[-1] < df_medium['EMA_6'].iloc[-1]:
        return False, "❌ < EMA6 5m"
    
    # 3. RSI
    rsi = df_medium['RSI'].iloc[-1]
    if rsi < config.RSI_OVERSOLD:
        return False, f"❌ RSI {rsi:.1f}"
    
    # 4. Timing EMA6 1m
    ema6 = df_fast['EMA_6'].iloc[-1]
    if abs(price - ema6) > ema6 * 0.002:
        return False, "❌ Longe EMA6"
    
    # 5. Volume
    if len(df_fast) < 3 or not (df_fast['volume'].iloc[-3:] == 
        sorted(df_fast['volume'].iloc[-3:])):
        return False, "❌ Volume"
    
    # 6. BB position
    if df_medium['BBP'].iloc[-1] > 0.95:
        return False, "❌ BB alta"
    
    return True, f"🟢 LONG {price:.4f} | RSI:{rsi:.1f}"

def check_short_entry(df_fast, df_medium, df_slow, config):
    """SHORT espelhado."""
    price = df_fast['close'].iloc[-1]
    
    if not is_downtrend(df_slow, config):
        return False, "❌ Sem trend 1h"
    
    if df_medium['close'].iloc[-1] > df_medium['EMA_6'].iloc[-1]:
        return False, "❌ > EMA6 5m"
    
    rsi = df_medium['RSI'].iloc[-1]
    if rsi > config.RSI_OVERBOUGHT:
        return False, f"❌ RSI {rsi:.1f}"
    
    ema6 = df_fast['EMA_6'].iloc[-1]
    if abs(price - ema6) > ema6 * 0.002:
        return False, "❌ Longe EMA6"
    
    if len(df_fast) < 3 or not (df_fast['volume'].iloc[-3:] == 
        sorted(df_fast['volume'].iloc[-3:])):
        return False, "❌ Volume"
    
    if df_medium['BBP'].iloc[-1] < 0.05:
        return False, "❌ BB baixa"
    
    return True, f"🔴 SHORT {price:.4f} | RSI:{rsi:.1f}"

def check_long_exit(df_medium, config):
    """Saída LONG."""
    if df_medium['close'].iloc[-1] > df_medium['BBU'].iloc[-1]:
        return True, "TP Banda superior"
    if (len(df_medium) >= 3 and 
        df_medium['MACD_hist'].iloc[-1] < df_medium['MACD_hist'].iloc[-2]):
        return True, "MACD fraco"
    return False, ""

def check_short_exit(df_medium, config):
    """Saída SHORT."""
    if df_medium['close'].iloc[-1] < df_medium['BBL'].iloc[-1]:
        return True, "TP Banda inferior"
    if (len(df_medium) >= 3 and 
        df_medium['MACD_hist'].iloc[-1] > df_medium['MACD_hist'].iloc[-2]):
        return True, "MACD fraco"
    return False, ""
