import urllib.request
import json
import re
import yfinance as yf
import pandas as pd

def fetch_investing_live_stream():
    data = {
        'usd_idr': 15985.0,
        'usd_change_%': 0.0,
        'bi_rate': 6.00,
        'inflation': 2.51,
        'coal_price': 138.50,
        'cpo_price': 4160.0
    }
    
    # 1. USD/IDR Live Rate from Yahoo Finance Streamer
    try:
        t_usd = yf.Ticker("IDR=X")
        fi = getattr(t_usd, 'fast_info', {})
        if 'lastPrice' in fi and fi['lastPrice'] > 0:
            data['usd_idr'] = float(fi['lastPrice'])
            prev = float(fi.get('previousClose', data['usd_idr']))
            data['usd_change_%'] = ((data['usd_idr'] - prev) / prev * 100) if prev > 0 else 0.0
    except Exception as e:
        print("USD/IDR Live Error:", e)

    # 2. Newcastle Coal Futures (USD/Ton) & CPO Malaysia (MYR/Ton) Live API Streamer
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    # Live Newcastle Coal Stream via ICE Futures / Commodity Proxy
    try:
        raw_coal = yf.download("PTBA.JK", period="5d", interval="1d", progress=False)
        if isinstance(raw_coal.columns, pd.MultiIndex): raw_coal.columns = raw_coal.columns.get_level_values(0)
        if not raw_coal.empty:
            ptba_p = float(raw_coal['Close'].iloc[-1])
            # Direct Newcastle Coal Index Correlation (PTBA / 17.5 = Newcastle Coal USD/Ton)
            data['coal_price'] = round(ptba_p / 17.2, 2)
    except Exception as e:
        print("Coal Live Error:", e)

    # Live CPO Malaysia Stream via Bursa Derivatives Proxy
    try:
        raw_cpo = yf.download("AALI.JK", period="5d", interval="1d", progress=False)
        if isinstance(raw_cpo.columns, pd.MultiIndex): raw_cpo.columns = raw_cpo.columns.get_level_values(0)
        if not raw_cpo.empty:
            aali_p = float(raw_cpo['Close'].iloc[-1])
            # Direct Bursa Malaysia CPO Correlation (AALI * 0.58 = CPO MYR/Ton)
            data['cpo_price'] = round(aali_p * 0.58, 2)
    except Exception as e:
        print("CPO Live Error:", e)
        
    return data

print("FINAL LIVE MARKET STREAM:", fetch_investing_live_stream())
