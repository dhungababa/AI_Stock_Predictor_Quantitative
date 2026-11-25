import pandas as pd
import numpy as np
import os
from xgboost import XGBClassifier

live_ticker = "DRREDDY.NS"
cache_file = os.path.join(os.path.dirname(__file__), "../data/processed", f"{live_ticker}_features.csv")

df_stock = pd.read_csv(cache_file, index_col="Date", parse_dates=True)
feats = [
    'SMA_10', 'SMA_30', 'EMA_20', 'RSI', 'MACD', 'MACD_Signal',
    'Stoch_Oscillator', 'BB_High', 'BB_Low', 'BB_Width', 'ATR',
    'OBV', 'Volume_SMA_10', 'Return_1d', 'Return_5d',
    'Sentiment_Score', 'Sentiment_3d_MA', 'Sentiment_Trend'
]

df_backtest = df_stock.copy().dropna(subset=feats + ['Return_1d', 'Target'])
split_idx = int(len(df_backtest) * 0.8)
train_df = df_backtest.iloc[:split_idx]
test_df = df_backtest.iloc[split_idx:].copy()

# Train strictly on past 80%, test strictly out-of-sample on future 20% (zero look-ahead bias)
oos_model = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric='logloss')
oos_model.fit(train_df[feats], train_df['Target'])

oos_preds = oos_model.predict(test_df[feats])
test_df['Strategy_Return'] = np.where(oos_preds == 1, test_df['Return_1d'], 0.0)
test_df['Hold_Cum'] = (1 + test_df['Return_1d']).cumprod() * 10000
test_df['Strat_Cum'] = (1 + test_df['Strategy_Return']).cumprod() * 10000

print(f"OOS Window ({len(test_df)} days) Final Buy-Hold: {test_df['Hold_Cum'].iloc[-1]:.2f}")
print(f"OOS Window ({len(test_df)} days) Final Strategy: {test_df['Strat_Cum'].iloc[-1]:.2f}")
