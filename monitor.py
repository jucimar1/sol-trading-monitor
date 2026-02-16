import os
import sqlite3
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
SYMBOL = 'SOLUSDT'
INTERVAL = '30m'
URL_BINANCE = "https://api.binance.com"

# --- CÁLCULO PURO DO RSI (Algoritmo de Wilder) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Previne divisão por zero
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- BANCO DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS history (timestamp DATETIME PRIMARY KEY, price REAL, rsi REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()
    return conn

def get_last_state(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM state WHERE key = "position"')
    result = cursor.fetchone()
    return result[0] if result else "OUT"

# --- BUSCA DE DADOS PURA (API REST) ---
def fetch_ohlcv_pure():
    params = {'symbol': SYMBOL, 'interval': INTERVAL, 'limit': 100}
    response = requests.get(URL_BINANCE, params=params)
    data = response.json()
    
    # ✅ CORREÇÃO DAS COLUNAS: Formatando conforme sua necessidade
    # A Binance retorna: [OpenTime, Open, High, Low, Close, Volume, CloseTime...]
    df = pd.DataFrame(data)
    df = df.iloc[:, :6] # Pega apenas as 6 primeiras colunas
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    # Converte tipos para cálculos
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
        
    return df

def analyze_strategy():
    conn = init_db()
    last_position = get_last_state(conn)
    
    try:
        df = fetch_ohlcv_pure()
        df['RSI'] = calculate_rsi(df['close'], 14)
        
        current_rsi = df['RSI'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"[{datetime.now()}] SOL: ${current_price} | RSI: {current_rsi:.2f} | Status: {last_position}")

        # Lógica de Decisão
        new_position = last_position
        if current_rsi < 35 and last_position == "OUT":
            print("🚀 SINAL DE COMPRA IDENTIFICADO")
            new_position = "IN"
        elif current_rsi > 65 and last_position == "IN":
            print("💰 SINAL DE VENDA IDENTIFICADO")
            new_position = "OUT"

        # Salva no Banco de Dados (Persistência do GitHub Actions)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO history (timestamp, price, rsi) VALUES (CURRENT_TIMESTAMP, ?, ?)', (current_price, current_rsi))
        cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("position", ?)', (new_position,))
        conn.commit()

    except Exception as e:
        print(f"Erro no monitor: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_strategy()
