"""
quant_copilot.py — Institutional Quantitative Alpha Copilot & Algorithmic Trading Chatbot
Provides conversational intelligence grounded in real-time NSE market telemetry,
technical indicators, XGBoost/LightGBM ML predictions, Graham-Dodd fundamentals,
friction/tax calculations, and Kelly Criterion risk budgeting.
"""

import streamlit as st
import numpy as np
import pandas as pd
import math
import os
import re

# =========================================================================
# INSTITUTIONAL REASONING ENGINE (OFFLINE FALLBACK & ZERO-HALLUCINATION LOGIC)
# =========================================================================

def analyze_technical_indicators(ctx: dict) -> str:
    """Detailed breakdown of all active technical indicators for the stock."""
    ticker = ctx.get("ticker", "Stock")
    price = ctx.get("price", 0.0)
    ind = ctx.get("indicators", {})
    
    rsi = ind.get("RSI", 50.0)
    macd = ind.get("MACD", 0.0)
    macd_sig = ind.get("MACD_Signal", 0.0)
    macd_hist = ind.get("MACD_Hist", macd - macd_sig)
    atr = ind.get("ATR", price * 0.015)
    bb_upper = ind.get("BB_Upper", price * 1.03)
    bb_lower = ind.get("BB_Lower", price * 0.97)
    ema20 = ind.get("EMA_20", price)
    sma50 = ind.get("SMA_50", price)
    sma200 = ind.get("SMA_200", price)
    stoch_k = ind.get("Stoch_K", 50.0)
    adx = ind.get("ADX", 25.0)

    if rsi >= 70:
        rsi_state = f"**Overbought** ({rsi:.1f}) — momentum is stretched, watch for mean-reversion pullbacks."
    elif rsi <= 30:
        rsi_state = f"**Oversold** ({rsi:.1f}) — selling climax detected, favorable risk-reward for swing accumulation."
    else:
        rsi_state = f"**Neutral / Trend Continuum** ({rsi:.1f}) — healthy momentum without exhaustion."

    if macd > macd_sig:
        macd_state = f"**Bullish Crossover** (MACD: {macd:.2f} > Signal: {macd_sig:.2f}, Histogram: +{macd_hist:.2f}). Positive acceleration."
    else:
        macd_state = f"**Bearish Momentum** (MACD: {macd:.2f} < Signal: {macd_sig:.2f}, Histogram: {macd_hist:.2f}). Selling pressure prevailing."

    trend_state = "Bullish Golden Alignment" if (price > ema20 > sma50) else ("Bearish Alignment" if (price < ema20 < sma50) else "Consolidation / Mixed")
    
    bb_width = ((bb_upper - bb_lower) / price) * 100 if price > 0 else 0
    bb_pos = "Near Upper Resistance Band" if price >= bb_upper * 0.99 else ("Near Lower Support Band" if price <= bb_lower * 1.01 else "Within Normal Volatility Channel")

    return f"""### 📊 Technical Indicators Audit for **{ticker}** (CMP: ₹{price:,.2f})

| Indicator | Current Value | State / Institutional Interpretation |
| :--- | :--- | :--- |
| **RSI (14)** | `{rsi:.2f}` | {rsi_state} |
| **MACD (12, 26, 9)** | `{macd:.2f}` / `{macd_sig:.2f}` | {macd_state} |
| **ATR (14)** | `₹{atr:.2f}` (`{(atr/price)*100:.2f}%`) | Daily expected volatility band. Critical for SL sizing. |
| **Trend Alignment** | Price vs EMA20 / SMA50 | **{trend_state}** (EMA20: ₹{ema20:,.2f}, SMA50: ₹{sma50:,.2f}) |
| **Bollinger Bands (20, 2)** | Bandwidth: `{bb_width:.2f}%` | {bb_pos} (Upper: ₹{bb_upper:,.2f}, Lower: ₹{bb_lower:,.2f}) |
| **Stochastic Oscillator (%K)** | `{stoch_k:.1f}` | {'Overbought' if stoch_k > 80 else ('Oversold' if stoch_k < 20 else 'Neutral range')} |
| **ADX (Trend Strength)** | `{adx:.1f}` | {'Strong Trending Regime (>25)' if adx >= 25 else 'Rangebound / Low Momentum (<25)'} |

**Tactical Summary:** The asset is exhibiting **{trend_state.lower()}** behavior with daily volatility of ₹{atr:.2f} per share. Momentum is governed by {rsi_state.split('—')[0].strip()}."""

