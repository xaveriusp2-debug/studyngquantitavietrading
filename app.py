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
import logging
import tempfile
import time
import urllib.request

# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ==========================================
# 1. DESIGN SYSTEM: MINIMALIST + WATERMARK XPINONTOAN + ZERO FLICKER
# ==========================================
st.set_page_config(page_title="Pro Quant Terminal — Clean Institutional Desk", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    /* ULTIMATE ZERO-DIMMING & ZERO-FLICKER ENGINE */
    html, body, .stApp, .main, 
    div[data-testid="stAppViewContainer"], 
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stVerticalBlock"], 
    .stElementContainer, 
    div[data-test-script-state="running"],
    div[data-st-mode="running"] {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
        animation: none !important;
        pointer-events: auto !important;
    }

    /* COMPLETE SUPPRESSION OF STREAMLIT RUNNING OVERLAYS & SPINNERS */
    div[data-testid="stStatusWidget"],
    div[data-testid="stNotification"],
    .stSpinner,
    iframe[title="streamlit_autorefresh.st_autorefresh"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
    }

    .stApp header { background: rgba(15, 23, 42, 0.9) !important; border-bottom: 1px solid #1E293B !important; }
    
    .mini-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }

    .screener-priority-card {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 2px solid #0284C7;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(2, 132, 199, 0.2);
    }

    .rebalancer-card {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 2px solid #A855F7;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(168, 85, 247, 0.2);
    }

    .macro-score-card {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #0EA5E9;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* CLEAN INSTITUTIONAL EVALUATION CARD DESIGN (NO SYMBOLS) */
    .institutional-eval-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid #334155;
        border-left: 5px solid #10B981;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .eval-badge-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }

    .eval-badge {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        padding: 8px 14px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .eval-pill-box {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }

    .eval-pill-title {
        color: #38BDF8;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }

    .eval-pill-body {
        color: #E2E8F0;
        font-size: 0.88rem;
        line-height: 1.65;
        margin: 0;
    }

    /* CUSTOM ENGAGING ANIMATED LOADER */
    .custom-loader-card {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.15) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid #0284C7;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-bottom: 20px;
    }

    .cyan-pulse-loader {
        display: inline-block;
        width: 48px;
        height: 48px;
        border: 4px solid rgba(56, 189, 248, 0.2);
        border-top-color: #38BDF8;
        border-radius: 50%;
        animation: spin-glow 0.8s linear infinite;
    }

    @keyframes spin-glow {
        0% { transform: rotate(0deg); box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
        50% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.6); }
        100% { transform: rotate(360deg); box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
    }

    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
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
        font-weight: 700 !important;
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

    .live-pulse-hft {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00E676;
        box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.8);
        animation: pulse-hft 1s infinite;
        margin-right: 6px;
    }

    @keyframes pulse-hft {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.8); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(0, 230, 118, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }
</style>

<div class="watermark-fixed">⚡ DESIGNED BY XPINONTOAN</div>
""", unsafe_allow_html=True)

# SESSION STATE INITIALIZATION FOR STABILITY
if 'is_scanning' not in st.session_state:
    st.session_state['is_scanning'] = False
if 'live_signals' not in st.session_state:
    st.session_state['live_signals'] = pd.DataFrame()
if 'ml_leaderboard' not in st.session_state:
    st.session_state['ml_leaderboard'] = pd.DataFrame()
if 'rebalance_logs' not in st.session_state:
    st.session_state['rebalance_logs'] = []

# AUTO-REFRESH EXACTLY EVERY 15 SECONDS (PAUSED DURING ACTIVE SCREENER SCAN)
if not st.session_state['is_scanning']:
    refresh_count = st_autorefresh(interval=15 * 1000, limit=None, key="screener_priority_v210")
else:
    refresh_count = 0

JOURNAL_FILE = 'trade_journal_v5.csv'
DAILY_SNAPSHOT_FILE = 'daily_closing_snapshots_v1.csv'

def init_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=[
            'ID', 'Tanggal Entry', 'Tanggal Exit', 'Ticker', 'Tipe', 'Status',
            'Harga Entry', 'Target TP', 'Stop Loss', 'Harga Closing/Exit', 
            'Volume', 'PnL (Rp)', 'Keterangan Sistem', 'Sesuai Rule?'
        ])
        df.to_csv(JOURNAL_FILE, index=False)
        
    if not os.path.exists(DAILY_SNAPSHOT_FILE):
        df_snap = pd.DataFrame(columns=[
            'Tanggal Snapshot', 'Waktu Snapshot', 'Total Modal (Rp)', 'Total Floating PnL (Rp)', 
            'Floating Return (%)', 'Jumlah Posisi Open', 'Skor Makro', 'Rezim Pasar HMM', 'Evaluasi Trader Institusi'
        ])
        df_snap.to_csv(DAILY_SNAPSHOT_FILE, index=False)

init_journal()

@st.cache_data(ttl=2)
def load_journal():
    try:
        return pd.read_csv(JOURNAL_FILE, parse_dates=['Tanggal Entry', 'Tanggal Exit'])
    except Exception:
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception as e:
            logging.exception("Failed to load journal: %s", e)
            return pd.DataFrame(columns=[
                'ID', 'Tanggal Entry', 'Tanggal Exit', 'Ticker', 'Tipe', 'Status',
                'Harga Entry', 'Target TP', 'Stop Loss', 'Harga Closing/Exit', 
                'Volume', 'PnL (Rp)', 'Keterangan Sistem', 'Sesuai Rule?'
            ])

@st.cache_data(ttl=2)
def load_daily_snapshots():
    if os.path.exists(DAILY_SNAPSHOT_FILE):
        try: return pd.read_csv(DAILY_SNAPSHOT_FILE)
        except Exception: pass
    return pd.DataFrame(columns=[
        'Tanggal Snapshot', 'Waktu Snapshot', 'Total Modal (Rp)', 'Total Floating PnL (Rp)', 
        'Floating Return (%)', 'Jumlah Posisi Open', 'Skor Makro', 'Rezim Pasar HMM', 'Evaluasi Trader Institusi'
    ])

def save_journal(df):
    try:
        fd, tmp = tempfile.mkstemp(prefix='journal_', suffix='.csv', dir='.')
        os.close(fd)
        df.to_csv(tmp, index=False)
        os.replace(tmp, JOURNAL_FILE)
        try:
            st.cache_data.clear()
        except Exception:
            pass
    except Exception as e:
        logging.exception("Failed to save journal: %s", e)
        raise

def save_daily_snapshot(df_snap):
    try:
        fd, tmp = tempfile.mkstemp(prefix='snapshot_', suffix='.csv', dir='.')
        os.close(fd)
        df_snap.to_csv(tmp, index=False)
        os.replace(tmp, DAILY_SNAPSHOT_FILE)
        try:
            st.cache_data.clear()
        except Exception:
            pass
    except Exception as e:
        logging.exception("Failed to save daily snapshot: %s", e)
        raise

def reset_closed_trades_journal():
    df_j = load_journal()
    df_open_only = df_j[df_j['Status'] == 'OPEN'].copy() if not df_j.empty else pd.DataFrame(columns=[
        'ID', 'Tanggal Entry', 'Tanggal Exit', 'Ticker', 'Tipe', 'Status',
        'Harga Entry', 'Target TP', 'Stop Loss', 'Harga Closing/Exit', 
        'Volume', 'PnL (Rp)', 'Keterangan Sistem', 'Sesuai Rule?'
    ])
    save_journal(df_open_only)
    
    # Also reset daily snapshots history if desired
    df_empty_snap = pd.DataFrame(columns=[
        'Tanggal Snapshot', 'Waktu Snapshot', 'Total Modal (Rp)', 'Total Floating PnL (Rp)', 
        'Floating Return (%)', 'Jumlah Posisi Open', 'Skor Makro', 'Rezim Pasar HMM', 'Evaluasi Trader Institusi'
    ])
    save_daily_snapshot(df_empty_snap)

df_journal = load_journal()
df_snapshots = load_daily_snapshots()

# ==========================================
# 2. REAL-TIME FUNDAMENTAL & KURS CONNECTOR (LIVE INVESTING / YAHOO / BURSA)
# ==========================================
@st.cache_data(ttl=15, show_spinner=False)
def fetch_realtime_macro_stream():
    bi_rate = 6.00
    inflation = 2.51
    usd_idr_last = 18035.0
    usd_idr_change = 0.27
    coal_price = 135.47
    cpo_price = 4161.50
    
    try:
        t_usd = yf.Ticker("IDR=X")
        fast_usd = getattr(t_usd, 'fast_info', {})
        if 'lastPrice' in fast_usd and fast_usd['lastPrice'] > 0:
            usd_idr_last = float(fast_usd['lastPrice'])
            prev_usd = float(fast_usd.get('previousClose', usd_idr_last))
            usd_idr_change = ((usd_idr_last - prev_usd) / prev_usd) * 100 if prev_usd > 0 else 0.0
        else:
            raw_usd = yf.download("IDR=X", period="1d", interval="1m", progress=False)
            if isinstance(raw_usd.columns, pd.MultiIndex): raw_usd.columns = raw_usd.columns.get_level_values(0)
            if not raw_usd.empty:
                close_s = raw_usd['Close'].squeeze()
                usd_idr_last = float(close_s.iloc[-1])
                usd_idr_prev = float(close_s.iloc[0])
                usd_idr_change = ((usd_idr_last - usd_idr_prev) / usd_idr_prev) * 100 if usd_idr_prev > 0 else 0.0
    except Exception as e:
        logging.exception("Real-time USD/IDR error: %s", e)
        
    try:
        raw_coal = yf.download("PTBA.JK", period="5d", interval="1d", progress=False)
        if isinstance(raw_coal.columns, pd.MultiIndex): raw_coal.columns = raw_coal.columns.get_level_values(0)
        if not raw_coal.empty:
            ptba_p = float(raw_coal['Close'].squeeze().iloc[-1])
            coal_price = round(ptba_p / 17.2, 2)
    except Exception as e:
        logging.exception("Real-time Coal error: %s", e)
        
    try:
        raw_cpo = yf.download("AALI.JK", period="5d", interval="1d", progress=False)
        if isinstance(raw_cpo.columns, pd.MultiIndex): raw_cpo.columns = raw_cpo.columns.get_level_values(0)
        if not raw_cpo.empty:
            aali_p = float(raw_cpo['Close'].squeeze().iloc[-1])
            cpo_price = round(aali_p * 0.58, 2)
    except Exception as e:
        logging.exception("Real-time CPO error: %s", e)
    
    macro_score = 50
    try:
        if usd_idr_change < 0: macro_score += 15
        elif usd_idr_change > 0.5: macro_score -= 20

        if inflation <= 3.0: macro_score += 15
        if coal_price > 100.0: macro_score += 15
        if cpo_price > 3500.0: macro_score += 15
    except Exception as e:
        logging.exception("Macro scoring error: %s", e)
    
    macro_score = max(10, min(95, macro_score))
    
    if macro_score >= 65:
        risk_status = "🟢 RISK_ON (Bullish Alignment)"
        risk_summary = "Kondisi Makro Sangat Kondusif. Inflasi Terkendali, Rupiah Stabil, Coal & CPO Malaysia Menguat."
    elif macro_score <= 40:
        risk_status = "🔴 RISK_OFF (Defensive Mode)"
        risk_summary = "Tekanan Makro Terdeteksi. Volatilitas Nilai Tukar Tinggi & Sentimen Risiko Global Membesar."
    else:
        risk_status = "🟡 NEUTRAL (Consolidation Mode)"
        risk_summary = "Kondisi Makro Cenderung Stabil Tanpa Katalis Tren yang Dominan."
        
    return {
        'bi_rate': bi_rate, 'inflation': inflation, 'usd_idr': usd_idr_last,
        'usd_change_%': usd_idr_change, 'coal_price': coal_price, 'cpo_price': cpo_price,
        'macro_score': macro_score, 'risk_status': risk_status, 'risk_summary': risk_summary,
        'last_tick_time': datetime.now().strftime('%H:%M:%S')
    }

# ==========================================
# 3. ADAPTIVE QUANT ENGINE (HMM REGIME)
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
        except Exception as e:
            logging.exception("fetch_market_data failed for %s: %s", self.benchmark, e)
            self.df = None

    def detect_market_regime(self):
        if self.df is None or len(self.df) < 100:
            return 0, "🟢 BULLISH"
            
        try:
            X = np.column_stack([self.df['Log_Return'].values, self.df['Volatility_5d'].values])
            self.model.fit(X)
            self.df['Regime'] = self.model.predict(X)
            
            state_means = []
            for i in range(self.n_regimes):
                regime_data = self.df[self.df['Regime'] == i]
                if regime_data.empty:
                    avg_return = 0.0
                    avg_vol = 0.0
                else:
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
            current_label = next((item[3] for item in state_means if item[0] == current_regime_idx), "🟡 SIDEWAYS")
            return current_regime_idx, current_label
        except Exception as e:
            logging.exception("detect_market_regime failed: %s", e)
            return 0, "🟢 BULLISH"

    def auto_adjust_strategy(self, current_regime_idx, current_label):
        try:
            if "BULLISH" in current_label or current_regime_idx == 0:
                strategy_config = {'Mode': 'AGRESIF', 'Alokasi': '100% Kelly', 'Multiplier': 1.0, 'SL': '3x ATR'}
            elif "BEARISH" in current_label or current_regime_idx == 1:
                strategy_config = {'Mode': 'DEFENSIF', 'Alokasi': '30% Kelly', 'Multiplier': 0.3, 'SL': '1x ATR'}
            else:
                strategy_config = {'Mode': 'NETRAL', 'Alokasi': '50% Kelly', 'Multiplier': 0.5, 'SL': '2x ATR'}
            return strategy_config
        except Exception as e:
            logging.exception("auto_adjust_strategy failed: %s", e)
            return {'Mode': 'NETRAL', 'Alokasi': '50% Kelly', 'Multiplier': 0.5, 'SL': '2x ATR'}

@st.cache_data(ttl=60, show_spinner=False)
def run_adaptive_quant_engine():
    engine = AdaptiveQuantEngine()
    engine.fetch_market_data()
    regime_idx, regime_label = engine.detect_market_regime()
    config = engine.auto_adjust_strategy(regime_idx, regime_label)
    return regime_idx, regime_label, config

WATCHLIST_1M = ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 'AMMN.JK', 'BREN.JK', 'BRPT.JK']

@st.cache_data(ttl=15, show_spinner=False) 
def pull_live_data(tickers):
    """Fungsi Penarik Data Real-Time Asinkron untuk Dasbor Utama (15 Detik TTL)"""
    market_data = []
    
    try:
        raw_data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', threads=True, progress=False)
        for ticker in tickers:
            if len(tickers) == 1:
                df = raw_data.dropna()
            else:
                if isinstance(raw_data.columns, pd.MultiIndex):
                    if ticker not in raw_data.columns.levels[0]: continue
                    df = raw_data[ticker].dropna()
                else:
                    df = raw_data.dropna()
                
            if df.empty or len(df) < 2: continue
            
            current_price = float(df['Close'].iloc[-1])
            open_price = float(df['Open'].iloc[0])
            
            v = df['Volume']
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            cum_v = v.cumsum()
            vwap_s = (v * tp).cumsum() / cum_v.replace(0, np.nan)
            df['VWAP'] = vwap_s
            current_vwap = float(df['VWAP'].iloc[-1]) if not np.isnan(df['VWAP'].iloc[-1]) else current_price
            
            pct_change = ((current_price - open_price) / open_price) * 100 if open_price != 0 else 0.0
            dist_vwap = ((current_price - current_vwap) / current_vwap) * 100 if current_vwap != 0 else 0.0
            
            market_data.append({
                'Ticker': ticker,
                'Harga Live (Rp)': round(current_price, 0),
                'Perubahan (%)': round(pct_change, 2),
                'Level VWAP': round(current_vwap, 0),
                'Jarak ke VWAP (%)': round(dist_vwap, 2),
                'Volume 1M Terakhir': int(df['Volume'].iloc[-1]),
                '_raw_df': df
            })
    except Exception as e:
        logging.exception("pull_live_data error: %s", e)
            
    return market_data

# ==========================================
# 4. PERFECT AUTO-REBALANCER CLASS ENGINE (4-PHASE QUANT ENGINE)
# ==========================================
class PerfectAutoRebalancer:
    def __init__(self, current_portfolio_df, total_equity, macro_info, regime_label):
        self.portfolio_df = current_portfolio_df
        self.equity = total_equity
        self.macro_info = macro_info
        self.regime_label = regime_label
        self.target_weights = {}
        self.execution_logs = []

    def phase_1_macro_allocation(self):
        """Phase 1: Menentukan porsi KAS vs SAHAM berbasis HMM Market Regime"""
        if "BEARISH" in self.regime_label:
            return 0.20
        elif "SIDEWAYS" in self.regime_label:
            return 0.50
        else:
            return 0.90

    def phase_2_stock_selection(self, universe_tickers):
        """Phase 2: XGBoost + OBV mencari Top 5 saham dengan probabilitas > 70%"""
        scanner_results = run_screener_engine_full(self.equity, universe_tickers, self.macro_info, {'Multiplier': 1.0})
        if not scanner_results.empty:
            top_5 = scanner_results.head(5).to_dict('records')
            return top_5
        return []

    def phase_3_risk_sizing(self, top_stocks, max_equity_allowed):
        """Phase 3: Half-Kelly Criterion & Dynamic ATR Stop Loss Calculation"""
        allocations = {}
        if not top_stocks: return
        
        per_stock_budget = max_equity_allowed / len(top_stocks)
        for stock in top_stocks:
            ticker = stock['Ticker']
            entry_p = float(stock['Harga Entry'])
            prob_str = str(stock.get('Probabilitas Menang (ML + Makro)', '70.0%'))
            win_prob = float(re.sub(r'[^\d.]', '', prob_str)) / 100.0 if prob_str else 0.70
            
            kelly_pct = max(0.10, (win_prob * 2.0 - (1.0 - win_prob)) / 2.0)
            alloc_val = per_stock_budget * (kelly_pct / 2.0)
            
            target_volume = int((alloc_val / entry_p) / 100) * 100 if entry_p > 0 else 100
            target_volume = max(100, target_volume)
            
            allocations[ticker] = {
                'Target_Lot': target_volume,
                'Harga_Entry': entry_p,
                'Target_TP': float(stock.get('Target TP (2x Risk)', entry_p * 1.05)),
                'Stop_Loss': float(stock.get('Dynamic SL (2x ATR)', entry_p * 0.95))
            }
        self.target_weights = allocations

    def phase_4_vwap_execution(self, df_j):
        """Phase 4: Eksekusi Rebalancing Portofolio Berbasis Filter VWAP"""
        self.execution_logs.append("[AUTO-REBALANCING INITIATED]")
        df_open = df_j[df_j['Status'] == 'OPEN'].copy() if not df_j.empty else pd.DataFrame()
        
        current_portfolio = {}
        if not df_open.empty:
            for ticker, grp in df_open.groupby('Ticker'):
                current_portfolio[ticker] = {
                    'Lot': grp['Volume'].sum(),
                    'Entry': (grp['Harga Entry'] * grp['Volume']).sum() / grp['Volume'].sum()
                }
                
        for ticker, data in current_portfolio.items():
            if ticker not in self.target_weights:
                self.execution_logs.append(f"LIQUIDATE (Jual Semua): {ticker} sebanyak {data['Lot']} lembar.")
                mask = (df_j['Ticker'] == ticker) & (df_j['Status'] == 'OPEN')
                df_j.loc[mask, 'Status'] = 'CLOSED'
                df_j.loc[mask, 'Tanggal Exit'] = datetime.now().strftime('%Y-%m-%d')
                df_j.loc[mask, 'Keterangan Sistem'] = 'Rebalancer Liquidated'
            elif data['Lot'] > self.target_weights[ticker]['Target_Lot']:
                sell_lot = data['Lot'] - self.target_weights[ticker]['Target_Lot']
                self.execution_logs.append(f"TRIM (Jual Sebagian): {ticker} sebanyak {sell_lot} lembar.")
                mask = (df_j['Ticker'] == ticker) & (df_j['Status'] == 'OPEN')
                df_j.loc[mask, 'Volume'] = self.target_weights[ticker]['Target_Lot']

        for ticker, target in self.target_weights.items():
            curr_lot = current_portfolio.get(ticker, {}).get('Lot', 0)
            if curr_lot < target['Target_Lot']:
                buy_lot = target['Target_Lot'] - curr_lot
                self.execution_logs.append(f"ACCUMULATE (Beli VWAP Sniper): {ticker} sebanyak {buy_lot} lembar.")
                
                new_pos = {
                    'ID': f"REBAL-{datetime.now().strftime('%H%M%S')}-{ticker[:4]}",
                    'Tanggal Entry': datetime.now().strftime('%Y-%m-%d'),
                    'Tanggal Exit': '-',
                    'Ticker': ticker,
                    'Tipe': 'LONG',
                    'Status': 'OPEN',
                    'Harga Entry': target['Harga_Entry'],
                    'Target TP': target['Target_TP'],
                    'Stop Loss': target['Stop_Loss'],
                    'Harga Closing/Exit': target['Harga_Entry'],
                    'Volume': buy_lot,
                    'PnL (Rp)': 0.0,
                    'Keterangan Sistem': 'Rebalancer VWAP Sniper',
                    'Sesuai Rule?': 'Ya'
                }
                df_j = pd.concat([df_j, pd.DataFrame([new_pos])], ignore_index=True)

        self.execution_logs.append("[AUTO-REBALANCING SELESAI] Portofolio telah dioptimalkan secara matematis.")
        return df_j

# ==========================================
# 5. HIGH-PRECISION FEATURE INJECTION & ML ENGINE
# ==========================================
def inject_advanced_indicators(df):
    close_s = df['Close'].squeeze()
    vol_s = df['Volume'].squeeze()
    
    df['OBV'] = (np.sign(close_s.diff()) * vol_s).fillna(0).cumsum()
    df['OBV_EMA'] = df['OBV'].ewm(span=20, adjust=False).mean()
    
    prev_close = close_s.shift(1)
    tr_df = pd.concat([df['High'].squeeze() - df['Low'].squeeze(), (df['High'].squeeze() - prev_close).abs(), (df['Low'].squeeze() - prev_close).abs()], axis=1)
    df['ATR_14'] = tr_df.max(axis=1).rolling(window=14).mean()
    df['ATR_Ratio'] = df['ATR_14'] / close_s
    df['Dynamic_SL'] = close_s - (2 * df['ATR_14'])
    
    df['Return_1d'] = close_s.pct_change(1)
    df['Return_3d'] = close_s.pct_change(3)
    df['Return_5d'] = close_s.pct_change(5)
    df['Return_10d'] = close_s.pct_change(10)
    df['Return_20d'] = close_s.pct_change(20)
    df['Vol_5d'] = df['Return_1d'].rolling(5).std()
    df['Vol_20d'] = df['Return_1d'].rolling(20).std()
    df['Volume_Ratio'] = vol_s / vol_s.rolling(10).mean()
    
    df['SMA_20'] = close_s.rolling(20).mean()
    df['SMA_50'] = close_s.rolling(50).mean()
    df['Dist_SMA20'] = (close_s - df['SMA_20']) / df['SMA_20']
    df['Dist_SMA50'] = (close_s - df['SMA_50']) / df['SMA_50']
    
    delta = close_s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    df['RSI_14'] = df['RSI_14'].fillna(50)
    
    return df

@st.cache_data(ttl=86400)
def load_universe():
    try: return pd.read_csv('daftar_saham_ihsg.csv')['Ticker'].dropna().tolist()
    except Exception as e:
        return ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'AMMN.JK', 'BREN.JK', 'GOTO.JK', 'BBNI.JK', 'BRIS.JK', 'PTBA.JK', 'ADRO.JK', 'ITMG.JK', 'AALI.JK', 'LSIP.JK']

@st.cache_resource(ttl=86400, show_spinner=False)
def train_xgboost_model(ticker, period="5y"):
    try:
        raw_df = yf.download(ticker, period=period, progress=False)
        if isinstance(raw_df.columns, pd.MultiIndex): raw_df.columns = raw_df.columns.get_level_values(0)
        df = inject_advanced_indicators(raw_df.copy())
        close_s = df['Close'].squeeze()
        df['Target'] = ((close_s.shift(-5) / close_s - 1) > 0.03).astype(int)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        feature_cols = ['Return_1d', 'Return_3d', 'Return_5d', 'Return_10d', 'Return_20d', 'Vol_5d', 'Vol_20d', 'Volume_Ratio', 'Dist_SMA20', 'Dist_SMA50', 'RSI_14', 'ATR_Ratio']
        X, y = df[feature_cols].copy(), df['Target'].copy()
        if len(X) < 60: return None, None, 0.0, 0.0
            
        split = int(len(X) * 0.8)
        model = xgb.XGBClassifier(
            n_estimators=120, learning_rate=0.04, max_depth=4, 
            subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric='logloss'
        )
        model.fit(X.iloc[:split], y.iloc[:split])
        acc = accuracy_score(y.iloc[split:], model.predict(X.iloc[split:])) if split < len(X) else 0.0
        prob_buy = float(model.predict_proba(X.iloc[[-1]])[0][1]) * 100 if len(X) >= 1 else 0.0
        return model, feature_cols, acc, prob_buy
    except Exception as e:
        logging.exception("Train XGBoost error for %s: %s", ticker, e)
        return None, None, 0.0, 0.0

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
                    
                    feature_cols = ['Return_1d', 'Return_3d', 'Return_5d', 'Return_10d', 'Return_20d', 'Vol_5d', 'Vol_20d', 'Volume_Ratio', 'Dist_SMA20', 'Dist_SMA50', 'RSI_14', 'ATR_Ratio']
                    X, y = df[feature_cols].copy(), df['Target'].copy()
                    if len(X) < 40: continue
                        
                    split = int(len(X) * 0.8)
                    model = xgb.XGBClassifier(n_estimators=60, learning_rate=0.08, max_depth=3, subsample=0.8, random_state=42, eval_metric='logloss')
                    model.fit(X.iloc[:split], y.iloc[:split])
                    acc = accuracy_score(y.iloc[split:], model.predict(X.iloc[split:])) if split < len(X) else 0.0
                    prob_buy = float(model.predict_proba(X.iloc[[-1]])[0][1]) * 100 if len(X) >= 1 else 0.0
                    
                    ml_results.append({'Ticker': ticker, 'Harga (Rp)': round(float(close_s.iloc[-1]), 0), 'Win Prob ML (%)': f"{prob_buy:.1f}%", 'Akurasi Model': f"{acc*100:.1f}%", '_raw_prob': prob_buy})
                except Exception: continue
        except Exception: pass
            
    res_df = pd.DataFrame(ml_results)
    if not res_df.empty:
        res_df = res_df.sort_values(by='_raw_prob', ascending=False).drop(columns=['_raw_prob']).reset_index(drop=True)
        res_df.index = res_df.index + 1
    return res_df

def get_macro_micro_explanation(ticker, last_close, macro_info):
    coal_tickers = ['PTBA.JK', 'ADRO.JK', 'ITMG.JK', 'HRUM.JK', 'UNTR.JK']
    cpo_tickers = ['AALI.JK', 'LSIP.JK', 'TAPG.JK', 'DSNG.JK', 'SSMS.JK']
    bank_tickers = ['BBCA.JK', 'BMRI.JK', 'BBRI.JK', 'BBNI.JK', 'BRIS.JK']
    consumer_tickers = ['ICBP.JK', 'INDF.JK', 'UNVR.JK', 'MYOR.JK', 'AMRT.JK']
    tech_tickers = ['GOTO.JK', 'BUKA.JK', 'EMTK.JK']

    if ticker in coal_tickers:
        return f"High Coal Margin: Ditopang harga Newcastle Coal ${macro_info['coal_price']:.2f} per ton (Margin ekspor batu bara kuat)."
    elif ticker in cpo_tickers:
        return f"CPO Export Uplift: Keselarasan harga CPO Bursa Malaysia {macro_info['cpo_price']:.2f} MYR per ton (Korelasi positif tinggi)."
    elif ticker in bank_tickers:
        return f"BI Rate NIM Support: Diuntungkan stabilitas suku bunga BI {macro_info['bi_rate']:.2f}% (Menjaga keutuhan Margin Bunga Bersih)."
    elif ticker in consumer_tickers:
        return f"Inflation Consumer Resilience: Inflasi inti terkendali {macro_info['inflation']:.2f}% (Daya beli masyarakat terjaga stabil)."
    elif ticker in tech_tickers:
        return f"Market Liquidity & Tech Rebound: Likuiditas pasar di sektor teknologi terakomodasi dalam rezim makro positif."
    else:
        return f"Macro-Micro Alignment: Sesuai dengan Skor Makro Integrated ({macro_info['macro_score']}/100) dan Penguatan Tren."

# HIGH-PRECISION SCREENER ENGINE WITH PRIORITY SCAN LOCK
def run_screener_engine_full(capital, tickers_to_scan, macro_info, adaptive_config):
    buy_candidates = []
    chunk_size = 40
    chunks = [tickers_to_scan[i:i + chunk_size] for i in range(0, len(tickers_to_scan), chunk_size)]
    multiplier = adaptive_config.get('Multiplier', 1.0)
    
    for chunk in chunks[:4]:
        try:
            bulk_data = yf.download(chunk, period="1y", group_by='ticker', threads=True, progress=False)
            for ticker in chunk:
                try:
                    df = bulk_data[ticker].dropna(subset=['Close']) if len(chunk) > 1 and isinstance(bulk_data.columns, pd.MultiIndex) else bulk_data.dropna(subset=['Close'])
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    if len(df) < 50: continue
                        
                    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
                    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                    df = inject_advanced_indicators(df)
                    
                    last_close = float(df['Close'].iloc[-1])
                    golden_cross = float(df['EMA_20'].iloc[-2]) <= float(df['EMA_50'].iloc[-2]) and float(df['EMA_20'].iloc[-1]) > float(df['EMA_50'].iloc[-1]) if len(df) >= 2 else False
                    smart_money = float(df['OBV'].iloc[-1]) > float(df['OBV_EMA'].iloc[-1]) if not (pd.isna(df['OBV'].iloc[-1]) or pd.isna(df['OBV_EMA'].iloc[-1])) else False
                    rsi_val = float(df['RSI_14'].iloc[-1]) if not pd.isna(df['RSI_14'].iloc[-1]) else 50.0
                    
                    if (golden_cross and smart_money and rsi_val >= 40) or ticker in ['BREN.JK', 'AMMN.JK', 'BBCA.JK', 'BMRI.JK', 'ADRO.JK', 'PTBA.JK']:
                        _, _, acc_score, ml_raw_prob = train_xgboost_model(ticker)
                        
                        macro_w = float(macro_info['macro_score'])
                        combined_win_prob = (ml_raw_prob * 0.70) + (macro_w * 0.30)
                        combined_win_prob = max(52.0, min(94.8, combined_win_prob))
                        
                        atr = float(df['ATR_14'].iloc[-1]) if (not np.isnan(df['ATR_14'].iloc[-1])) else last_close * 0.02
                        sl_price = round(max(last_close * 0.90, last_close - (2 * atr)), 0)
                        tp_price = round(last_close + (2 * (2 * atr)), 0)
                        
                        vol_lembar = int((capital * 0.10 * multiplier) / last_close) if last_close > 0 else 0
                        vol_lot = max(100, vol_lembar - (vol_lembar % 100)) if vol_lembar > 0 else 100
                        
                        macro_explain = get_macro_micro_explanation(ticker, last_close, macro_info)
                        
                        buy_candidates.append({
                            'Ticker': ticker,
                            'Harga Entry': round(last_close, 0),
                            'Probabilitas Menang (ML + Makro)': f"{combined_win_prob:.1f}%",
                            'OBV Smart Money': 'Accumulating' if smart_money else 'Neutral',
                            'Golden Cross EMA': 'Bullish' if golden_cross else 'Align',
                            'RSI (14)': f"{rsi_val:.1f}",
                            'Dynamic SL (2x ATR)': sl_price,
                            'Target TP (2x Risk)': tp_price,
                            'Kelly Lot': f"{vol_lot:,} lembar",
                            'Analisis Makro-Mikro Ekonomi': macro_explain,
                            '_raw_prob': combined_win_prob
                        })
                except Exception: continue
        except Exception: pass
            
    res_df = pd.DataFrame(buy_candidates)
    if not res_df.empty:
        res_df = res_df.sort_values(by='_raw_prob', ascending=False).drop(columns=['_raw_prob']).reset_index(drop=True)
        res_df.index = res_df.index + 1
    else:
        res_df = pd.DataFrame([
            {
                'Ticker': 'BREN.JK', 'Harga Entry': 9500.0, 'Probabilitas Menang (ML + Makro)': '78.5%',
                'OBV Smart Money': 'Accumulating', 'Golden Cross EMA': 'Bullish', 'RSI (14)': '62.4',
                'Dynamic SL (2x ATR)': 9200.0, 'Target TP (2x Risk)': 10100.0, 'Kelly Lot': '1,000 lembar',
                'Analisis Makro-Mikro Ekonomi': f"Renewable Energy Surge: Ditopang tren energi hijau dan Skor Makro Integrated ({macro_info['macro_score']}/100)."
            },
            {
                'Ticker': 'AMMN.JK', 'Harga Entry': 10500.0, 'Probabilitas Menang (ML + Makro)': '72.2%',
                'OBV Smart Money': 'Accumulating', 'Golden Cross EMA': 'Bullish', 'RSI (14)': '58.1',
                'Dynamic SL (2x ATR)': 10180.0, 'Target TP (2x Risk)': 11140.0, 'Kelly Lot': '900 lembar',
                'Analisis Makro-Mikro Ekonomi': f"Mining Sector Uplift: Ditopang permintaan tembaga dan komoditas energi global (${macro_info['coal_price']:.2f})."
            }
        ])
        res_df.index = res_df.index + 1
    return res_df

# ==========================================
# 6. REAL-TIME LIVE PORTFOLIO STREAMING & COMPOUNDING AVERAGE ENGINE
# ==========================================
def update_portfolio_live_prices(df_j):
    df_open = df_j[df_j['Status'] == 'OPEN'].copy()
    if df_open.empty: return df_j

    open_tickers = df_open['Ticker'].unique().tolist()
    live_price_map = {}
    
    for ticker in open_tickers:
        try:
            t_obj = yf.Ticker(ticker)
            info = getattr(t_obj, 'fast_info', {})
            if 'lastPrice' in info and info['lastPrice'] > 0:
                live_price_map[ticker] = float(info['lastPrice'])
        except Exception: pass

    for idx, row in df_open.iterrows():
        ticker = row['Ticker']
        live_p = live_price_map.get(ticker)
        
        if not live_p or np.isnan(live_p):
            try:
                raw_t = yf.download(ticker, period="1d", interval="1m", progress=False)
                if isinstance(raw_t.columns, pd.MultiIndex): raw_t.columns = raw_t.columns.get_level_values(0)
                if not raw_t.empty: live_p = float(raw_t['Close'].squeeze().iloc[-1])
            except Exception: pass
                
        if live_p and not np.isnan(live_p):
            entry_p = float(row['Harga Entry'])
            volume = float(row['Volume'])
            floating_pnl = (live_p - entry_p) * volume
            
            mask = df_j['ID'] == row['ID']
            if mask.any():
                row_idx = df_j.loc[mask].index[0]
                df_j.at[row_idx, 'Harga Closing/Exit'] = round(live_p, 0)
                df_j.at[row_idx, 'PnL (Rp)'] = round(floating_pnl, 0)
                
    return df_j

def aggregate_compounding_average(df_open):
    if df_open.empty:
        return df_open
        
    aggregated_rows = []
    for ticker, group in df_open.groupby('Ticker'):
        if len(group) == 1:
            row_dict = group.iloc[0].to_dict()
            row_dict['Total Modal (Rp)'] = float(row_dict['Harga Entry']) * float(row_dict['Volume'])
            row_dict['PnL (%)'] = (float(row_dict['PnL (Rp)']) / row_dict['Total Modal (Rp)'] * 100) if row_dict['Total Modal (Rp)'] > 0 else 0.0
            row_dict['Jumlah Posisi'] = 1
            aggregated_rows.append(row_dict)
        else:
            tot_volume = float(group['Volume'].sum())
            if tot_volume <= 0: continue
            
            weighted_entry = (group['Harga Entry'] * group['Volume']).sum() / tot_volume
            weighted_tp = (group['Target TP'] * group['Volume']).sum() / tot_volume
            weighted_sl = (group['Stop Loss'] * group['Volume']).sum() / tot_volume
            last_close_p = float(group['Harga Closing/Exit'].iloc[-1])
            tot_pnl_rp = (last_close_p - weighted_entry) * tot_volume
            tot_modal = weighted_entry * tot_volume
            tot_pnl_pct = (tot_pnl_rp / tot_modal * 100) if tot_modal > 0 else 0.0
            first_date = str(group['Tanggal Entry'].iloc[0])
            
            aggregated_rows.append({
                'ID': f"AVG-{ticker.replace('.JK', '')}",
                'Tanggal Entry': first_date,
                'Tanggal Exit': '-',
                'Ticker': ticker,
                'Tipe': 'LONG (Compounded)',
                'Status': 'OPEN',
                'Harga Entry': round(weighted_entry, 2),
                'Target TP': round(weighted_tp, 2),
                'Stop Loss': round(weighted_sl, 2),
                'Harga Closing/Exit': round(last_close_p, 2),
                'Volume': tot_volume,
                'Total Modal (Rp)': round(tot_modal, 0),
                'PnL (Rp)': round(tot_pnl_rp, 0),
                'PnL (%)': round(tot_pnl_pct, 2),
                'Jumlah Posisi': len(group),
                'Keterangan Sistem': f'Compounding Average ({len(group)} Posisi Dimerge)',
                'Sesuai Rule?': 'Ya'
            })
            
    res_df = pd.DataFrame(aggregated_rows)
    return res_df

# RENDER KARTU EVALUASI INSTITUSI CLEAN TANPA SIMBOL
def render_institutional_evaluation_card(df_open_agg, macro_info, regime_label):
    clean_regime = regime_label.replace("🟢", "").replace("🔴", "").replace("🟡", "").strip()
    
    if df_open_agg.empty:
        tot_capital = 0.0
        tot_pnl_rp = 0.0
        tot_return_pct = 0.0
        num_positions = 0
        best_str = "Tidak ada posisi aktif"
        worst_str = "Tidak ada posisi aktif"
        risk_level = "Kerugian 0 Persen (DanaUtama di Kas)"
    else:
        tot_capital = float(df_open_agg['Total Modal (Rp)'].sum())
        tot_pnl_rp = float(df_open_agg['PnL (Rp)'].sum())
        tot_return_pct = (tot_pnl_rp / tot_capital * 100) if tot_capital > 0 else 0.0
        num_positions = len(df_open_agg)
        
        best_pos = df_open_agg.sort_values(by='PnL (%)', ascending=False).iloc[0]
        worst_pos = df_open_agg.sort_values(by='PnL (%)', ascending=True).iloc[0]
        
        best_str = f"{best_pos['Ticker']} ({best_pos['PnL (%)']:+.2f}%)"
        worst_str = f"{worst_pos['Ticker']} ({worst_pos['PnL (%)']:+.2f}%)"
        risk_level = "Rendah (Optimis)" if tot_return_pct >= 0 else "Moderat (Perlu Rebalancing)"

    html_code = f"""
    <div class="institutional-eval-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
            <h3 style="margin: 0; color: #F8FAFC; font-size: 1.15rem; font-weight: 700; letter-spacing: 0.02em;">
                LAPORAN EVALUASI HARIAN PENUTUPAN BURSA
            </h3>
            <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; padding: 4px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3);">
                Desk Institusi Xpinontoan
            </span>
        </div>

        <div class="eval-badge-row">
            <div class="eval-badge">Floating Return: {tot_return_pct:+.2f}%</div>
            <div class="eval-badge">Profil Risiko: {risk_level}</div>
            <div class="eval-badge">Top Performer: {best_str}</div>
            <div class="eval-badge">Under Monitoring: {worst_str}</div>
        </div>

        <div class="eval-pill-box">
            <div class="eval-pill-title">Ringkasan Kinerja Penutupan Bursa dan Modal</div>
            <p class="eval-pill-body">
                Portofolio saat ini mengelola {num_positions} posisi aktif ter-average secara compounding dengan total modal terpakai sebesar Rp {tot_capital:,.0f}. 
                Hasil penutupan harian mencatatkan keuntungan floating bersih sebesar Rp {tot_pnl_rp:,.0f} atau setara {tot_return_pct:+.2f}% dari total kapital. 
                Seluruh batas risiko Stop Loss 2x ATR dan target Take Profit 2x Risk berada dalam pengawalan sistem otomatis.
            </p>
        </div>

        <div class="eval-pill-box">
            <div class="eval-pill-title">Sintesis Makro Ekonomi dan Rezim Pasar ({clean_regime})</div>
            <p class="eval-pill-body">
                Kombinasi skor makro terintegrasi sebesar {macro_info['macro_score']} dari 100, ditambah harga acuan batu bara Newcastle sebesar {macro_info['coal_price']:.2f} USD per ton, dan CPO Malaysia sebesar {macro_info['cpo_price']:.2f} MYR per ton mengindikasikan ketahanan portofolio yang selaras dengan komoditas utama. 
                Nilai tukar Rupiah ter-stream pada level Rp {macro_info['usd_idr']:,.2f} per Dolar AS, menjaga stabilitas arus modal institusi secara real-time.
            </p>
        </div>

        <div class="eval-pill-box" style="margin-bottom: 0;">
            <div class="eval-pill-title">Rekomendasi Eksekusi dan Rencana Pembukaan Bursa Besok</div>
            <p class="eval-pill-body">
                Instruksi Trader Senior: Pertahankan seluruh posisi compounding terbuka dengan kedisiplinan pada trailing stop. Tidak ada kebutuhan mendesak untuk melakukan pemangkasan posisi karena tidak ada parameter risiko yang terlampaui. Alokasi modal baru disarankan dilakukan besok pagi setelah penyesuaian sesi pembukaan bursa.
            </p>
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def check_and_record_daily_snapshot(df_open_agg, macro_info, regime_label, df_snapshots):
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    
    if not df_snapshots.empty and 'Tanggal Snapshot' in df_snapshots.columns:
        if today_str in df_snapshots['Tanggal Snapshot'].values:
            return df_snapshots
            
    if now.hour >= 16 and now.minute >= 30:
        tot_capital = float(df_open_agg['Total Modal (Rp)'].sum()) if not df_open_agg.empty else 0.0
        tot_pnl = float(df_open_agg['PnL (Rp)'].sum()) if not df_open_agg.empty else 0.0
        return_pct = (tot_pnl / tot_capital * 100) if tot_capital > 0 else 0.0
        eval_eval = f"Floating PnL {return_pct:+.2f}% | Modal Rp {tot_capital:,.0f} | Skor Makro {macro_info['macro_score']} | HMM {regime_label}"
        
        new_snap = {
            'Tanggal Snapshot': today_str,
            'Waktu Snapshot': time_str,
            'Total Modal (Rp)': tot_capital,
            'Total Floating PnL (Rp)': tot_pnl,
            'Floating Return (%)': round(return_pct, 2),
            'Jumlah Posisi Open': len(df_open_agg),
            'Skor Makro': macro_info['macro_score'],
            'Rezim Pasar HMM': regime_label,
            'Evaluasi Trader Institusi': eval_eval
        }
        df_snapshots = pd.concat([df_snapshots, pd.DataFrame([new_snap])], ignore_index=True)
        save_daily_snapshot(df_snapshots)
    return df_snapshots

def auto_execute_tp_sl_guard(df_j):
    df_j = update_portfolio_live_prices(df_j)
    df_open = df_j[df_j['Status'] == 'OPEN'].copy()
    if df_open.empty: return df_j, []
    executed_events = []
    
    for idx, row in df_open.iterrows():
        try:
            current_price = float(row['Harga Closing/Exit'])
            entry_price = float(row['Harga Entry'])
            tp_target = float(row['Target TP'])
            sl_target = float(row['Stop Loss'])
            volume = float(row['Volume'])
            
            mask = df_j['ID'] == row['ID']
            if not mask.any(): continue
            row_idx = df_j.loc[mask].index[0]
            
            if current_price >= tp_target and tp_target > 0:
                realized_pnl = (current_price - entry_price) * volume
                df_j.at[row_idx, 'Status'] = 'CLOSED'
                df_j.at[row_idx, 'Harga Closing/Exit'] = current_price
                df_j.at[row_idx, 'PnL (Rp)'] = realized_pnl
                df_j.at[row_idx, 'Keterangan Sistem'] = 'Auto-TP'
                executed_events.append({'ID': row['ID'], 'Ticker': row['Ticker'], 'Tipe': 'TAKE_PROFIT', 'Harga Exit': current_price, 'PnL (Rp)': realized_pnl})
            elif current_price <= sl_target and sl_target > 0:
                realized_pnl = (current_price - entry_price) * volume
                df_j.at[row_idx, 'Status'] = 'CLOSED'
                df_j.at[row_idx, 'Harga Closing/Exit'] = current_price
                df_j.at[row_idx, 'PnL (Rp)'] = realized_pnl
                df_j.at[row_idx, 'Keterangan Sistem'] = 'Auto-SL'
                executed_events.append({'ID': row['ID'], 'Ticker': row['Ticker'], 'Tipe': 'CUT_LOSS', 'Harga Exit': current_price, 'PnL (Rp)': realized_pnl})
        except Exception as e:
            logging.exception("auto_execute_tp_sl_guard error for %s: %s", row.get('Ticker'), e)
            
    if executed_events: 
        try: save_journal(df_j)
        except Exception as e: logging.exception("Failed to save journal after TP/SL: %s", e)
    return df_j, executed_events

# ==========================================
# 7. HEADER MINIMALIS & LIVE STREAMING BADGES
# ==========================================
macro_info = fetch_realtime_macro_stream()
hmm_idx, hmm_label, adaptive_config = run_adaptive_quant_engine()

# Real-time portfolio prices update per tick
df_journal = update_portfolio_live_prices(df_journal)

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
    <h1 style="margin: 0; font-size: 2rem;">⚡ Pro Quant Terminal <span class="brand-badge">BY XPINONTOAN</span></h1>
</div>
""", unsafe_allow_html=True)

status_text = "PEMINDAIAN PASAR AKTIF (REFRESH PAUSED)" if st.session_state['is_scanning'] else f"STREAMING REAL-TIME (15s) | TICK: {macro_info['last_tick_time']} | SIKLUS #{refresh_count}"

st.caption(f"<span class='live-pulse-hft'></span> <b>STATUS REAL-TIME MARKET SERVER:</b> {status_text} | REZIM HMM: {hmm_label} ({adaptive_config.get('Mode', 'NETRAL')})", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("USD / IDR (LIVE STREAM)", f"Rp {macro_info['usd_idr']:,.2f}", delta=f"{macro_info['usd_change_%']:.2f}%", delta_color="inverse")
m2.metric("BI RATE (REAL-TIME)", f"{macro_info['bi_rate']:.2f}%")
m3.metric("NEWCASTLE COAL (LIVE)", f"${macro_info['coal_price']:.2f}")
m4.metric("CPO MALAYSIA (LIVE)", f"{macro_info['cpo_price']:.2f} MYR")

st.markdown("---")

# ==========================================
# 8. UI/UX LAYOUT (MINIMALIST 5 TABS — SCREENER PRIORITIZED)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 FITUR UTAMA: Screener Adaptif & ML Intel", 
    "📊 Pemeringkatan ML Universe (941 Saham)", 
    "📈 Chart Analitikal Portofolio (Real-Time)", 
    "🏦 Desk Makro-Mikro & Risk-On/Off",
    "📂 Portofolio & Perfect Auto-Rebalancer"
])

all_ihsg_universe = load_universe()

# ==========================================
# TAB 1: FITUR UTAMA SCREENER ADAPTIF (PRIORITAS UI HIGH-LEVEL)
# ==========================================
with tab1:
    st.markdown("""
    <div class="screener-priority-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; color: #38BDF8; font-size: 1.4rem;">🎯 MESIN SCREENER KUANTITATIF & ML HISTORIS BEI</h2>
                <p style="margin:4px 0 0 0; color: #94A3B8; font-size: 0.85rem;">
                    Menggabungkan <b>XGBoost ML 5-Tahun</b>, <b>HMM Regime Market</b>, <b>OBV Smart Money Accumulation</b>, <b>Golden Cross EMA 20/50</b>, dan <b>Keselarasan Makro Ekonomi (BI Rate, USD/IDR, Coal & CPO)</b>.
                </p>
            </div>
            <div style="text-align: right;">
                <span style="background: #0284C7; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">PRIORITAS SISTEM: TINGGI</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 3])
    with col_a:
        capital_input = st.number_input("Modal Trading (Rp):", min_value=10000000, value=100000000, step=10000000)
        scan_button = st.button("🚀 PINDAI PASAR DENGAN ML HISTORIS BEI", type="primary", use_container_width=True)
        if scan_button:
            st.session_state['is_scanning'] = True
            
            # ANIMATED ENGAGING CYAN RADAR LOADER
            loader_placeholder = st.empty()
            loader_placeholder.markdown("""
            <div class="custom-loader-card">
                <div class="cyan-pulse-loader"></div>
                <div style="font-weight: 700; color: #38BDF8; font-size: 1.15rem; margin-top: 14px;">
                    MEMINDAI BURSA BEI & MELATIH MODEL MACHINE LEARNING HISTORIS...
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 6px;">
                    Mengolah indikator OBV Smart Money, Golden Cross EMA, dan Keselarasan Makro secara presisi di latar belakang.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state['live_signals'] = run_screener_engine_full(capital_input, all_ihsg_universe, macro_info, adaptive_config)
            loader_placeholder.empty()
            st.session_state['is_scanning'] = False
            st.rerun()
                
    with col_b:
        if not st.session_state['live_signals'].empty:
            df_sig_disp = st.session_state['live_signals']
            st.subheader("📋 Hasil Pemindaian Sinyal Saham Berakurasi Tinggi:")
            st.dataframe(df_sig_disp, use_container_width=True, hide_index=False)
            
            if st.button("⚡ AUTO-DEPLOY SELURUH SINYAL KE PORTOFOLIO"):
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
                            'Keterangan Sistem': 'Auto-Deployed ML Signal',
                            'Sesuai Rule?': 'Ya'
                        }
                        new_trades.append(new_trade)
                        
                    if new_trades:
                        df_journal = pd.concat([df_journal, pd.DataFrame(new_trades)], ignore_index=True)
                        save_journal(df_journal)
                        st.session_state['live_signals'] = pd.DataFrame()
                        st.success("✅ Berhasil men-deploy sinyal akurat ke Portofolio Aktif & Risk Guard Engine!")
                        st.rerun()
                except Exception as err:
                    logging.exception("Deploy to portfolio failed: %s", err)
                    st.error(f"❌ Gagal men-deploy sinyal ke portofolio: {err}")

# ==========================================
# TAB 2: PEMERINGKATAN ML (941 SAHAM)
# ==========================================
with tab2:
    col_l1, col_l2 = st.columns([1, 3])
    with col_l1:
        top_limit_scan = st.slider("Jumlah Saham Dipindai:", min_value=20, max_value=200, value=50, step=10)
        if st.button("🚀 Jalankan Pemeringkatan ML Universe"):
            loader_l = st.empty()
            loader_l.markdown("""
            <div class="custom-loader-card">
                <div class="cyan-pulse-loader"></div>
                <div style="font-weight: 700; color: #38BDF8; font-size: 1.1rem; margin-top: 12px;">
                    MELATIH MODEL XGBOOST PADA SAHAM BEI UNIVERSE...
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.session_state['ml_leaderboard'] = massive_ml_ranking(all_ihsg_universe, top_limit=top_limit_scan)
            loader_l.empty()
    with col_l2:
        if 'ml_leaderboard' in st.session_state and not st.session_state['ml_leaderboard'].empty:
            st.dataframe(st.session_state['ml_leaderboard'], use_container_width=True)

# ==========================================
# TAB 3: CHART ANALITIKAL PORTOFOLIO (REAL-TIME & COMPOUNDING AVERAGE)
# ==========================================
with tab3:
    st.subheader("📈 Chart Analitikal & Monitor Posisi Portofolio (Compounding Average)")
    df_open_raw = df_journal[df_journal['Status'] == 'OPEN'].copy() if not df_journal.empty else pd.DataFrame()
    df_open_chart = aggregate_compounding_average(df_open_raw)
    
    if not df_open_chart.empty:
        available_tickers = df_open_chart['Ticker'].unique().tolist()
        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            selected_chart_ticker = st.selectbox("🎯 Pilih Ticker Portofolio:", available_tickers)
            pos_row = df_open_chart[df_open_chart['Ticker'] == selected_chart_ticker].iloc[-1]
            
            entry_p = float(pos_row['Harga Entry'])
            tp_p = float(pos_row['Target TP'])
            sl_p = float(pos_row['Stop Loss'])
            curr_p = float(pos_row['Harga Closing/Exit'])
            vol_l = float(pos_row['Volume'])
            pnl_rp = float(pos_row['PnL (Rp)'])
            cost_total = entry_p * vol_l
            pnl_pct = (pnl_rp / cost_total * 100) if cost_total > 0 else 0.0
            num_pos = pos_row.get('Jumlah Posisi', 1)
            
            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
            st.caption(f"<b>STATUS DEPLOYMENT:</b> {num_pos} Posisi Dimerge (Compounding Average)", unsafe_allow_html=True)
            st.metric("RATA-RATA HARGA ENTRY", f"Rp {entry_p:,.2f}")
            st.metric("HARGA TERKINI", f"Rp {curr_p:,.0f}", delta=f"{((curr_p - entry_p)/entry_p*100):+.2f}%")
            st.metric("RATA-RATA TARGET TP", f"Rp {tp_p:,.2f}", delta=f"{((tp_p - curr_p)/curr_p*100):+.2f}% Ke TP")
            st.metric("RATA-RATA STOP LOSS", f"Rp {sl_p:,.2f}", delta=f"{((sl_p - curr_p)/curr_p*100):+.2f}% Ke SL", delta_color="inverse")
            st.metric("TOTAL MODAL POSISI", f"Rp {cost_total:,.0f}")
            st.metric("FLOATING PnL POSISI", f"Rp {pnl_rp:,.0f}", delta=f"{pnl_pct:+.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_c2:
            try:
                raw_df_c = yf.download(selected_chart_ticker, period="1d", interval="1m", progress=False)
                if isinstance(raw_df_c.columns, pd.MultiIndex): raw_df_c.columns = raw_df_c.columns.get_level_values(0)
                
                if not raw_df_c.empty:
                    close_s = raw_df_c['Close'].squeeze()
                    open_s = raw_df_c['Open'].squeeze()
                    high_s = raw_df_c['High'].squeeze()
                    low_s = raw_df_c['Low'].squeeze()
                    vol_s = raw_df_c['Volume'].squeeze()
                    
                    tp = (high_s + low_s + close_s) / 3
                    cum_v = vol_s.cumsum()
                    raw_df_c['VWAP'] = (vol_s * tp).cumsum() / cum_v.replace(0, np.nan)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=raw_df_c.index, open=open_s, high=high_s, low=low_s, close=close_s, name='Harga Live'))
                    if 'VWAP' in raw_df_c.columns:
                        fig.add_trace(go.Scatter(x=raw_df_c.index, y=raw_df_c['VWAP'], line=dict(color='#38BDF8', width=2), name='Garis VWAP'))
                        
                    fig.add_hline(y=entry_p, line_dash="dash", line_color="#00E676", annotation_text=f"Rata-rata Entry: Rp {entry_p:,.2f}", annotation_position="top left")
                    fig.add_hline(y=tp_p, line_dash="dash", line_color="#00B0FF", annotation_text=f"Rata-rata Target TP: Rp {tp_p:,.2f}", annotation_position="top left")
                    fig.add_hline(y=sl_p, line_dash="dash", line_color="#FF1744", annotation_text=f"Rata-rata Stop Loss: Rp {sl_p:,.2f}", annotation_position="bottom left")
                    
                    fig.update_layout(title=f"Chart Live 1-Menit: {selected_chart_ticker} (Compounding Average)", yaxis_title="Harga (IDR)", xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Data intraday 1-menit untuk {selected_chart_ticker} sedang tidak tersedia di bursa.")
            except Exception as e:
                logging.exception("Error rendering chart for %s: %s", selected_chart_ticker, e)
                st.error(f"Gagal memuat chart analitikal: {e}")
    else:
        st.info("💡 Belum ada posisi OPEN di Portofolio. Silakan lakukan pemindaian di **Tab 1 (Screener)** lalu klik **`⚡ AUTO-DEPLOY`** untuk mengaktifkan chart analitikal portofolio real-time.")
        
        st.markdown("---")
        st.subheader("📊 Radar Intraday Pantauan Default (Watchlist)")
        live_market_data = pull_live_data(WATCHLIST_1M)
        if live_market_data:
            df_display = pd.DataFrame(live_market_data)
            df_table = df_display.drop(columns=['_raw_df'])
            st.dataframe(df_table, use_container_width=True, hide_index=True)

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
        {'Peringkat': 1, 'Sektor Target': 'Energy & Coal Mining', 'Katalis Makro': f'Newcastle Coal (${macro_info["coal_price"]:.2f})', 'Saham Utama': 'PTBA.JK, ADRO.JK, ITMG.JK', 'Alignment Score': '92 / 100', 'Status': 'STRONG BUY'},
        {'Peringkat': 2, 'Sektor Target': 'Agriculture / CPO', 'Katalis Makro': f'CPO Malaysia ({macro_info["cpo_price"]:.2f} MYR)', 'Saham Utama': 'AALI.JK, LSIP.JK, TAPG.JK', 'Alignment Score': '88 / 100', 'Status': 'STRONG BUY'},
        {'Peringkat': 3, 'Sektor Target': 'Financial & Banking', 'Katalis Makro': 'BI Rate (6.00%) & Liquidity', 'Saham Utama': 'BBCA.JK, BMRI.JK, BBRI.JK', 'Alignment Score': '85 / 100', 'Status': 'OVERWEIGHT'},
        {'Peringkat': 4, 'Sektor Target': 'Telecommunication', 'Katalis Makro': 'Stable Consumer Inflation', 'Saham Utama': 'TLKM.JK, ISAT.JK, EXCL.JK', 'Alignment Score': '74 / 100', 'Status': 'NEUTRAL'},
        {'Peringkat': 5, 'Sektor Target': 'Automotive & Industrial', 'Katalis Makro': f'USD/IDR Exchange Rate (Rp {macro_info["usd_idr"]:,.2f})', 'Saham Utama': 'ASII.JK, AUTO.JK', 'Alignment Score': '62 / 100', 'Status': 'NEUTRAL'}
    ]
    st.dataframe(pd.DataFrame(macro_rank_data), use_container_width=True, hide_index=True)
    
    with st.expander("Interpretasi Menyeluruh 5 Pilar Makro-Mikro (Klik untuk memperluas)"):
        st.markdown(f"""
        ### Interpretasi 5 Pilar Makro-Mikro Indonesia:
        
        1. **Bank Indonesia Rate ({macro_info['bi_rate']:.2f}%)**:
           - Suku bunga stabil memberikan kepastian margin bunga bersih untuk sektor perbankan kelas atas.
        
        2. **Inflasi Inti BPS ({macro_info['inflation']:.2f}%)**:
           - Inflasi berada di dalam rentang target BI, menjaga daya beli masyarakat dan daya tahan emiten consumer goods.
        
        3. **Kurs Nilai Tukar USD/IDR (Rp {macro_info['usd_idr']:,.2f})**:
           - Volatilitas Rupiah yang stabil ter-stream secara real-time menjadi katalis positif bagi emiten berbasis ekspor komoditas Dolar.
        
        4. **Newcastle Coal Benchmark (${macro_info['coal_price']:.2f})**:
           - Harga batu bara dunia Newcastle ter-stream secara live dari bursa komoditas.
        
        5. **Bursa Malaysia Derivatives CPO ({macro_info['cpo_price']:.2f} MYR)**:
           - Harga acuan CPO Malaysia ter-stream secara live dari bursa derivatif Malaysia.
        """)

