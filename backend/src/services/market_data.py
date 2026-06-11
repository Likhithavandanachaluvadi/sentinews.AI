"""
Market data service using yfinance for Indian NSE stocks.
Automatically appends .NS suffix for NSE ticker lookups.
Integrated with screener.com for institutional-grade metrics.
All financial figures are displayed in INR (₹) where applicable.
"""
from matplotlib.pylab import rint
from soupsieve import match
import yfinance as yf
import logging
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


def _to_nse_ticker(ticker: str) -> str:
    """
    Converts a raw NSE ticker symbol to the yfinance-compatible format.
    For Indian NSE stocks, yfinance requires the '.NS' suffix.
    e.g. 'RELIANCE' → 'RELIANCE.NS', 'TCS' → 'TCS.NS'
    Already-suffixed tickers are returned as-is.
    """
    ticker = ticker.upper().strip()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return ticker
    # Special handling for tickers with & or - (e.g. M&M, BAJAJ-AUTO)
    return f"{ticker}.NS"


def _format_inr(value: Optional[float]) -> str:
    """Format a number into readable INR units (Cr, L, etc.)."""
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"₹{value / 1e12:.2f}L Cr"
    if value >= 1e9:
        return f"₹{value / 1e7:.2f} Cr"
    if value >= 1e6:
        return f"₹{value / 1e5:.2f} L"
    return f"₹{value:,.2f}"


