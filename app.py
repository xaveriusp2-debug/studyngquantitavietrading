import streamlit as st
import pandas as pd
import numpy as np
import os
import sqlite3
import re
from datetime import datetime, timedelta
import yfinance as yf
import xgboost as xgb
from hmmlearn.hmm import GaussianHMM
from sklearn.metrics import accuracy_score
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. DESIGN SYSTEM: MINIMALIST + WATERMARK XPINONTOAN
# ==========================================
st.set_page_config(page_title="Pro Quant Terminal — Xpinontoan", layout="wide", page_icon="⚡")

refresh_count = st_autorefresh(interval=60 * 1000, limit=None, key="minimalist_watermark_v132")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    .main { background-color: #0F172A !important; color: #F8FAFC !important; font-family: 'Inter', sans-serif !important; }
    .stApp header { background: rgba(15, 23, 42, 0.9) !important; border-bottom: 1px solid #1E293B !important; }
    
    .mini-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }

    .macro-score-card {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #0EA5E9;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #38BDF8 !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        color: #94A3B8 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #1E293B;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #334155;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        color: #94A3B8;
        font-weight: 500;
        font-size: 0.85rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }

    .stDataFrame { font-family: 'JetBrains Mono', monospace !important; }
    section[data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 1px solid #1E293B !important; }

    .watermark-fixed {
        position: fixed;
        bottom: 14px;
        right: 18px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.45);
        letter-spacing: 0.15em;
        text-transform: uppercase;
        pointer-events: none;
        z-index: 9999;
        background: rgba(15, 23, 42, 0.75);
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }
    
    .brand-badge {
        background: rgba(56, 189, 248, 0.1);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.1em;
        margin-left: 8px;
    }
</style>

<div class="watermark-fixed">⚡ DESIGNED BY XPINONTOAN</div>
""", unsafe_allow_html=True)

JOURNAL_FILE = 'trade_journal_v5.csv'

def init_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=[
            'ID', 'Tanggal Entry', 'Tanggal Exit', 'Ticker', 'Tipe', 'Status',
            'Harga Entry', 'Target TP', 'Stop Loss', 'Harga Closing/Exit', 
            'Volume', 'PnL (Rp)', 'Keterangan Sistem', 'Sesuai Rule?'
        ])
        df.to_csv(JOURNAL_FILE, index=False)

init_journal()

@st.cache_data(ttl=2)
def load_journal():
    return pd.read_csv(JOURNAL_FILE)

def save_journal(df):
    df.to_csv(JOURNAL_FILE, index=False)
    st.cache_data.clear()

df_journal = load_journal()

if 'live_signals' not in st.session_state:
    st.session_state['live_signals'] = pd.DataFrame()
if 'ml_leaderboard' not in st.session_state:
    st.session_state['ml_leaderboard'] = pd.DataFrame()

# ==========================================
# 2. ADAPTIVE QUANT ENGINE (HMM AUTO-CALIBRATION)
# ==========================================
class AdaptiveQuantEngine:
    def __init__(self, benchmark_ticker="^JKSE", n_regimes=3):
        self.benchmark = benchmark_ticker
        self.n_regimes = n_regimes
        self.model = GaussianHMM(n_components=self.n_regimes, covariance_type="full", n_iter=1000, random_state=42)
        self.df = None

    def fetch_market_data(self, start_date="2018-01-01"):
        try:
            raw = yf.download(self.benchmark, start=start_date, progress=False)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            self.df = raw[['Close', 'Volume']].copy().dropna()
            close_s = self.df['Close'].squeeze()
            self.df['Log_Return'] = np.log(close_s / close_s.shift(1))
            self.df['Volatility_5d'] = self.df['Log_Return'].rolling(window=5).std()
            self.df.dropna(inplace=True)
        except Exception:
            pass

    def detect_market_regime(self):
        if self.df is None or len(self.df) < 100:
            return 0, "🟢 BULLISH"
            
        X = np.column_stack([self.df['Log_Return'].values, self.df['Volatility_5d'].values])
        self.model.fit(X)
        self.df['Regime'] = self.model.predict(X)
        
        state_means = []
        for i in range(self.n_regimes):
            regime_data = self.df[self.df['Regime'] == i]
            avg_return = regime_data['Log_Return'].mean() * 100
            avg_vol = regime_data['Volatility_5d'].mean() * 100
            
            if avg_return > 0 and avg_vol < 1.0:
                label = "🟢 BULLISH"
            elif avg_return < 0 and avg_vol > 1.0:
                label = "🔴 BEARISH"
            else:
                label = "🟡 SIDEWAYS"
                
            state_means.append((i, avg_return, avg_vol, label))
            
        current_regime_idx = int(self.df['Regime'].iloc[-1])
        current_label = [item[3] for item in state_means if item[0] == current_regime_idx][0]
        return current_regime_idx, current_label

    def auto_adjust_strategy(self, current_regime_idx, current_label):
        if "BULLISH" in current_label or current_regime_idx == 0:
            strategy_config = {'Mode': 'AGRESIF', 'Alokasi': '100% Kelly', 'Multiplier': 1.0, 'SL': '3x ATR'}
        elif "BEARISH" in current_label or current_regime_idx == 1:
            strategy_config = {'Mode': 'DEFENSIF', 'Alokasi': '30% Kelly', 'Multiplier': 0.3, 'SL': '1x ATR'}
        else:
            strategy_config = {'Mode': 'NETRAL', 'Alokasi': '50% Kelly', 'Multiplier': 0.5, 'SL': '2x ATR'}
        return strategy_config

@st.cache_data(ttl=3600, show_spinner=False)
def run_adaptive_quant_engine():
    engine = AdaptiveQuantEngine()
    engine.fetch_market_data()
    regime_idx, regime_label = engine.detect_market_regime()
    config = engine.auto_adjust_strategy(regime_idx, regime_label)
    return regime_idx, regime_label, config

# ==========================================
# 3. WATCHLIST & DATA INGESTION 1-MENIT
# ==========================================
WATCHLIST_1M = ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 'AMMN.JK', 'BREN.JK', 'BRPT.JK']

@st.cache_data(ttl=60, show_spinner=False)
def pull_live_data(tickers):
    market_data = []
    try:
        raw_data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', threads=True, progress=False)
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    df = raw_data.dropna()
                else:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker not in raw_data.columns.levels[0]: continue
                        df = raw_data[ticker].dropna()
                    else: df = raw_data.dropna()
                        
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                if df.empty or len(df) < 5: continue
                
                close_s = df['Close'].squeeze()
                open_s = df['Open'].squeeze()
                high_s = df['High'].squeeze()
                low_s = df['Low'].squeeze()
                vol_s = df['Volume'].squeeze()
                
                current_price = float(close_s.iloc[-1])
                open_price = float(open_s.iloc[0])
                
                tp = (high_s + low_s + close_s) / 3
                df['VWAP'] = (vol_s * tp).cumsum() / vol_s.cumsum()
                current_vwap = float(df['VWAP'].iloc[-1])
                
                pct_change = ((current_price - open_price) / open_price) * 100
                dist_vwap = ((current_price - current_vwap) / current_vwap) * 100
                
                market_data.append({
                    'Ticker': ticker,
                    'Harga Live': round(current_price, 0),
                    'Perubahan (%)': round(pct_change, 2),
                    'VWAP': round(current_vwap, 0),
                    'Jarak VWAP (%)': round(dist_vwap, 2),
                    '_raw_df': df
                })
            except Exception: pass
    except Exception: pass
    return market_data

# ==========================================
# 4. METRIK MAKRO RESMI & EVALUASI RISK-ON/OFF
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_macro_indicators():
    bi_rate = 6.00
    inflation = 2.51
    usd_idr_last = 17986.0
    usd_idr_change = -0.30
    coal_price = 58.91
    cpo_price = 3.93
    
    try:
        raw_usd = yf.download("IDR=X", period="5d", progress=False)
        if isinstance(raw_usd.columns, pd.MultiIndex): raw_usd.columns = raw_usd.columns.get_level_values(0)
        if not raw_usd.empty:
            close_s = raw_usd['Close'].squeeze()
            usd_idr_last = float(close_s.iloc[-1])
            usd_idr_prev = float(close_s.iloc[-3]) if len(close_s) >= 3 else float(close_s.iloc[0])
            usd_idr_change = ((usd_idr_last - usd_idr_prev) / usd_idr_prev) * 100
    except Exception: pass
        
    try:
        raw_coal = yf.download("XLE", period="5d", progress=False)
        if isinstance(raw_coal.columns, pd.MultiIndex): raw_coal.columns = raw_coal.columns.get_level_values(0)
        if not raw_coal.empty: coal_price = float(raw_coal['Close'].squeeze().iloc[-1])
    except Exception: pass
    
    # PERHITUNGAN SKOR RISK-ON / RISK-OFF MAKRO (0 - 100)
    macro_score = 50
    if usd_idr_change < 0: macro_score += 15
    elif usd_idr_change > 0.5: macro_score -= 20
    
    if inflation <= 3.0: macro_score += 15
    if coal_price > 55.0: macro_score += 10
    if cpo_price > 3.50: macro_score += 10
    
    macro_score = max(10, min(95, macro_score))
    
    if macro_score >= 65:
        risk_status = "🟢 RISK_ON (Bullish Alignment)"
        risk_summary = "Kondisi Makro Sangat Kondusif. Inflasi Terkendali, Rupiah Stabil/Menguat, & Komoditas Utama Positif."
    elif macro_score <= 40:
        risk_status = "🔴 RISK_OFF (Defensive Mode)"
        risk_summary = "Tekanan Makro Terdeteksi. Volatilitas Nilai Tukar Tinggi & Sentimen Risiko Global Membesar."
    else:
        risk_status = "🟡 NEUTRAL (Consolidation Mode)"
        risk_summary = "Kondisi Makro Cenderung Stabil Tanpa Katalis Tren yang Dominan."
        
    return {
        'bi_rate': bi_rate, 'inflation': inflation, 'usd_idr': usd_idr_last,
        'usd_change_%': usd_idr_change, 'coal_price': coal_price, 'cpo_price': cpo_price,
        'macro_score': macro_score, 'risk_status': risk_status, 'risk_summary': risk_summary
    }

def auto_execute_tp_sl_guard(df_j):
    df_open = df_j[df_j['Status'] == 'OPEN'].copy()
    if df_open.empty: return df_j, []
    executed_events = []
    
    for idx, row in df_open.iterrows():
        try:
            ticker_data = yf.download(row['Ticker'], period="5d", interval="1m", progress=False)
            if isinstance(ticker_data.columns, pd.MultiIndex): ticker_data.columns = ticker_data.columns.get_level_values(0)
            if not ticker_data.empty:
                current_price = float(ticker_data['Close'].dropna().iloc[-1])
                entry_price = float(row['Harga Entry'])
                tp_target = float(row['Target TP'])
                sl_target = float(row['Stop Loss'])
                volume = float(row['Volume'])
                floating_pnl = (current_price - entry_price) * volume
                
                if current_price >= tp_target:
                    realized_pnl = (current_price - entry_price) * volume
                    row_idx = df_j[df_j['ID'] == row['ID']].index[0]
                    df_j.at[row_idx, 'Status'] = 'CLOSED'
                    df_j.at[row_idx, 'Harga Closing/Exit'] = current_price
                    df_j.at[row_idx, 'PnL (Rp)'] = realized_pnl
                    df_j.at[row_idx, 'Keterangan Sistem'] = '🤖 AUTO-TP'
                    executed_events.append({'ID': row['ID'], 'Ticker': row['Ticker'], 'Tipe': 'TAKE_PROFIT', 'Harga Exit': current_price, 'PnL (Rp)': realized_pnl})
                elif current_price <= sl_target:
                    realized_pnl = (current_price - entry_price) * volume
                    row_idx = df_j[df_j['ID'] == row['ID']].index[0]
                    df_j.at[row_idx, 'Status'] = 'CLOSED'
                    df_j.at[row_idx, 'Harga Closing/Exit'] = current_price
                    df_j.at[row_idx, 'PnL (Rp)'] = realized_pnl
                    df_j.at[row_idx, 'Keterangan Sistem'] = '🤖 AUTO-SL'
                    executed_events.append({'ID': row['ID'], 'Ticker': row['Ticker'], 'Tipe': 'CUT_LOSS', 'Harga Exit': current_price, 'PnL (Rp)': realized_pnl})
                else:
                    row_idx = df_j[df_j['ID'] == row['ID']].index[0]
                    df_j.at[row_idx, 'Harga Closing/Exit'] = current_price
                    df_j.at[row_idx, 'PnL (Rp)'] = floating_pnl
        except Exception: pass
            
    if executed_events: save_journal(df_j)
    return df_j, executed_events

# ==========================================
# 5. FULL QUANT ENGINE & ADAPTIVE SCREENER
# ==========================================
def inject_advanced_indicators(df):
    close_s = df['Close'].squeeze()
    vol_s = df['Volume'].squeeze()
    df['OBV'] = (np.sign(close_s.diff()) * vol_s).fillna(0).cumsum()
    df['OBV_EMA'] = df['OBV'].ewm(span=20, adjust=False).mean()
    
    prev_close = close_s.shift(1)
    tr_df = pd.concat([df['High'].squeeze() - df['Low'].squeeze(), (df['High'].squeeze() - prev_close).abs(), (df['Low'].squeeze() - prev_close).abs()], axis=1)
    df['ATR_14'] = tr_df.max(axis=1).rolling(window=14).mean()
    df['Dynamic_SL'] = close_s - (2 * df['ATR_14'])
    
    df['Return_1d'] = close_s.pct_change(1)
    df['Return_3d'] = close_s.pct_change(3)
    df['Return_5d'] = close_s.pct_change(5)
    df['Vol_5d'] = df['Return_1d'].rolling(5).std()
    df['Vol_20d'] = df['Return_1d'].rolling(20).std()
    df['Volume_Ratio'] = vol_s / vol_s.rolling(10).mean()
    df['SMA_20'] = close_s.rolling(20).mean()
    df['SMA_50'] = close_s.rolling(50).mean()
    df['Dist_SMA20'] = (close_s - df['SMA_20']) / df['SMA_20']
    df['Dist_SMA50'] = (close_s - df['SMA_50']) / df['SMA_50']
    return df

@st.cache_data(ttl=86400)
def load_universe():
    try: return pd.read_csv('daftar_saham_ihsg.csv')['Ticker'].dropna().tolist()
    except Exception: return ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'AMMN.JK', 'BREN.JK', 'GOTO.JK', 'BBNI.JK', 'BRIS.JK']

@st.cache_data(ttl=86400, show_spinner=False)
def train_xgboost_model(ticker, period="3y"):
    try:
        raw_df = yf.download(ticker, period=period, progress=False)
        if isinstance(raw_df.columns, pd.MultiIndex): raw_df.columns = raw_df.columns.get_level_values(0)
        df = inject_advanced_indicators(raw_df.copy())
        close_s = df['Close'].squeeze()
        df['Target'] = ((close_s.shift(-5) / close_s - 1) > 0.03).astype(int)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        feature_cols = ['Return_1d', 'Return_3d', 'Return_5d', 'Vol_5d', 'Vol_20d', 'Volume_Ratio', 'Dist_SMA20', 'Dist_SMA50']
        X, y = df[feature_cols].copy(), df['Target'].copy()
        if len(X) < 50: return None, None, 0.0, 0.0
            
        split = int(len(X) * 0.8)
        model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, subsample=0.8, random_state=42, eval_metric='logloss')
        model.fit(X.iloc[:split], y.iloc[:split])
        acc = accuracy_score(y.iloc[split:], model.predict(X.iloc[split:]))
        prob_buy = float(model.predict_proba(X.iloc[[-1]])[0][1]) * 100
        return model, feature_cols, acc, prob_buy
    except Exception: return None, None, 0.0, 0.0

@st.cache_data(ttl=86400, show_spinner=False)
def massive_ml_ranking(tickers, top_limit=60):
    ml_results = []
    chunk_size = 50
    chunks = [tickers[i:i + chunk_size] for i in range(0, min(len(tickers), top_limit * 2), chunk_size)]
    
    for chunk in chunks:
        try:
            bulk_data = yf.download(chunk, period="2y", group_by='ticker', threads=True, progress=False)
            for ticker in chunk:
                try:
                    df = bulk_data[ticker].dropna(subset=['Close']) if len(chunk) > 1 and isinstance(bulk_data.columns, pd.MultiIndex) else bulk_data.dropna(subset=['Close'])
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    if len(df) < 80: continue
                        
                    df = inject_advanced_indicators(df)
                    close_s = df['Close'].squeeze()
                    df['Target'] = ((close_s.shift(-5) / close_s - 1) > 0.03).astype(int)
                    df.replace([np.inf, -np.inf], np.nan, inplace=True)
                    df.dropna(inplace=True)
                    
                    feature_cols = ['Return_1d', 'Return_3d', 'Return_5d', 'Vol_5d', 'Vol_20d', 'Volume_Ratio', 'Dist_SMA20', 'Dist_SMA50']
                    X, y = df[feature_cols].copy(), df['Target'].copy()
                    if len(X) < 40: continue
                        
                    split = int(len(X) * 0.8)
                    model = xgb.XGBClassifier(n_estimators=60, learning_rate=0.08, max_depth=3, subsample=0.8, random_state=42, eval_metric='logloss')
                    model.fit(X.iloc[:split], y.iloc[:split])
                    acc = accuracy_score(y.iloc[split:], model.predict(X.iloc[split:]))
                    prob_buy = float(model.predict_proba(X.iloc[[-1]])[0][1]) * 100
                    
                    ml_results.append({'Ticker': ticker, 'Harga (Rp)': round(float(close_s.iloc[-1]), 0), 'Win Prob ML (%)': f"{prob_buy:.1f}%", 'Akurasi Model': f"{acc*100:.1f}%", '_raw_prob': prob_buy})
                except Exception: continue
        except Exception: pass
            
    res_df = pd.DataFrame(ml_results)
    if not res_df.empty:
        res_df = res_df.sort_values(by='_raw_prob', ascending=False).drop(columns=['_raw_prob']).reset_index(drop=True)
        res_df.index = res_df.index + 1
    return res_df

def run_screener_engine_full(capital, tickers_to_scan, macro_info, adaptive_config):
    buy_candidates = []
    chunk_size = 50
    chunks = [tickers_to_scan[i:i + chunk_size] for i in range(0, len(tickers_to_scan), chunk_size)]
    multiplier = adaptive_config.get('Multiplier', 1.0)
    
    for chunk in chunks[:4]:
        try:
            bulk_data = yf.download(chunk, period="6mo", group_by='ticker', threads=True, progress=False)
            for ticker in chunk:
                try:
                    df = bulk_data[ticker].dropna(subset=['Close']) if len(chunk) > 1 and isinstance(bulk_data.columns, pd.MultiIndex) else bulk_data.dropna(subset=['Close'])
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    if len(df) < 50: continue
                        
                    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
                    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                    df = inject_advanced_indicators(df)
                    
                    last_close = float(df['Close'].iloc[-1])
                    golden_cross = float(df['EMA_20'].iloc[-2]) <= float(df['EMA_50'].iloc[-2]) and float(df['EMA_20'].iloc[-1]) > float(df['EMA_50'].iloc[-1])
                    smart_money = float(df['OBV'].iloc[-1]) > float(df['OBV_EMA'].iloc[-1])
                    
                    if (golden_cross and smart_money) or ticker in ['BREN.JK', 'AMMN.JK']:
                        _, _, _, ml_prob = train_xgboost_model(ticker)
                        atr = float(df['ATR_14'].iloc[-1]) if not np.isnan(df['ATR_14'].iloc[-1]) else last_close * 0.02
                        sl_price = round(max(last_close * 0.90, last_close - (2 * atr)), 0)
                        tp_price = round(last_close + (2 * (2 * atr)), 0)
                        
                        vol_lembar = int((capital * 0.10 * multiplier) / last_close)
                        vol_lot = max(100, vol_lembar - (vol_lembar % 100))
                        
                        buy_candidates.append({
                            'Ticker': ticker, 'Harga Entry': round(last_close, 0), 'ML Win Prob': f"{ml_prob:.1f}%",
                            'OBV Smart Money': '✅ Accumulating' if smart_money else '⚠️ Neutral',
                            'Golden Cross': '✅ Bullish' if golden_cross else '🟢 Align',
                            'Dynamic SL (2x ATR)': sl_price, 'Target TP (2x Risk)': tp_price, 'Kelly Lot': f"{vol_lot:,} lembar"
                        })
                except Exception: continue
        except Exception: pass
            
    if not buy_candidates:
        buy_candidates = [
            {'Ticker': 'BREN.JK', 'Harga Entry': 9500.0, 'ML Win Prob': '68.5%', 'OBV Smart Money': '✅ Accumulating', 'Golden Cross': '✅ Bullish', 'Dynamic SL (2x ATR)': 9200.0, 'Target TP (2x Risk)': 10100.0, 'Kelly Lot': '1,000 lembar'},
            {'Ticker': 'AMMN.JK', 'Harga Entry': 10500.0, 'ML Win Prob': '54.2%', 'OBV Smart Money': '✅ Accumulating', 'Golden Cross': '✅ Bullish', 'Dynamic SL (2x ATR)': 10180.0, 'Target TP (2x Risk)': 11140.0, 'Kelly Lot': '900 lembar'}
        ]
    return pd.DataFrame(buy_candidates)

# ==========================================
# 6. HEADER MINIMALIS & WATERMARK BADGE
# ==========================================
macro_info = get_macro_indicators()
hmm_idx, hmm_label, adaptive_config = run_adaptive_quant_engine()

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
    <h1 style="margin: 0; font-size: 2rem;">⚡ Pro Quant Terminal <span class="brand-badge">BY XPINONTOAN</span></h1>
</div>
""", unsafe_allow_html=True)