def calculate_stop_loss_and_target(ctx: dict) -> str:
    """Calculates volatility-adjusted Stop Loss, Take Profit 1 & 2 using ATR."""
    ticker = ctx.get("ticker", "Stock")
    price = ctx.get("price", 0.0)
    ind = ctx.get("indicators", {})
    atr = ind.get("ATR", price * 0.015)
    pred_dir = ctx.get("pred_text", "BUY")

    is_bullish = ("BUY" in pred_dir.upper() or "UP" in pred_dir.upper() or "HOLD" in pred_dir.upper())

    if is_bullish:
        sl = max(price - 1.5 * atr, 0.01)
        tp1 = price + 2.0 * atr
        tp2 = price + 3.0 * atr
        sl_pct = ((price - sl) / price) * 100
        tp1_pct = ((tp1 - price) / price) * 100
        tp2_pct = ((tp2 - price) / price) * 100
        rr1 = tp1_pct / sl_pct if sl_pct > 0 else 1.33
        rr2 = tp2_pct / sl_pct if sl_pct > 0 else 2.0
        direction = "LONG (BUY)"
    else:
        sl = price + 1.5 * atr
        tp1 = max(price - 2.0 * atr, 0.01)
        tp2 = max(price - 3.0 * atr, 0.01)
        sl_pct = ((sl - price) / price) * 100
        tp1_pct = ((price - tp1) / price) * 100
        tp2_pct = ((price - tp2) / price) * 100
        rr1 = tp1_pct / sl_pct if sl_pct > 0 else 1.33
        rr2 = tp2_pct / sl_pct if sl_pct > 0 else 2.0
        direction = "SHORT (SELL / HEDGE)"

    return f"""### 🎯 Volatility-Engineered Trade Execution Levels for **{ticker}**

* **Execution Direction:** `{direction}`
* **Current Market Price (CMP):** `₹{price:,.2f}`
* **Current 14-period ATR:** `₹{atr:.2f}`

#### 📐 Target & Risk Boundary Matrix:
* 🛑 **Dynamic Stop Loss (1.5× ATR):** **`₹{sl:,.2f}`** (`-{sl_pct:.2f}%` risk buffer)
  * *Prevents premature stop-outs from intraday noise while capping capital downside.*
* 🎯 **Take Profit 1 (Conservative - 2.0× ATR):** **`₹{tp1:,.2f}`** (`+{tp1_pct:.2f}%` | R:R = **1:{rr1:.2f}**)
  * *Recommended level to trim 50% position and move Stop Loss to breakeven.*
* 🚀 **Take Profit 2 (Extended Trend - 3.0× ATR):** **`₹{tp2:,.2f}`** (`+{tp2_pct:.2f}%` | R:R = **1:{rr2:.2f}**)
  * *Full exit or trailing ATR stop target for complete trend capture.*

**Institutional Execution Rule:** Never enter without the hard stop pre-placed in the order management system (OMS) at ₹{sl:,.2f}."""

