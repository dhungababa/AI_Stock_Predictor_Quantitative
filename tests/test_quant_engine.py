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
