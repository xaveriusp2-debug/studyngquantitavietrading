import yfinance as yf
import pandas as pd
import numpy as np
from hmmlearn.hmm import GaussianHMM
import matplotlib.pyplot as plt
import sys

# Ensure UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

class HiddenMarkovRegimeDetector:
    """
    Algoritma Unsupervised Hidden Markov Model (HMM) 3-State Market Regime:
    - State 0: Low Volatility Bull Market (RISK_ON)
    - State 1: High Volatility Sideways / Transition
    - State 2: High Volatility Bear Market (RISK_OFF)
    """
    def __init__(self, ticker="^JKSE", period="5y"):
        self.ticker = ticker
        self.period = period
        self.model = None

    def fetch_and_prepare_data(self):
        print(f"📥 Menarik data historis {self.ticker}...")
        raw = yf.download(self.ticker, period=self.period, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
            
        df = raw[['Close', 'Volume']].copy().dropna()
        close_s = df['Close'].squeeze()
        vol_s = df['Volume'].squeeze()
        
        # Fitur HMM: Log Return (Ekspektasi Return) & Volatilitas 5-Hari
        df['Log_Return'] = np.log(close_s / close_s.shift(1))
        df['Volatility_5d'] = df['Log_Return'].rolling(window=5).std()
        df.dropna(inplace=True)
        
        return df

    def fit_hmm(self, df, n_components=3):
        print(f"🧠 Melatih Hidden Markov Model (HMM) dengan {n_components} Regresi Status Tersembunyi...")
        X = df[['Log_Return', 'Volatility_5d']].values
        
        self.model = GaussianHMM(n_components=n_components, covariance_type="full", n_iter=100, random_state=42)
        self.model.fit(X)
        
        hidden_states = self.model.predict(X)
        df['HMM_State'] = hidden_states
        
        # Identifikasi State mana yang Bullish vs Bearish berdasarkan Mean Return & Volatilitas
        state_means = []
        for i in range(n_components):
            mean_ret = df[df['HMM_State'] == i]['Log_Return'].mean()
            mean_vol = df[df['HMM_State'] == i]['Volatility_5d'].mean()
            state_means.append((i, mean_ret, mean_vol))
            
        # Urutkan berdasarkan mean return (tertinggi = Bullish)
        state_means.sort(key=lambda x: x[1], reverse=True)
        
        bull_state = state_means[0][0]
        sideways_state = state_means[1][0]
        bear_state = state_means[2][0]
        
        state_labels = {
            bull_state: "🟢 BULLISH (Low Volatility Risk-On)",
            sideways_state: "🟡 SIDEWAYS / TRANSITION",
            bear_state: "🔴 BEARISH (High Volatility Risk-Off)"
        }
        
        df['Regime_Label'] = df['HMM_State'].map(state_labels)
        current_regime = df['Regime_Label'].iloc[-1]
        
        print("\n✅ Matrix Matriks Transisi HMM Status Tersembunyi:")
        print(pd.DataFrame(self.model.transmat_, columns=[f"State {i}" for i in range(n_components)]))
        
        print(f"\n🔮 Rezim Pasar Terkini Terdeteksi (HMM Unsupervised): {current_regime}")
        return df

if __name__ == "__main__":
    print("🚀 ALGORITMA HMM (HIDDEN MARKOV MODEL) MARKET REGIME DETECTOR\n")
    detector = HiddenMarkovRegimeDetector(ticker="^JKSE", period="3y")
    df_hmm = detector.fetch_and_prepare_data()
    df_res = detector.fit_hmm(df_hmm)
    
    print("\n--- SAMPLE DATA REZIM TERKINI (5 HARI TERAKHIR) ---")
    print(df_res[['Close', 'Log_Return', 'Volatility_5d', 'Regime_Label']].tail(5).to_string())