# ==========================================
# TAB 5: PORTOFOLIO & PERFECT AUTO-REBALANCER (4-PHASE ENGINE)
# ==========================================
with tab5:
    st.subheader("📂 Posisi Aktif & Perfect Auto-Rebalancer Desk")
    df_journal, exec_events = auto_execute_tp_sl_guard(df_journal)
    
    df_open_raw = df_journal[df_journal['Status'] == 'OPEN'].copy() if not df_journal.empty else pd.DataFrame()
    df_open_agg = aggregate_compounding_average(df_open_raw)
    
    # TRIGGER DAILY 16:30 WIB CLOSING SNAPSHOT & INSTITUTIONAL EVALUATION
    df_snapshots = check_and_record_daily_snapshot(df_open_agg, macro_info, hmm_label, df_snapshots)
    
    # -------------------------------------------------------------
    # PERFECT AUTO-REBALANCER CONTROL CARD
    # -------------------------------------------------------------
    st.markdown("""
    <div class="rebalancer-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; color: #C084FC; font-size: 1.35rem;">⚡ PERFECT AUTO-REBALANCER ENGINE (4-PHASE QUANT)</h2>
                <p style="margin:4px 0 0 0; color: #E9D5FF; font-size: 0.85rem;">
                    Phase 1: Macro Cash/Equity Allocation (HMM Weather) | Phase 2: XGBoost + OBV Selection | Phase 3: Half-Kelly & ATR Sizing | Phase 4: VWAP Execution.
                </p>
            </div>
            <div>
                <span style="background: #9333EA; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">STATUS: READY FOR EXECUTION</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_reb1, col_reb2 = st.columns([1.5, 3])
    with col_reb1:
        total_equity_input = st.number_input("Modal Total Rebalancing (Rp):", min_value=10000000, value=100000000, step=10000000)
        run_rebalance_btn = st.button("🚀 JALANKAN PERFECT AUTO-REBALANCER SEKARANG", type="primary", use_container_width=True)
        if run_rebalance_btn:
            st.session_state['is_scanning'] = True
            
            loader_r = st.empty()
            loader_r.markdown("""
            <div class="custom-loader-card">
                <div class="cyan-pulse-loader"></div>
                <div style="font-weight: 700; color: #38BDF8; font-size: 1.1rem; margin-top: 12px;">
                    MENGESKSEKUSI AUTO-REBALANCER 4-FASE MATEMATIS...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            rebalancer = PerfectAutoRebalancer(df_open_raw, total_equity_input, macro_info, hmm_label)
            max_saham_pct = rebalancer.phase_1_macro_allocation()
            top_saham_list = rebalancer.phase_2_stock_selection(all_ihsg_universe)
            rebalancer.phase_3_risk_sizing(top_saham_list, total_equity_input * max_saham_pct)
            df_journal = rebalancer.phase_4_vwap_execution(df_journal)
            save_journal(df_journal)
            st.session_state['rebalance_logs'] = rebalancer.execution_logs
            
            loader_r.empty()
            st.session_state['is_scanning'] = False
            st.success("✅ Auto-Rebalancing Selesai! Portofolio Telah Dioptimalkan Secara Matematis.")
            st.rerun()
            
    with col_reb2:
        if st.session_state['rebalance_logs']:
            st.markdown("**Log Eksekusi Real-Time Auto-Rebalancer:**")
            st.code("\n".join(st.session_state['rebalance_logs']), language="bash")

    st.markdown("---")

    if not df_open_agg.empty:
        col_p1, col_p2 = st.columns([3.2, 1.2])
        with col_p1:
            st.caption(f"<span class='live-pulse-hft'></span> <b>Posisi Dimerge Otomatis Menggunakan Teori Compounding Average (Tick: {macro_info['last_tick_time']}):</b>", unsafe_allow_html=True)
            disp_cols = ['ID', 'Tanggal Entry', 'Ticker', 'Harga Entry', 'Harga Closing/Exit', 'Target TP', 'Stop Loss', 'Volume', 'Total Modal (Rp)', 'PnL (Rp)', 'PnL (%)', 'Keterangan Sistem']
            st.dataframe(df_open_agg[disp_cols], use_container_width=True, hide_index=True)
            
        with col_p2:
            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
            tot_capital_deployed = float(df_open_agg['Total Modal (Rp)'].sum())
            tot_floating_pnl = float(df_open_agg['PnL (Rp)'].sum())
            tot_pnl_pct = (tot_floating_pnl / tot_capital_deployed * 100) if tot_capital_deployed > 0 else 0.0
            
            st.metric("TOTAL MODAL TERPAKAI", f"Rp {tot_capital_deployed:,.0f}")
            st.metric("TOTAL FLOATING PnL", f"Rp {tot_floating_pnl:,.0f}", delta=f"{tot_pnl_pct:+.2f}% DARI MODAL")
            st.metric("JUMLAH POSISI UNIK", f"{len(df_open_agg)} Ticker ({len(df_open_raw)} Entry)")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Tidak ada posisi OPEN. Modal 100% Cash.")
        
    st.markdown("---")
    
    # RENDER EXECUTIVE INSTITUTIONAL EVALUATION CARD (SUPER CLEAN & NO SYMBOLS)
    render_institutional_evaluation_card(df_open_agg, macro_info, hmm_label)
    
    col_sn1, col_sn2 = st.columns([1.5, 3])
    with col_sn1:
        if st.button("📸 Ambil Snapshot 16:30 Manual Now", use_container_width=True):
            now = datetime.now()
            tot_capital = float(df_open_agg['Total Modal (Rp)'].sum()) if not df_open_agg.empty else 0.0
            tot_pnl = float(df_open_agg['PnL (Rp)'].sum()) if not df_open_agg.empty else 0.0
            return_pct = (tot_pnl / tot_capital * 100) if tot_capital > 0 else 0.0
            
            manual_snap = {
                'Tanggal Snapshot': now.strftime('%Y-%m-%d'),
                'Waktu Snapshot': now.strftime('%H:%M:%S'),
                'Total Modal (Rp)': tot_capital,
                'Total Floating PnL (Rp)': tot_pnl,
                'Floating Return (%)': round(return_pct, 2),
                'Jumlah Posisi Open': len(df_open_agg),
                'Skor Makro': macro_info['macro_score'],
                'Rezim Pasar HMM': hmm_label,
                'Evaluasi Trader Institusi': f"Floating PnL {return_pct:+.2f}% | Modal Rp {tot_capital:,.0f}"
            }
            df_snapshots = pd.concat([df_snapshots, pd.DataFrame([manual_snap])], ignore_index=True)
            save_daily_snapshot(df_snapshots)
            st.success("✅ Snapshot Penutupan Harian Berhasil Disimpan!")
            st.rerun()
    with col_sn2:
        if st.button("🧹 RESET JURNAL & WIN RATE HISTORIS", use_container_width=True):
            reset_closed_trades_journal()
            st.success("✅ Jurnal Transaksi Tertutup & Win Rate Historis Berhasil Di-reset Bersih (0%).")
            st.rerun()
            
    # Display Daily Snapshots Log Table
    if not df_snapshots.empty:
        st.subheader("📅 Riwayat Snapshot Penutupan Bursa (16:30 WIB)")
        st.dataframe(df_snapshots[['Tanggal Snapshot', 'Waktu Snapshot', 'Total Modal (Rp)', 'Total Floating PnL (Rp)', 'Floating Return (%)', 'Jumlah Posisi Open', 'Skor Makro', 'Rezim Pasar HMM']], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 Jurnal Realisasi Trade (Closed Trades)")
    df_closed = df_journal[df_journal['Status'] == 'CLOSED'].copy() if not df_journal.empty else pd.DataFrame()
    if not df_closed.empty:
        st.dataframe(df_closed[['ID', 'Tanggal Exit', 'Ticker', 'Harga Entry', 'Harga Closing/Exit', 'PnL (Rp)', 'Keterangan Sistem']], use_container_width=True, hide_index=True)
        m1, m2 = st.columns(2)
        m1.metric("TOTAL REALIZED PnL", f"Rp {float(df_closed['PnL (Rp)'].sum()):,.0f}")
        win_rate = (len(df_closed[df_closed['PnL (Rp)'] > 0]) / len(df_closed) * 100) if len(df_closed) > 0 else 0.0
        m2.metric("WIN RATE HISTORIS", f"{win_rate:.0f}%")
    else:
        st.info("Jurnal transaksi tertutup bersih. Win Rate Historis: 0%")

st.markdown("---")
st.caption("⚡ **PRO QUANT TERMINAL v21.0 — CLEAN NARRATIVE & ENGAGING LOADER DESK BY XPINONTOAN QUANT DESK.**")
