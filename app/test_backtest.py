import pandas as pd
import joblib
import numpy as np
import os

live_ticker = "DRREDDY.NS"
cache_file = os.path.join('../data/processed', f"{live_ticker}_features.csv")
model_path = os.path.join('../models', f"{live_ticker}_Combined.joblib")

df_stock = pd.read_csv(cache_file, index_col="Date", parse_dates=True)
model = joblib.load(model_path)
feats = ['SMA_10', 'SMA_30', 'EMA_20', 'RSI', 'MACD', 'MACD_Signal', 'Stoch_Oscillator', 'BB_High', 'BB_Low', 'BB_Width', 'ATR', 'OBV', 'Volume_SMA_10', 'Return_1d', 'Return_5d', 'Sentiment_Score', 'Sentiment_3d_MA', 'Sentiment_Trend']

df_backtest = df_stock.copy().dropna(subset=feats + ['Return_1d'])
historical_preds = model.predict(df_backtest[feats])
df_backtest['Strategy_Return'] = np.where(historical_preds == 1, df_backtest['Return_1d'], 0) 
df_backtest['Hold_Cum'] = (1 + df_backtest['Return_1d']).cumprod() * 10000
df_backtest['Strat_Cum'] = (1 + df_backtest['Strategy_Return']).cumprod() * 10000

final_hold = df_backtest['Hold_Cum'].iloc[-1]
final_strat = df_backtest['Strat_Cum'].iloc[-1]

print("Final Hold:", final_hold)
print("Final Strat:", final_strat)
