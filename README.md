# Quantitative Equity Alpha & Risk Terminal

## Overview
Multi-factor Indian equity (NSE) quantitative research terminal combining **XGBoost** classification, **ProsusAI/finbert** financial news sentiment scoring, walk-forward **TimeSeriesSplit** validation, Indian statutory friction modeling, and vectorized **Monte Carlo Geometric Brownian Motion (GBM)** VaR/CVaR risk analytics.

## Data & Empirical Findings (Zero Look-Ahead Validation)
- **Universe:** 22 Nifty 50 equities (`RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.NS`, etc.) over ~5 years (`1,206` daily bars per ticker, Nov 2021 – Sep 2026) via `yfinance`.
- **18 Quantitative Factors (`src/features.py`):** 15 price/volume/volatility indicators (`SMA_10`, `SMA_30`, `EMA_20`, `RSI`, `MACD`, `Stoch`, Bollinger Bands, `ATR`, `OBV`, `Return_1d/5d`) + 3 FinBERT NLP sentiment factors.
- **Honest Out-of-Sample Results (`models/comparative_results.csv`):**
  - Across 5-fold `TimeSeriesSplit` cross-validation, out-of-sample directional accuracy ranges realistically between **48% and 54% (`0.48–0.56` ROC-AUC)** across tickers, demonstrating weak daily equity predictability after transaction costs.
  - The interactive backtester enforces strict **out-of-sample walk-forward training** (fitting only on history strictly prior to the evaluation window) and models Indian delivery/execution frictions (**0.10% STT**, **INR 20 brokerage**, **5 bps slippage**) exclusively on entry/exit turnover.

## Modules
1. **FinBERT NLP Pipeline (`src/sentiment.py`):** Batch-scores headlines using HuggingFace `ProsusAI/finbert` (`PyTorch` inference) into daily net sentiment and trend features.
2. **Risk Analytics (`app/monte_carlo_var.py`):** 1,000-path vectorized Monte Carlo GBM engine estimating 95%/99% Parametric & Historical VaR and Expected Shortfall (CVaR).
3. **Simulated L2 Slippage Estimator (`app/market_depth.py`):** Synthetic 10-tier NSE bid/ask ladder heuristic around spot price to approximate order-book impact and VWAP slippage (note: NSE L2 tick feeds require institutional colocation/paid data).
4. **11-Factor Rule Committee (`src/microbots.py`):** Deterministic quantitative scoring across trend, India VIX regime, FinBERT sentiment, liquidity turnover, statutory tax drag, and Fractional Half-Kelly sizing.

## Running & Testing
```bash
pip install -r requirements.txt
pytest tests/ -v
streamlit run app/app.py
```

## Tech Stack
`Python`, `XGBoost`, `scikit-learn`, `Transformers (FinBERT)`, `PyTorch`, `yfinance`, `ta`, `Pandas`, `NumPy`, `Plotly`, `Streamlit`, `Pytest`
