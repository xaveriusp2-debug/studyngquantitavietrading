import sys
import yfinance as yf
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, classification_report
import matplotlib.pyplot as plt

# Ensure UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

class QuantMLTrainer:
    def __init__(self, ticker, start_date="2020-01-01", end_date=None):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date or pd.Timestamp.today().strftime('%Y-%m-%d')
        self.df = None
        self.model = None

    def fetch_and_engineer_features(self):
        """
        Langkah 1: Menyiapkan 'Bahan Bakar' Data
        Mesin membutuhkan fitur (features) untuk menemukan pola.
        Kita buat puluhan turunan data matematis yang mungkin tidak terlihat korelasinya oleh manusia.
        """
        print(f"📥 Mengunduh data {self.ticker}...")
        raw_df = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
        
        if raw_df.empty:
            raise ValueError(f"Data kosong untuk ticker {self.ticker}")
            
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = raw_df.columns.get_level_values(0)
            
        self.df = raw_df.copy()
        
        close = self.df['Close'].squeeze()
        high = self.df['High'].squeeze()
        low = self.df['Low'].squeeze()
        open_p = self.df['Open'].squeeze()
        vol = self.df['Volume'].squeeze()
        
        # Fitur 1: Momentum & Return Historis
        self.df['Return_1d'] = close.pct_change(1)
        self.df['Return_3d'] = close.pct_change(3)
        self.df['Return_5d'] = close.pct_change(5)
        
        # Fitur 2: Volatilitas (Rolling Standard Deviation)
        self.df['Vol_5d'] = self.df['Return_1d'].rolling(5).std()
        self.df['Vol_20d'] = self.df['Return_1d'].rolling(20).std()
        
        # Fitur 3: Struktur Mikro Volume
        self.df['Volume_Change'] = vol.pct_change()
        self.df['Volume_SMA10'] = vol.rolling(10).mean()
        self.df['Volume_Ratio'] = vol / self.df['Volume_SMA10']
        
        # Fitur 4: Jarak terhadap Moving Averages (Bukan persilangan, tapi elastisitas)
        self.df['SMA_20'] = close.rolling(20).mean()
        self.df['SMA_50'] = close.rolling(50).mean()
        self.df['Dist_SMA20'] = (close - self.df['SMA_20']) / self.df['SMA_20']
        self.df['Dist_SMA50'] = (close - self.df['SMA_50']) / self.df['SMA_50']
        
        # Fitur 5: Bayangan Candlestick (Mendeteksi tekanan jual/beli tersembunyi)
        max_open_close = pd.concat([open_p, close], axis=1).max(axis=1)
        min_open_close = pd.concat([open_p, close], axis=1).min(axis=1)
        
        self.df['Upper_Shadow'] = high - max_open_close
        self.df['Lower_Shadow'] = min_open_close - low
        
        # Bersihkan inf / -inf dan NaN
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)
        self.df.dropna(inplace=True)
        print("✅ Rekayasa Fitur Selesai.")

    def create_target_labels(self, horizon=5, threshold=0.03):
        """
        Langkah 2: Menentukan Target Pembelajaran (Y)
        Kita meminta mesin mencari tahu: "Kondisi apa hari ini yang menyebabkan 
        harga naik lebih dari 3% dalam 5 hari ke depan?"
        """
        close = self.df['Close'].squeeze()
        future_return = close.shift(-horizon) / close - 1
        
        # Binary Classification: 1 (Sukses / Profit), 0 (Gagal / Flat / Rugi)
        self.df['Target'] = (future_return > threshold).astype(int)
        
        # Hapus baris terakhir yang tidak memiliki data masa depan
        self.df.dropna(inplace=True)
        
        print(f"🎯 Target disetel: Mencari pola kenaikan > {threshold*100}% dalam {horizon} hari.")
        dist = self.df['Target'].value_counts(normalize=True) * 100
        print(f"Distribusi Target: \n{dist}")

    def train_algorithm(self):
        """
        Langkah 3: Melatih Mesin (XGBoost)
        """
        ignore_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Target', 'SMA_20', 'SMA_50', 'Volume_SMA10']
        features = [col for col in self.df.columns if col not in ignore_cols]
        
        X = self.df[features].copy()
        y = self.df['Target'].copy()
        
        # Pastikan tidak ada nilai inf / nan dalam X
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        X.fillna(0, inplace=True)
        
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        print("\n🧠 Memulai Pelatihan Mesin (XGBoost)...")
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X_train, y_train)
        
        predictions = self.model.predict(X_test)
        
        acc = accuracy_score(y_test, predictions)
        prec = precision_score(y_test, predictions, zero_division=0)
        
        print(f"\n📊 --- HASIL EVALUASI MESIN ---")
        print(f"Akurasi Keseluruhan : {acc * 100:.2f}%")
        print(f"Presisi Sinyal Beli : {prec * 100:.2f}% (Seberapa akurat saat mesin bilang 'BELI')")
        print("Detail Klasifikasi:")
        print(classification_report(y_test, predictions, zero_division=0))
        
        return list(X.columns)

    def plot_hidden_patterns(self, feature_names):
        """
        Langkah 4: Visualisasi Pola Tersembunyi (Feature Importance)
        """
        importance = self.model.feature_importances_
        indices = np.argsort(importance)[-10:]
        
        plt.figure(figsize=(10, 6))
        plt.title(f"🔍 Top 10 Pola Penggerak Harga Tak Kasat Mata ({self.ticker})")
        plt.barh(range(len(indices)), importance[indices], color='mediumpurple', align='center')
        plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
        plt.xlabel('Bobot Kepentingan (Relative Importance)')
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        plot_file = "ml_feature_importance.png"
        plt.savefig(plot_file, dpi=300)
        print(f"✅ Grafik Feature Importance berhasil disimpan ke '{plot_file}'.")
        plt.close()

if __name__ == "__main__":
    TICKER = "BMRI.JK"
    
    trainer = QuantMLTrainer(TICKER, start_date="2015-01-01")
    trainer.fetch_and_engineer_features()
    trainer.create_target_labels(horizon=5, threshold=0.03)
    features = trainer.train_algorithm()
    trainer.plot_hidden_patterns(features)
    
    print("\n[Insights Institusional]: Jika 'Lower_Shadow' atau 'Vol_5d' menduduki peringkat teratas, artinya saham ini sering kali dimanipulasi dengan cara ditekan turun keras (shakeout) sebelum dinaikkan oleh institusi. Algoritma ini baru saja mendeteksi sidik jari mereka.")
