import os
import sqlite3
import ccxt
import pandas as pd
import pandas_ta as ta
import time

# --- CONFIGURAÇÕES E BANCO DE DATOS ---
SYMBOL = 'SOL/USDT'
TIMEFRAME = '30m'

def init_db():
    """Inicializa o banco de dados SQLite para persistência no GitHub Actions"""
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            timestamp DATETIME PRIMARY KEY,
            price REAL,
            rsi REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
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

# --- LÓGICA DE DADOS (CORRIGIDA) ---
def fetch_ohlcv():
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_API_SECRET'),
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    print(f"Buscando dados de {SYMBOL}...")
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
    
    # ✅ CORREÇÃO DAS COLUNAS: Definindo nomes claros para o Pandas TA
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def analyze_strategy():
    conn = init_db()
    last_position = get_last_state(conn)
    
    try:
        df = fetch_ohlcv()
        
        # Cálculo do RSI usando pandas_ta
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        current_rsi = df['RSI'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"Preço: {current_price} | RSI: {current_rsi:.2f} | Posição Atual: {last_position}")

        # Exemplo Simples de Estratégia
        new_position = last_position
        if current_rsi < 30 and last_position == "OUT":
            print("🚀 SINAL DE COMPRA (RSI SOBREVENDIDO)")
            new_position = "IN"
            # Aqui entraria a lógica de exchange.create_order(...)
            
        elif current_rsi > 70 and last_position == "IN":
            print("💰 SINAL DE VENDA (RSI SOBRECOMPRADO)")
            new_position = "OUT"
            # Aqui entraria a lógica de exchange.create_order(...)

        save_trade_state(conn, current_price, current_rsi, new_position)

    except Exception as e:
        print(f"Erro na execução: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_strategy()
