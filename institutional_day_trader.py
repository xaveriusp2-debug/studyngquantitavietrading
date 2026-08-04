import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class InstitutionalDayTrader:
    def __init__(self, capital, win_rate=0.55, risk_reward=1.5):
        self.capital = capital
        self.win_rate = win_rate
        self.risk_reward = risk_reward
        self.macro_bias = "NEUTRAL"
        
    def calculate_kelly_size(self):
        """Menghitung porsi modal per trade menggunakan Kelly Criterion"""
        # Rumus: f = p - (1-p) / b
        kelly_fraction = self.win_rate - ((1 - self.win_rate) / self.risk_reward)
        
        # Half-Kelly digunakan di industri untuk meredam volatilitas (drawdown)
        half_kelly = max(0, kelly_fraction / 2) 
        return half_kelly * self.capital

    def check_macro_regime(self):
        """Filter Makro: Mengecek tren USD/IDR sebagai proksi risiko pasar Indonesia"""
        print("Menganalisis Rezim Makro Kuantitatif (USD/IDR)...")
        try:
            usd_idr = yf.download("IDR=X", period="5d", interval="1d", progress=False)
            
            if usd_idr.empty:
                return "NEUTRAL"
                
            if isinstance(usd_idr.columns, pd.MultiIndex):
                usd_idr.columns = usd_idr.columns.get_level_values(0)
                
            close_series = usd_idr['Close'].dropna()
            if len(close_series) < 3:
                return "NEUTRAL"
                
            p_last = float(close_series.iloc[-1])
            p_prev = float(close_series.iloc[-3])
            
            price_change = (p_last - p_prev) / p_prev
            
            if price_change > 0.005:
                self.macro_bias = "RISK_OFF"
            elif price_change < -0.005:
                self.macro_bias = "RISK_ON"
            else:
                self.macro_bias = "NEUTRAL"
        except Exception as e:
            print(f"Peringatan data makro: {e}")
            self.macro_bias = "NEUTRAL"
            
        return self.macro_bias

    def calculate_vwap(self, df):
        """Metode eksekusi institusional (Broker AK)"""
        v = df['Volume']
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (v * tp).cumsum() / v.cumsum()
        return df

    def scan_intraday(self, tickers):
        """Memindai saham menggunakan data 1 menit"""
        bias = self.check_macro_regime()
        print(f"Status Makro Hari Ini: {bias}")
        
        if bias == "RISK_OFF":
            print("Peringatan: Makro negatif. Mengurangi ukuran posisi (De-leveraging).")
            self.capital *= 0.5 

        trade_size = self.calculate_kelly_size()
        candidates = []
        
        print(f"Modal per transaksi (Half-Kelly): Rp {trade_size:,.2f}\n")
        
        for ticker in tickers:
            try:
                # Mengambil data intraday 1 menit untuk hari ini
                df = yf.download(ticker, period="1d", interval="1m", progress=False)
                
                # Jika pasar tutup atau interval 1m kosong, coba interval 5m sebagai cadangan
                if df.empty or len(df) < 5:
                    df = yf.download(ticker, period="5d", interval="5m", progress=False)
                    
                if df.empty or len(df) < 5:
                    continue
                    
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                df = self.calculate_vwap(df)
                
                last_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2])
                last_vwap = float(df['VWAP'].iloc[-1])
                avg_vol = float(df['Volume'].mean())
                
                # Filter Likuiditas: Abaikan saham tidak likuid
                if avg_vol < 1000:
                    continue
                
                # Strategi Reversion ke VWAP (Beli saat harga di bawah VWAP tapi mulai berbalik naik)
                if last_price < last_vwap and (last_price > prev_price):
                    candidates.append({
                        'Ticker': ticker,
                        'Harga Saat Ini (Rp)': round(last_price, 0),
                        'Target VWAP (Rp)': round(last_vwap, 0),
                        'Cut Loss 1% (Rp)': round(last_price * 0.99, 0),
                        'Alokasi Dana (Rp)': round(trade_size, 0)
                    })
            except Exception as e:
                print(f"Gagal memproses {ticker}: {e}")
                continue
                
        return pd.DataFrame(candidates)

# ==========================================
# EKSEKUSI SISTEM DAY TRADING
# ==========================================
if __name__ == "__main__":
    # Inisialisasi: Modal Rp 100 Juta, Win Rate 55%, Rasio R/R 1:1.5
    bot = InstitutionalDayTrader(capital=100000000, win_rate=0.55, risk_reward=1.5)
    
    # Fokus pada Big Caps BEI
    big_caps = ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'BBNI.JK', 'AMMN.JK']
    
    hasil = bot.scan_intraday(big_caps)
    
    print("=== SINYAL INTRADAY (VWAP & KELLY) ===")
    if hasil.empty:
        print("Belum ada setup probabilitas tinggi saat ini (Pasar mungkin sedang tutup atau harga belum memenuhi kriteria VWAP reversion).")
    else:
        try:
            print(hasil.to_markdown(index=False))
        except Exception:
            print(hasil.to_string(index=False))
