import os
import pandas as pd
import numpy as np
import json
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score

def validate_models():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    features_dir = os.path.join(base_dir, "../data/processed")
    models_dir = os.path.join(base_dir, "../models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("[SYSTEM] Starting Comparative Modelling (Time-Series Cross Validation)...")
    
    momentum_cols = ['SMA_10', 'SMA_30', 'EMA_20', 'RSI', 'MACD', 'MACD_Signal', 'Stoch_Oscillator', 'BB_High', 'BB_Low', 'BB_Width', 'ATR', 'OBV', 'Volume_SMA_10', 'Return_1d', 'Return_5d']
    sentiment_cols = ['Sentiment_Score', 'Sentiment_3d_MA', 'Sentiment_Trend']
    combined_cols = momentum_cols + sentiment_cols
    
    results = []
    
    for filename in os.listdir(features_dir):
        if not filename.endswith("_features.csv"): continue
        ticker = filename.replace("_features.csv", "")
        
        df = pd.read_csv(os.path.join(features_dir, filename), index_col="Date", parse_dates=True)
        if df.empty or len(df) < 50:
            print(f"[WARNING] Not enough data for {ticker}, skipping.")
            continue
            
        print(f"\n[SYSTEM] Training models for {ticker}...")
        
        # We use TimeSeriesSplit to prevent look-ahead bias
        # This simulates trading in the real world where you only know the past
        tscv = TimeSeriesSplit(n_splits=5)
        
        models = {
            "Momentum_Only": {"features": momentum_cols, "model": XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, use_label_encoder=False, eval_metric='logloss')},
            "Sentiment_Only": {"features": sentiment_cols, "model": XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, use_label_encoder=False, eval_metric='logloss')},
            "Combined": {"features": combined_cols, "model": XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, use_label_encoder=False, eval_metric='logloss')}
        }
        
        stock_results = {"Ticker": ticker}
        
        for model_name, config in models.items():
            X = df[config["features"]]
            y = df["Target"]
            
            fold_accs, fold_aucs = [], []
            
            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                clf = config["model"]
                clf.fit(X_train, y_train)
                
                preds = clf.predict(X_test)
                # Softmax probabilities for ROC-AUC
                probs = clf.predict_proba(X_test)[:, 1]
                
                fold_accs.append(accuracy_score(y_test, preds))
                try:
                    fold_aucs.append(roc_auc_score(y_test, probs))
                except ValueError:
                    # Sometimes a fold might only have one class
                    pass
                    
            avg_acc = np.mean(fold_accs)
            avg_auc = np.mean(fold_aucs) if fold_aucs else 0.5
            
            stock_results[f"{model_name}_Acc"] = avg_acc
            stock_results[f"{model_name}_AUC"] = avg_auc
            
            print(f"         {model_name.ljust(15)} -> Accuracy: {avg_acc:.2%}, AUC: {avg_auc:.2f}")
            
            # Save the final model trained on all data for deployment
            clf_final = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, use_label_encoder=False, eval_metric='logloss')
            clf_final.fit(X, y)
            joblib.dump(clf_final, os.path.join(models_dir, f"{ticker}_{model_name}.joblib"))
            
        results.append(stock_results)
        
    # Save the aggregated research results for the Streamlit dashboard to display
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join(models_dir, "comparative_results.csv"), index=False)
    print("\n[SUCCESS] Comparative modelling complete. Results saved for dashboard.")

if __name__ == "__main__":
    validate_models()
