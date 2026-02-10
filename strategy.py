"""
Lógica de trading baseada no canal dinâmico:
- LONG: Preço na EMA6 (suporte) + confirmação multi-timeframe
- SHORT: Preço na EMA6 (resistência) + confirmação multi-timeframe
- SAÍDA: Rompimento das bandas de Bollinger ou perda de momentum
"""

def is_uptrend(df_slow, df_medium, config):
    """
    Verifica se há tendência de alta no contexto geral (1h).
    Condições:
        - Preço acima da EMA99 (tendência de longo prazo)
        - MACD positivo ou cruzando para cima
    """
    if df_slow['close'].iloc[-1] < df_slow[f'ema{config.EMA_LONG}'].iloc[-1]:
        return False
    
    macd_hist = df_slow['MACDh_12_26_9'].iloc[-1]
    if macd_hist < 0:
        # Verifica se está cruzando para cima (2 últimos candles)
        if df_slow['MACDh_12_26_9'].iloc[-2] >= macd_hist:
            return False
    
    return True

def is_downtrend(df_slow, df_medium, config):
    """
    Verifica se há tendência de baixa no contexto geral (1h).
    Condições:
        - Preço abaixo da EMA99 (tendência de longo prazo)
        - MACD negativo ou cruzando para baixo
    """
    if df_slow['close'].iloc[-1] > df_slow[f'ema{config.EMA_LONG}'].iloc[-1]:
        return False
    
    macd_hist = df_slow['MACDh_12_26_9'].iloc[-1]
    if macd_hist > 0:
        # Verifica se está cruzando para baixo
        if df_slow['MACDh_12_26_9'].iloc[-2] <= macd_hist:
            return False
    
    return True

def check_long_entry(df_fast, df_medium, df_slow, config):
    """
    Condições para entrada LONG:
    1. Tendência de alta no 1h (contexto)
    2. Preço acima da EMA6 no 15m (confirmação)
    3. RSI > 30 no 15m (saída da sobrevenda)
    4. Preço tocando EMA6 no 1m (timing preciso)
    5. Volume crescente nas últimas 3 velas (confirmação)
    """
    # Condição 1: Tendência de alta no 1h
    if not is_uptrend(df_slow, df_medium, config):
        return False, "❌ Sem tendência de alta no 1h"
    
    # Condição 2: Preço acima da EMA6 no 15m
    if df_medium['close'].iloc[-1] < df_medium[f'ema{config.EMA_SHORT}'].iloc[-1]:
        return False, "❌ Preço abaixo da EMA6 no 15m"
    
    # Condição 3: RSI > 30 no 15m
    if df_medium['rsi'].iloc[-1] < 30:
        return False, f"❌ RSI muito baixo ({df_medium['rsi'].iloc[-1]:.2f})"
    
    # Condição 4: Preço tocando EMA6 no 1m (tolerância 0.15%)
    ema6_fast = df_fast[f'ema{config.EMA_SHORT}'].iloc[-1]
    current_price = df_fast['close'].iloc[-1]
    tolerance = ema6_fast * 0.0015  # 0.15%
    
    if abs(current_price - ema6_fast) > tolerance:
        return False, f"❌ Preço longe da EMA6 no 1m (dif: {abs(current_price - ema6_fast):.4f})"
    
    # Condição 5: Volume crescente
    volumes = df_fast['volume'].iloc[-3:]
    if not (volumes.iloc[0] < volumes.iloc[1] < volumes.iloc[2]):
        return False, "❌ Volume não está crescendo"
    
    # ✅ Todas as condições atendidas
    return True, f"✅ SINAL LONG CONFIRMADO\nPreço: {current_price:.4f}\nEMA6 (1m): {ema6_fast:.4f}\nRSI (15m): {df_medium['rsi'].iloc[-1]:.2f}"

def check_short_entry(df_fast, df_medium, df_slow, config):
    """
    Condições para entrada SHORT:
    1. Tendência de baixa no 1h (contexto)
    2. Preço abaixo da EMA6 no 15m (confirmação)
    3. RSI < 70 no 15m (saída da sobrecompra)
    4. Preço tocando EMA6 no 1m (timing preciso)
    5. Volume crescente nas últimas 3 velas (confirmação)
    """
    # Condição 1: Tendência de baixa no 1h
    if not is_downtrend(df_slow, df_medium, config):
        return False, "❌ Sem tendência de baixa no 1h"
    
    # Condição 2: Preço abaixo da EMA6 no 15m
    if df_medium['close'].iloc[-1] > df_medium[f'ema{config.EMA_SHORT}'].iloc[-1]:
        return False, "❌ Preço acima da EMA6 no 15m"
    
    # Condição 3: RSI < 70 no 15m
    if df_medium['rsi'].iloc[-1] > 70:
        return False, f"❌ RSI muito alto ({df_medium['rsi'].iloc[-1]:.2f})"
    
    # Condição 4: Preço tocando EMA6 no 1m (tolerância 0.15%)
    ema6_fast = df_fast[f'ema{config.EMA_SHORT}'].iloc[-1]
    current_price = df_fast['close'].iloc[-1]
    tolerance = ema6_fast * 0.0015
    
    if abs(current_price - ema6_fast) > tolerance:
        return False, f"❌ Preço longe da EMA6 no 1m (dif: {abs(current_price - ema6_fast):.4f})"
    
    # Condição 5: Volume crescente
    volumes = df_fast['volume'].iloc[-3:]
    if not (volumes.iloc[0] < volumes.iloc[1] < volumes.iloc[2]):
        return False, "❌ Volume não está crescendo"
    
    # ✅ Todas as condições atendidas
    return True, f"✅ SINAL SHORT CONFIRMADO\nPreço: {current_price:.4f}\nEMA6 (1m): {ema6_fast:.4f}\nRSI (15m): {df_medium['rsi'].iloc[-1]:.2f}"

def check_long_exit(df_medium, config):
    """
    Condições para saída de LONG:
    1. Rompimento da banda superior de Bollinger
    2. Perda de momentum (MACD histograma decrescendo após pico)
    """
    # Condição 1: Rompimento da banda superior
    if df_medium['close'].iloc[-1] > df_medium['BBU_20_2.0'].iloc[-1]:
        return True, "⚠️ SAÍDA: Rompimento da banda superior"
    
    # Condição 2: Perda de momentum
    hist = df_medium['MACDh_12_26_9']
    if len(hist) >= 3:
        if hist.iloc[-1] < hist.iloc[-2] and hist.iloc[-2] > hist.iloc[-3]:
            return True, "⚠️ SAÍDA: Perda de momentum (MACD)"
    
    return False, ""

def check_short_exit(df_medium, config):
    """
    Condições para saída de SHORT:
    1. Rompimento da banda inferior de Bollinger
    2. Perda de momentum (MACD histograma crescendo após vale)
    """
    # Condição 1: Rompimento da banda inferior
    if df_medium['close'].iloc[-1] < df_medium['BBL_20_2.0'].iloc[-1]:
        return True, "⚠️ SAÍDA: Rompimento da banda inferior"
    
    # Condição 2: Perda de momentum
    hist = df_medium['MACDh_12_26_9']
    if len(hist) >= 3:
        if hist.iloc[-1] > hist.iloc[-2] and hist.iloc[-2] < hist.iloc[-3]:
            return True, "⚠️ SAÍDA: Perda de momentum (MACD)"
    
    return False, ""
