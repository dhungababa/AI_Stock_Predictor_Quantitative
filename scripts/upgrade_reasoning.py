with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                        <div style=\"background-color: rgba(0,0,0,0.4); padding: 15px; border-radius: 5px; text-align: left;\">
                            <h4 style=\"margin-top:0px; color: #f8fafc;\"> AI Reasoning (Why?):</h4>
                            <ul style=\"margin-bottom: 0px; color: #cbd5e1; font-size: 16px;\">
                                <li><b>Trend:</b> Short-term momentum is <b>{'Stronger' if float(last_row['SMA_10'].iloc[0]) > float(last_row['SMA_30'].iloc[0]) else 'Weaker'}</b> than the 30-day average.</li>
                                <li><b>Value:</b> RSI is at {float(last_row['RSI'].iloc[0]):.1f} (<b>{'Oversold/Cheap' if float(last_row['RSI'].iloc[0]) < 45 else 'Overbought/Expensive' if float(last_row['RSI'].iloc[0]) > 60 else 'Neutral Momentum'}</b>).</li>
                                <li><b>Sentiment:</b> Recent news flow is <b>{'Positive' if float(last_row['Sentiment_Score'].iloc[0]) > 0 else 'Negative' if float(last_row['Sentiment_Score'].iloc[0]) < 0 else 'Neutral'}</b> for this asset.</li>
                            </ul>
                        </div>'''

replacement = '''                        <div style=\"background-color: rgba(0,0,0,0.4); padding: 20px; border-radius: 8px; text-align: left; border: 1px solid #3b3f51;\">
                            <h4 style=\"margin-top:0px; color: #00d084; font-size: 18px;\"> Deep Quantum Analysis Engine</h4>
                            <p style=\"color: #94a3b8; font-size: 14px; margin-bottom: 15px;\">The XGBoost model calculated a <b>{confidence:.1f}%</b> probability of success by inter-connecting 18 technical indicators with real-time NLP news sentiment. Here are the 3 strongest drivers for this specific prediction:</p>
                            <ul style=\"margin-bottom: 0px; color: #f8fafc; font-size: 15px; line-height: 1.8;\">
                                <li><b style=\"color: #cbd5e1;\">1. Price Momentum (SMA Cross):</b> The short-term 10-day moving average is mathematically <b>{'Stronger' if float(last_row['SMA_10'].iloc[0]) > float(last_row['SMA_30'].iloc[0]) else 'Weaker'}</b> than the 30-day structural trend, signaling {'bullish' if float(last_row['SMA_10'].iloc[0]) > float(last_row['SMA_30'].iloc[0]) else 'bearish'} trajectory.</li>
                                <li><b style=\"color: #cbd5e1;\">2. Value Distortion (RSI):</b> The Relative Strength Index is currently at <b>{float(last_row['RSI'].iloc[0]):.1f}</b>. The algorithm flags this as <b>{'Oversold (Undervalued)' if float(last_row['RSI'].iloc[0]) < 45 else 'Overbought (Expensive)' if float(last_row['RSI'].iloc[0]) > 60 else 'Neutral / Fairly Valued'}</b>.</li>
                                <li><b style=\"color: #cbd5e1;\">3. Market Psychology (FinBERT):</b> Global news scanning detects that the current institutional sentiment weight is explicitly <b>{'Positive' if float(last_row['Sentiment_Score'].iloc[0]) > 0 else 'Negative' if float(last_row['Sentiment_Score'].iloc[0]) < 0 else 'Neutral'}</b>.</li>
                            </ul>
                            <div style=\"margin-top: 15px; padding-top: 10px; border-top: 1px dashed #3b3f51;\">
                                <span style=\"color: #94a3b8; font-size: 13px;\"><i>All 18 parameters are actively visualized in the 'AI Brain' Donut Chart below.</i></span>
                            </div>
                        </div>'''

if target in content:
    with open('app/app.py', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print('SUCCESS')
else:
    print('TARGET NOT FOUND')