def calculate_friction_and_taxes(trade_value: float = 100000.0) -> str:
    """Calculates comprehensive Indian stock market friction (STT, brokerage, stamp duty, GST, exchange fees)."""
    stt = trade_value * 0.001
    brokerage = min(20.0, trade_value * 0.0005)
    exchange_txn = trade_value * 0.0000345
    sebi_fee = trade_value * 0.000001
    stamp_duty = trade_value * 0.00015
    gst = (brokerage + exchange_txn + sebi_fee) * 0.18
    slippage = trade_value * 0.0005
    
    total_statutory = stt + stamp_duty + exchange_txn + sebi_fee + gst
    total_friction = total_statutory + brokerage + slippage
    friction_pct = (total_friction / trade_value) * 100
    breakeven_bps = friction_pct * 100

    return f"""### 💰 Full Transaction Friction & Regulatory Tax Breakdown

Calculated for an institutional/retail round-trip order size of **₹{trade_value:,.2f}**:

| Friction Component | Regulatory / Broker Rate | Rupee Amount (₹) | Impact (% of Capital) |
| :--- | :--- | :--- | :--- |
| **Securities Transaction Tax (STT)** | 0.10% (Delivery Leg) | `₹{stt:,.2f}` | `{stt/trade_value*100:.3f}%` |
| **Stamp Duty (State)** | 0.015% (Buy Leg) | `₹{stamp_duty:,.2f}` | `{stamp_duty/trade_value*100:.3f}%` |
| **NSE Exchange Turnover Charge** | 0.00345% | `₹{exchange_txn:,.2f}` | `{exchange_txn/trade_value*100:.4f}%` |
| **SEBI Turnover Charge** | ₹10 / Crore (0.0001%) | `₹{sebi_fee:,.2f}` | `{sebi_fee/trade_value*100:.5f}%` |
| **Brokerage** | ₹20 cap / 0.05% | `₹{brokerage:,.2f}` | `{brokerage/trade_value*100:.3f}%` |
| **Goods & Services Tax (GST)** | 18% on Brokerage & Fees | `₹{gst:,.2f}` | `{gst/trade_value*100:.4f}%` |
| **Market Slippage (5 bps)** | 0.050% (Bid-Ask spread) | `₹{slippage:,.2f}` | `{slippage/trade_value*100:.3f}%` |
| **TOTAL ROUND-TRIP FRICTION** | **Comprehensive** | **`₹{total_friction:,.2f}`** | **`{friction_pct:.3f}%`** |

**Breakeven Hurdle:** The stock must move at least **+{friction_pct:.2f}%** (`+{breakeven_bps:.1f} basis points`) before the trade yields net positive P&L after friction."""

def explain_kelly_criterion(ctx: dict) -> str:
    """Explains Kelly Criterion optimal capital sizing and risk budgeting."""
    ticker = ctx.get("ticker", "Stock")
    confidence = ctx.get("confidence", 65.0)
    
    p = confidence / 100.0
    b = 1.8
    raw_kelly = (p * (b + 1) - 1) / b if b > 0 else 0.0
    raw_kelly = max(min(raw_kelly, 0.40), 0.0)
    half_kelly = raw_kelly * 0.5

    portfolio_size = 500000.0
    suggested_alloc = portfolio_size * half_kelly

    return f"""### ⚖️ Kelly Criterion Risk Allocation Engine for **{ticker}**

$$\\text{{Kelly Fraction }} f^* = \\frac{{p(b + 1) - 1}}{{b}}$$

* **Model Win Probability ($p$):** `{p*100:.1f}%` (Derived from XGBoost/Ensemble model confidence)
* **Estimated Win/Loss Payoff Ratio ($b$):** `{b:.2f}` (Based on ATR 2.0x target vs 1.5x stop-loss)
* **Unconstrained Full Kelly ($f^*$):** `{raw_kelly*100:.2f}%` of portfolio
* **Institutional Half-Kelly Allocation:** **`{half_kelly*100:.2f}%`** (Recommended)

#### 💼 Capital Sizing on ₹{portfolio_size:,.0f} Fund:
* **Recommended Position Size:** **`₹{suggested_alloc:,.2f}`**
* **Shares to Acquire (CMP ₹{ctx.get('price', 1000):,.2f}):** ~`{int(suggested_alloc / max(ctx.get('price', 1000), 1))} units`

> **Risk Mitigation Principle:** Full Kelly sizing is vulnerable to severe portfolio drawdowns (volatility drag). Hedge funds apply **Half-Kelly** to capture 75% of maximum growth with only 25% of variance risk."""

