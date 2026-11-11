"""
market_depth.py — Level-2 Market Depth, Order Book Ladder & Slippage Engine
Institutional quantitative module for NSE order book simulation, depth visualization,
real-time VWAP calculation, and market impact analysis.
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def simulate_l2_order_book(current_price: float, atr: float, spread_bps: float = 2.5) -> dict:
    """
    Generates a realistic 10-level L2 Bid/Ask order book ladder conforming to
    NSE market microstructure (tick size = INR 0.05).

    Parameters
    ----------
    current_price : float
        Current spot or last traded market price in INR.
    atr : float
        Average True Range volatility metric in INR.
    spread_bps : float, default=2.5
        Target bid-ask spread in basis points (1 bps = 0.01%).

    Returns
    -------
    dict
        Dictionary containing 10-level bids and asks, top-of-book metrics,
        spread metrics in paise and bps, VWAPs, and cumulative volume ladders.
    """
    # Guard invalid inputs
    price = max(1.0, float(current_price))
    vol_atr = max(0.05, float(atr)) if atr and atr > 0 else max(0.5, price * 0.015)

    tick = 0.05  # Standard NSE equity tick size in INR

    # Half-spread calculation in INR (clamped to at least 1 tick)
    raw_half_spread = price * (max(0.5, float(spread_bps)) / 10000.0) / 2.0
    half_spread_ticks = max(1, int(round(raw_half_spread / tick)))

    best_bid = round(price - (half_spread_ticks * tick), 2)
    best_ask = round(price + (half_spread_ticks * tick), 2)
    if best_ask <= best_bid:
        best_ask = round(best_bid + tick, 2)

    mid_price = round((best_bid + best_ask) / 2.0, 2)
    spread = round(best_ask - best_bid, 2)
    spread_paise = round(spread * 100.0, 1)
    spread_bps_calc = round((spread / mid_price) * 10000.0, 2)

    # Base liquidity scaling inversely with price (e.g. higher share quantities for lower priced stocks)
    notional_base_per_level = 350000.0  # Approx INR 3.5 Lakhs nominal depth per ladder tier
    base_qty = max(15, int(notional_base_per_level / price))

    # Deterministic pseudo-random seed based on price and ATR to keep ladder steady within a tick
    seed_val = int(abs(hash(f"{round(price, 2)}_{round(vol_atr, 2)}")) % (2**31 - 1))
    rng = np.random.RandomState(seed_val)

    # Generate 10 Bid levels (prices descending from best_bid)
    # Generate 10 Ask levels (prices ascending from best_ask)
    bids = []
    asks = []

    cum_bid_vol = 0
    cum_ask_vol = 0

    # Dynamic step tick interval based on volatility: 1 to 4 ticks per level
    step_ticks = max(1, int(round((vol_atr * 0.012) / tick)))

    for i in range(1, 11):
        # Bid price descending
        bid_p = round(best_bid - ((i - 1) * step_ticks * tick), 2)
        if bid_p <= 0.05:
            bid_p = 0.05

        # Liquidity concentration: Level 1 has tight touch size; Levels 2-6 build institutional depth
        depth_multiplier = 0.75 + (0.22 * min(i, 5)) + rng.uniform(-0.15, 0.25)
        bid_q = max(10, int(base_qty * depth_multiplier))
        cum_bid_vol += bid_q
        bid_orders = max(1, int(3 + (bid_q / max(1, base_qty * 0.25)) + rng.randint(1, 7)))

        bids.append({
            "level": i,
            "price": bid_p,
            "quantity": bid_q,
            "cum_quantity": cum_bid_vol,
            "order_count": bid_orders,
            "notional": round(bid_p * bid_q, 2),
        })

        # Ask price ascending
        ask_p = round(best_ask + ((i - 1) * step_ticks * tick), 2)
        ask_depth_mult = 0.75 + (0.22 * min(i, 5)) + rng.uniform(-0.15, 0.25)
        ask_q = max(10, int(base_qty * ask_depth_mult))
        cum_ask_vol += ask_q
        ask_orders = max(1, int(3 + (ask_q / max(1, base_qty * 0.25)) + rng.randint(1, 7)))

        asks.append({
            "level": i,
            "price": ask_p,
            "quantity": ask_q,
            "cum_quantity": cum_ask_vol,
            "order_count": ask_orders,
            "notional": round(ask_p * ask_q, 2),
        })

    # VWAP Calculations across full 10-level book
    total_bid_notional = sum(b["notional"] for b in bids)
    total_ask_notional = sum(a["notional"] for a in asks)

    bid_vwap = round(total_bid_notional / max(1, cum_bid_vol), 2)
    ask_vwap = round(total_ask_notional / max(1, cum_ask_vol), 2)
    total_book_notional = total_bid_notional + total_ask_notional
    total_book_vol = cum_bid_vol + cum_ask_vol
    book_vwap = round(total_book_notional / max(1, total_book_vol), 2)

    # Order flow imbalance: (Bid Vol - Ask Vol) / (Bid Vol + Ask Vol) * 100
    imbalance = round(((cum_bid_vol - cum_ask_vol) / max(1, total_book_vol)) * 100.0, 2)

    return {
        "bids": bids,
        "asks": asks,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "spread_bps": spread_bps_calc,
        "spread_paise": spread_paise,
        "mid_price": mid_price,
        "vwap": book_vwap,
        "bid_vwap": bid_vwap,
        "ask_vwap": ask_vwap,
        "total_bid_vol": cum_bid_vol,
        "total_ask_vol": cum_ask_vol,
        "bid_ask_imbalance": imbalance,
        "levels": 10,
    }


def calculate_execution_slippage(book: dict, order_qty: int, side: str = "BUY", atr: float = 20.0) -> dict:
    """
    Simulates realistic order execution by walking the 10-level order book.
    If the order size exceeds available cumulative volume, applies the institutional
    square-root market impact law to the residual volume.

    Parameters
    ----------
    book : dict
        Order book dictionary returned by simulate_l2_order_book.
    order_qty : int
        Number of shares to execute.
    side : str
        'BUY' (fills against Asks) or 'SELL' (fills against Bids).
    atr : float
        Average True Range for residual market impact modeling.

    Returns
    -------
    dict
        Execution metrics including effective VWAP, touch price, slippage in paise/bps,
        total trade notional, and friction fee breakdown.
    """
    qty = max(1, int(order_qty))
    side = side.upper()

    if side == "BUY":
        ladder = book["asks"]
        touch_price = book["best_ask"]
        total_available = book["total_ask_vol"]
    else:
        ladder = book["bids"]
        touch_price = book["best_bid"]
        total_available = book["total_bid_vol"]

    remaining = qty
    total_cost = 0.0
    fills = []

    for level in ladder:
        if remaining <= 0:
            break
        fill_q = min(remaining, level["quantity"])
        cost = fill_q * level["price"]
        total_cost += cost
        remaining -= fill_q
        fills.append({"price": level["price"], "quantity": fill_q, "level": level["level"]})

    # If order exceeds the 10-level depth, estimate institutional market impact on remainder
    excess_qty = 0
    if remaining > 0:
        excess_qty = remaining
        last_level_price = ladder[-1]["price"]
        # Almgren-Chriss / Square-root market impact law approximation
        impact_factor = (excess_qty / max(1, total_available)) ** 0.5 * (atr / max(1.0, touch_price)) * 0.25
        if side == "BUY":
            excess_avg_price = last_level_price * (1.0 + impact_factor)
        else:
            excess_avg_price = max(0.05, last_level_price * (1.0 - impact_factor))

        total_cost += excess_qty * excess_avg_price
        fills.append({"price": excess_avg_price, "quantity": excess_qty, "level": ">10 (Market Impact)"})

    exec_vwap = total_cost / qty
    total_notional = total_cost

    if side == "BUY":
        slippage_inr = exec_vwap - touch_price
    else:
        slippage_inr = touch_price - exec_vwap

    slippage_inr = max(0.0, slippage_inr)
    slippage_bps = (slippage_inr / touch_price) * 10000.0 if touch_price > 0 else 0.0
    slippage_paise = slippage_inr * 100.0

    # Institutional Indian execution friction model:
    # 0.10% STT, Zerodha Rs 20 flat brokerage, 0.0035% Exchange + GST charges
    stt = total_notional * 0.0010
    brokerage = 20.0
    exchange_charges = total_notional * 0.000035
    total_friction = stt + brokerage + exchange_charges + (slippage_inr * qty)

    return {
        "order_qty": qty,
        "side": side,
        "touch_price": touch_price,
        "exec_vwap": round(exec_vwap, 2),
        "slippage_inr": round(slippage_inr, 2),
        "slippage_paise": round(slippage_paise, 1),
        "slippage_bps": round(slippage_bps, 2),
        "total_notional": round(total_notional, 2),
        "stt": round(stt, 2),
        "brokerage": brokerage,
        "exchange_charges": round(exchange_charges, 2),
        "total_friction": round(total_friction, 2),
        "excess_qty": excess_qty,
        "fills": fills,
    }


def render_order_book_component(current_price: float, atr: float, ticker: str):
    """
    Renders an institutional trading order book visualization in Streamlit with:
    - Live Bid-Ask spread display in paise and bps
    - Real-time VWAP calculation and order flow imbalance
    - Plotly cumulative depth chart (Emerald Bids vs Crimson Asks)
    - Full 10-level institutional order ladder with depth micro-bars
    - Interactive Order Execution Slippage Calculator

    Parameters
    ----------
    current_price : float
        Current spot price.
    atr : float
        Average True Range.
    ticker : str
        Stock ticker symbol.
    """
    book = simulate_l2_order_book(current_price=current_price, atr=atr, spread_bps=2.5)

    # ----------------------------------------------------
    # TOP KPI ROW: SPREAD, VWAP, LIQUIDITY
    # ----------------------------------------------------
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">TOP OF BOOK SPREAD</div>
            <div style="font-size: 24px; font-weight: 800; color: #00f0ff; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                {book['spread_paise']} <span style="font-size: 14px; color: #94a3b8;">paise</span>
            </div>
            <div style="font-size: 12px; color: #38bdf8; margin-top: 2px;">{book['spread_bps']:.2f} bps | Spread: ₹{book['spread']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 208, 132, 0.25); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">BEST BID / ASK</div>
            <div style="font-size: 20px; font-weight: 800; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                <span style="color: #00d084;">₹{book['best_bid']:.2f}</span>
                <span style="color: #64748b; font-size: 16px;"> / </span>
                <span style="color: #f43f5e;">₹{book['best_ask']:.2f}</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Mid: ₹{book['mid_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">ORDER BOOK VWAP</div>
            <div style="font-size: 24px; font-weight: 800; color: #a78bfa; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                ₹{book['vwap']:.2f}
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Bid VWAP ₹{book['bid_vwap']:.2f} | Ask ₹{book['ask_vwap']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        imbalance_color = "#00d084" if book["bid_ask_imbalance"] >= 0 else "#f43f5e"
        imbalance_icon = "▲ BUY PRESSURE" if book["bid_ask_imbalance"] >= 0 else "▼ SELL PRESSURE"
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid {imbalance_color}44; border-radius: 8px; padding: 14px 16px; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: 600;">ORDER FLOW IMBALANCE</div>
            <div style="font-size: 24px; font-weight: 800; color: {imbalance_color}; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                {book['bid_ask_imbalance']:+.1f}%
            </div>
            <div style="font-size: 12px; color: {imbalance_color}; margin-top: 2px; font-weight: 700;">{imbalance_icon}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # DUAL-PANE: PLOTLY DEPTH CHART & L2 LADDER TABLE
    # ----------------------------------------------------
    col_chart, col_ladder = st.columns([1.1, 0.9])

    with col_chart:
        st.markdown("##### 📊 Cumulative Market Liquidity Depth Chart")

        # Prepare cumulative depth data for Plotly
        # Bids: Prices sorted ascending (from lowest level 10 up to best_bid)
        bid_df = pd.DataFrame(book["bids"]).sort_values("price", ascending=True)
        # In a depth chart, cumulative volume at lowest bid is maximum; as price rises to best_bid, cumulative diminishes to level 1
        # Or cumulative from best_bid moving outward:
        # Standard: Bid cumulative volume sum from touch downward
        bids_sorted_desc = pd.DataFrame(book["bids"]).sort_values("price", ascending=False)
        bids_sorted_desc["depth"] = bids_sorted_desc["quantity"].cumsum()
        bids_chart_df = bids_sorted_desc.sort_values("price", ascending=True)

        asks_sorted_asc = pd.DataFrame(book["asks"]).sort_values("price", ascending=True)
        asks_sorted_asc["depth"] = asks_sorted_asc["quantity"].cumsum()

        fig_depth = go.Figure()

        # Emerald Bids Trace (Area fill)
        fig_depth.add_trace(go.Scatter(
            x=bids_chart_df["price"],
            y=bids_chart_df["depth"],
            mode="lines",
            name="Bid Depth (Buy Liquidity)",
            line=dict(color="#00d084", width=2.5, shape="hv"),
            fill="tozeroy",
            fillcolor="rgba(0, 208, 132, 0.22)",
            hovertemplate="<b>Bid Level</b><br>Price: ₹%{x:.2f}<br>Cum Volume: %{y:,} shares<extra></extra>",
        ))

        # Crimson Asks Trace (Area fill)
        fig_depth.add_trace(go.Scatter(
            x=asks_sorted_asc["price"],
            y=asks_sorted_asc["depth"],
            mode="lines",
            name="Ask Depth (Sell Liquidity)",
            line=dict(color="#f43f5e", width=2.5, shape="hv"),
            fill="tozeroy",
            fillcolor="rgba(244, 63, 94, 0.22)",
            hovertemplate="<b>Ask Level</b><br>Price: ₹%{x:.2f}<br>Cum Volume: %{y:,} shares<extra></extra>",
        ))

        # Vertical dashed line at Mid-Price
        max_depth = max(book["total_bid_vol"], book["total_ask_vol"])
        fig_depth.add_trace(go.Scatter(
            x=[book["mid_price"], book["mid_price"]],
            y=[0, max_depth * 1.05],
            mode="lines",
            name=f"Mid Price (₹{book['mid_price']:.2f})",
            line=dict(color="#38bdf8", width=1.5, dash="dash"),
            hovertemplate=f"Mid Price: ₹{book['mid_price']:.2f}<extra></extra>",
        ))

        fig_depth.update_layout(
            height=370,
            margin=dict(l=20, r=20, t=25, b=25),
            paper_bgcolor="rgba(10, 14, 39, 0.0)",
            plot_bgcolor="rgba(15, 23, 42, 0.55)",
            font=dict(family="Inter", color="#94a3b8", size=11),
            hovermode="x unified",
            xaxis=dict(
                title="Price (INR)",
                gridcolor="rgba(255, 255, 255, 0.05)",
                zerolinecolor="rgba(255, 255, 255, 0.05)",
                tickformat=".2f",
            ),
            yaxis=dict(
                title="Cumulative Shares",
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
        st.plotly_chart(fig_depth, use_container_width=True)

    with col_ladder:
        st.markdown("##### ⚡ 10-Level L2 Depth Ladder")
        # Build professional market depth HTML table with micro-bars
        max_q = max(max(b["quantity"] for b in book["bids"]), max(a["quantity"] for a in book["asks"]))

        rows_html = []
        for i in range(10):
            b = book["bids"][i]
            a = book["asks"][i]
            b_pct = int((b["quantity"] / max(1, max_q)) * 100)
            a_pct = int((a["quantity"] / max(1, max_q)) * 100)

            rows_html.append(f"""
            <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.04); font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <td style="color: #64748b; padding: 4px 6px; text-align: center;">{b['order_count']}</td>
                <td style="color: #cbd5e1; padding: 4px 6px; text-align: right; position: relative;">
                    <div style="position: absolute; right: 0; top: 2px; bottom: 2px; width: {b_pct}%; background: rgba(0, 208, 132, 0.12); pointer-events: none;"></div>
                    <span style="position: relative; z-index: 1;">{b['quantity']:,}</span>
                </td>
                <td style="color: #00d084; font-weight: 700; padding: 4px 6px; text-align: right;">₹{b['price']:.2f}</td>
                <td style="color: #64748b; padding: 4px 6px; text-align: center; border-left: 1px solid rgba(255, 255, 255, 0.08); border-right: 1px solid rgba(255, 255, 255, 0.08);">L{i+1}</td>
                <td style="color: #f43f5e; font-weight: 700; padding: 4px 6px; text-align: left;">₹{a['price']:.2f}</td>
                <td style="color: #cbd5e1; padding: 4px 6px; text-align: left; position: relative;">
                    <div style="position: absolute; left: 0; top: 2px; bottom: 2px; width: {a_pct}%; background: rgba(244, 63, 94, 0.12); pointer-events: none;"></div>
                    <span style="position: relative; z-index: 1;">{a['quantity']:,}</span>
                </td>
                <td style="color: #64748b; padding: 4px 6px; text-align: center;">{a['order_count']}</td>
            </tr>
            """)

        ladder_table_html = f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 10px; max-height: 370px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid #475569; font-size: 10px; text-transform: uppercase; color: #94a3b8;">
                        <th style="padding: 4px 6px; text-align: center;">Ord</th>
                        <th style="padding: 4px 6px; text-align: right;">Bid Qty</th>
                        <th style="padding: 4px 6px; text-align: right; color: #00d084;">Bid ₹</th>
                        <th style="padding: 4px 6px; text-align: center;">Tier</th>
                        <th style="padding: 4px 6px; text-align: left; color: #f43f5e;">Ask ₹</th>
                        <th style="padding: 4px 6px; text-align: left;">Ask Qty</th>
                        <th style="padding: 4px 6px; text-align: center;">Ord</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #94a3b8; padding-top: 6px; border-top: 1px solid #334155; margin-top: 6px;">
                <span>Total Bids: <b style="color: #00d084;">{book['total_bid_vol']:,}</b></span>
                <span>Total Asks: <b style="color: #f43f5e;">{book['total_ask_vol']:,}</b></span>
            </div>
        </div>
        """
        st.markdown(ladder_table_html, unsafe_allow_html=True)

    # ----------------------------------------------------
    # INTERACTIVE ORDER EXECUTION & SLIPPAGE SIMULATOR
    # ----------------------------------------------------
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🎯 Institutional Order Execution & Slippage Impact Calculator")

    slip_col_ctrl1, slip_col_ctrl2, slip_col_ctrl3 = st.columns([1.2, 1.2, 1.6])

    with slip_col_ctrl1:
        trade_side = st.radio(
            "Execution Direction:",
            ["BUY (Market Order)", "SELL (Market Order)"],
            horizontal=True,
            key=f"orderbook_side_{ticker}",
        )
        side_clean = "BUY" if "BUY" in trade_side else "SELL"

    with slip_col_ctrl2:
        preset_choice = st.selectbox(
            "Institutional Order Size Preset:",
            ["500 shares", "2,500 shares", "10,000 shares", "Custom Order Size"],
            index=1,
            key=f"orderbook_preset_{ticker}",
        )

    with slip_col_ctrl3:
        if preset_choice == "500 shares":
            order_qty_val = 500
        elif preset_choice == "2,500 shares":
            order_qty_val = 2500
        elif preset_choice == "10,000 shares":
            order_qty_val = 10000
        else:
            order_qty_val = st.number_input(
                "Enter Custom Share Quantity:",
                min_value=1,
                max_value=200000,
                value=3500,
                step=500,
                key=f"orderbook_custom_qty_{ticker}",
            )

    # Compute execution results
    res = calculate_execution_slippage(book=book, order_qty=order_qty_val, side=side_clean, atr=atr)

    # Determine impact badge color & severity
    if res["slippage_bps"] < 5.0:
        impact_badge = "⚡ MINIMAL SLIPPAGE (< 5 bps) — EXCELLENT LIQUIDITY"
        impact_badge_color = "#00d084"
    elif res["slippage_bps"] < 15.0:
        impact_badge = "⚠️ MODERATE MARKET IMPACT (5-15 bps) — AVERAGE DEPTH"
        impact_badge_color = "#f59e0b"
    else:
        impact_badge = "🚨 HIGH SLIPPAGE (> 15 bps) — BOOK DEPLETION DETECTED"
        impact_badge_color = "#ef4444"

    res_c1, res_c2, res_c3, res_c4 = st.columns(4)

    with res_c1:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">TOUCH PRICE</div>
            <div style="font-size: 20px; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
                ₹{res['touch_price']:.2f}
            </div>
            <div style="font-size: 11px; color: #64748b;">Top of Book Touch</div>
        </div>
        """, unsafe_allow_html=True)

    with res_c2:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">EXECUTION VWAP</div>
            <div style="font-size: 20px; font-weight: 700; color: #00f0ff; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
                ₹{res['exec_vwap']:.2f}
            </div>
            <div style="font-size: 11px; color: #38bdf8;">Effective Fill Price</div>
        </div>
        """, unsafe_allow_html=True)

    with res_c3:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">ESTIMATED SLIPPAGE</div>
            <div style="font-size: 20px; font-weight: 700; color: {impact_badge_color}; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
                {res['slippage_bps']:.2f} <span style="font-size: 12px;">bps</span>
            </div>
            <div style="font-size: 11px; color: {impact_badge_color}; font-weight: 600;">₹{res['slippage_inr']:.2f} ({res['slippage_paise']:.0f} paise/sh)</div>
        </div>
        """, unsafe_allow_html=True)

    with res_c4:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">ORDER NOTIONAL VALUE</div>
            <div style="font-size: 20px; font-weight: 700; color: #a78bfa; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
                ₹{res['total_notional']:,.2f}
            </div>
            <div style="font-size: 11px; color: #94a3b8;">{res['order_qty']:,} shares @ VWAP</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top: 10px; background: rgba(15, 23, 42, 0.6); border: 1px solid {impact_badge_color}55; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
        <span style="color: {impact_badge_color}; font-weight: 700; font-size: 12px; letter-spacing: 0.5px;">{impact_badge}</span>
        <span style="color: #94a3b8; font-size: 11px;">
            STT (0.10%): <b style="color: #cbd5e1;">₹{res['stt']:,.2f}</b> | 
            Brokerage: <b style="color: #cbd5e1;">₹{res['brokerage']:.2f}</b> | 
            Exchange/SEBI: <b style="color: #cbd5e1;">₹{res['exchange_charges']:,.2f}</b> | 
            Total Friction: <b style="color: #ef4444;">-₹{res['total_friction']:,.2f}</b>
        </span>
    </div>
    """, unsafe_allow_html=True)
