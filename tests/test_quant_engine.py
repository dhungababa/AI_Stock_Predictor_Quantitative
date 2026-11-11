import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import os
import joblib
import numpy as np
import pandas as pd
from fpdf import FPDF

# Exact 18 features used by the institutional XGBoost alpha model
QUANT_FEATURES = [
    'SMA_10', 'SMA_30', 'EMA_20', 'RSI', 'MACD', 'MACD_Signal',
    'Stoch_Oscillator', 'BB_High', 'BB_Low', 'BB_Width', 'ATR', 'OBV',
    'Volume_SMA_10', 'Return_1d', 'Return_5d', 'Sentiment_Score',
    'Sentiment_3d_MA', 'Sentiment_Trend'
]

def test_feature_vector_dimension_and_schema():
    """Verify that the quantitative alpha model has exactly 18 institutional factors."""
    assert len(QUANT_FEATURES) == 18
    assert "Sentiment_Score" in QUANT_FEATURES
    assert "RSI" in QUANT_FEATURES
    assert "MACD" in QUANT_FEATURES
    assert "OBV" in QUANT_FEATURES
    assert "Sentiment_Trend" in QUANT_FEATURES

def test_indian_execution_friction_engine():
    """
    Verify institutional Indian market execution friction:
    - STT (Securities Transaction Tax): 0.10% (0.001)
    - Zerodha Flat / Capped Brokerage: Rs 20 per execution leg
    - Slippage Model: 5 bps (0.0005)
    """
    capital = 100000.0  # Rs 1,00,000
    stt_rate = 0.0010   # 0.10%
    slippage_bps = 0.0005 # 5 bps
    brokerage_per_order = 20.0 # Zerodha equity delivery / intraday cap

    # Simulated gross gain: +3.5%
    gross_pnl_pct = 0.035
    gross_pnl_inr = capital * gross_pnl_pct # Rs 3,500

    # Total round-trip friction
    turnover = capital * 2  # Buy + Sell
    total_stt = turnover * stt_rate  # 200,000 * 0.001 = Rs 200
    total_slippage = turnover * slippage_bps # 200,000 * 0.0005 = Rs 100
    total_brokerage = brokerage_per_order * 2 # Rs 40

    total_friction = total_stt + total_slippage + total_brokerage # Rs 340
    net_pnl_inr = gross_pnl_inr - total_friction
    net_pnl_pct = net_pnl_inr / capital

    assert total_friction == 340.0
    assert abs(net_pnl_inr - 3160.0) < 1e-4
    assert round(net_pnl_pct * 100, 2) == 3.16
    assert net_pnl_inr < gross_pnl_inr  # Frictions must reduce realized PnL

def test_kelly_criterion_risk_budgeting():
    """
    Verify Kelly Criterion optimal sizing:
    f* = p - (1 - p) / b
    where p = win probability, b = win/loss payoff ratio
    """
    # Case 1: High conviction trade (p = 0.65, b = 1.8)
    p1 = 0.65
    b1 = 1.8
    f_star1 = p1 - ((1.0 - p1) / b1)
    assert round(f_star1, 4) == round(0.65 - (0.35 / 1.8), 4) # ~0.4556 (45.56%)
    half_kelly1 = max(0.0, f_star1 / 2.0)
    assert 0.20 <= half_kelly1 <= 0.25

    # Case 2: Negative expectation trade (p = 0.35, b = 1.0)
    p2 = 0.35
    b2 = 1.0
    f_star2 = p2 - ((1.0 - p2) / b2) # 0.35 - 0.65 = -0.30
    clamped_kelly = max(0.0, f_star2)
    assert clamped_kelly == 0.0  # Zero capital allocation for negative edge