def get_market_context(ticker: str) -> list[str]:
    """
    Fetches real-time market data for a given NSE ticker using yfinance.
    Automatically adds .NS suffix for Indian stock lookup.
    Returns a list of context strings ready for LLM injection.
    """
    context_chunks = []
    nse_ticker = _to_nse_ticker(ticker)

    try:
        stock = yf.Ticker(nse_ticker)
        info = stock.info

        # Check if data was actually returned (yfinance silently returns
        # empty dicts for invalid tickers)
        if not info or info.get("quoteType") is None:
            logger.warning(f"No data returned from yfinance for {nse_ticker}, trying BSE fallback")
            # Try BSE fallback
            bse_ticker = ticker.upper() + ".BO"
            stock = yf.Ticker(bse_ticker)
            info = stock.info
            if not info or info.get("quoteType") is None:
                raise ValueError(f"No market data found for ticker: {ticker}")

        # Company overview
        name = info.get("longName") or info.get("shortName", ticker)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        summary = info.get("longBusinessSummary", "No description available.")
        exchange = info.get("exchange", "NSE")

        context_chunks.append(
            f"Company Overview: {name} is listed on {exchange} and operates in the "
            f"{industry} industry within the {sector} sector.\n{summary}"
        )

        # Financial snapshot (in INR)
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        pe_ratio = info.get("trailingPE")
        pb_ratio = info.get("priceToBook")
        market_cap = info.get("marketCap")
        revenue = info.get("totalRevenue")
        profit_margin = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        eps = info.get("trailingEps")
        dividend_yield = info.get("dividendYield")
        week_52_high = info.get("fiftyTwoWeekHigh")
        week_52_low = info.get("fiftyTwoWeekLow")

        financial_lines = [f"Financial Snapshot for {name} ({ticker.upper()} | NSE):"]

        if price:
            change = ""
            if prev_close:
                pct = ((price - prev_close) / prev_close) * 100
                change = f"  ({'+' if pct >= 0 else ''}{pct:.2f}% vs prev close)"
            financial_lines.append(f"- Current Price: ₹{price:,.2f}{change}")
        if week_52_high:
            financial_lines.append(f"- 52-Week High: ₹{week_52_high:,.2f}")
        if week_52_low:
            financial_lines.append(f"- 52-Week Low: ₹{week_52_low:,.2f}")
        if market_cap:
            financial_lines.append(f"- Market Cap: {_format_inr(market_cap)}")
        if pe_ratio:
            financial_lines.append(f"- P/E Ratio (TTM): {pe_ratio:.2f}x")
        if pb_ratio:
            financial_lines.append(f"- Price/Book: {pb_ratio:.2f}x")
        if eps:
            financial_lines.append(f"- EPS (TTM): ₹{eps:.2f}")
        if revenue:
            financial_lines.append(f"- Annual Revenue: {_format_inr(revenue)}")
        if profit_margin:
            financial_lines.append(f"- Net Profit Margin: {profit_margin * 100:.1f}%")
        if roe:
            financial_lines.append(f"- Return on Equity (ROE): {roe * 100:.1f}%")
        if debt_to_equity:
            financial_lines.append(f"- Debt/Equity Ratio: {debt_to_equity:.2f}")
        if dividend_yield:
            financial_lines.append(f"- Dividend Yield: {dividend_yield * 100:.2f}%")

        context_chunks.append("\n".join(financial_lines))

        # Fetch Financial Statement growth (QoQ and YoY) and margins
        history_lines = ["\nFinancial Statements Growth & Margins History:"]
        
        def find_col(df, keywords):
            for c in df.columns:
                c_str = str(c).lower()
                if any(kw in c_str for kw in keywords):
                    return c
            return None

        # 1. Quarterly Financials
        try:
            q_fin = stock.quarterly_financials
            if q_fin is not None and not q_fin.empty:
                q_fin_t = q_fin.T
                rev_col = find_col(q_fin_t, ["total revenue", "revenue"])
                net_col = find_col(q_fin_t, ["net income"])
                gross_col = find_col(q_fin_t, ["gross profit"])
                op_col = find_col(q_fin_t, ["operating income"])

                history_lines.append("- Quarterly Metrics:")
                for index, row in q_fin_t.head(4).iterrows():
                    date_str = index.strftime('%Y-%m-%d') if hasattr(index, 'strftime') else str(index)
                    r_val = row.get(rev_col) if rev_col else None
                    n_val = row.get(net_col) if net_col else None
                    g_val = row.get(gross_col) if gross_col else None
                    o_val = row.get(op_col) if op_col else None

                    g_margin = f"{(g_val / r_val) * 100:.1f}%" if g_val is not None and r_val else "N/A"
                    o_margin = f"{(o_val / r_val) * 100:.1f}%" if o_val is not None and r_val else "N/A"
                    n_margin = f"{(n_val / r_val) * 100:.1f}%" if n_val is not None and r_val else "N/A"

                    r_fmt = _format_inr(r_val) if r_val is not None else "N/A"
                    n_fmt = _format_inr(n_val) if n_val is not None else "N/A"

                    history_lines.append(
                        f"  * Quarter Ending {date_str}: Revenue = {r_fmt}, Net Income = {n_fmt}, "
                        f"Gross Margin = {g_margin}, Operating Margin = {o_margin}, Net Margin = {n_margin}"
                    )

                if len(q_fin_t) >= 2:
                    lat_idx = q_fin_t.index[0]
                    prev_idx = q_fin_t.index[1]
                    
                    lat_date = lat_idx.strftime('%Y-%m-%d') if hasattr(lat_idx, 'strftime') else str(lat_idx)
                    prev_date = prev_idx.strftime('%Y-%m-%d') if hasattr(prev_idx, 'strftime') else str(prev_idx)

                    if rev_col:
                        lat_r = q_fin_t.loc[lat_idx, rev_col]
                        prev_r = q_fin_t.loc[prev_idx, rev_col]
                        if lat_r and prev_r:
                            qoq_r = ((lat_r - prev_r) / prev_r) * 100
                            history_lines.append(f"  * Revenue QoQ Growth (latest vs prev quarter): {qoq_r:.1f}% ({lat_date} vs {prev_date})")

                    if net_col:
                        lat_n = q_fin_t.loc[lat_idx, net_col]
                        prev_n = q_fin_t.loc[prev_idx, net_col]
                        if lat_n and prev_n:
                            qoq_n = ((lat_n - prev_n) / prev_n) * 100
                            history_lines.append(f"  * Net Income QoQ Growth (latest vs prev quarter): {qoq_n:.1f}% ({lat_date} vs {prev_date})")

                if len(q_fin_t) >= 5:
                    lat_idx = q_fin_t.index[0]
                    yoy_idx = q_fin_t.index[4]
                    
                    lat_date = lat_idx.strftime('%Y-%m-%d') if hasattr(lat_idx, 'strftime') else str(lat_idx)
                    yoy_date = yoy_idx.strftime('%Y-%m-%d') if hasattr(yoy_idx, 'strftime') else str(yoy_idx)

                    if rev_col:
                        lat_r = q_fin_t.loc[lat_idx, rev_col]
                        yoy_r = q_fin_t.loc[yoy_idx, rev_col]
                        if lat_r and yoy_r:
                            yoy_r_q = ((lat_r - yoy_r) / yoy_r) * 100
                            history_lines.append(f"  * Revenue YoY Quarterly Growth: {yoy_r_q:.1f}% ({lat_date} vs {yoy_date})")

                    if net_col:
                        lat_n = q_fin_t.loc[lat_idx, net_col]
                        yoy_n = q_fin_t.loc[yoy_idx, net_col]
                        if lat_n and yoy_n:
                            yoy_n_q = ((lat_n - yoy_n) / yoy_n) * 100
                            history_lines.append(f"  * Net Income YoY Quarterly Growth: {yoy_n_q:.1f}% ({lat_date} vs {yoy_date})")

        except Exception as e:
            logger.warning(f"Error extracting quarterly financials for {ticker}: {e}")

        # 2. Annual Financials
        try:
            ann_fin = stock.financials
            if ann_fin is not None and not ann_fin.empty:
                ann_fin_t = ann_fin.T
                rev_col = find_col(ann_fin_t, ["total revenue", "revenue"])
                net_col = find_col(ann_fin_t, ["net income"])
                gross_col = find_col(ann_fin_t, ["gross profit"])
                op_col = find_col(ann_fin_t, ["operating income"])

                history_lines.append("- Annual Metrics:")
                for index, row in ann_fin_t.head(4).iterrows():
                    date_str = index.strftime('%Y-%m-%d') if hasattr(index, 'strftime') else str(index)
                    r_val = row.get(rev_col) if rev_col else None
                    n_val = row.get(net_col) if net_col else None
                    g_val = row.get(gross_col) if gross_col else None
                    o_val = row.get(op_col) if op_col else None

                    g_margin = f"{(g_val / r_val) * 100:.1f}%" if g_val is not None and r_val else "N/A"
                    o_margin = f"{(o_val / r_val) * 100:.1f}%" if o_val is not None and r_val else "N/A"
                    n_margin = f"{(n_val / r_val) * 100:.1f}%" if n_val is not None and r_val else "N/A"

                    r_fmt = _format_inr(r_val) if r_val is not None else "N/A"
                    n_fmt = _format_inr(n_val) if n_val is not None else "N/A"

                    history_lines.append(
                        f"  * Year Ending {date_str}: Revenue = {r_fmt}, Net Income = {n_fmt}, "
                        f"Gross Margin = {g_margin}, Operating Margin = {o_margin}, Net Margin = {n_margin}"
                    )

                if len(ann_fin_t) >= 2:
                    lat_idx = ann_fin_t.index[0]
                    prev_idx = ann_fin_t.index[1]
                    
                    lat_date = lat_idx.strftime('%Y-%m-%d') if hasattr(lat_idx, 'strftime') else str(lat_idx)
                    prev_date = prev_idx.strftime('%Y-%m-%d') if hasattr(prev_idx, 'strftime') else str(prev_idx)

                    if rev_col:
                        lat_r = ann_fin_t.loc[lat_idx, rev_col]
                        prev_r = ann_fin_t.loc[prev_idx, rev_col]
                        if lat_r and prev_r:
                            yoy_r = ((lat_r - prev_r) / prev_r) * 100
                            history_lines.append(f"  * Annual Revenue YoY Growth: {yoy_r:.1f}% ({lat_date} vs {prev_date})")

                    if net_col:
                        lat_n = ann_fin_t.loc[lat_idx, net_col]
                        prev_n = ann_fin_t.loc[prev_idx, net_col]
                        if lat_n and prev_n:
                            yoy_n = ((lat_n - prev_n) / prev_n) * 100
                            history_lines.append(f"  * Annual Net Income YoY Growth: {yoy_n:.1f}% ({lat_date} vs {prev_date})")

        except Exception as e:
            logger.warning(f"Error extracting annual financials for {ticker}: {e}")

        if len(history_lines) > 1:
            context_chunks.append("\n".join(history_lines))

        # Compute ROCE (Return on Capital Employed)
        roce = None
        try:
            ebit = None
            ann_fin = stock.financials
            if ann_fin is not None and not ann_fin.empty:
                ann_fin_t = ann_fin.T
                ebit_col = find_col(ann_fin_t, ["operating income", "ebit"])
                if ebit_col:
                    ebit = ann_fin_t[ebit_col].iloc[0]
            
            bal_sheet = stock.balance_sheet
            if bal_sheet is not None and not bal_sheet.empty:
                bal_sheet_t = bal_sheet.T
                assets_col = find_col(bal_sheet_t, ["total assets", "assets"])
                curr_liab_col = find_col(bal_sheet_t, ["total current liabilities", "current liabilities"])
                
                if assets_col:
                    total_assets = bal_sheet_t[assets_col].iloc[0]
                    curr_liab = bal_sheet_t[curr_liab_col].iloc[0] if curr_liab_col else 0
                    cap_employed = total_assets - curr_liab
                    if cap_employed and ebit is not None:
                        roce = (ebit / cap_employed) * 100
        except Exception as e:
            logger.warning(f"Failed to calculate ROCE for {ticker}: {e}")

        # Format and compile Screener.in Key Statistics
        screener_lines = ["\nScreener.in Key Statistics:"]
        
        m_cap = info.get("marketCap")
        curr_p = info.get("currentPrice") or info.get("regularMarketPrice")
        high_52 = info.get("fiftyTwoWeekHigh")
        low_52 = info.get("fiftyTwoWeekLow")
        pe = info.get("trailingPE")
        book_v = info.get("bookValue")
        div_y = info.get("dividendYield")
        roe_val = info.get("returnOnEquity")
        face_v = info.get("faceValue")
        peg_r = info.get("pegRatio")
        pb_r = info.get("priceToBook")

        m_cap_cr = f"₹{m_cap / 10000000:,.1f} Cr" if m_cap else "N/A"
        curr_p_fmt = f"₹{curr_p:,.2f}" if curr_p else "N/A"
        high_low_52 = f"₹{high_52:,.2f} / ₹{low_52:,.2f}" if high_52 and low_52 else "N/A"
        pe_fmt = f"{pe:.2f}" if pe else "N/A"
        book_v_fmt = f"₹{book_v:.2f}" if book_v else "N/A"
        div_y_fmt = f"{div_y * 100:.2f}%" if div_y else "N/A"
        roe_fmt = f"{roe_val * 100:.2f}%" if roe_val else "N/A"
        roce_fmt = f"{roce:.2f}%" if roce is not None else "N/A"
        face_v_fmt = f"₹{face_v}" if face_v else "N/A"
        peg_fmt = f"{peg_r:.2f}" if peg_r else "N/A"
        pb_fmt = f"{pb_r:.2f}" if pb_r else "N/A"

        screener_lines.append(f"- Market Cap: {m_cap_cr}")
        screener_lines.append(f"- Current Price: {curr_p_fmt}")
        screener_lines.append(f"- High / Low: {high_low_52}")
        screener_lines.append(f"- Stock P/E: {pe_fmt}")
        screener_lines.append(f"- PEG Ratio: {peg_fmt}")
        screener_lines.append(f"- Price to Book: {pb_fmt}")
        screener_lines.append(f"- Book Value: {book_v_fmt}")
        screener_lines.append(f"- Dividend Yield: {div_y_fmt}")
        screener_lines.append(f"- ROCE: {roce_fmt}")
        screener_lines.append(f"- ROE: {roe_fmt}")
        screener_lines.append(f"- Face Value: {face_v_fmt}")

        context_chunks.append("\n".join(screener_lines))

        # # Analyst recommendations
        # target_price = info.get("targetMeanPrice")
        # analyst_count = info.get("numberOfAnalystOpinions")
        # recommendation = info.get("recommendationKey", "N/A").replace("_", " ").title()
        # target_high = info.get("targetHighPrice")
        # target_low = info.get("targetLowPrice")

        # if target_price:
        #     rec_text = (
        #         f"Analyst Consensus for {name}: Recommendation is '{recommendation}'. "
        #         f"Mean target price is ₹{target_price:.2f}"
        #     )
        #     if analyst_count:
        #         rec_text += f" across {analyst_count} analyst opinions"
        #     if target_high and target_low:
        #         rec_text += f". Target range: ₹{target_low:.2f} – ₹{target_high:.2f}."
            # context_chunks.append(rec_text)

    except Exception as e:
        logger.warning(f"yfinance data fetch failed for {ticker} ({nse_ticker}): {e}")
        context_chunks.append(
            f"Note: Real-time market data for '{ticker}' (NSE) could not be retrieved. "
            f"Analysis will be based on available news and qualitative context."
        )

    return context_chunks