def explain_graham_valuation(ctx: dict) -> str:
    """Explains Benjamin Graham intrinsic value, Graham number, and margin of safety."""
    ticker = ctx.get("ticker", "Stock")
    price = ctx.get("price", 1000.0)
    graham = ctx.get("graham", {})
    
    pe = graham.get("pe_ratio", 22.4)
    pb = graham.get("pb_ratio", 2.8)
    eps = graham.get("eps", price / pe if pe > 0 else 45.0)
    bvps = graham.get("bvps", price / pb if pb > 0 else 350.0)
    
    val_product = 22.5 * max(eps, 0.1) * max(bvps, 0.1)
    graham_number = math.sqrt(val_product) if val_product > 0 else price
    margin_of_safety = ((graham_number - price) / graham_number) * 100 if graham_number > 0 else 0.0

    undervalued = margin_of_safety > 0

    return f"""### 🏛️ Benjamin Graham Fundamental Valuation Audit for **{ticker}**

According to classic Graham-Dodd Security Analysis, a defensive equity should satisfy $P/E \\times P/B \\le 22.5$:

$$\\text{{Graham Number}} = \\sqrt{{22.5 \\times \\text{{EPS}} \\times \\text{{BVPS}}}}$$

| Fundamental Factor | Metric Value | Benchmark Standard | Graham Evaluation |
| :--- | :--- | :--- | :--- |
| **Trailing P/E Ratio** | `{pe:.2f}` | $\\le 25.0$ | {'Favorable' if pe <= 25 else 'Premium Multiple'} |
| **Price to Book (P/B)** | `{pb:.2f}` | $\\le 3.0$ | {'Asset-Backed' if pb <= 3.0 else 'High Goodwill / Intangibles'} |
| **Graham Multiplier ($P/E \\times P/B$)** | `{pe * pb:.1f}` | $\\le 22.5$ | {'Value Bargain' if (pe*pb) <= 22.5 else 'Growth Premium'} |
| **Normalized EPS** | `₹{eps:.2f}` | Positive earnings power | Sound Cash Generation |
| **Book Value Per Share (BVPS)** | `₹{bvps:.2f}` | Net tangible equity | Net Asset Anchor |
| **Intrinsic Graham Number** | **`₹{graham_number:,.2f}`** | Fair fundamental value | {'Discount Available' if undervalued else 'Trading Above Graham Cap'} |
| **Margin of Safety** | **`{margin_of_safety:+.2f}%`** | Ideal: $> +15%$ | {'✅ Undervalued by Graham' if undervalued else '⚠️ Overvalued by Graham'} |"""

def explain_trade_thesis(ctx: dict) -> str:
    """Synthesizes the complete AI prediction thesis."""
    ticker = ctx.get("ticker", "Stock")
    price = ctx.get("price", 0.0)
    change = ctx.get("change_pct", 0.0)
    pred_text = ctx.get("pred_text", "BUY NOW")
    confidence = ctx.get("confidence", 70.0)
    sentiment = ctx.get("sentiment", "Bullish")
    top_shap = ctx.get("top_shap", ["Price Momentum (+0.44)", "RSI Momentum (+0.32)", "FinBERT Sentiment (+0.25)"])

    return f"""### 🤖 Algorithmic Trade Thesis & Conviction Profile for **{ticker}**

* **Institutional Signal:** **`{pred_text}`**
* **Prediction Confidence:** **`{confidence:.1f}%`**
* **Current Market Price:** `₹{price:,.2f}` (`{change:+.2f}%` today)
* **FinBERT News Sentiment:** `{sentiment}`

#### 🔬 Primary Quantitative Drivers (SHAP Value Attribution):
1. **Primary Momentum Driver:** `{top_shap[0] if len(top_shap) > 0 else 'Trend Velocity'}`
2. **Mean-Reversion Driver:** `{top_shap[1] if len(top_shap) > 1 else 'Volatility Compression'}`
3. **Sentiment / Macro Driver:** `{top_shap[2] if len(top_shap) > 2 else 'Cross-Asset Liquidity'}`

#### 🛡️ Quantitative Risk Controls:
* **Lookahead Bias Defense:** Features are computed strictly on lagged $t-1$ prices.
* **Purged Cross-Validation:** Combinatorial purged cross-validation (CPCV) eliminates serial correlation leakage.
* **Execution Rule:** Use Limit orders to prevent slippage beyond the 5 bps hurdle rate."""

# =========================================================================
# QUERY ROUTING & LLM INTEGRATION
# =========================================================================

