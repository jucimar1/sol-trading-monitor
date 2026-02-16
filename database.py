import sqlite3
import os
import pandas as pd

def init_db(db_path='trading_data.db'):
    """Cria banco SQLite LIMPO sempre - solução 100% confiável"""
    
    # Remove arquivo existente (evita corrupção)
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Arquivo '{db_path}' removido (evitando corrupção)")
    
    # Cria banco NOVO
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')  # Modo robusto
    
    # Tabela histórico
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            timestamp DATETIME PRIMARY KEY,
            price REAL,
            rsi REAL
        )
    ''')
    
    # Tabela estado
    conn.execute('''
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    print(f"✅ Banco '{db_path}' criado do zero")
    return conn

def save_data(conn, price, rsi):
    """Salva preço e RSI no histórico"""
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO history (timestamp, price, rsi) VALUES (CURRENT_TIMESTAMP, ?, ?)', 
        (price, rsi)
    )
    conn.commit()
    print(f"💾 Dados salvos: ${price:.4f}, RSI: {rsi:.1f}")

def get_last_rsi(conn):
    """Retorna último RSI salvo"""
    cursor = conn.cursor()
    cursor.execute('SELECT rsi FROM history ORDER BY timestamp DESC LIMIT 1')
    result = cursor.fetchone()
    return result[0] if result else None

def set_order_state(conn, status):
    """Salva estado da posição"""
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO state (key, value) VALUES ("pos", ?)', 
        (status,)
    )
    conn.commit()
    print(f"📊 Posição salva: {status}")

def get_order_state(conn, default="IDLE"):
    """Pega estado atual da posição"""
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM state WHERE key="pos"')
    result = cursor.fetchone()
    return result[0] if result else default
