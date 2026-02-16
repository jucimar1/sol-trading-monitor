import os
import sqlite3
import pandas as pd
import requests
from config import Config
from indicators import enrich_dataframe
from strategy import check_long_entry, check_short_entry
from database import init_db, save_data, get_last_rsi, set_order_state  # ← Use funções do database.py

def send_telegram(msg):
    if not Config.TELEGRAM_BOT_TOKEN: 
        print(f"📱 Telegram: {msg}")  # Debug local
        return
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def fetch_data(interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {'symbol': Config.SYMBOL, 'interval': interval, 'limit': 150}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return enrich_dataframe(df, Config)

def main():
    conn = None
    try:
        conn = init_db()  # ← Usa import correto
        
        # Pega posição atual
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM state WHERE key="pos"')
        row = cursor.fetchone()
        current_pos = row[0] if row else "IDLE"
        
        # Busca dados
        print("🔄 Buscando dados...")
        df_f = fetch_data(Config.TIMEFRAMES['fast'])
        df_m = fetch_data(Config.TIMEFRAMES['medium'])
        df_s = fetch_data(Config.TIMEFRAMES['slow'])
        
        price = df_f['close'].iloc[-1]
        rsi_5m = df_m['RSI'].iloc[-1]
        
        print(f"SOL: ${price:.4f} | RSI 5m: {rsi_5m:.1f} | Pos: {current_pos}")

        new_pos = current_pos
        if current_pos == "IDLE":
            ok_l, msg_l = check_long_entry(df_f, df_m, df_s, Config)
            if ok_l:
                send_telegram(f"🚀 *SINAL LONG*\\n{msg_l}")
                new_pos = "LONG"
            else:
                ok_s, msg_s = check_short_entry(df_f, df_m, df_s, Config)
                if ok_s:
                    send_telegram(f"🔴 *SINAL SHORT*\\n{msg_s}")
                    new_pos = "SHORT"
        
        # Saída por RSI extremo
        elif (current_pos == "LONG" and rsi_5m > 70) or (current_pos == "SHORT" and rsi_5m < 30):
            send_telegram(f"🏁 *FECHANDO POSIÇÃO* em ${price:.4f}")
            new_pos = "IDLE"

        # Salva novo estado
        cursor.execute('INSERT OR REPLACE INTO state (key, value) VALUES ("pos", ?)', (new_pos,))
        conn.commit()
        print(f"✅ Estado salvo: {new_pos}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
