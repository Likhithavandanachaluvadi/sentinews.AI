"""
Dynamic Retrieval System for SentiNews Query Intelligence.

Replaces the static retriever node with an intent-aware data fetching strategy.

RETRIEVAL GATING BY INTENT:
  EDUCATIONAL          → No live API calls. Static knowledge only.
  RESTRICTED_ADVISORY  → No live API calls. Educational redirect only.
  STOCK_MOVEMENT       → Price + recent news ONLY (no financials scraping).
  SENTIMENT_PULSE      → News ONLY.
  MARKET_OVERVIEW      → Index + macro data ONLY.
  MACROECONOMIC        → Macro APIs only.
  STOCK_ANALYSIS       → Full data: yfinance + screener + news.
  COMPARISON           → Full data for EACH ticker.
  GENERALIZED          → Full data (safe default).

FRESHNESS POLICIES:
  MAX_NEWS_AGE_HOURS         = 2
  MAX_MARKET_DATA_AGE_MINS   = 15

SOURCE FILTERING:
  Blocks generic tech news (BBC, Wired, Verge, Gizmodo, TechCrunch, etc.)
  Only allows finance-specific sources or known financial publications.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import json
import re

from src.agents.retriever import extract_ticker
from src.services.market_data import get_enhanced_market_context
from src.services.news_service import fetch_news_for_ticker
from src.core.debug_logger import debug_logger

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Freshness Constants
# -----------------------------------------------------------------------
MAX_NEWS_AGE_HOURS = 2
MAX_MARKET_DATA_AGE_MINS = 15

# -----------------------------------------------------------------------
# SOURCE FILTERING & VALIDATION
# -----------------------------------------------------------------------

BLOCKED_SOURCES = {
    # Generic tech news (BLOCKED)
    "bbc", "bbc news", "bbc.com", "bbc.co.uk",
    "wired", "wired.com",
    "verge", "theverge", "theverge.com",
    "gizmodo", "gizmodo.com",
    "techcrunch", "techcrunch.com",
    "engadget", "engadget.com",
    "ars technica", "arstechnica.com",
    "the next web", "thenextweb.com",
    "hacker news", "news.ycombinator.com",
    "reddit", "reddit.com",
    "twitter", "x.com", "twitter.com",
    "medium", "medium.com",
    "substack", "substack.com",
    # Entertainment (BLOCKED)
    "buzzfeed", "buzzfeed.com",
    "vox", "vox.com",
    "atlantic", "theatlantic.com",
    "vice", "vice.com",
    "variety", "variety.com",
    "hollywood reporter", "hollywoodreporter.com",
}

PREFERRED_FINANCE_SOURCES = {
    # Tier 1: Primary Financial Data
    "yfinance", "yahoo finance", "finance.yahoo.com",
    "screener.in", "screener",
    "nseindia", "bseindia", "nse india", "bse india",
    "rbi", "reserve bank of india",
    
    # Tier 2: Quality Financial Publishers
    "reuters", "reuters.com",
    "bloomberg", "bloomberg.com",
    "economic times", "economictimes.indiatimes.com",
    "business standard", "business-standard.com",
    "cnbc", "cnbc.com", "cnbc-tv18", "cnbctv18.com",
    "moneycontrol", "moneycontrol.com",
    "ticker.in",
    "bsense", "bsense.com",
    "hindu business line", "thehindubusinessline.com",
    
    # Tier 2.5: Quality Indian Business News
    "financial express", "financialexpress.com",
    "mint", "mint.com", "livemint.com",
    "indianexpress", "indianexpress.com",
    "theprint", "theprint.in",
    "firstpost", "firstpost.com",
    
    # Tier 3: Brokerage & Research
    "tradingview", "tradingview.com",
    "bsense", "tickertape", "tickertape.in",
    "stockedge", "stockedge.com",
}


def is_finance_relevant_source(source_name: str) -> bool:
    """
    Check if a source is finance-relevant and should be included.
    Blocks generic tech/entertainment news.
    Returns True if source is acceptable, False if blocked.
    """
    if not source_name:
        return False
    
    source_lower = source_name.lower().strip()
    
    # Hard block: Generic tech/entertainment
    for blocked in BLOCKED_SOURCES:
        if blocked in source_lower:
            logger.debug(f"BLOCKED source: {source_name}")
            return False
    
    # Prefer known finance sources
    for preferred in PREFERRED_FINANCE_SOURCES:
        if preferred in source_lower:
            logger.debug(f"PREFERRED source: {source_name}")
            return True
    
    # Allow if explicitly mentions finance keywords
    finance_keywords = [
        "stock", "market", "finance", "trading", "invest",
        "equity", "share", "nse", "bse", "ticker",
        "earnings", "quarterly", "revenue", "profit",
        "analyst", "rating", "recommendation",
    ]
    
    for keyword in finance_keywords:
        if keyword in source_lower:
            logger.debug(f"FINANCE KEYWORD match: {source_name}")
            return True
    
    # Default: reject unknown sources (safe default)
    logger.debug(f"REJECTED unknown source: {source_name}")
    return False


def is_blocked_source(source_name: str) -> bool:
    if not source_name:
        return False
    source_lower = source_name.lower().strip()
    return any(blocked in source_lower for blocked in BLOCKED_SOURCES)


def company_aliases_for_ticker(ticker: str) -> list[str]:
    aliases = [ticker.lower()] if ticker else []
    try:
        json_path = Path(__file__).resolve().parents[1] / "indian_tickers.json"
        if json_path.exists():
            with json_path.open("r", encoding="utf-8") as f:
                ticker_map = json.load(f)
            aliases.extend([name for name, symbol in ticker_map.items() if symbol == ticker.upper()])
    except Exception as exc:
        logger.debug(f"Could not load ticker aliases for {ticker}: {exc}")
    return [alias.lower() for alias in aliases if alias]


def filter_news_results(news_items: list[str], ticker: str) -> tuple[list[str], list[str]]:
    """
    Filter news results to:
    1. Remove generic tech news
    2. Ensure ticker relevance
    
    Returns: (filtered_news, blocked_sources_list)
    """
    filtered = []
    blocked = []
    aliases = company_aliases_for_ticker(ticker)
    
    for item in news_items:
        item_str = str(item).lower()
        
        source = extract_news_source(item)
        
        if is_blocked_source(source):
            blocked.append(source)
            logger.warning(f"Filtering out blocked source: {source}")
            continue
        
        # Stock analysis requires ticker, company-name, or trusted finance-source relevance.
        has_entity_match = any(alias in item_str for alias in aliases)
        has_finance_source = source and is_finance_relevant_source(source)
        if ticker and not has_entity_match and not has_finance_source:
            blocked.append(source or "entity_mismatch")
            logger.warning(f"Filtering out non-company-specific news item: {str(item)[:100]}")
            continue
        
        filtered.append(item)
    
    return filtered, blocked


def extract_news_source(item: str) -> str:
    """
    Extract the publisher from news_service chunks.

    Expected format:
      [YYYY-MM-DD] Moneycontrol - Headline: Description

    The text inside [] is the publication date, not the source.
    """
    item_str = str(item).strip()
    dated_match = re.match(r"^\[[^\]]+\]\s+(.+?)\s+-\s+", item_str)
    if dated_match:
        return dated_match.group(1).strip()

    undated_match = re.match(r"^(.+?)\s+-\s+", item_str)
    if undated_match:
        return undated_match.group(1).strip()

    return ""


# -----------------------------------------------------------------------
# Intent → Data fetch strategy map
# -----------------------------------------------------------------------
FETCH_STRATEGY = {
    # intent_key         : (fetch_market, fetch_financials, fetch_news)
    "STOCK_ANALYSIS":     (True,  True,  True),
    "STOCK_MOVEMENT":     (True,  False, True),
    "MARKET_OVERVIEW":    (True,  False, False),
    "MACROECONOMIC":      (False, False, False),   # uses macro_context node
    "SENTIMENT_PULSE":    (False, False, True),
    "EDUCATIONAL":        (False, False, False),   # zero live calls
    "COMPARISON":         (True,  True,  True),
    "RESTRICTED_ADVISORY":(False, False, False),   # immediate refusal
    "GENERALIZED":        (True,  True,  True),    # safe default: full data
}

# UI blocks per intent (drives frontend rendering)
UI_BLOCKS_MAP = {
    "STOCK_ANALYSIS":      ["ExecutiveSummary", "ConfidenceGauge", "FundamentalCard", "TechnicalCard", "SentimentCard", "ScenarioCards", "RiskFactors", "Citations"],
    "STOCK_MOVEMENT":      ["MovementDrivers", "NewsTimeline", "SentimentPulse"],
    "MARKET_OVERVIEW":     ["MarketSnapshot", "SectorHeatmap"],
    "MACROECONOMIC":       ["MacroSummary", "PolicyImpact"],
    "SENTIMENT_PULSE":     ["SentimentPulse", "NewsTimeline"],
    "EDUCATIONAL":         ["EducationalExplainer", "ConceptGlossary"],
    "COMPARISON":          ["ComparisonTable", "FundamentalCard", "TechnicalCard"],
    "RESTRICTED_ADVISORY": ["SafeRefusal", "EducationalRedirect"],
    "GENERALIZED":         ["ExecutiveSummary", "ConfidenceGauge", "FundamentalCard", "TechnicalCard", "SentimentCard", "Citations"],
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _freshness_tag() -> str:
    return _now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


async def dynamic_retriever_node(state: dict) -> dict:
    """
    Intent-aware LangGraph node for data retrieval.
    
    CRITICAL FEATURE: Source filtering prevents generic tech news contamination.
    
    Reads `state['intent']` to decide WHAT data to fetch, then 
    populates `state['context']` and `state['data_freshness']`.
    
    Source filtering ensures:
    - BBC, Wired, Verge, Gizmodo, TechCrunch are BLOCKED
    - Only finance-specific sources are allowed
    - Ticker relevance is checked
    """
    intent = state.get("intent", {})
    primary_intent = intent.get("primary_intent", "GENERALIZED")
    extracted_ticker = intent.get("extracted_ticker")
    query = state.get("query", "")

    # -----------------------------------------------------------------------
    # Fast path: No live data needed
    # -----------------------------------------------------------------------
    if primary_intent in ("EDUCATIONAL", "RESTRICTED_ADVISORY"):
        logger.info(f"Intent={primary_intent}: skipping all live API calls.")
        
        debug_logger.log_retrieval_operation(
            ticker="N/A",
            intent=primary_intent,
            sources_retrieved=0,
            data_types=[],
            execution_ms=0,
        )
        
        return {
            "context": [],
            "ticker": extracted_ticker or "",
            "data_freshness": _freshness_tag(),
            "ui_blocks": UI_BLOCKS_MAP.get(primary_intent, ["EducationalExplainer"]),
        }

    # -----------------------------------------------------------------------
    # Resolve ticker
    # -----------------------------------------------------------------------
    # Priority: explicitly provided > intent classifier extraction > query extraction
    ticker = (
        state.get("ticker")
        or extracted_ticker
        or extract_ticker(query)
    )
    ticker = ticker.upper().strip() if ticker else "NIFTY"

    logger.info(f"Dynamic retriever: intent={primary_intent}, ticker={ticker}")

    fetch_market, fetch_financials, fetch_news = FETCH_STRATEGY.get(
        primary_intent, (True, True, True)
    )

    context: list[str] = []
    data_types_fetched = []
    total_sources = 0
    blocked_sources_list = []

    # -----------------------------------------------------------------------
    # Fetch market/financial data
    # -----------------------------------------------------------------------
    if fetch_market:
        try:
            market_ctx = await get_enhanced_market_context(ticker)
            context.extend(market_ctx)
            data_types_fetched.append("market_data")
            total_sources += len(market_ctx)
            logger.debug(f"Market context fetched: {len(market_ctx)} items")
        except Exception as e:
            logger.warning(f"Market data fetch failed for {ticker}: {e}")
            context.append(
                f"[DATA UNAVAILABLE] Live market data for {ticker} could not be retrieved. "
                "Confidence should be lowered accordingly."
            )

    # -----------------------------------------------------------------------
    # Fetch news with SOURCE FILTERING
    # -----------------------------------------------------------------------
    if fetch_news:
        try:
            news_ctx = await fetch_news_for_ticker(ticker)
            
            # ===== STEP 1: SOURCE FILTERING =====
            filtered_news, blocked = filter_news_results(news_ctx, ticker)
            blocked_sources_list.extend(blocked)
            
            if blocked:
                logger.warning(
                    f"Blocked {len(blocked)} non-finance sources: {set(blocked)}"
                )

            # ===== STEP 2: FRESHNESS FILTER =====
            # Drop news older than MAX_NEWS_AGE_HOURS
            cutoff = _now_utc() - timedelta(hours=MAX_NEWS_AGE_HOURS)
            fresh_news = []
            stale_count = 0
            for item in filtered_news:
                item_str = str(item)
                # Date-only news chunks do not include publication time. Treat
                # same-day items as fresh instead of converting midnight UTC
                # into an artificial stale timestamp.
                try:
                    if item_str.startswith("["):
                        date_str = item_str[1:11]
                        item_day = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if item_day >= _now_utc().date():
                            fresh_news.append(item)
                        elif datetime.combine(item_day, datetime.min.time(), tzinfo=timezone.utc) >= cutoff:
                            fresh_news.append(item)
                        else:
                            stale_count += 1
                    else:
                        fresh_news.append(item)  # No date tag → keep
                except Exception:
                    fresh_news.append(item)

            if stale_count > 0:
                logger.info(f"Filtered {stale_count} stale news items (older than {MAX_NEWS_AGE_HOURS}h)")

            if not fresh_news and filtered_news:
                # If ALL filtered news is old, keep the most recent 3 anyway with a staleness warning
                logger.warning(f"All news for {ticker} is older than {MAX_NEWS_AGE_HOURS}h. Using most recent 3.")
                fresh_news = filtered_news[:3]
                fresh_news.insert(0, f"[STALENESS WARNING] Latest news for {ticker} may be more than {MAX_NEWS_AGE_HOURS} hours old.")

            context.extend(fresh_news)
            data_types_fetched.append("news")
            total_sources += len(fresh_news)
            
            logger.info(
                f"News retrieval: fetched={len(news_ctx)}, "
                f"finance_relevant={len(filtered_news)}, "
                f"fresh={len(fresh_news)}, "
                f"blocked_sources={len(blocked)}"
            )
            
        except Exception as e:
            logger.error(f"News fetch failed for {ticker}: {e}")
            context.append(
                f"[DATA UNAVAILABLE] News context for {ticker} could not be retrieved at this moment."
            )

    # ===== DEBUG LOGGING =====
    debug_logger.log_retrieval_operation(
        ticker=ticker,
        intent=primary_intent,
        sources_retrieved=total_sources,
        data_types=data_types_fetched,
        execution_ms=0,
        filtered_sources=[c[:50] for c in context[:3]],
        blocked_sources=blocked_sources_list[:5] if blocked_sources_list else None,
    )

    return {
        "context": context,
        "ticker": ticker,
        "data_freshness": _freshness_tag(),
        "ui_blocks": UI_BLOCKS_MAP.get(primary_intent, UI_BLOCKS_MAP["GENERALIZED"]),
    }
