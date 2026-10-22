import os
import pandas as pd
import numpy as np
import ta

def engineer_features():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    price_dir = os.path.join(base_dir, "../data/raw/prices")
    sentiment_dir = os.path.join(base_dir, "../data/processed")
    out_dir = os.path.join(base_dir, "../data/processed")
    
    print("[SYSTEM] Starting Feature Engineering for Momentum and Sentiment...")
    
    for filename in os.listdir(price_dir):
        if not filename.endswith("_prices.csv"): continue
        ticker = filename.replace("_prices.csv", "")
        
        # 1. Load Price Data
        price_path = os.path.join(price_dir, filename)
        df_price = pd.read_csv(price_path, index_col=0, parse_dates=True)
        # Ensure Close is numeric
        df_price['Close'] = pd.to_numeric(df_price['Close'], errors='coerce')
        df_price.dropna(subset=['Close'], inplace=True)
        
        # 2. Load Sentiment Data
        sent_path = os.path.join(sentiment_dir, f"{ticker}_sentiment.csv")
        if not os.path.exists(sent_path):
            print(f"[WARNING] No sentiment data found for {ticker}, skipping.")
            continue
            
        df_sent = pd.read_csv(sent_path, index_col="Date", parse_dates=True)
        
        # 3. Merge Datasets
        df = df_price.join(df_sent, how="left")
        # Forward fill sentiment for weekends/holidays where news might have occurred
        df['Sentiment_Score'] = df['Sentiment_Score'].ffill().fillna(0)
        
        # 4. Momentum / Technical Features (using the 'ta' library)
        print(f"         Calculating Technical Indicators for {ticker}...")
        
        # --- Momentum & Trend Features ---
        df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
        df['SMA_30'] = ta.trend.sma_indicator(df['Close'], window=30)
        df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['MACD'] = ta.trend.macd(df['Close'])
        df['MACD_Signal'] = ta.trend.macd_signal(df['Close'])
        df['Stoch_Oscillator'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
        
        # --- Volatility Features ---
        df['BB_High'] = ta.volatility.bollinger_hband(df['Close'])
        df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'])
        df['BB_Width'] = ta.volatility.bollinger_wband(df['Close'])
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
        
        # --- Volume Features ---
        df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
        df['Volume_SMA_10'] = df['Volume'].rolling(10).mean()
        
        # --- Price Return Features ---
        df['Return_1d'] = df['Close'].pct_change(1)
        df['Return_5d'] = df['Close'].pct_change(5)
        
        # 5. Advanced Sentiment Features
        # Rolling sentiment smooths out the noise
        df['Sentiment_3d_MA'] = df['Sentiment_Score'].rolling(window=3).mean()
        df['Sentiment_Trend'] = df['Sentiment_Score'] - df['Sentiment_3d_MA']
        
        # 6. Target Variable: Next Day's Return Direction
        # (1 if the stock goes up tomorrow, 0 if it goes down)
        # Shift(-1) safely pulls tomorrow's return to today's row to avoid look-ahead bias
        df['Next_Day_Return'] = df['Close'].pct_change().shift(-1)
        df['Target'] = (df['Next_Day_Return'] > 0).astype(int)
        
        # Drop NaN values caused by rolling windows and shifting
        df.dropna(inplace=True)
        
        # Save finalized feature set
        final_path = os.path.join(out_dir, f"{ticker}_features.csv")
        df.to_csv(final_path)
        print(f"[SUCCESS] Saved engineered features for {ticker} (Shape: {df.shape})")

if __name__ == "__main__":
    engineer_features()
