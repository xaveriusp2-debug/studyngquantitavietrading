import urllib.request
import re
import yfinance as yf

def fetch_investing_live():
    results = {}
    urls = {
        'USD_IDR': 'https://www.investing.com/currencies/usd-idr',
        'COAL': 'https://www.investing.com/commodities/rotterdam-coal-futures',
        'CPO': 'https://www.investing.com/commodities/crude-palm-oil'
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for key, url in urls.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8')
            m = re.search(r'data-test="instrument-price-last"[^>]*>([\d,.]+)<', html)
            if not m:
                m = re.search(r'data-test="price-val"[^>]*>([\d,.]+)<', html)
            if not m:
                m = re.search(r'"last_price":([\d.]+)', html)
            if not m:
                m = re.search(r'class="[^"]*text-2xl[^"]*"[^>]*>([\d,.]+)<', html)
            if m:
                results[key] = m.group(1)
            else:
                results[key] = "N/A"
        except Exception as e:
            results[key] = str(e)
            
    return results

print("Investing Live Scrape:", fetch_investing_live())

# Also test Yahoo Finance fallback tickers:
# USD/IDR: IDR=X
# Coal ETF / Energy proxy: XLE or KOL
# BI Rate: BI 7-Day Repo (6.00% benchmark)
usd = yf.Ticker("IDR=X").fast_info.get('lastPrice')
print("Yahoo IDR=X Price:", usd)
