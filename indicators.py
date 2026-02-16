"""
Módulo para cálculo de indicadores técnicos otimizados.
Compatível com pandas_ta + preenchimento inteligente de NaN.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_bollinger_bands(df: pd.DataFrame, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands com nomes padronizados."""
    bb = df.ta.bbands(length=length, std=std)
    # Renomeia para consistência
    bb.columns = ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']
    logger.debug(f"BB calculadas: {len(bb)} barras, std={std}")
    return bb

def calculate_ema(df: pd.Series, periods: list) -> dict:
    """EMAs múltiplas como dicionário."""
    emas = {}
    for period in periods:
        ema_series = df.ta.ema(length=period)
        emas[f'EMA_{period}'] = ema_series
        logger.debug(f"EMA{period}: {ema_series.iloc[-1]:.4f}")
    return emas

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD completo (linha, sinal, histograma)."""
    macd = df.ta.macd(fast=fast, slow=slow, signal=signal)
    macd.columns = ['MACD', 'MACD_signal', 'MACD_hist']
    logger.debug(f"MACD {fast}-{slow}-{signal}: hist={macd['MACD_hist'].iloc[-1]:.4f}")
    return macd

def calculate_rsi(df: pd.Series, length: int = 14) -> pd.Series:
    """RSI com limites visuais."""
    rsi = df.ta.rsi(length=length)
    logger.debug(f"RSI{length}: {rsi.iloc[-1]:.1f}")
    return rsi

def fill_nans_smart(df: pd.DataFrame) -> pd.DataFrame:
    """Preenchimento inteligente: ffill + últimos valores válidos."""
    df = df.fillna(method='ffill').fillna(method='bfill')
    # Últimas 3 barras com valor atual se ainda NaN
    for col in df.columns:
        if df[col].isna().iloc[-1]:
            df[col].iloc[-1] = df[col].dropna().iloc[-1]
    return df

def enrich_dataframe(df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Enriquece DataFrame com TODOS indicadores.
    Garante dados limpos para strategy.py.
    """
    logger.info(f"🧮 Calculando indicadores para {len(df)} barras...")
    
    df_out = df.copy()
    
    # 1. Bollinger Bands
    bb = calculate_bollinger_bands(df_out, config.BB_LENGTH, config.BB_STD)
    df_out = pd.concat([df_out, bb], axis=1)
    
    # 2. EMAs
    emas = calculate_ema(df_out['close'], [config.EMA_SHORT, config.EMA_LONG])
    for name, series in emas.items():
        df_out[name] = series
    
    # 3. MACD (usa config se disponível)
    macd_fast = getattr(config, 'MACD_FAST', 12)
    macd_slow = getattr(config, 'MACD_SLOW', 26)
    macd_signal = getattr(config, 'MACD_SIGNAL', 9)
    macd = calculate_macd(df_out, macd_fast, macd_slow, macd_signal)
    df_out = pd.concat([df_out, macd], axis=1)
    
    # 4. RSI
    df_out['RSI'] = calculate_rsi(df_out['close'], config.RSI_LENGTH)
    
    # 5. Limpeza NaN + últimos dados
    df_out = fill_nans_smart(df_out)
    
    # 6. Drop linhas iniciais sem indicadores
    df_out = df_out.dropna()
    
    logger.info(f"✅ DataFrame enriquecido: {len(df_out)} barras válidas")
    logger.debug(f"Últimos valores: RSI={df_out['RSI'].iloc[-1]:.1f}, "
                f"BB_pos={df_out['BBP'].iloc[-1]:.3f}, MACD_h={df_out['MACD_hist'].iloc[-1]:.4f}")
    
    return df_out.tail(100)  # Últimas 100 barras para performance