async def get_enhanced_market_context(ticker: str) -> list[str]:
    """
    Async function to fetch comprehensive market context including:
    - yfinance data (prices, financials, historical)
    - Screener.com institutional metrics (PEG, ROCE, peer comparison)
    - Technical indicators (RSI, MACD, SMA20, SMA50, Bollinger Bands)
    - Additional growth and valuation metrics

    Returns a list of context strings ready for LLM injection.
    """
    from src.services.technical_analysis_engine import get_programmatic_technical_indicators

    # Get base market context from yfinance
    context_chunks = get_market_context(ticker)

    # Fetch and compute technical indicators
    try:
        price_history = get_price_history(ticker, period="3mo")
        if price_history and len(price_history) >= 50:
            tech_indicators = get_programmatic_technical_indicators(price_history)
            if "error" not in tech_indicators:
                tech_text = "Technical Indicators (Computed from price history):\n"
                tech_text += f"- Current Price: ₹{tech_indicators.get('current_price', 'N/A')}\n"
                tech_text += f"- RSI (14): {tech_indicators.get('RSI_14', 'N/A')}\n"
                tech_text += f"- SMA 20: ₹{tech_indicators.get('SMA_20', 'N/A')}\n"
                tech_text += f"- SMA 50: ₹{tech_indicators.get('SMA_50', 'N/A')}\n"
                tech_text += f"- MACD: {tech_indicators.get('MACD', 'N/A')}\n"
                tech_text += f"- MACD Signal: {tech_indicators.get('MACD_Signal', 'N/A')}\n"
                tech_text += f"- Bollinger Band Upper: ₹{tech_indicators.get('BB_Upper', 'N/A')}\n"
                tech_text += f"- Bollinger Band Lower: ₹{tech_indicators.get('BB_Lower', 'N/A')}\n"
                tech_text += f"- Trend: {tech_indicators.get('Trend_Analysis', 'N/A')}\n"
                tech_text += f"- Momentum: {tech_indicators.get('Momentum_Analysis', 'N/A')}"
                context_chunks.append(tech_text)
                logger.info(f"Technical indicators computed for {ticker}")
        else:
            logger.warning(f"Insufficient price history for technical analysis: {len(price_history) if price_history else 0} candles")
    except Exception as e:
        logger.warning(f"Failed to compute technical indicators for {ticker}: {e}")

    print("MARKET CONTEXT =")
    print("\n".join(context_chunks))
    
    # Try to enhance with screener metrics
    # try:
    #     from src.services.screener_service import (
    #         ScreenerService,
    #         enrich_with_screener_metrics
    #     )
    try:
        from src.services.screener_service import (
            ScreenerService,
            enrich_with_screener_metrics
        )

        print("IMPORT SUCCESS")
        print("CLASS =", ScreenerService)
        print(
            "METHOD =",
            hasattr(ScreenerService, "fetch_peer_comparison")
        )

        # Fetch screener institutional metrics
        context_chunks = await enrich_with_screener_metrics(ticker, context_chunks)
        print("AFTER ENRICH")
        print("REACHED PEER SECTION")
        print("TOTAL CHUNKS =", len(context_chunks))
        # Fetch peer comparison if sector is available
        sector = None
        print("CONTEXT CHUNKS =", context_chunks)
        print("CLASS =", ScreenerService)
        print("METHOD =", hasattr(ScreenerService, "fetch_peer_comparison"))
        print("IMPORTING SCREENER SERVICE"),
        for chunk in context_chunks:
            print("CHUNK START")
            print(chunk[:300])
            import re

            match = re.search(
             r'within the\s+([A-Za-z\s&]+?)\s+sector',
             chunk,
                re.IGNORECASE
              )

            if match:
                print("MATCH FOUND")
                print("SECTOR =", match.group(1))
                sector = match.group(1).strip()
                break
        print("DETECTED SECTOR =", sector)
        print("SECTOR BEFORE IF =", sector)
        print("SECTOR =", sector)
        if True:
            print("CALLING PEER COMPARISON")
            peer_data = await ScreenerService.fetch_peer_comparison(
                ticker,
                sector
            )
            if peer_data.get('peers'):
                self_data = peer_data.get("self", {})
                peer_names = []
                market_caps = []
                pes = []
                roes = []

                for peer in peer_data.get("peers", []):
                    peer_names.append(peer.get("name") or "N/A")
                    market_caps.append(peer.get("market_cap", "N/A"))
                    pes.append(peer.get("stock_pe", "N/A"))
                    roes.append(peer.get("roe", "N/A"))
                peer_text = (
                    f"| Metric | {ticker.upper()} | {' | '.join(peer_names)} |\n"
                    f"|---------|---------|{'|'.join(['---------'] * len(peer_names))}|\n"
                )
                peer_text += f"| Market Cap | {self_data.get('market_cap', 'N/A')} | {' | '.join(market_caps)} |\n"
                peer_text += f"| P/E Ratio | {self_data.get('stock_pe', 'N/A')} | {' | '.join(pes)} |\n"
                peer_text += f"| ROE | {self_data.get('roe', 'N/A')} | {' | '.join(roes)} |\n"

                context_chunks.append(peer_text)
                print("PEER TEXT =", peer_text)
                print("FINAL CONTEXT CHUNKS =")
                print("INSIDE IF BLOCK")
                for chunk in context_chunks:
                    print(chunk)
        else:
            print("Skipping peer comparison due to missing sector")
