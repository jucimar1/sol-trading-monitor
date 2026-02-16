import sqlite3
import os

def init_db(db_path='trading_data.db'):
    """Cria banco SQLite LIMPO sempre - solução 100% confiável"""
    
    # ❌ SEMPRE remove arquivo existente (evita corrupção)
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Arquivo '{db_path}' removido (evitando corrupção)")
    
    # ✅ Cria banco NOVO e cria tabelas
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')  # Modo robusto
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            timestamp DATETIME PRIMARY KEY,
            price REAL,
            rsi REAL
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    print(f"✅ Banco '{db_path}' criado do zero")
    return conn