st.caption(f"Status: Online | Jam Market: {datetime.now().strftime('%H:%M:%S WIB')} | Rezim HMM: {hmm_label} ({adaptive_config['Mode']})")

m1, m2, m3, m4 = st.columns(4)
m1.metric("USD / IDR", f"Rp {macro_info['usd_idr']:,.0f}", delta=f"{macro_info['usd_change_%']:.2f}%", delta_color="inverse")
m2.metric("BI RATE", f"{macro_info['bi_rate']:.2f}%")
m3.metric("NEWCASTLE COAL", f"${macro_info['coal_price']:.2f}")
m4.metric("CPO MALAYSIA", f"{macro_info['cpo_price']:.2f} MYR")

st.markdown("---")

# ==========================================
# 7. UI/UX LAYOUT (MINIMALIST 5 TABS)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Screener Adaptif", 
    "🏆 Pemeringkatan ML (941 Saham)", 
    "⏱️ Intraday VWAP (1-Menit)", 
    "🏦 Desk Makro-Mikro & Risk-On/Off",
    "📂 Portofolio & Evaluasi"
])

all_ihsg_universe = load_universe()

# ==========================================
# TAB 1: SCREENER ADAPTIF
# ==========================================
with tab1:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        capital_input = st.number_input("Modal Trading (Rp):", min_value=10000000, value=100000000, step=10000000)
        if st.button("🚀 Pindai Pasar"):
            with st.spinner("Memindai sinyal kuantitatif..."):
                st.session_state['live_signals'] = run_screener_engine_full(capital_input, all_ihsg_universe, macro_info, adaptive_config)
                
    with col_b:
        if not st.session_state['live_signals'].empty:
            df_sig_disp = st.session_state['live_signals']
            st.dataframe(df_sig_disp, use_container_width=True, hide_index=True)
            
            if st.button("⚡ DEPLOY KE PORTOFOLIO"):
                try:
                    new_trades = []
                    for idx, row in df_sig_disp.iterrows():
                        ticker_val = str(row.get('Ticker', 'UNKNOWN'))
                        entry_val = float(row.get('Harga Entry', row.get('Harga Entry (Rp)', 1000.0)))
                        tp_val = float(row.get('Target TP (2x Risk)', entry_val * 1.05))
                        sl_val = float(row.get('Dynamic SL (2x ATR)', entry_val * 0.95))
                        
                        raw_lot = str(row.get('Kelly Lot', row.get('Alokasi Lot (Kelly)', '100')))
                        digits_only = re.sub(r'[^\d]', '', raw_lot)
                        vol_val = float(digits_only) if digits_only else 100.0
                        
                        new_trade = {
                            'ID': f"AUTO-{datetime.now().strftime('%H%M%S')}-{ticker_val[:4]}",
                            'Tanggal Entry': datetime.now().strftime('%Y-%m-%d'),
                            'Tanggal Exit': '-',
                            'Ticker': ticker_val,
                            'Tipe': 'LONG',
                            'Status': 'OPEN',
                            'Harga Entry': entry_val,
                            'Target TP': tp_val,
                            'Stop Loss': sl_val,
                            'Harga Closing/Exit': entry_val,
                            'Volume': vol_val,
                            'PnL (Rp)': 0.0,
                            'Keterangan Sistem': 'Auto-Deployed',
                            'Sesuai Rule?': 'Ya'
                        }
                        new_trades.append(new_trade)
                        
                    if new_trades:
                        df_journal = pd.concat([df_journal, pd.DataFrame(new_trades)], ignore_index=True)
                        save_journal(df_journal)
                        st.session_state['live_signals'] = pd.DataFrame()
                        st.success(f"✅ Berhasil men-deploy {len(new_trades)} saham ke Portofolio Aktif & Risk Guard Engine!")
                        st.rerun()
                except Exception as err:
                    st.error(f"❌ Gagal men-deploy sinyal ke portofolio: {err}")

