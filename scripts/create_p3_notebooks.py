import os
import json

def create_notebook(path, cells):
    nb = {
        'cells': [{'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': [c]} for c in cells],
        'metadata': {},
        'nbformat': 4,
        'nbformat_minor': 5
    }
    with open(path, 'w') as f:
        json.dump(nb, f)

os.makedirs('notebooks', exist_ok=True)

create_notebook('notebooks/01_data_collection.ipynb', [
    '# Week 1: Price & News Data Collection\nimport yfinance as yf\n\n# Exploratory test for downloading single stock data\ndf = yf.download("RELIANCE.NS", period="2y", interval="1d", auto_adjust=True)\ndf.head()'
])

create_notebook('notebooks/02_sentiment_scoring.ipynb', [
    '# Week 2: FinBERT Sentiment Scoring\nfrom transformers import AutoTokenizer, AutoModelForSequenceClassification\nimport torch\n\ntokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")\nmodel = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")\n\n# Test on a single headline\nheadline = "Reliance announces massive revenue growth."\ninputs = tokenizer(headline, return_tensors="pt")\noutputs = model(**inputs)\nprobs = torch.softmax(outputs.logits, dim=1)\nprint(probs)'
])

create_notebook('notebooks/03_feature_engineering.ipynb', [
    '# Week 3: Feature Engineering\nimport pandas as pd\nimport ta\n\n# Example of calculating RSI and Moving Averages\n# df["RSI"] = ta.momentum.rsi(df["Close"], window=14)\n# df["SMA_10"] = ta.trend.sma_indicator(df["Close"], window=10)'
])

create_notebook('notebooks/04_comparative_modelling.ipynb', [
    '# Week 4: Comparative Modelling\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.model_selection import TimeSeriesSplit\n\n# This notebook explores TimeSeriesSplit vs normal K-Fold to prevent look-ahead bias.\n# tscv = TimeSeriesSplit(n_splits=5)'
])
print('Notebooks successfully created.')
