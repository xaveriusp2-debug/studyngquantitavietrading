import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

def fetch_data_and_params(ticker, start_date, end_date):
    """Menarik data historis dan menghitung parameter dasar GBM"""
    print(f"Menarik data {ticker} dari {start_date} hingga {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date)
    
    if data.empty:
        raise ValueError(f"Tidak ada data ditemukan untuk ticker {ticker}")
    
    # Menggunakan Close / Adj Close
    if 'Adj Close' in data.columns:
        prices = data['Adj Close']
    elif 'Close' in data.columns:
        prices = data['Close']
    else:
        prices = data.iloc[:, 0]
        
    # Pastikan prices berupa Series (1D)
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
        
    # Menghitung log returns harian
    log_returns = np.log(prices / prices.shift(1)).dropna()
    
    # Parameter dasar (Daily)
    mu_daily = float(log_returns.mean())
    sigma_daily = float(log_returns.std())
    last_price = float(prices.iloc[-1])
    
    print(f"Harga Terakhir (S0): {last_price:.2f}")
    print(f"Drift Harian (mu): {mu_daily:.6f}")
    print(f"Volatilitas Harian (sigma): {sigma_daily:.6f}")
    
    return last_price, mu_daily, sigma_daily, log_returns

def merton_jump_diffusion_mc(S0, mu, sigma, days=30, paths=10000, 
                             lambda_j=0.05, mu_j=-0.02, sigma_j=0.05):
    """
    Menjalankan simulasi Monte Carlo MJD secara tervektorisasi.
    Parameter Jump (Default asumsi):
    - lambda_j : Probabilitas terjadinya jump per hari (contoh: 5%)
    - mu_j     : Rata-rata besaran jump (contoh: -2%, pasar cenderung gap down saat panik)
    - sigma_j  : Volatilitas dari jump tersebut (contoh: 5%)
    """
    print(f"\nMemulai simulasi {paths} jalur untuk {days} hari ke depan...")
    
    # 1. Komponen GBM (Continuous Diffusion)
    # Z adalah variabel acak normal standar untuk pergerakan harian
    Z = np.random.standard_normal((days, paths))
    gbm_returns = (mu - 0.5 * sigma**2) + sigma * Z
    
    # 2. Komponen Jump (Poisson Process)
    # Menentukan apakah terjadi lompatan pada hari tersebut (0 = tidak, 1, 2, dst = ya)
    poisson_jumps = np.random.poisson(lambda_j, (days, paths))
    
    # Menentukan besaran lompatan jika terjadi
    jump_sizes = np.random.normal(mu_j, sigma_j, (days, paths))
    
    # Total komponen jump
    total_jumps = poisson_jumps * jump_sizes
    
    # 3. Total Return Harian (GBM + Jumps)
    total_daily_returns = gbm_returns + total_jumps
    
    # 4. Membangun Jalur Harga (Cumulative Sum dari Log Returns)
    price_paths = S0 * np.exp(np.cumsum(total_daily_returns, axis=0))
    
    # Menambahkan harga S0 di awal array (hari ke-0)
    S0_array = np.full((1, paths), S0)
    price_paths = np.vstack((S0_array, price_paths))
    
    return price_paths

if __name__ == "__main__":
    # Ticker IHSG di Yahoo Finance adalah ^JKSE
    TICKER = "^JKSE"
    START = "2020-01-01"
    END = "2026-08-03"
    DAYS_AHEAD = 30
    SIMULATIONS = 10000
    
    # 1. Tarik Data & Parameter
    S0, mu, sigma, hist_returns = fetch_data_and_params(TICKER, START, END)
    
    # 2. Jalankan Simulasi MJD
    paths = merton_jump_diffusion_mc(
        S0=S0, mu=mu, sigma=sigma, 
        days=DAYS_AHEAD, paths=SIMULATIONS,
        lambda_j=0.03,  # 3% peluang gap harga ekstrem per hari
        mu_j=-0.015,    # Rata-rata gap down -1.5%
        sigma_j=0.04    # Volatilitas gap 4%
    )
    
    # 3. Visualisasi Hasil
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Subplot 1: Plot 100 jalur harga pertama
    axes[0].plot(paths[:, :100], lw=1, alpha=0.6)
    axes[0].set_title(f"Merton Jump-Diffusion: 100 Sample Paths ({TICKER})")
    axes[0].set_xlabel("Hari Bursa (Trading Days)")
    axes[0].set_ylabel("Harga / Indeks")
    axes[0].grid(True, alpha=0.3)
    
    # Subplot 2: Histogram Distribusi Harga Akhir (Hari ke-30)
    final_prices = paths[-1, :]
    axes[1].hist(final_prices, bins=100, color='royalblue', edgecolor='black', alpha=0.7)
    
    # Menandai S0, Median, dan Value at Risk (VaR 95%)
    axes[1].axvline(S0, color='black', linestyle='dashed', linewidth=2, label=f"S0: {S0:.2f}")
    axes[1].axvline(np.median(final_prices), color='green', linestyle='dashed', linewidth=2, label=f"Median: {np.median(final_prices):.2f}")
    axes[1].axvline(np.percentile(final_prices, 5), color='red', linestyle='dashed', linewidth=2, label=f"5% VaR: {np.percentile(final_prices, 5):.2f}")
    
    axes[1].set_title(f"Distribusi Harga Akhir setelah {DAYS_AHEAD} Hari\n(10.000 Simulasi)")
    axes[1].set_xlabel("Harga / Indeks")
    axes[1].set_ylabel("Frekuensi")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_filename = "merton_jump_diffusion_plot.png"
    plt.savefig(plot_filename, dpi=300)
    print(f"\nPlot berhasil disimpan ke {plot_filename}")
    
    print(f"\nRingkasan Proyeksi 30 Hari:")
    print(f"Harga Awal      : {S0:.2f}")
    print(f"Median Proyeksi : {np.median(final_prices):.2f}")
    print(f"Skenario 5% Bawah (Worst Case): {np.percentile(final_prices, 5):.2f}")
    print(f"Skenario 5% Atas (Best Case)  : {np.percentile(final_prices, 95):.2f}")
