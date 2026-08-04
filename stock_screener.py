import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_indicators(df):
    """Menghitung EMA 20, EMA 50, dan Bollinger Bands"""
    # Menghitung EMA
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Menghitung Bollinger Bands (SMA 20 & 2 Standard Deviation)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Std_Dev'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + (df['Std_Dev'] * 2)
    df['BB_Lower'] = df['SMA_20'] - (df['Std_Dev'] * 2)
    
    return df

def screen_stocks(tickers, lookback_days=100):
    """Memindai daftar saham untuk mencari sinyal beli terbaru"""
    buy_candidates = []
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    
    print(f"Memulai pemindaian {len(tickers)} saham dari {start_date.strftime('%Y-%m-%d')} hingga {end_date.strftime('%Y-%m-%d')}...\n")
    
    for ticker in tickers:
        try:
            # Unduh data historis
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty or len(df) < 50:
                continue

            # Jika DataFrame memiliki MultiIndex kolom (seperti di yfinance versi baru), ratakan kolomnya
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = calculate_indicators(df)
            
            # Mendapatkan data 2 hari terakhir untuk mengecek persilangan (Cross)
            prev_day = df.iloc[-2]
            last_day = df.iloc[-1]
            
            prev_ema20 = float(prev_day['EMA_20'])
            prev_ema50 = float(prev_day['EMA_50'])
            last_ema20 = float(last_day['EMA_20'])
            last_ema50 = float(last_day['EMA_50'])
            last_close = float(last_day['Close'])
            last_bb_upper = float(last_day['BB_Upper'])
            
            # Logika Golden Cross: Kemarin EMA 20 di bawah EMA 50, hari ini EMA 20 di atas EMA 50
            golden_cross = (prev_ema20 <= prev_ema50) and (last_ema20 > last_ema50)
            
            # Logika Bollinger Bands: Harga tidak boleh melebihi Upper Band (mencegah overbought/FOMO)
            bb_condition = last_close < last_bb_upper
            
            if golden_cross and bb_condition:
                buy_candidates.append({
                    'Ticker': ticker,
                    'Harga Saat Ini': round(last_close, 2),
                    'EMA 20': round(last_ema20, 2),
                    'EMA 50': round(last_ema50, 2),
                    'BB Upper': round(last_bb_upper, 2),
                    'Stop Loss (5%)': round(last_close * 0.95, 2) # Perhitungan Cut Loss 5%
                })
                
        except Exception as e:
            print(f"Gagal memproses {ticker}: {e}")
            
    return pd.DataFrame(buy_candidates)

# ==========================================
# EKSEKUSI SCRIPT
# ==========================================
if __name__ == "__main__":
    # Daftar saham IDX30 & Saham Populer di BEI
    daftar_saham = [
        'BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 
        'GOTO.JK', 'AMMN.JK', 'BREN.JK', 'UNVR.JK', 'ICBP.JK',
        'INDF.JK', 'KLBF.JK', 'CPIN.JK', 'PGAS.JK', 'ADRO.JK',
        'PTBA.JK', 'ITMG.JK', 'BRIS.JK', 'MEDC.JK', 'MDKA.JK'
    ]
    
    hasil_screener = screen_stocks(daftar_saham)
    
    print("\n=== HASIL SCREENING SAHAM (GOLDEN CROSS + BB) ===")
    if hasil_screener.empty:
        print("Tidak ada saham yang memenuhi kriteria strategi pada penutupan pasar terakhir.")
    else:
        # Menampilkan data dalam format tabel
        try:
            print(hasil_screener.to_markdown(index=False))
        except Exception:
            print(hasil_screener.to_string(index=False))
        
    print("\n[Catatan Eksekusi]")
    print("* Masuk (Entry) : Beli pada 'Harga Saat Ini' saat pasar buka berikutnya jika sinyal bertahan.")
    print("* Keluar (Exit) : Segera Cut Loss jika harga menyentuh angka 'Stop Loss (5%)' ATAU jika kedepannya EMA 20 memotong ke bawah EMA 50 (Death Cross).")
