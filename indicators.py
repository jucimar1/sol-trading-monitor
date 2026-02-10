"""
Módulo para cálculo de indicadores técnicos:
- Bollinger Bands (bandas superior/inferior/central)
- EMA6 e EMA99 (canal dinâmico + tendência)
- MACD (momentum)
- RSI (força relativa)
"""

import pandas as pd
import pandas_ta as ta

def calculate_bollinger_bands(df, length=20, std=2.0):
    """
    Calcula Bollinger Bands.
    Retorna: DataFrame com colunas BBL (inferior), BBM (média), BBU (superior)
    """
    bb = df.ta.bbands(length=length, std=std)
    return bb

def calculate_ema(df, periods=[6, 99]):
    """
    Calcula EMAs para os períodos especificados.
    Retorna: Dicionário com EMAs calculadas
    """
    emas = {}
    for period in periods:
        emas[f'ema{period}'] = df['close'].ta.ema(length=period)
    return emas

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    Calcula MACD (Moving Average Convergence Divergence).
    Retorna: DataFrame com MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
    """
    return df.ta.macd(fast=fast, slow=slow, signal=signal)

def calculate_rsi(df, length=14):
    """
    Calcula RSI (Relative Strength Index).
    Retorna: Série com valores RSI
    """
    return df['close'].ta.rsi(length=length)

def enrich_dataframe(df, config):
    """
    Enriquece o DataFrame com todos os indicadores necessários.
    Parâmetros:
        df: DataFrame com colunas OHLCV
        config: Objeto Config com parâmetros
    Retorna:
        DataFrame com indicadores adicionados
    """
    # Calcula Bollinger Bands
    bb = calculate_bollinger_bands(df, config.BB_LENGTH, config.BB_STD)
    df = pd.concat([df, bb], axis=1)
    
    # Calcula EMAs
    emas = calculate_ema(df, [config.EMA_SHORT, config.EMA_LONG])
    for key, value in emas.items():
        df[key] = value
    
    # Calcula MACD
    macd = calculate_macd(df)
    df = pd.concat([df, macd], axis=1)
    
    # Calcula RSI
    df['rsi'] = calculate_rsi(df, config.RSI_LENGTH)
    
    return df
