# ⚡ Pro Quant Terminal — Designed by Xpinontoan

Pro Quant Terminal adalah platform analisis kuantitatif, pemeringkatan machine learning, dan eksekusi otomatis untuk bursa saham Indonesia (BEI / IDX).

## 🚀 Fitur Utama

- **🎯 Screener Adaptif**: Sinyal gabungan Golden Cross EMA 20/50, OBV Smart Money, Dynamic SL 2x ATR, dan Half-Kelly Lot Sizing.
- **🏆 Pemeringkatan XGBoost Machine Learning**: Model ML teruji pada 941 saham BEI untuk memprediksi probabilitas kenaikan >3% dalam 5 hari perdagangan.
- **⏱️ Intraday VWAP Floor (1-Menit)**: Visualisasi candle intraday 1-menit dan garis institusi VWAP real-time.
- **🏦 Desk Makro-Mikro & Risk-On/Off**: Evaluasi kuantitatif indikator makro (BI Rate, Inflation, USD/IDR, Newcastle Coal, CPO Malaysia) dengan Skor Risiko Makro terintegrasi.
- **📂 Active Portfolio & Risk Guard**: Pengawasan otomatis posisi terbuka dengan Auto Take-Profit dan Auto Cut-Loss Real-Time.
- **🔌 IPOT Execution Engine Module**: Integrasi Direct Market Access (DMA) ke broker Indo Premier Securities via API HMAC-SHA256 (`ipot_engine.py`).

## 🛠️ Cara Memulai

### 1. Prasyarat & Instalasi Dependency
```bash
pip install -r requirements.txt
```

### 2. Menjalankan Terminal secara Lokal
```bash
streamlit run app.py
```

---
*Powered by Xpinontoan Quant Desk.*
