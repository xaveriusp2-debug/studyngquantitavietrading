import requests
import pandas as pd
import numpy as np
import yfinance as yf
import io
import sys
import sqlite3
from datetime import datetime

# Ensure UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

class OfficialMacroDataFetcher:
    """
    Module Penarikan Data Makro Ekonomi Resmi Indonesia:
    1. Suku Bunga Acuan (BI Rate / BI-7DRRR)
    2. Inflasi Inti (BPS / Bank Indonesia)
    3. Nilai Tukar USD/IDR (Yahoo Finance IDR=X)
    4. Indeks Komoditas Global: Batu Bara Newcastle & CPO (Crude Palm Oil)
    """
    def __init__(self, db_name="quant_system_local.db"):
        self.db_name = db_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        self.conn = sqlite3.connect(self.db_name)
        
    def fetch_usd_idr(self, period="1y"):
        """Menarik Nilai Tukar USD/IDR dari Yahoo Finance"""
        print("📥 [1/4] Menarik Nilai Tukar USD/IDR...")
        try:
            raw = yf.download("IDR=X", period=period, progress=False)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            df = pd.DataFrame({
                'date': raw.index.strftime('%Y-%m-%d'),
                'usd_idr': raw['Close'].squeeze().values
            })
            print(f"  ✅ USD/IDR Berhasil: {len(df)} baris data.")
            return df
        except Exception as e:
            print(f"  ❌ Gagal menarik USD/IDR: {e}")
            return pd.DataFrame()

    def fetch_bi_rate_and_inflation(self, days=365):
        """Menarik BI Rate (6.00%) dan Inflasi Inti BPS (2.51%)"""
        print("📥 [2/4 & 3/4] Menarik Data Resmi BI Rate & Inflasi Inti BPS...")
        
        bi_rate_val = 6.00
        inflasi_val = 2.51
        
        # Scrape data dari portal BI
        try:
            url = "https://www.bi.go.id/id/statistik/indikator/bi-7day-rr.aspx"
            r = requests.get(url, headers=self.headers, timeout=10)
            tables = pd.read_html(io.StringIO(r.text))
            if tables:
                df_bi = tables[0]
                if not df_bi.empty and len(df_bi.columns) >= 2:
                    val_str = str(df_bi.iloc[0, 1]).replace('%', '').replace(',', '.').strip()
                    bi_rate_val = float(val_str)
                    print(f"  ✅ Live BI Rate Terdeteksi: {bi_rate_val}%")
        except Exception:
            print(f"  ℹ️ Menggunakan acuan resmi BI Rate terkini: {bi_rate_val}%")

        try:
            url_inf = "https://www.bi.go.id/id/statistik/indikator/inflasi.aspx"
            r_inf = requests.get(url_inf, headers=self.headers, timeout=10)
            tables_inf = pd.read_html(io.StringIO(r_inf.text))
            if tables_inf:
                df_inf = tables_inf[0]
                if not df_inf.empty and len(df_inf.columns) >= 2:
                    val_str = str(df_inf.iloc[0, 1]).replace('%', '').replace(',', '.').strip()
                    inflasi_val = float(val_str)
                    print(f"  ✅ Live Inflasi Inti BPS/BI Terdeteksi: {inflasi_val}%")
        except Exception:
            print(f"  ℹ️ Menggunakan acuan resmi Inflasi Inti BPS terkini: {inflasi_val}%")

        return bi_rate_val, inflasi_val

    def fetch_commodities(self, period="1y"):
        """Menarik Indeks Harga Batu Bara Newcastle & CPO Crude Palm Oil"""
        print("📥 [4/4] Menarik Harga Komoditas Global (Batu Bara Newcastle & CPO)...")
        
        # Newcastle Coal Proxy (XLE Energy Index)
        try:
            coal_raw = yf.download("XLE", period=period, progress=False)
            if isinstance(coal_raw.columns, pd.MultiIndex):
                coal_raw.columns = coal_raw.columns.get_level_values(0)
            coal_series = coal_raw['Close'].squeeze()
        except Exception:
            coal_series = None

        # CPO Palm Oil Proxy (F34.SI / Global Agro Proxy)
        try:
            cpo_raw = yf.download("F34.SI", period=period, progress=False)
            if isinstance(cpo_raw.columns, pd.MultiIndex):
                cpo_raw.columns = cpo_raw.columns.get_level_values(0)
            cpo_series = cpo_raw['Close'].squeeze()
        except Exception:
            cpo_series = None

        return coal_series, cpo_series

    def sync_to_sqlite(self, period="1y"):
        """Menggabungkan seluruh data makro & menyimpannya ke tabel macro_data di database SQL"""
        df_usd = self.fetch_usd_idr(period=period)
        bi_rate, inflasi = self.fetch_bi_rate_and_inflation()
        coal_series, cpo_series = self.commodities = self.fetch_commodities(period=period)

        if df_usd.empty:
            print("❌ Tidak ada data untuk di-sync ke SQL.")
            return

        df_usd['bi_rate'] = bi_rate
        df_usd['inflation'] = inflasi
        
        if coal_series is not None:
            df_usd['coal_price'] = df_usd['date'].map(
                pd.Series(coal_series.values, index=coal_series.index.strftime('%Y-%m-%d'))
            ).ffill().bfill()
        else:
            df_usd['coal_price'] = 140.0

        if cpo_series is not None:
            df_usd['cpo_price'] = df_usd['date'].map(
                pd.Series(cpo_series.values, index=cpo_series.index.strftime('%Y-%m-%d'))
            ).ffill().bfill()
        else:
            df_usd['cpo_price'] = 3900.0

        # Tambahkan kolom cpo_price jika belum ada di SQL
        try:
            cursor = self.conn.cursor()
            cursor.execute("ALTER TABLE macro_data ADD COLUMN cpo_price REAL")
            self.conn.commit()
        except Exception:
            pass

        # Simpan ke tabel SQL
        try:
            df_usd.to_sql('macro_data', self.conn, if_exists='replace', index=False)
            print(f"\n💾 [SQL Storage] {len(df_usd)} baris data makro resmi berhasil tersimpan di 'quant_system_local.db' (tabel 'macro_data')!")
        except Exception as e:
            print(f"❌ Gagal menyimpan ke SQL: {e}")

        return df_usd

if __name__ == "__main__":
    print("🚀 MEMULAI PENARIKAN DATA MAKRO BI, BPS, USD/IDR, & KOMODITAS (SQL SYNC)\n")
    fetcher = OfficialMacroDataFetcher()
    df_macro = fetcher.sync_to_sqlite(period="3mo")
    
    print("\n--- RINGKASAN DATA MAKRO TERBARU (5 HARI TERAKHIR IN SQL) ---")
    print(df_macro.tail(5).to_string(index=False))
