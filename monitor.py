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
DB_NAME = 'trading_data.db'

# --- FUNÇÃO DE NOTIFICAÇÃO TELEGRAM ---
def send_telegram_message(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# --- CÁLCULO PURO DO RSI (Wilder's Smoothing) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- BANCO DE DATOS COM PROTEÇÃO CONTRA CORRUPÇÃO ---
def init_db():
    if os.path.exists(DB_NAME) and os.path.getsize(DB_NAME) == 0:
        os.remove(DB_NAME)
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS history (timestamp DATETIME PRIMARY KEY, price REAL, rsi REAL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
        conn.commit()
        return conn
    except sqlite3.DatabaseError:
        if os.path.exists(DB_NAME): os.remove(DB_NAME)
        return init_db()

def get_last_state(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM state WHERE key = "position"')
    result = cursor.fetchone()
    return result[0] if result else "OUT"

# --- BUSCA DE DADOS (API DIRETA) ---
def fetch_ohlcv():
    params = {'symbol': SYMBOL, 'interval': INTERVAL, 'limit': 100}
    response = requests.get(URL_BINANCE, params=params)
    response.raise_for_status()
    data = response.json()
    
    # ✅ COLUNAS CORRETAS: timestamp, open, high, low, close, volume
    df = pd.DataFrame(data).iloc[:, :6]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
    return df

# --- ESTRATÉGIA ---
def analyze_strategy():
    conn = init_db()
    last_position = get_last_state(conn)
    
    try:
        df = fetch_ohlcv()
        df['RSI'] = calculate_rsi(df['close'], 14)
        
        current_rsi = df['RSI'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        msg = f"🤖 *SOL Monitor*\nPreço: ${current_price}\nRSI: {current_rsi:.2f}\nStatus: {last_position}"
        print(msg.replace('*', ''))

        new_position = last_position
        if current_rsi < 30 and last_position == "OUT":
            new_position = "IN"
            send_telegram_message("🚀 *SINAL DE COMPRA (SOL)*\nRSI abaixo de 30!")
        elif current_rsi > 70 and last_position == "IN":
            new_position = "OUT"
            send_telegram_message("💰 *SINAL DE VENDA (SOL)*\nRSI acima de 70!")

        # Salva estado e histórico
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO history (timestamp, price, rsi) VALUES (CURRENT_TIMESTAMP, ?, ?)', (current_price, current_rsi))
        cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("position", ?)', (new_position,))
        conn.commit()

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_strategy()
