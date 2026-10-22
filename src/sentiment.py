import os
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

def process_sentiment():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    news_dir = os.path.join(base_dir, "../data/raw/news")
    out_dir = os.path.join(base_dir, "../data/processed")
    os.makedirs(out_dir, exist_ok=True)
    
    # HuggingFace cache settings to prevent Windows path issues
    os.environ["HF_HOME"] = r"C:\Users\devas\Desktop\finanace\hf_cache"
    
    print("[SYSTEM] Loading ProsusAI/finbert from HuggingFace...")
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    
    # Use GPU if available, else CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    labels = ["positive", "negative", "neutral"]
    
    for filename in os.listdir(news_dir):
        if not filename.endswith("_news.csv"): continue
        ticker = filename.replace("_news.csv", "")
        
        out_path = os.path.join(out_dir, f"{ticker}_sentiment.csv")
        if os.path.exists(out_path):
            print(f"[SYSTEM] {ticker} already processed. Skipping to save time...")
            continue
            
        print(f"\n[SYSTEM] Scoring sentiment for {ticker}...")
        df = pd.read_csv(os.path.join(news_dir, filename))
        
        daily_scores = []
        # Group headlines by date to calculate an aggregate daily score
        grouped = df.groupby("Date")
        
        for date, group in tqdm(grouped, desc=ticker):
            headlines = group["Headline"].tolist()
            
            # Batch tokenize for performance
            inputs = tokenizer(headlines, return_tensors="pt", padding=True, truncation=True).to(device)
            with torch.no_grad():
                logits = model(**inputs).logits
                probs = torch.softmax(logits, dim=1)
                
            # Calculate a daily aggregated sentiment score
            # Score = Average(Positive Prob - Negative Prob)
            pos_idx = labels.index("positive")
            neg_idx = labels.index("negative")
            
            # Calculate net sentiment for each headline, then average across the day
            net_sentiment = (probs[:, pos_idx] - probs[:, neg_idx]).mean().item()
            
            daily_scores.append({
                "Date": date,
                "Sentiment_Score": net_sentiment
            })
            
        sentiment_df = pd.DataFrame(daily_scores)
        sentiment_df.to_csv(os.path.join(out_dir, f"{ticker}_sentiment.csv"), index=False)
        print(f"[SUCCESS] Saved aggregated sentiment for {ticker}")

if __name__ == "__main__":
    process_sentiment()
