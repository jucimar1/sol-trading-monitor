import os
import sqlite3
import pandas as pd
import requests
from datetime import datetime
from config import Config
from strategy import check_long_entry, check_short_entry, check_long_exit, check_short_exit

# --- CÁLCULOS MATEMÁTICOS PUROS ---
def add_indicators(df):
    # EMA
    df['EMA_6'] = df['close'].ewm(span=Config.EMA_SHORT, adjust=False).mean()
    df['EMA_99'] = df['close'].ewm(span=Config.EMA_LONG, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=Config.RSI_LENGTH).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=Config.RSI_LENGTH).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=Config.MACD_FAST, adjust=False).mean()
    exp2 = df['close'].ewm(span=Config.MACD_SLOW, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=Config.MACD_SIGNAL, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # Bollinger Bands
    df['MA20'] = df['close'].rolling(window=Config.BB_LENGTH).mean()
    df['std'] = df['close'].rolling(window=Config.BB_LENGTH).std()
    df['BBU'] = df['MA20'] + (df['std'] * Config.BB_STD)
    df['BBL'] = df['MA20'] - (df['std'] * Config.BB_STD)
    df['BBP'] = (df['close'] - df['BBL']) / (df['BBU'] - df['BBL']) # %B
    
    return df

def fetch_binance_data(symbol, interval):
    url = "https://api.binance.com"
    params = {'symbol': symbol.replace('/', ''), 'interval': interval, 'limit': 150}
    res = requests.get(url, params=params)
    df = pd.DataFrame(res.json()).iloc[:, :6]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in df.columns[1:]: df[col] = pd.to_numeric(df[col])
    return add_indicators(df)

# --- BANCO DE DATOS ---
def init_db():
    conn = sqlite3.connect('trading_data.db')
    conn.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
    return conn

def run_monitor():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM state WHERE key = "position"')
    pos_row = cursor.fetchone()
    current_pos = pos_row[0] if pos_row else "IDLE"

    try:
        # 1. Baixa dados nos 3 timeframes da Config
        df_fast = fetch_binance_data(Config.SYMBOL, Config.TIMEFRAMES['fast'])
        df_medium = fetch_binance_data(Config.SYMBOL, Config.TIMEFRAMES['medium'])
        df_slow = fetch_binance_data(Config.SYMBOL, Config.TIMEFRAMES['slow'])

        price = df_fast['close'].iloc[-1]
        print(f"[{datetime.now()}] Preço: {price} | Pos: {current_pos}")

        new_pos = current_pos
        # 2. Lógica de Entrada
        if current_pos == "IDLE":
            is_long, msg_l = check_long_entry(df_fast, df_medium, df_slow, Config)
            if is_long:
                print(msg_l)
                new_pos = "LONG"
            else:
                is_short, msg_s = check_short_entry(df_fast, df_medium, df_slow, Config)
                if is_short:
                    print(msg_s)
                    new_pos = "SHORT"

        # 3. Lógica de Saída
        elif current_pos == "LONG":
            exit_l, msg_ex = check_long_exit(df_medium, Config)
            if exit_l:
                print(f"Saindo LONG: {msg_ex}")
                new_pos = "IDLE"
        
        elif current_pos == "SHORT":
            exit_s, msg_ex = check_short_exit(df_medium, Config)
            if exit_s:
                print(f"Saindo SHORT: {msg_ex}")
                new_pos = "IDLE"

        # 4. Salva estado
        cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("position", ?)', (new_pos,))
        conn.commit()

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_monitor()
