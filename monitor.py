import os
import sqlite3
import pandas as pd
import requests
from config import Config
from indicators import enrich_dataframe
from strategy import check_long_entry, check_short_entry
from database import init_db

def send_telegram(msg):
    if not Config.TELEGRAM_BOT_TOKEN: return
    url = f"https://api.telegram.org{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def fetch_data(interval):
    url = "https://api.binance.com"
    params = {'symbol': Config.SYMBOL, 'interval': interval, 'limit': 150}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data).iloc[:, :6]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in df.columns[1:]: df[col] = pd.to_numeric(df[col])
    return enrich_dataframe(df, Config)

def init_db():
    db = 'trading_data.db'
    if os.path.exists(db) and os.path.getsize(db) == 0: os.remove(db)
    conn = sqlite3.connect(db)
    conn.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
    return conn

def main():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM state WHERE key="pos"')
    row = cursor.fetchone()
    current_pos = row[0] if row else "IDLE"
    
    try:
        df_f = fetch_data(Config.TIMEFRAMES['fast'])
        df_m = fetch_data(Config.TIMEFRAMES['medium'])
        df_s = fetch_data(Config.TIMEFRAMES['slow'])
        
        print(f"SOL: ${df_f['close'].iloc[-1]} | RSI 5m: {df_m['RSI'].iloc[-1]:.1f} | Pos: {current_pos}")

        new_pos = current_pos
        if current_pos == "IDLE":
            ok_l, msg_l = check_long_entry(df_f, df_m, df_s, Config)
            if ok_l:
                send_telegram(f"🚀 *SINAL LONG*\n{msg_l}")
                new_pos = "LONG"
            else:
                ok_s, msg_s = check_short_entry(df_f, df_m, df_s, Config)
                if ok_s:
                    send_telegram(f"🔴 *SINAL SHORT*\n{msg_s}")
                    new_pos = "SHORT"
        
        # Lógica de saída simples (exemplo: RSI oposto)
        elif (current_pos == "LONG" and df_m['RSI'].iloc[-1] > 70) or \
             (current_pos == "SHORT" and df_m['RSI'].iloc[-1] < 30):
            send_telegram(f"🏁 *FECHANDO POSIÇÃO* em {df_f['close'].iloc[-1]}")
            new_pos = "IDLE"

        cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("pos", ?)', (new_pos,))
        conn.commit()
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    conn = init_db()
    main()
    conn.close()