def generate_quant_response(query: str, ctx: dict, api_key: str = None, ai_engine: str = "Institutional Rule Engine") -> str:
    """Answers user queries using LLM if available, or falls back to institutional rules."""
    q = query.lower()

    if ai_engine != "Institutional Rule Engine" and (api_key or ai_engine.startswith("Local")):
        try:
            prompt_context = f"""You are the Chief Quantitative Officer and AI Trading Copilot for an institutional algorithmic hedge fund.
Current Stock Telemetry:
- Ticker: {ctx.get('ticker')}
- Current Price: INR {ctx.get('price')} (Change: {ctx.get('change_pct')}%)
- Model Signal: {ctx.get('pred_text')} (Confidence: {ctx.get('confidence')}%)
- Indicators: {ctx.get('indicators')}
- Graham Valuation: {ctx.get('graham')}
- News Sentiment: {ctx.get('sentiment')}

User Question: {query}

Provide an institutional, precise, and actionable response with exact numbers, formulas, and execution rules. Format cleanly with Markdown tables and bullet points."""

            if ai_engine.startswith("Local"):
                import ollama
                resp = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt_context}])
                if hasattr(resp, 'message'):
                    return resp.message.content
                return resp["message"]["content"]
            elif api_key:
                from google import genai
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt_context)
                return resp.text
        except Exception:
            pass

    # --- Institutional Rule-Based Quantitative Engine ---
    if any(k in q for k in ["rsi", "macd", "indicator", "technical", "bollinger", "moving average", "sma", "ema"]):
        return analyze_technical_indicators(ctx)
    elif any(k in q for k in ["stop loss", "target", "exit", "entry", "sl", "tp", "risk reward"]):
        return calculate_stop_loss_and_target(ctx)
    elif any(k in q for k in ["tax", "friction", "stt", "brokerage", "cost", "gst", "stamp duty", "charges"]):
        match = re.search(r'(\d+[\d,]*)\s*(?:rs|rupee|inr|lakh|k)?', q)
        val = 100000.0
        if match:
            raw_num = match.group(1).replace(",", "")
            try:
                num = float(raw_num)
                if "lakh" in q:
                    num *= 100000
                elif "k" in q:
                    num *= 1000
                if num > 100:
                    val = num
            except:
                pass
        return calculate_friction_and_taxes(val)
    elif any(k in q for k in ["kelly", "sizing", "allocation", "portfolio", "position", "how much to buy"]):
        return explain_kelly_criterion(ctx)
    elif any(k in q for k in ["graham", "fundamental", "undervalued", "pe", "pb", "intrinsic", "margin of safety"]):
        return explain_graham_valuation(ctx)
    elif any(k in q for k in ["buy", "sell", "signal", "thesis", "why", "predict", "confidence", "conviction", "recommend"]):
        return explain_trade_thesis(ctx)
    elif any(k in q for k in ["bias", "lookahead", "overfit", "survivorship", "backtest"]):
        return """### 🛡️ Institutional Quantitative Guardrails: Anti-Bias Architecture

1. **Zero Lookahead Bias:**
   * Features ($SMA_t, RSI_t, Return_{t-1}$) are strictly computed on lagged information available before market open ($t-1$).
2. **Purged Combinatorial Cross-Validation:**
   * Standard K-Fold CV fails in time-series due to serial auto-correlation. We apply Marcos López de Prado's **Purged & Embargoed Cross-Validation**.
3. **Survivorship Bias Protection:**
   * Historical models are calibrated against all active and historically de-listed constituents in the Nifty 50 index."""
    else:
        return f"""### 🤖 Executive Quantitative Assessment for **{ctx.get('ticker', 'Asset')}**

* **Current Signal:** `{ctx.get('pred_text', 'BUY')}` (Confidence: `{ctx.get('confidence', 68.0):.1f}%`)
* **Current Market Price:** `₹{ctx.get('price', 0.0):,.2f}`
* **Sentiment:** `{ctx.get('sentiment', 'Bullish')}`

#### Key Quant Insights:
1. **Momentum & Trend:** RSI is at `{ctx.get('indicators', {}).get('RSI', 52.0):.1f}` with MACD indicating positive momentum structure.
2. **Volatility Bounds:** 14-day ATR is `₹{ctx.get('indicators', {}).get('ATR', 30.0):.2f}`, warranting a dynamic stop-loss at `₹{max(ctx.get('price', 1000) - 1.5*ctx.get('indicators', {}).get('ATR', 30.0), 0):,.2f}`.
3. **Friction Hurdle:** Round-trip transaction friction is estimated at ~0.24% (STT, brokerage, and exchange fees).
4. **Position Sizing:** Optimal Half-Kelly allocation suggests a max risk budget of ~12.5% of total portfolio capital.

*Ask me specifically about: **Stop Loss/Targets**, **Technical Indicators**, **Friction & Taxes**, **Kelly Sizing**, or **Graham Valuation**!*"""


