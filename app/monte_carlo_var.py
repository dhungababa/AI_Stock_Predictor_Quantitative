"""
monte_carlo_var.py — 1,000-Path Monte Carlo Geometric Brownian Motion (GBM) & VaR Engine
Institutional quantitative risk module simulating stochastic asset trajectories,
calculating Parametric and Historical Value at Risk (VaR), Conditional VaR (CVaR/Expected Shortfall),
and stress-test macro crisis scenario projections.
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def run_monte_carlo_simulation(
    current_price: float,
    hist_df,
    days: int = 30,
    num_sims: int = 1000
) -> dict:
    """
    Simulates stochastic price trajectories via Geometric Brownian Motion (GBM):
    S_t = S_{t-1} * exp((mu - 0.5 * sigma^2)*dt + sigma*sqrt(dt)*Z)

    Calculates:
    - 95% and 99% Parametric and Historical Value at Risk (VaR) in rupees on a standard ₹5,00,000 portfolio.
    - Conditional VaR (CVaR / Expected Shortfall).
    - Stress-test scenario projections (Lehman -25%, COVID -35%, Demonetization -12%, etc.).

    Parameters
    ----------
    current_price : float
        Current spot price of the stock in INR.
    hist_df : pd.DataFrame, pd.Series, or array-like
        Historical data containing closing prices or returns.
    days : int, default=30
        Forecast horizon in trading days.
    num_sims : int, default=1000
        Number of Monte Carlo stochastic paths to simulate.

    Returns
    -------
    dict
        Comprehensive quantitative risk dictionary with trajectory matrices,
        confidence bands, VaR/CVaR in INR, and stress test evaluations.
    """
    price = max(1.0, float(current_price))
    horizon_days = max(5, int(days))
    n_sims = max(100, int(num_sims))
    portfolio_base = 500000.0  # Standard INR 5,00,000 institutional allocation

    # Extract historical price series
    close_series = None
    if isinstance(hist_df, pd.DataFrame):
        if "Close" in hist_df.columns:
            close_series = hist_df["Close"].dropna()
        elif "close" in hist_df.columns:
            close_series = hist_df["close"].dropna()
    elif isinstance(hist_df, pd.Series):
        close_series = hist_df.dropna()

    # Compute historical log returns and volatility
    if close_series is not None and len(close_series) >= 15:
        prices_arr = close_series.values.astype(float)
        # Filter valid positive prices
        prices_arr = prices_arr[prices_arr > 0]
        if len(prices_arr) >= 15:
            log_returns = np.diff(np.log(prices_arr))
            daily_mu = float(np.mean(log_returns))
            daily_sigma = float(np.std(log_returns, ddof=1))
        else:
            daily_mu = 0.12 / 252.0
            daily_sigma = 0.24 / np.sqrt(252.0)
    else:
        # Fallback to realistic Indian equity baseline: 12% drift, 24% annual vol
        daily_mu = 0.12 / 252.0
        daily_sigma = 0.24 / np.sqrt(252.0)

    # Guard zero or negative volatility
    if daily_sigma < 1e-5 or math.isnan(daily_sigma):
        daily_sigma = 0.22 / np.sqrt(252.0)
    if math.isnan(daily_mu):
        daily_mu = 0.12 / 252.0

    ann_mu = daily_mu * 252.0
    ann_sigma = daily_sigma * np.sqrt(252.0)

    # ----------------------------------------------------
    # GEOMETRIC BROWNIAN MOTION (GBM) VECTORIZED SIMULATION
    # ----------------------------------------------------
    # Fixed seed for repeatable analysis while allowing dynamic variation
    rng = np.random.RandomState(42)
    dt = 1.0  # Daily time-step
    drift_term = (daily_mu - 0.5 * (daily_sigma ** 2)) * dt
    diffusion_scale = daily_sigma * np.sqrt(dt)

    # Matrix shape: (num_sims, days) standard normal shocks
    Z = rng.standard_normal((n_sims, horizon_days))
    daily_returns_matrix = np.exp(drift_term + (diffusion_scale * Z))

    # Construct price paths of shape (num_sims, days + 1)
    price_paths = np.empty((n_sims, horizon_days + 1))
    price_paths[:, 0] = price
    price_paths[:, 1:] = price * np.cumprod(daily_returns_matrix, axis=1)

    # Terminal metrics
    terminal_prices = price_paths[:, -1]
    terminal_returns = (terminal_prices - price) / price
    terminal_pnl = portfolio_base * terminal_returns
    terminal_portfolio_values = portfolio_base + terminal_pnl

    # ----------------------------------------------------
    # VALUE AT RISK (VaR) & CONDITIONAL VaR (CVaR / ES)
    # ----------------------------------------------------
    # Historical / Empirical VaR from Monte Carlo simulations
    # 95% VaR is the 5th percentile of PnL; 99% VaR is the 1st percentile
    pnl_5th = float(np.percentile(terminal_pnl, 5.0))
    pnl_1st = float(np.percentile(terminal_pnl, 1.0))

    var_95_hist = max(0.0, -pnl_5th)
    var_99_hist = max(0.0, -pnl_1st)
    var_95_hist_pct = (var_95_hist / portfolio_base) * 100.0
    var_99_hist_pct = (var_99_hist / portfolio_base) * 100.0

    # Parametric VaR (Analytical normal distribution formula over horizon T)
    T_years = horizon_days / 252.0
    z_95 = 1.6448536
    z_99 = 2.3263479

    loss_ret_95_param = (z_95 * ann_sigma * np.sqrt(T_years)) - (ann_mu * T_years)
    loss_ret_99_param = (z_99 * ann_sigma * np.sqrt(T_years)) - (ann_mu * T_years)

    var_95_param = max(0.0, portfolio_base * loss_ret_95_param)
    var_99_param = max(0.0, portfolio_base * loss_ret_99_param)
    var_95_param_pct = (var_95_param / portfolio_base) * 100.0
    var_99_param_pct = (var_99_param / portfolio_base) * 100.0

    # Conditional VaR (Expected Shortfall / Tail Loss beyond VaR)
    tail_95 = terminal_pnl[terminal_pnl <= pnl_5th]
    cvar_95 = max(var_95_hist, float(-np.mean(tail_95))) if len(tail_95) > 0 else var_95_hist
    cvar_95_pct = (cvar_95 / portfolio_base) * 100.0

    tail_99 = terminal_pnl[terminal_pnl <= pnl_1st]
    cvar_99 = max(var_99_hist, float(-np.mean(tail_99))) if len(tail_99) > 0 else var_99_hist
    cvar_99_pct = (cvar_99 / portfolio_base) * 100.0

    # ----------------------------------------------------
    # STRESS-TEST HISTORICAL BLACK-SWAN SCENARIOS
    # ----------------------------------------------------
    stress_scenarios = [
        {
            "id": "lehman_2008",
            "name": "2008 Lehman Brothers Liquidity Crisis",
            "shock_pct": -25.0,
            "description": "Global interbank liquidity freeze & severe equity de-leveraging.",
            "loss_inr": round(portfolio_base * 0.25, 2),
            "stressed_val": round(portfolio_base * 0.75, 2),
            "stressed_price": round(price * 0.75, 2),
            "severity": "CRITICAL",
            "color": "#ef4444",
        },
        {
            "id": "covid_2020",
            "name": "2020 COVID-19 Flash Crash",
            "shock_pct": -35.0,
            "description": "Unprecedented nationwide pandemic lockdown & circuit-breaker halts.",
            "loss_inr": round(portfolio_base * 0.35, 2),
            "stressed_val": round(portfolio_base * 0.65, 2),
            "stressed_price": round(price * 0.65, 2),
            "severity": "CATASTROPHIC",
            "color": "#dc2626",
        },
        {
            "id": "demonet_2016",
            "name": "2016 Demonetization Liquidity Squeeze",
            "shock_pct": -12.0,
            "description": "Sudden cash withdrawal & short-term domestic consumer demand shock.",
            "loss_inr": round(portfolio_base * 0.12, 2),
            "stressed_val": round(portfolio_base * 0.88, 2),
            "stressed_price": round(price * 0.88, 2),
            "severity": "MODERATE",
            "color": "#f59e0b",
        },
        {
            "id": "yen_unwind_2024",
            "name": "2024 Black Monday Yen Carry Trade Shock",
            "shock_pct": -8.0,
            "description": "Bank of Japan rate hike triggering global margin call liquidation.",
            "loss_inr": round(portfolio_base * 0.08, 2),
            "stressed_val": round(portfolio_base * 0.92, 2),
            "stressed_price": round(price * 0.92, 2),
            "severity": "CONTROLLED",
            "color": "#38bdf8",
        },
        {
            "id": "budget_rally",
            "name": "Bullish Macro Expansion / RBI Rate Cut Rally",
            "shock_pct": +15.0,
            "description": "Aggressive monetary easing, Capex budget push & FII capital inflow.",
            "loss_inr": -round(portfolio_base * 0.15, 2),
            "stressed_val": round(portfolio_base * 1.15, 2),
            "stressed_price": round(price * 1.15, 2),
            "severity": "EXPANSIONARY",
            "color": "#00d084",
        },
    ]

    # Trajectory confidence quantiles across simulation days
    bands = {
        "p1": np.percentile(price_paths, 1.0, axis=0),
        "p5": np.percentile(price_paths, 5.0, axis=0),
        "p25": np.percentile(price_paths, 25.0, axis=0),
        "median": np.percentile(price_paths, 50.0, axis=0),
        "mean": np.mean(price_paths, axis=0),
        "p75": np.percentile(price_paths, 75.0, axis=0),
        "p95": np.percentile(price_paths, 95.0, axis=0),
        "p99": np.percentile(price_paths, 99.0, axis=0),
    }

    # Sample 50 paths for the Plotly fan visualization
    sample_indices = rng.choice(n_sims, size=min(50, n_sims), replace=False)
    sample_paths = price_paths[sample_indices]

    prob_profit = float(np.mean(terminal_returns > 0) * 100.0)
    prob_loss_gt_10pct = float(np.mean(terminal_returns < -0.10) * 100.0)

    return {
        "price_paths": price_paths,
        "sample_paths": sample_paths,
        "days": horizon_days,
        "num_sims": n_sims,
        "current_price": price,
        "portfolio_base": portfolio_base,
        "mu_daily": daily_mu,
        "sigma_daily": daily_sigma,
        "mu_annualized": ann_mu,
        "sigma_annualized": ann_sigma,
        "var_95_hist": round(var_95_hist, 2),
        "var_99_hist": round(var_99_hist, 2),
        "var_95_param": round(var_95_param, 2),
        "var_99_param": round(var_99_param, 2),
        "var_95_hist_pct": round(var_95_hist_pct, 2),
        "var_99_hist_pct": round(var_99_hist_pct, 2),
        "var_95_param_pct": round(var_95_param_pct, 2),
        "var_99_param_pct": round(var_99_param_pct, 2),
        "cvar_95": round(cvar_95, 2),
        "cvar_99": round(cvar_99, 2),
        "cvar_95_pct": round(cvar_95_pct, 2),
        "cvar_99_pct": round(cvar_99_pct, 2),
        "terminal_prices": terminal_prices,
        "terminal_portfolio_values": terminal_portfolio_values,
        "terminal_pnl": terminal_pnl,
        "bands": bands,
        "stress_scenarios": stress_scenarios,
        "prob_profit": round(prob_profit, 1),
        "prob_loss_gt_10pct": round(prob_loss_gt_10pct, 1),
        "expected_terminal_price": round(float(np.mean(terminal_prices)), 2),
        "median_terminal_price": round(float(np.median(terminal_prices)), 2),
    }


def render_monte_carlo_component(current_price: float, hist_df, ticker: str):
    """
    Renders an institutional quantitative Monte Carlo & Value at Risk (VaR)
    dashboard in Streamlit with:
    - Interactive simulation horizon slider (10 to 90 trading days)
    - Risk metric cards on standard INR 5,00,000 capital base
    - Plotly fan-chart with 95% and 99% confidence bands + 50 sample trajectory paths
    - Distribution histogram of terminal wealth with VaR thresholds
    - Stress-testing scenario projection matrix

    Parameters
    ----------
    current_price : float
        Current stock price in INR.
    hist_df : pd.DataFrame or pd.Series
        Historical price data.
    ticker : str
        Stock ticker symbol.
    """
    ctrl_col1, ctrl_col2 = st.columns([2, 1])
    with ctrl_col1:
        sim_days = st.select_slider(
            "Forecast Horizon (Trading Days):",
            options=[10, 21, 30, 45, 60, 90],
            value=30,
            key=f"mc_days_slider_{ticker}",
        )
    with ctrl_col2:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color: #00f0ff; font-size: 13px; font-weight: 700; text-align: right;'>"
            f"⚡ 1,000 GBM Stochastic Paths"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Run simulation
    mc = run_monte_carlo_simulation(
        current_price=current_price,
        hist_df=hist_df,
        days=sim_days,
        num_sims=1000,
    )

    # ----------------------------------------------------
    # TOP RISK METRIC CARDS (INR 5,00,000 ALLOCATION)
    # ----------------------------------------------------
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)

    with c_m1:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">PORTFOLIO BASE</div>
            <div style="font-size: 22px; font-weight: 800; color: #00f0ff; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                ₹5,00,000
            </div>
            <div style="font-size: 12px; color: #38bdf8; margin-top: 2px;">Standard Institutional Base</div>
        </div>
        """, unsafe_allow_html=True)

    with c_m2:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">95% VALUE AT RISK (VaR)</div>
            <div style="font-size: 22px; font-weight: 800; color: #f59e0b; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                -₹{mc['var_95_hist']:,.0f}
            </div>
            <div style="font-size: 12px; color: #fbbf24; margin-top: 2px;">{mc['var_95_hist_pct']:.1f}% Max Expected Loss (Param: ₹{mc['var_95_param']:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)

    with c_m3:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">99% VALUE AT RISK (VaR)</div>
            <div style="font-size: 22px; font-weight: 800; color: #ef4444; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                -₹{mc['var_99_hist']:,.0f}
            </div>
            <div style="font-size: 12px; color: #f87171; margin-top: 2px;">{mc['var_99_hist_pct']:.1f}% Tail Risk (Param: ₹{mc['var_99_param']:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)

    with c_m4:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(220, 38, 38, 0.45); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">CONDITIONAL VaR (CVaR)</div>
            <div style="font-size: 22px; font-weight: 800; color: #dc2626; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                -₹{mc['cvar_95']:,.0f}
            </div>
            <div style="font-size: 12px; color: #ef4444; margin-top: 2px;">95% Expected Shortfall ({mc['cvar_95_pct']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # INTERACTIVE PLOTLY FAN-CHART & TRAJECTORIES
    # ----------------------------------------------------
    st.markdown("##### 📈 Stochastic Trajectory Fan-Chart (Confidence Ribbons & 50 Sample Paths)")

    time_steps = list(range(mc["days"] + 1))
    fig_mc = go.Figure()

    # 1. 50 individual sample paths (subtle opacity)
    for i, path in enumerate(mc["sample_paths"]):
        show_leg = True if i == 0 else False
        fig_mc.add_trace(go.Scatter(
            x=time_steps,
            y=path,
            mode="lines",
            line=dict(color="rgba(0, 240, 255, 0.12)", width=1),
            name="Simulated Path (Sample of 50)" if show_leg else None,
            showlegend=show_leg,
            hoverinfo="skip",
        ))

    # 2. 99% Confidence Band (Shaded area between p1 and p99)
    fig_mc.add_trace(go.Scatter(
        x=time_steps,
        y=mc["bands"]["p99"],
        mode="lines",
        line=dict(color="rgba(168, 85, 247, 0.4)", width=1),
        name="99% Upper Bound",
        showlegend=False,
        hoverinfo="skip",
    ))
    fig_mc.add_trace(go.Scatter(
        x=time_steps,
        y=mc["bands"]["p1"],
        mode="lines",
        line=dict(color="rgba(168, 85, 247, 0.4)", width=1),
        fill="tonexty",
        fillcolor="rgba(168, 85, 247, 0.12)",
        name="99% Confidence Interval (p1 - p99)",
        hovertemplate="99% Interval: ₹%{y:.2f}<extra></extra>",
    ))

    # 3. 95% Confidence Band (Shaded area between p5 and p95)
    fig_mc.add_trace(go.Scatter(
        x=time_steps,
        y=mc["bands"]["p95"],
        mode="lines",
        line=dict(color="rgba(0, 212, 255, 0.6)", width=1.2),
        name="95% Upper Bound",
        showlegend=False,
        hoverinfo="skip",
    ))
    fig_mc.add_trace(go.Scatter(
        x=time_steps,
        y=mc["bands"]["p5"],
        mode="lines",
        line=dict(color="rgba(0, 212, 255, 0.6)", width=1.2),
        fill="tonexty",
        fillcolor="rgba(0, 212, 255, 0.22)",
        name="95% Confidence Interval (p5 - p95)",
        hovertemplate="95% Interval: ₹%{y:.2f}<extra></extra>",
    ))

    # 4. Median Expected Trajectory (Bold Neon Cyan)
    fig_mc.add_trace(go.Scatter(
        x=time_steps,
        y=mc["bands"]["median"],
        mode="lines",
        line=dict(color="#00f0ff", width=3),
        name=f"Median Path (₹{mc['median_terminal_price']:.2f})",
        hovertemplate="Day %{x}: ₹%{y:.2f} (Median)<extra></extra>",
    ))

    # 5. Current Price Reference Line (Dashed)
    fig_mc.add_trace(go.Scatter(
        x=[0, mc["days"]],
        y=[mc["current_price"], mc["current_price"]],
        mode="lines",
        line=dict(color="#94a3b8", width=1.5, dash="dash"),
        name=f"Spot Price (₹{mc['current_price']:.2f})",
        hovertemplate=f"Spot Reference: ₹{mc['current_price']:.2f}<extra></extra>",
    ))

    fig_mc.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(10, 14, 39, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.55)",
        font=dict(family="Inter", color="#94a3b8", size=11),
        hovermode="x unified",
        xaxis=dict(
            title="Forecast Trading Days (T + N)",
            gridcolor="rgba(255, 255, 255, 0.05)",
            zerolinecolor="rgba(255, 255, 255, 0.05)",
        ),
        yaxis=dict(
            title="Simulated Stock Price (INR)",
            gridcolor="rgba(255, 255, 255, 0.05)",
            zerolinecolor="rgba(255, 255, 255, 0.05)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color="#cbd5e1"),
        ),
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # ----------------------------------------------------
    # TERMINAL WEALTH DISTRIBUTION HISTOGRAM
    # ----------------------------------------------------
    col_hist, col_stats = st.columns([1.3, 0.7])

    with col_hist:
        st.markdown("##### 📊 Terminal Portfolio Value Distribution (INR 5,00,000 Base)")

        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=mc["terminal_portfolio_values"],
            nbinsx=40,
            marker=dict(
                color="rgba(0, 240, 255, 0.65)",
                line=dict(color="rgba(0, 240, 255, 0.9)", width=1),
            ),
            name="Terminal Portfolio Value",
            hovertemplate="Portfolio Value: ₹%{x:,.0f}<br>Count: %{y}<extra></extra>",
        ))

        # Vertical line for Baseline Portfolio (₹5,00,000)
        fig_dist.add_vline(
            x=mc["portfolio_base"],
            line_width=2,
            line_dash="dash",
            line_color="#94a3b8",
            annotation_text="Base: ₹5L",
            annotation_position="top left",
            annotation_font_color="#94a3b8",
        )

        # Vertical line for 95% VaR Cutoff
        var95_cutoff = mc["portfolio_base"] - mc["var_95_hist"]
        fig_dist.add_vline(
            x=var95_cutoff,
            line_width=2,
            line_dash="dot",
            line_color="#f59e0b",
            annotation_text=f"95% VaR (-₹{mc['var_95_hist']:,.0f})",
            annotation_position="top left",
            annotation_font_color="#f59e0b",
        )

        # Vertical line for 99% VaR Cutoff
        var99_cutoff = mc["portfolio_base"] - mc["var_99_hist"]
        fig_dist.add_vline(
            x=var99_cutoff,
            line_width=2,
            line_dash="dot",
            line_color="#ef4444",
            annotation_text=f"99% VaR (-₹{mc['var_99_hist']:,.0f})",
            annotation_position="bottom left",
            annotation_font_color="#ef4444",
        )

        fig_dist.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=25, b=20),
            paper_bgcolor="rgba(10, 14, 39, 0.0)",
            plot_bgcolor="rgba(15, 23, 42, 0.55)",
            font=dict(family="Inter", color="#94a3b8", size=10),
            xaxis=dict(
                title="Terminal Portfolio Value (INR)",
                gridcolor="rgba(255, 255, 255, 0.05)",
                zerolinecolor="rgba(255, 255, 255, 0.05)",
            ),
            yaxis=dict(
                title="Simulated Scenarios",
                gridcolor="rgba(255, 255, 255, 0.05)",
                zerolinecolor="rgba(255, 255, 255, 0.05)",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_stats:
        st.markdown("##### 🎲 Quantitative Probability Matrix")
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 14px; font-size: 12px; height: 300px;">
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #94a3b8;">Probability of Profit:</span>
                <span style="color: #00d084; font-weight: 700;">{mc['prob_profit']}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #94a3b8;">Risk of >10% Capital Loss:</span>
                <span style="color: {'#ef4444' if mc['prob_loss_gt_10pct'] > 15 else '#f59e0b'}; font-weight: 700;">{mc['prob_loss_gt_10pct']}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #94a3b8;">Annualized Volatility (σ):</span>
                <span style="color: #cbd5e1; font-weight: 700;">{mc['sigma_annualized']*100:.1f}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #94a3b8;">Annualized Drift (μ):</span>
                <span style="color: #cbd5e1; font-weight: 700;">{mc['mu_annualized']*100:+.1f}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #94a3b8;">Expected Terminal Price:</span>
                <span style="color: #00f0ff; font-weight: 700;">₹{mc['expected_terminal_price']:.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0;">
                <span style="color: #94a3b8;">Median Terminal Price:</span>
                <span style="color: #a78bfa; font-weight: 700;">₹{mc['median_terminal_price']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # STRESS-TEST SCENARIOS PROJECTION MATRIX
    # ----------------------------------------------------
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🚨 Macro Black-Swan Crisis Stress-Testing Matrix")

    stress_cards = []
    for sc in mc["stress_scenarios"]:
        sign_str = f"-₹{sc['loss_inr']:,.0f}" if sc["loss_inr"] > 0 else f"+₹{abs(sc['loss_inr']):,.0f}"
        shock_sign = f"{sc['shock_pct']:+.0f}%"
        stress_cards.append(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid {sc['color']}44; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #f8fafc; font-weight: 700; font-size: 13px;">{sc['name']}</span>
                <span style="background: {sc['color']}22; color: {sc['color']}; border: 1px solid {sc['color']}; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 700;">
                    {shock_sign} SHOCK
                </span>
            </div>
            <p style="color: #94a3b8; font-size: 11px; margin: 4px 0 8px 0;">{sc['description']}</p>
            <div style="display: flex; justify-content: space-between; font-size: 12px; font-family: 'JetBrains Mono', monospace; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                <span>Projected Loss: <b style="color: {sc['color']};">{sign_str}</b></span>
                <span>Stressed Portfolio: <b style="color: #cbd5e1;">₹{sc['stressed_val']:,.0f}</b></span>
                <span>Target Price: <b style="color: #38bdf8;">₹{sc['stressed_price']:.2f}</b></span>
            </div>
        </div>
        """)

    st.markdown("".join(stress_cards), unsafe_allow_html=True)