#                 peer_text = "\n=== PEER COMPARISON ===\n"
# #                 peer_text = """
# # | Metric | TCS | Infosys | HCL Tech | Wipro |
# # |---------|---------|---------|---------|---------|
# # | Market Cap | ₹8.4L Cr | ₹6.5L Cr | ₹4L Cr | ₹2L Cr |
# # | P/E Ratio | 17.1 | 25 | 22 | 18 |
# # | ROE | 48.4% | 30% | 24% | 18% |
# # """
#                 context_chunks.append(peer_text)
#                 print("PEER TEXT =", peer_text)
#                 peer_text += f"Top competitors in {sector}:\n"
#                 for i, peer in enumerate(peer_data['peers'], 1):
#                     name = peer.get('name', 'Unknown')
#                     market_cap = peer.get('market_cap', 'N/A')
#                     pe = peer.get('stock_pe', 'N/A')
#                     roe = peer.get('roe', 'N/A')
#                     peer_text += f"{i}. {name} - Market Cap: {market_cap}, P/E: {pe}, ROE: {roe}\n"

    except ImportError:
        logger.warning("Screener service not available, using basic market context only")
    except Exception as e:
        logger.warning(f"Failed to fetch enhanced metrics for {ticker}: {e}")
    print("LAST CONTEXT CHUNK =", context_chunks[-1])
    print("AFTER LAST CONTEXT")
    return context_chunks


def get_price_history(ticker: str, period: str = "1mo") -> list[dict]:
    """
    Returns price history data for charting. Automatically appends .NS suffix.
    """
    nse_ticker = _to_nse_ticker(ticker)
    try:
        stock = yf.Ticker(nse_ticker)
        hist = stock.history(period=period)

        if hist.empty:
            # Try BSE fallback
            stock = yf.Ticker(ticker.upper() + ".BO")
            hist = stock.history(period=period)

        return [
            {
                "date": str(index.date()),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            }
            for index, row in hist.iterrows()
        ]
    except Exception as e:
        logger.warning(f"Price history fetch failed for {ticker}: {e}")
        return []
