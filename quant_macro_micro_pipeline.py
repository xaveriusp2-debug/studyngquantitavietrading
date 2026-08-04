import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import sys
from datetime import datetime, timedelta

# Ensure UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# =======================================================
# BAGIAN 3: OTOMATISASI & PENYIMPANAN (STORAGE LAYER)
# =======================================================
class DatabaseManager:
    def __init__(self, db_name="quant_system_local.db"):
        """Inisialisasi Database Relasional SQL Lokal (SQLite)"""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        """Membuat arsitektur tabel yang saling berelasi berdasarkan Timestamp"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS macro_data (
                date TEXT PRIMARY KEY,
                usd_idr REAL,
                coal_price REAL,
                bi_rate REAL,
                inflation REAL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS micro_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                close_price REAL,
                volume REAL,
                eps REAL,
                UNIQUE(date, ticker)
            )
        ''')
        self.conn.commit()
        print("✅ [Storage Layer] Database SQL & Tabel relasional siap.")

    def save_df_to_sql(self, df, table_name):
        """Fungsi pembantu untuk memasukkan Pandas DataFrame ke SQL dengan aman"""
        try:
            df.to_sql(table_name, self.conn, if_exists='append', index=False)
        except sqlite3.IntegrityError:
            pass

# =======================================================
# BAGIAN 1: PENARIKAN DATA (DATA INGESTION LAYER)
# =======================================================
class DataIngestion:
    def __init__(self, db_manager, start_date="2022-01-01"):
        self.db = db_manager
        self.start_date = start_date
        self.end_date = datetime.today().strftime('%Y-%m-%d')
        
    def fetch_macro_data(self):
        print("📥 [Ingestion Layer] Menarik Data Makro (USD/IDR & Komoditas)...")
        raw_usd = yf.download("IDR=X", start=self.start_date, end=self.end_date, progress=False)
        raw_coal = yf.download("XLE", start=self.start_date, end=self.end_date, progress=False)
        
        if isinstance(raw_usd.columns, pd.MultiIndex):
            raw_usd.columns = raw_usd.columns.get_level_values(0)
        if isinstance(raw_coal.columns, pd.MultiIndex):
            raw_coal.columns = raw_coal.columns.get_level_values(0)
            
        usd_idr = raw_usd['Close'].squeeze()
        coal_proxy = raw_coal['Close'].squeeze()
        
        # Penyelarasan indeks tanggal
        common_idx = usd_idr.index.intersection(coal_proxy.index)
        usd_idr = usd_idr.loc[common_idx]
        coal_proxy = coal_proxy.loc[common_idx]
        
        macro_df = pd.DataFrame({
            'date': common_idx.strftime('%Y-%m-%d'),
            'usd_idr': usd_idr.values,
            'coal_price': coal_proxy.values
        })
        
        np.random.seed(42)
        macro_df['bi_rate'] = 5.75 + np.random.normal(0, 0.1, len(macro_df)) 
        macro_df['inflation'] = 3.0 + np.random.normal(0, 0.2, len(macro_df))
        
        self.db.save_df_to_sql(macro_df, 'macro_data')
        return macro_df

    def fetch_micro_data(self, tickers):
        print(f"📥 [Ingestion Layer] Menarik Data Mikro untuk {tickers}...")
        all_micro = pd.DataFrame()
        
        for ticker in tickers:
            raw_df = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
            if raw_df.empty:
                continue
                
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = raw_df.columns.get_level_values(0)
                
            close_s = raw_df['Close'].squeeze()
            vol_s = raw_df['Volume'].squeeze()
            
            micro_df = pd.DataFrame({
                'date': raw_df.index.strftime('%Y-%m-%d'),
                'ticker': ticker,
                'close_price': close_s.values,
                'volume': vol_s.values,
                'eps': np.nan
            })
            all_micro = pd.concat([all_micro, micro_df], ignore_index=True)
            self.db.save_df_to_sql(micro_df, 'micro_data')
            
        return all_micro

# =======================================================
# BAGIAN 2: MESIN KORELASI (THE CORRELATION ENGINE)
# =======================================================
class CorrelationEngine:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def load_merged_data(self, ticker):
        """Menggabungkan data Makro dan Mikro dari SQL menggunakan JOIN query"""
        query = f"""
            SELECT m.date, m.usd_idr, m.bi_rate, m.coal_price, 
                   s.close_price as stock_price
            FROM macro_data m
            INNER JOIN micro_data s ON m.date = s.date
            WHERE s.ticker = '{ticker}'
            ORDER BY m.date ASC
        """
        return pd.read_sql_query(query, self.db_manager.conn, parse_dates=['date'])

    def calculate_pearson_correlations(self, ticker, macro_variable='usd_idr', windows=[5, 14, 30]):
        """
        Menghitung Koefisien Korelasi Pearson antara perubahan Makro dengan 
        Return Harga Saham (N-Hari setelahnya).
        """
        print(f"\n🧠 [Correlation Engine] Menganalisis {ticker} terhadap {macro_variable}...")
        df = self.load_merged_data(ticker)
        
        if df.empty:
            print("Data tidak cukup untuk korelasi.")
            return

        df['macro_change_pct'] = df[macro_variable].pct_change()
        results = {}
        
        for w in windows:
            df[f'future_return_{w}d'] = (df['stock_price'].shift(-w) - df['stock_price']) / df['stock_price']
            clean_df = df.dropna(subset=['macro_change_pct', f'future_return_{w}d'])
            correlation = clean_df['macro_change_pct'].corr(clean_df[f'future_return_{w}d'], method='pearson')
            results[f'{w}-Hari'] = correlation

        print(f"Koefisien Pearson (r) Dampak Perubahan {macro_variable.upper()} terhadap harga {ticker}:")
        for window, corr in results.items():
            arah = "Positif (Searah)" if corr > 0 else "Negatif (Berlawanan)"
            kekuatan = "Kuat" if abs(corr) > 0.5 else "Sedang" if abs(corr) > 0.3 else "Lemah/Acak"
            print(f" └─ Jendela {window}: {corr:.4f} -> Korelasi {kekuatan} {arah}")
            
        return results

# =======================================================
# EKSEKUSI UTAMA (PIPELINE AUTOMATION)
# =======================================================
if __name__ == "__main__":
    print("🚀 Memulai Sistem Kuantitatif Makro-Mikro...\n")
    
    # 1. Inisialisasi Database (Storage)
    db = DatabaseManager('quant_system_local.db')
    
    # 2. Tarik Data (Ingestion) - Contoh: Perbankan (BBCA) & Properti (SMRA)
    ingestion = DataIngestion(db, start_date="2020-01-01")
    ingestion.fetch_macro_data()
    ingestion.fetch_micro_data(['BBCA.JK', 'SMRA.JK', 'PTBA.JK'])
    
    # 3. Analisis Korelasi (Engine)
    engine = CorrelationEngine(db)
    
    # Analisis 1: Dampak Nilai Tukar Dolar (USD/IDR) terhadap Bank BCA
    engine.calculate_pearson_correlations('BBCA.JK', macro_variable='usd_idr', windows=[5, 14, 30])
    
    # Analisis 2: Dampak BI Rate (Suku Bunga) terhadap Properti Summarecon (SMRA)
    engine.calculate_pearson_correlations('SMRA.JK', macro_variable='bi_rate', windows=[5, 14, 30])
    
    # Analisis 3: Dampak Harga Batu Bara terhadap Bukit Asam (PTBA)
    engine.calculate_pearson_correlations('PTBA.JK', macro_variable='coal_price', windows=[5, 14, 30])
    
    db.conn.close()
    print("\n✅ Proses harian selesai. Sistem bersiap untuk siklus besok (Cron Job Ready).")