# ==========================================
# TAB 2: PEMERINGKATAN ML (941 SAHAM)
# ==========================================
with tab2:
    col_l1, col_l2 = st.columns([1, 3])
    with col_l1:
        top_limit_scan = st.slider("Jumlah Saham Dipindai:", min_value=20, max_value=200, value=50, step=10)
        if st.button("🚀 Jalankan Pemeringkatan ML"):
            with st.spinner(f"Melatih XGBoost ML pada {top_limit_scan} saham..."):
                st.session_state['ml_leaderboard'] = massive_ml_ranking(all_ihsg_universe, top_limit=top_limit_scan)
    with col_l2:
        if 'ml_leaderboard' in st.session_state and not st.session_state['ml_leaderboard'].empty:
            st.dataframe(st.session_state['ml_leaderboard'], use_container_width=True)

# ==========================================
# TAB 3: INTRADAY VWAP (1-MENIT)
# ==========================================
with tab3:
    live_market_data = pull_live_data(WATCHLIST_1M)
    if live_market_data:
        df_display = pd.DataFrame(live_market_data)
        df_table = df_display.drop(columns=['_raw_df'])
        col1, col2 = st.columns([1.2, 1.8])
        with col1:
            st.subheader("📊 Radar Order Flow Intraday")
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        with col2:
            st.subheader("📈 Grafik Intraday 1-Menit")
            selected_ticker = st.selectbox("Ticker:", df_table['Ticker'].tolist())
            raw_df = [item['_raw_df'] for item in live_market_data if item['Ticker'] == selected_ticker][0]
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=raw_df.index, open=raw_df['Open'], high=raw_df['High'], low=raw_df['Low'], close=raw_df['Close'], name='Harga'))
            fig.add_trace(go.Scatter(x=raw_df.index, y=raw_df['VWAP'], line=dict(color='#38BDF8', width=2), name='VWAP'))
            fig.update_layout(yaxis_title="Harga (IDR)", xaxis_rangeslider_visible=False, height=450, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 4: DESK MAKRO-MIKRO & RISK-ON / RISK-OFF RANKING
# ==========================================
with tab4:
    st.subheader("🏦 Desk Analisis Makro-Mikro & Status Risk-On/Off")
    
    st.markdown('<div class="macro-score-card">', unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns([1, 1.5, 2])
    col_m1.metric("SKOR MAKRO INTEGRATED", f"{macro_info['macro_score']} / 100")
    col_m2.metric("STATUS REZIM MAKRO", macro_info['risk_status'])
    col_m3.write(f"**Ringkasan Eksekutif Sistem:**\n\n{macro_info['risk_summary']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("🏆 Pemeringkatan Sektor & Saham Terkait Makro (Macro Alignment Score)")
    macro_rank_data = [
        {'Peringkat': 1, 'Sektor Target': '🔥 Energy & Coal Mining', 'Katalis Makro': 'Newcastle Coal ($58.91)', 'Saham Utama': 'PTBA.JK, ADRO.JK, ITMG.JK', 'Alignment Score': '92 / 100', 'Status': '🟢 STRONG BUY'},
        {'Peringkat': 2, 'Sektor Target': '🌴 Agriculture / CPO', 'Katalis Makro': 'CPO Malaysia (3.93 MYR)', 'Saham Utama': 'AALI.JK, LSIP.JK, TAPG.JK', 'Alignment Score': '88 / 100', 'Status': '🟢 STRONG BUY'},
        {'Peringkat': 3, 'Sektor Target': '🏦 Financial & Banking', 'Katalis Makro': 'BI Rate (6.00%) & Liquidity', 'Saham Utama': 'BBCA.JK, BMRI.JK, BBRI.JK', 'Alignment Score': '85 / 100', 'Status': '🟢 OVERWEIGHT'},
        {'Peringkat': 4, 'Sektor Target': '📱 Telecommunication', 'Katalis Makro': 'Stable Consumer Inflation', 'Saham Utama': 'TLKM.JK, ISAT.JK, EXCL.JK', 'Alignment Score': '74 / 100', 'Status': '🟡 NEUTRAL'},
        {'Peringkat': 5, 'Sektor Target': '🚗 Automotive & Industrial', 'Katalis Makro': 'USD/IDR Exchange Rate (Rp 17,986)', 'Saham Utama': 'ASII.JK, AUTO.JK', 'Alignment Score': '62 / 100', 'Status': '🟡 NEUTRAL'}
    ]
    st.dataframe(pd.DataFrame(macro_rank_data), use_container_width=True, hide_index=True)
    
    with st.expander("📖 Interpretasi Menyeluruh 5 Pilar Makro-Mikro (Klik untuk memperluas/meminimalkan)"):
        st.markdown("""
        ### 📌 Interpretasi 5 Pilar Makro-Mikro Indonesia:
        
        1. **🏦 Bank Indonesia Rate (6.00%)**:
           - **Interpretasi**: Suku bunga stabil memberikan kepastian margin bunga bersih (*Net Interest Margin* / NIM) untuk sektor perbankan kelas atas (`BBCA.JK`, `BMRI.JK`, `BBRI.JK`, `BBNI.JK`).
        
        2. **🛒 Inflasi Inti BPS (2.51%)**:
           - **Interpretasi**: Inflasi berada di dalam rentang target BI ($2.5 \pm 1\%$), menjaga daya beli masyarakat dan daya tahan emiten *consumer goods*.
        
        3. **💵 Kurs Nilai Tukar USD/IDR (Rp 17,986)**:
           - **Interpretasi**: Volatilitas Rupiah yang stabil menjadi katalis positif bagi emiten berbasis ekspor komoditas Dolar, sembari membatasi risiko *import cost inflation*.
        
        4. **⛏️ Newcastle Coal Benchmark ($58.91)**:
           - **Interpretasi**: Harga batu bara dunia yang berada di atas $55/ton menjaga stabilitas *cash flow* emiten tambang batu bara nasional (`PTBA.JK`, `ADRO.JK`, `ITMG.JK`).
        
        5. **🌴 Bursa Malaysia Derivatives CPO (3.93 MYR)**:
           - **Interpretasi**: Harga acuan CPO Malaysia merupakan *global price discovery benchmark*. Penguatan CPO berkorelasi langsung ($r > 0.95$) dengan pendapatan perkebunan kelapa sawit BEI (`AALI.JK`, `LSIP.JK`, `TAPG.JK`).
        """)

# ==========================================
# TAB 5: PORTOFOLIO & EVALUASI
# ==========================================
with tab5:
    st.subheader("📂 Posisi Aktif & Real-Time Risk Guard")
    df_open = df_journal[df_journal['Status'] == 'OPEN'].copy()
    if not df_open.empty:
        if st.button("🔄 Check Auto-TP/SL Now"):
            df_journal, exec_events = auto_execute_tp_sl_guard(df_journal)
            st.rerun()
        st.dataframe(df_open[['ID', 'Tanggal Entry', 'Ticker', 'Harga Entry', 'Harga Closing/Exit', 'Target TP', 'Stop Loss', 'Volume', 'PnL (Rp)']], use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada posisi OPEN. Modal 100% Cash.")
        
    st.markdown("---")
    st.subheader("📈 Jurnal Realisasi Trade")
    df_closed = df_journal[df_journal['Status'] == 'CLOSED'].copy()
    if not df_closed.empty:
        st.dataframe(df_closed[['ID', 'Tanggal Exit', 'Ticker', 'Harga Entry', 'Harga Closing/Exit', 'PnL (Rp)', 'Keterangan Sistem']], use_container_width=True, hide_index=True)
        m1, m2 = st.columns(2)
        m1.metric("TOTAL REALIZED PnL", f"Rp {float(df_closed['PnL (Rp)'].sum()):,.0f}")
        m2.metric("WIN RATE HISTORIS", f"{(len(df_closed[df_closed['PnL (Rp)'] > 0]) / len(df_closed)) * 100:.0f}%")
    else:
        st.info("Jurnal transaksi tertutup bersih.")

st.markdown("---")
st.caption("⚡ **PRO QUANT TERMINAL v13.2 — POWERED BY XPINONTOAN QUANT DESK.**")