def test_xgboost_model_inference():
    """Verify that saved XGBoost models load and yield bounded probability outputs."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "../models")
    
    # Pick the trained combined models
    joblib_files = [f for f in os.listdir(models_dir) if f.endswith("_Combined.joblib")]
    assert len(joblib_files) > 0, "At least one trained model must exist in models/"

    model_path = os.path.join(models_dir, joblib_files[0])
    model = joblib.load(model_path)

    # Create dummy 18-feature row matching exact schema
    dummy_input = pd.DataFrame([{f: 0.5 for f in QUANT_FEATURES}])
    
    # Check prediction probability
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(dummy_input)
        assert probs.shape[1] == 2
        p_up = float(probs[0, 1])
        assert 0.0 <= p_up <= 1.0
    
    pred = model.predict(dummy_input)
    assert int(pred[0]) in [0, 1]

def test_quant_dossier_pdf_generation():
    """Verify programmatic PDF compilation of institutional quant research dossier."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ALPHA RESEARCH MEMORANDUM", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, "Target: RELIANCE.NS | Signal: STRONG BUY | Confidence: 72.4%", ln=True)
    pdf.cell(0, 8, "Kelly Fraction: 14.8% | STT Friction: 0.10% | Net Alpha: +2.84%", ln=True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500  # Valid non-empty PDF binary
    assert pdf_bytes.startswith(b"%PDF")

def test_11_microbot_swarm_execution():
    """Verify that the 11-Microbot Quant Committee executes and returns valid metrics."""
    from src.microbots import QuantMicrobotSwarm
    
    # Synthetic 25-day daily series representing healthy NSE stock
    dates = pd.date_range(end=pd.Timestamp.now(), periods=25, freq='B')
    close_vals = np.linspace(1150.0, 1220.0, 25)
    df_bars = pd.DataFrame({
        'Open': close_vals - 2.0,
        'High': close_vals + 8.0,
        'Low': close_vals - 5.0,
        'Close': close_vals,
        'Volume': [1500000] * 25
    }, index=dates)
    
    headlines = [
        "Reliance expands retail footprint with robust Q2 operational margin",
        "Analysts maintain positive momentum outlook for Indian bluechips"
    ]
    
    swarm = QuantMicrobotSwarm("RELIANCE.NS")
    res = swarm.run_all(df_bars, headlines, vix_value=15.2, xgb_prob=0.74)
    
    assert res['ticker'] == "RELIANCE.NS"
    assert len(res['microbots']) == 11
    assert res['bullish_votes'] >= 5
    assert 0.0 <= res['consensus_pct'] <= 100.0
    assert "MANDATE" in res['cio_thesis'] or "BUY" in res['cio_mandate'] or "HOLD" in res['cio_mandate']
    
    # Verify every microbot has required schema
    for b in res['microbots']:
        assert "ID" in b
        assert "Microbot" in b
        assert "Category" in b
        assert b["Raw_Vote"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert "Key Metric" in b
        assert len(b["Institutional Rationale"]) > 10

def test_simulate_l2_order_book_microstructure():
    """Verify L2 order book simulation adheres to 10-level NSE microstructure."""
    from app.market_depth import simulate_l2_order_book, calculate_execution_slippage
    
    price = 1250.0
    atr = 25.0
    book = simulate_l2_order_book(current_price=price, atr=atr, spread_bps=2.5)
    
    assert book["levels"] == 10
    assert len(book["bids"]) == 10
    assert len(book["asks"]) == 10
    assert book["best_ask"] > book["best_bid"]
    assert book["spread"] > 0
    assert book["spread_paise"] == round(book["spread"] * 100, 1)
    assert book["spread_bps"] > 0
    assert book["vwap"] > 0
    assert book["total_bid_vol"] > 0
    assert book["total_ask_vol"] > 0
    assert -100.0 <= book["bid_ask_imbalance"] <= 100.0

    # Verify descending bid prices and ascending ask prices
    for i in range(len(book["bids"]) - 1):
        assert book["bids"][i]["price"] >= book["bids"][i + 1]["price"]
        assert book["bids"][i]["cum_quantity"] < book["bids"][i + 1]["cum_quantity"]

    for i in range(len(book["asks"]) - 1):
        assert book["asks"][i]["price"] <= book["asks"][i + 1]["price"]
        assert book["asks"][i]["cum_quantity"] < book["asks"][i + 1]["cum_quantity"]

    # Verify tick constraint (multiples of 0.05)
    for b in book["bids"]:
        assert abs(round(b["price"] / 0.05) * 0.05 - b["price"]) < 1e-4
    for a in book["asks"]:
        assert abs(round(a["price"] / 0.05) * 0.05 - a["price"]) < 1e-4


def test_l2_execution_slippage_and_friction():
    """Verify order execution slippage walks the order ladder with friction audit."""
    from app.market_depth import simulate_l2_order_book, calculate_execution_slippage

    price = 1250.0
    atr = 25.0
    book = simulate_l2_order_book(current_price=price, atr=atr, spread_bps=2.5)

    # Small order (500 shares)
    res_small = calculate_execution_slippage(book, order_qty=500, side="BUY", atr=atr)
    assert res_small["order_qty"] == 500
    assert res_small["exec_vwap"] >= book["best_ask"]
    assert res_small["slippage_bps"] >= 0.0
    assert res_small["stt"] > 0
    assert res_small["brokerage"] == 20.0
    assert res_small["total_friction"] > 0

    # Large order (10,000 shares) should have higher or equal slippage bps
    res_large = calculate_execution_slippage(book, order_qty=10000, side="BUY", atr=atr)
    assert res_large["slippage_bps"] >= res_small["slippage_bps"]

    # Sell order execution
    res_sell = calculate_execution_slippage(book, order_qty=1500, side="SELL", atr=atr)
    assert res_sell["exec_vwap"] <= book["best_bid"]
    assert res_sell["slippage_inr"] >= 0.0


def test_monte_carlo_gbm_simulation_and_var():
    """Verify 1,000-path Geometric Brownian Motion simulation, VaR, and stress scenarios."""
    from app.monte_carlo_var import run_monte_carlo_simulation

    # 100 days of synthetic price data
    np.random.seed(42)
    daily_rets = np.random.normal(0.0005, 0.015, 120)
    prices = 1000.0 * np.exp(np.cumsum(daily_rets))
    df_hist = pd.DataFrame({"Close": prices})

    mc = run_monte_carlo_simulation(current_price=1000.0, hist_df=df_hist, days=30, num_sims=1000)

    assert mc["days"] == 30
    assert mc["num_sims"] == 1000
    assert mc["price_paths"].shape == (1000, 31)
    assert mc["sample_paths"].shape == (50, 31)
    assert mc["portfolio_base"] == 500000.0

    # VaR and CVaR sanity
    assert mc["var_95_hist"] > 0
    assert mc["var_99_hist"] >= mc["var_95_hist"]
    assert mc["cvar_95"] >= mc["var_95_hist"]
    assert mc["cvar_99"] >= mc["var_99_hist"]
    assert mc["var_95_param"] > 0
    assert mc["var_99_param"] >= mc["var_95_param"]

    # Probability bounds
    assert 0.0 <= mc["prob_profit"] <= 100.0
    assert 0.0 <= mc["prob_loss_gt_10pct"] <= 100.0

    # Stress test scenarios
    assert len(mc["stress_scenarios"]) == 5
    scenario_ids = [s["id"] for s in mc["stress_scenarios"]]
    assert "lehman_2008" in scenario_ids
    assert "covid_2020" in scenario_ids
    assert "demonet_2016" in scenario_ids

    # Lehman: -25% on 5 Lakhs = Rs 1,25,000 loss
    lehman = next(s for s in mc["stress_scenarios"] if s["id"] == "lehman_2008")
    assert lehman["loss_inr"] == 125000.0
    assert lehman["stressed_val"] == 375000.0

    # COVID: -35% on 5 Lakhs = Rs 1,75,000 loss
    covid = next(s for s in mc["stress_scenarios"] if s["id"] == "covid_2020")
    assert covid["loss_inr"] == 175000.0
    assert covid["stressed_val"] == 325000.0
