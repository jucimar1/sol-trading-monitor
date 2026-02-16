import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
import threading
import time
from datetime import datetime
from config import Config
from indicators import enrich_dataframe

class TradingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SOL/USDT Monitor - Tempo Real")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Estado real
        self.current_pos = "IDLE"
        self.price = 0
        self.rsi_fast = 0
        self.rsi_medium = 0  
        self.rsi_slow = 0
        self.running = True
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2d2d2d', height=60)
        header.pack(fill='x', pady=5)
        header.pack_propagate(False)
        
        tk.Label(header, text="🚀 SOL/USDT Multi-Timeframe Monitor - Tempo Real", 
                font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#00ff88').pack(pady=10)
        
        # Container principal
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # ESQUERDA - Info Principal + Gráfico
        left_frame = tk.Frame(main_frame, bg='#1a1a1a')
        left_frame.pack(side='left', fill='both', expand=True)
        
        # POSIÇÃO ATUAL (gigante)
        pos_frame = tk.Frame(left_frame, bg='#2d2d2d', height=100)
        pos_frame.pack(fill='x', pady=(0,10))
        pos_frame.pack_propagate(False)
        
        self.pos_label = tk.Label(pos_frame, text="⚪ IDLE", font=('Arial', 28, 'bold'), 
                                 bg='#2d2d2d', fg='#666666')
        self.pos_label.pack(expand=True)
        
        # PREÇO + RSI PRINCIPAL
        info_frame = tk.Frame(left_frame, bg='#2d2d2d', height=80)
        info_frame.pack(fill='x', pady=(0,10))
        info_frame.pack_propagate(False)
        
        self.price_label = tk.Label(info_frame, text="$0.0000", font=('Arial', 24, 'bold'), 
                                   bg='#2d2d2d', fg='#00ff88')
        self.price_label.pack(side='left', padx=20, pady=10)
        
        self.rsi_label = tk.Label(info_frame, text="RSI 5m: 50.0", font=('Arial', 18, 'bold'), 
                                 bg='#2d2d2d', fg='#ffaa00')
        self.rsi_label.pack(side='left', padx=20, pady=15)
        
        # GRÁFICO Canvas
        self.canvas = tk.Canvas(left_frame, bg='#0d1117', height=450, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, pady=(0,10))
        
        # DIREITA - Timeframes + Sinais
        right_frame = tk.Frame(main_frame, bg='#2d2d2d', width=380)
        right_frame.pack(side='right', fill='y', padx=(10,0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="📊 TIMEFRAMES RSI", font=('Arial', 14, 'bold'),
                bg='#2d2d2d', fg='#ffffff').pack(pady=10)
        
        # RSI por timeframe
        self.tf_labels = {}
        timeframes = [('1m', 'Rápido'), ('5m', 'Médio'), ('1h', 'Lento')]
        for tf, nome in timeframes:
            frame = tk.Frame(right_frame, bg='#2d2d2d')
            frame.pack(fill='x', pady=3)
            tk.Label(frame, text=f"{nome}:", font=('Arial', 11, 'bold'), 
                    bg='#2d2d2d', fg='#888888').pack(anchor='w')
            self.tf_labels[tf] = tk.Label(frame, text="--", font=('Arial', 14, 'bold'), 
                                         bg='#2d2d2d', fg='#ffffff')
            self.tf_labels[tf].pack(anchor='w')
    
    def fetch_real_data(self, interval):
        """Busca dados REAIS da Binance - igual monitor.py"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': Config.SYMBOL, 
                'interval': interval, 
                'limit': 100
            }
            data = requests.get(url, params=params, timeout=10).json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
                'taker_buy_quote', 'ignore'
            ])
            
            # Converte para float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calcula indicadores REAIS
            df_enriched = enrich_dataframe(df, Config)
            return df_enriched
            
        except Exception as e:
            print(f"Erro {interval}: {e}")
            return pd.DataFrame()
    
    def update_display(self):
        """Atualiza TODOS os dados reais"""
        try:
            # Busca 3 timeframes REAIS
            df_fast = self.fetch_real_data('1m')
            df_medium = self.fetch_real_data('5m') 
            df_slow = self.fetch_real_data('1h')
            
            if not df_fast.empty:
                self.price = df_fast['close'].iloc[-1]
                self.rsi_fast = df_fast['RSI'].iloc[-1]
                
            if not df_medium.empty:
                self.rsi_medium = df_medium['RSI'].iloc[-1]
                
            if not df_slow.empty:
                self.rsi_slow = df_slow['RSI'].iloc[-1]
            
            # Atualiza labels
            self.price_label.config(text=f"${self.price:.4f}")
            self.rsi_label.config(text=f"RSI 5m: {self.rsi_medium:.1f}")
            
            # Posição visual (simulada - conecta com database depois)
            color = {'LONG': '#00ff88', 'SHORT': '#ff4444', 'IDLE': '#666666'}
            pos_text = {'LONG': '🟢 LONG', 'SHORT': '🔴 SHORT', 'IDLE': '⚪ IDLE'}
            self.pos_label.config(text=pos_text[self.current_pos], fg=color[self.current_pos])
            
            # Timeframes RSI
            self.tf_labels['1m'].config(text=f"{self.rsi_fast:.1f}", fg=self.get_rsi_color(self.rsi_fast))
            self.tf_labels['5m'].config(text=f"{self.rsi_medium:.1f}", fg=self.get_rsi_color(self.rsi_medium))
            self.tf_labels['1h'].config(text=f"{self.rsi_slow:.1f}", fg=self.get_rsi_color(self.rsi_slow))
            
            # Gráfico real
            self.draw_real_chart(df_fast)
            
        except Exception as e:
            print(f"Erro update: {e}")
    
    def get_rsi_color(self, rsi):
        """Cor do RSI por zona"""
        if rsi > 70: return '#ff4444'  # Sobrecomprado
        elif rsi < 30: return '#00ff88'  # Sobrevendido  
        else: return '#ffaa00'  # Neutro
    
    def draw_real_chart(self, df):
        """Gráfico candlestick REAL dos últimos 30 candles"""
        self.canvas.delete("all")
        w, h = 880, 420
        
        if df.empty:
            self.canvas.create_text(w//2, h//2, text="Carregando...", fill='#666', font=('Arial', 16))
            return
        
        # Grid
        for x in range(50, w, 35):
            self.canvas.create_line(x, 20, x, h-20, fill='#333', width=1)
        for y in range(50, h, 25):
            self.canvas.create_line(20, y, w-20, y, fill='#333', width=1)
        
        # Normaliza preços
        prices = df['close'].tail(30).values
        min_p, max_p = prices.min(), prices.max()
        price_range = max_p - min_p if max_p > min_p else 1
        
        # Desenha candles
        bar_width = 25
        for i, (idx, row) in enumerate(df.tail(30).iterrows()):
            x = 50 + i * 35
            
            # Normaliza Y
            high_y = h - 50 - ((row['high'] - min_p) / price_range) * 300
            low_y = h - 50 - ((row['low'] - min_p) / price_range) * 300  
            close_y = h - 50 - ((row['close'] - min_p) / price_range) * 300
            
            # Cor do candle
            color = '#00ff88' if row['close'] >= row['open'] else '#ff4444'
            
            # Corpo do candle
            body_top = min(close_y, h-50 - ((row['open'] - min_p) / price_range) * 300)
            body_bottom = max(close_y, h-50 - ((row['open'] - min_p) / price_range) * 300)
            self.canvas.create_rectangle(x, body_top, x+bar_width, body_bottom, 
                                       fill=color, outline='#555', width=1)
            
            # Pavios
            self.canvas.create_line(x+12, high_y, x+12, body_top, fill=color, width=2)
            self.canvas.create_line(x+12, body_bottom, x+12, low_y, fill=color, width=2)
        
        # Labels eixo Y
        for i, p in enumerate([min_p, (min_p+max_p)/2, max_p]):
            y = h - 50 - (i * 150)
            self.canvas.create_text(35, y, text=f"${p:.2f}", anchor='w', 
                                  fill='#888', font=('Arial', 10))
    
    def monitor_loop(self):
        """Atualiza a cada 10 segundos"""
        while self.running:
            self.root.after(0, self.update_display)  # Thread safe
            time.sleep(10)
    
    def start_monitoring(self):
        """Inicia monitoramento"""
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        self.update_display()  # Primeira execução
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
