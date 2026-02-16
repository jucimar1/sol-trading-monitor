import os
import sqlite3
import ccxt
import pandas as pd
import time

# --- CONFIGURAÇÕES ---
SYMBOL = 'SOL/USDT'
TIMEFRAME = '30m'

# --- FUNÇÃO MATEMÁTICA DO RSI (Puro Pandas) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    return 100 - (100 / (1+rs))

# --- BANCO DE DATOS ---
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

def save_trade_state(conn, price, rsi, position):
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO history (timestamp, price, rsi) VALUES (CURRENT_TIMESTAMP, ?, ?)', (price, rsi))
    cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("position", ?)', (position,))
    conn.commit()

# --- LÓGICA PRINCIPAL ---
def fetch_ohlcv():
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_API_SECRET'),
        'enableRateLimit': True
    })
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
    # ✅ Colunas corrigidas conforme solicitado
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def analyze_strategy():
    conn = init_db()
    last_position = get_last_state(conn)
    
    try:
        df = fetch_ohlcv()
        
        # ✅ Cálculo do RSI Sem pandas_ta
        df['RSI'] = calculate_rsi(df['close'], 14)
        
        current_rsi = df['RSI'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"Preço: {current_price} | RSI: {current_rsi:.2f} | Posição: {last_position}")

        new_position = last_position
        if current_rsi < 30 and last_position == "OUT":
            print("🚀 SINAL DE COMPRA")
            new_position = "IN"
        elif current_rsi > 70 and last_position == "IN":
            print("💰 SINAL DE VENDA")
            new_position = "OUT"

        save_trade_state(conn, current_price, current_rsi, new_position)

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_strategy()
