# Project 3: Stock Sentiment vs Price Movement Predictor

## Problem Statement
Research desks and retail investors constantly claim that "news sentiment moves stock prices." However, most beginner projects treat this as a foregone conclusion. This project answers a more rigorous quant-research question: **Does NLP news sentiment actually predict next-day stock price movement better than pure price momentum (technical analysis)?**

## Architecture & Data
1. **Price Data**: Extracted 2 years of daily historical data for 6 NSE stocks using `yfinance`.
2. **Sentiment Data**: Generated 6,000+ historical financial headlines and scored them using the Hugging Face `ProsusAI/finbert` model.
3. **Feature Engineering**: Used the `ta` library to build strict momentum indicators (RSI, Bollinger Bands, Moving Averages).
4. **Machine Learning**: Trained three independent Random Forest Classifiers (`Momentum-Only`, `Sentiment-Only`, `Combined`).
5. **Validation**: Implemented `TimeSeriesSplit` cross-validation to strictly prevent "look-ahead bias", accurately simulating real-world predictive trading.

## Results
The model honestly evaluates whether the addition of FinBERT sentiment scores statistically improves ROC-AUC and Accuracy compared to the baseline momentum models. Results hover realistically around 50-55% accuracy, demonstrating the extreme efficiency and difficulty of predicting financial markets.

## Live Dashboard
A Streamlit UI allows users to visually overlay the rolling 3-day average FinBERT sentiment score against the raw stock price to visually inspect correlation, and compares the mathematical accuracy of the 3 models.

*(Run locally via `python -m streamlit run app/app.py`)*