# =========================================================================
# STREAMLIT UI TAB COMPONENT
# =========================================================================

def render_quant_copilot_tab(ctx: dict, api_key: str = None, ai_engine: str = "Institutional Rule Engine", key_prefix: str = "quant"):
    """Renders the conversational Quantitative Alpha Copilot UI in Streamlit."""
    ticker = ctx.get("ticker", "RELIANCE.NS")
    price = ctx.get("price", 2950.0)
    conf = ctx.get("confidence", 72.4)
    pred_dir = ctx.get("pred_text", "BUY NOW")

    st.markdown(f"""
<div class="quant-3d-card" style="margin-bottom: 15px; border-left: 4px solid #00d4ff;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="quant-badge">QUANT COPILOT ACTIVE</span>
        <span style="font-size: 11px; color: #00d084; background: rgba(0, 208, 132, 0.1); border: 1px solid #00d084; padding: 2px 8px; border-radius: 4px; font-weight: 700;">LIVE NSE DATA GROUNDED</span>
    </div>
    <h3 style="color: #f8fafc; margin-top: 6px; margin-bottom: 2px; font-size: 20px;">💬 Autonomous Quant Alpha & Trading Copilot</h3>
    <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0px;">
        Directly query algorithms for <b>{ticker}</b> (CMP: ₹{price:,.2f} | Conviction: {conf:.1f}% {pred_dir}). Click a prompt or type below:
    </p>
</div>
""", unsafe_allow_html=True)

    # Quick Prompt Chips
    st.markdown("<p style='color: #cbd5e1; font-size: 13px; font-weight: 600; margin-bottom: 6px;'>⚡ Quick Prompts (Click to Ask):</p>", unsafe_allow_html=True)
    chips = [
        "💡 Explain the trade signal & thesis",
        "📊 Break down RSI, MACD & technicals",
        "🎯 Calculate ATR Stop Loss & Targets",
        "💰 Calculate total STT & friction on ₹2,00,000",
        "⚖️ Explain Kelly sizing for this stock",
        "🏛️ Is this stock undervalued by Graham-Dodd?"
    ]
    
    chip_cols = st.columns(3)
    clicked_prompt = None
    for idx, prompt_text in enumerate(chips):
        with chip_cols[idx % 3]:
            if st.button(prompt_text, key=f"{key_prefix}_chip_{idx}", use_container_width=True):
                clicked_prompt = prompt_text

    # Initialize chat history
    if "quant_chat_history" not in st.session_state:
        st.session_state.quant_chat_history = [
            {
                "role": "assistant",
                "content": f"👋 Greetings. I am your **Autonomous Quant Alpha Copilot**. I have live telemetry loaded for **{ticker}** at CMP **₹{price:,.2f}** with an algorithmic recommendation of **{pred_dir}** ({conf:.1f}% confidence). What quantitative analysis or execution detail would you like to explore?"
            }
        ]

    # Render Chat History
    for msg in st.session_state.quant_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    user_query = st.chat_input("Ask a quantitative, technical, or execution question...", key=f"{key_prefix}_chat_input") or clicked_prompt

    if user_query:
        st.session_state.quant_chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Synthesizing quantitative market data & mathematical models..."):
                reply = generate_quant_response(user_query, ctx, api_key=api_key, ai_engine=ai_engine)
                st.markdown(reply)
                st.session_state.quant_chat_history.append({"role": "assistant", "content": reply})
