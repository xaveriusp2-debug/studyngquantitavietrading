import pandas as pd
import requests
import io
import sys
import re

# Ensure UTF-8 stdout printing
sys.stdout.reconfigure(encoding='utf-8')

def generate_ihsg_csv(filename='daftar_saham_ihsg.csv'):
    print("Membangun koneksi ke database publik untuk menarik daftar emiten...")
    
    url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        tables = pd.read_html(io.StringIO(response.text))
        clean_tickers = set()
        
        for df_table in tables:
            for col in df_table.columns:
                col_name = str(col).lower()
                if 'kode' in col_name or 'symbol' in col_name or 'code' in col_name:
                    col_values = df_table[col].dropna().astype(str).tolist()
                    for val in col_values:
                        # Membersihkan string seperti 'BEI: AALI', 'AALI', 'BEI:BBCA'
                        val_clean = re.sub(r'BEI:\s*', '', val, flags=re.IGNORECASE).strip().upper()
                        # Ekstrak 4 huruf kapital
                        match = re.search(r'\b[A-Z]{4}\b', val_clean)
                        if match:
                            code = match.group(0)
                            clean_tickers.add(f"{code}.JK")
                            
        sorted_tickers = sorted(list(clean_tickers))
        
        if not sorted_tickers:
            raise ValueError("Tidak ada kode ticker 4-huruf yang ditemukan.")
            
        df_final = pd.DataFrame(sorted_tickers, columns=['Ticker'])
        df_final.to_csv(filename, index=False)
        
        print(f"✅ SUKSES: File '{filename}' berhasil di-generate!")
        print(f"📊 Total Emiten yang ditarik: {len(df_final)} saham.")
        print("Sistem Quant Trading Anda sekarang memiliki amunisi data penuh.")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat menarik data: {e}")

if __name__ == "__main__":
    generate_ihsg_csv()
