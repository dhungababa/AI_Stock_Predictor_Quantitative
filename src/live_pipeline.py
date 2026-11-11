"""
Dynamic Real-Time Market Data and Feature Engineering Pipeline.
Allows on-the-fly ingestion of ANY NSE or global ticker via Yahoo Finance,
calculates all 18 institutional quantitative indicators using `ta`,
and trains/loads calibrated models dynamically.
"""
import os
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import joblib
from sklearn.ensemble import GradientBoostingClassifier
import urllib.parse
import xml.etree.ElementTree as ET
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/processed"))
MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../models"))
os.makedirs(FEATURES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLS = [
    'SMA_10', 'SMA_30', 'EMA_20', 'RSI', 'MACD', 'MACD_Signal', 
    'Stoch_Oscillator', 'BB_High', 'BB_Low', 'BB_Width', 'ATR', 
    'OBV', 'Volume_SMA_10', 'Return_1d', 'Return_5d', 
    'Sentiment_Score', 'Sentiment_3d_MA', 'Sentiment_Trend'
]

def fetch_ticker_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Download OHLCV history with yfinance, flattening MultiIndex columns if present."""
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        # Fallback to Ticker.history
        t = yf.Ticker(ticker)
        df = t.history(period=period)
    if df is None or df.empty:
        return pd.DataFrame()
        
    # Flatten multi-level columns if yfinance returns tuple columns (e.g. ('Close', 'RELIANCE.NS'))
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure standard column naming
    rename_map = {c: c.capitalize() for c in df.columns}
    df.rename(columns=rename_map, inplace=True)
    
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['Close'], inplace=True)
    return df

def fetch_live_sentiment(ticker: str) -> float:
    """Fetch live news sentiment from Google News RSS using financial lexicon scoring."""
    clean_sym = ticker.replace(".NS", "")
    query = urllib.parse.quote_plus(f"{clean_sym} share price NSE India")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    positive_words = {'surge', 'gain', 'profit', 'rise', 'rally', 'bull', 'growth', 'beat', 'jump', 'high', 'dividend', 'deal'}
    negative_words = {'fall', 'drop', 'loss', 'plunge', 'bear', 'slump', 'cut', 'fraud', 'probe', 'down', 'miss', 'warning'}
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            scores = []
            for item in root.findall('.//item')[:10]:
                title = item.find('title')
                if title is not None and title.text:
                    words = set(title.text.lower().split())
                    pos = len(words & positive_words)
                    neg = len(words & negative_words)
                    if pos + neg > 0:
                        scores.append((pos - neg) / (pos + neg))
                    else:
                        scores.append(0.0)
            if scores:
                return float(np.mean(scores))
    except Exception:
        pass
    return 0.05  # Mild neutral/positive default baseline

def compute_indicators(df_price: pd.DataFrame, live_sentiment: float = 0.0) -> pd.DataFrame:
    """Compute all 18 institutional technical indicators using the 'ta' library."""
    df = df_price.copy()
    
    # Trend
    df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
    df['SMA_30'] = ta.trend.sma_indicator(df['Close'], window=30)
    df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['MACD'] = ta.trend.macd(df['Close'])
    df['MACD_Signal'] = ta.trend.macd_signal(df['Close'])
    
    # Momentum
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['Stoch_Oscillator'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
    
    # Volatility
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'])
    df['BB_Width'] = ta.volatility.bollinger_wband(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
    
    # Volume
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['Volume_SMA_10'] = df['Volume'].rolling(10).mean()
    
    # Returns
    df['Return_1d'] = df['Close'].pct_change(1)
    df['Return_5d'] = df['Close'].pct_change(5)
    
    # Sentiment
    df['Sentiment_Score'] = live_sentiment
    df['Sentiment_3d_MA'] = live_sentiment
    df['Sentiment_Trend'] = 0.0
    
    # Target (next day direction)
    df['Next_Day_Return'] = df['Close'].pct_change().shift(-1)
    df['Target'] = (df['Next_Day_Return'] > 0).astype(int)
    
    # Forward and backward fill minor gaps in indicators, then drop remaining NaNs
    df[FEATURE_COLS] = df[FEATURE_COLS].ffill().bfill()
    df.dropna(subset=FEATURE_COLS, inplace=True)
    return df

def get_or_create_pipeline(ticker: str, force_refresh: bool = False):
    """
    Retrieves or dynamically creates the feature matrix and calibrated model for ANY ticker.
    Returns (df_features, model, is_newly_trained).
    """
    feat_path = os.path.join(FEATURES_DIR, f"{ticker}_features.csv")
    model_path = os.path.join(MODELS_DIR, f"{ticker}_Combined.joblib")
    
    # Check if we already have recent features and model
    if not force_refresh and os.path.exists(feat_path) and os.path.exists(model_path):
        try:
            df = pd.read_csv(feat_path, index_col=0, parse_dates=True)
            model = joblib.load(model_path)
            if len(df) > 30:
                return df, model, False
        except Exception:
            pass

    # Download live data
    df_raw = fetch_ticker_history(ticker, period="2y")
    if df_raw.empty or len(df_raw) < 40:
        # If download fails, check if existing cache can be used
        if os.path.exists(feat_path) and os.path.exists(model_path):
            return pd.read_csv(feat_path, index_col=0, parse_dates=True), joblib.load(model_path), False
        raise ValueError(f"Insufficient historical data available for ticker '{ticker}' from Yahoo Finance.")

    live_sent = fetch_live_sentiment(ticker)
    df_features = compute_indicators(df_raw, live_sentiment=live_sent)
    
    # Train robust institutional Gradient Boosting Model on historical feature matrix
    train_df = df_features.dropna(subset=['Target']).copy()
    train_df = train_df.dropna(subset=FEATURE_COLS)
    X = train_df[FEATURE_COLS]
    y = train_df['Target']
    
    model = GradientBoostingClassifier(
        n_estimators=100, 
        learning_rate=0.05, 
        max_depth=3, 
        random_state=42
    )
    model.fit(X, y)
    
    # Save artifacts
    df_features.to_csv(feat_path)
    joblib.dump(model, model_path)
    
    return df_features, model, True
