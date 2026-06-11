"""
Unified Response Envelope Builder
Ensures all API responses conform to the standard response schema.
Transforms LangGraph outputs into frontend-friendly UnifiedResponseEnvelope.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from src.agents.schemas import (
    UnifiedResponseEnvelope,
    IntentMeta,
    ResponseMeta,
    ConfidenceMetrics,
    EvidenceCitation,
)
from src.core.debug_logger import logger

# UI BLOCK MAPPING: Intent -> List of components to render
UI_BLOCKS_BY_INTENT = {
    "STOCK_ANALYSIS": [
        "ExecutiveSummary",
        "ConfidenceGauge",
        "FundamentalCard",
        "TechnicalCard",
        "SentimentCard",
        "ScenarioCards",
        "RiskFactors",
        "Citations",
    ],
    "STOCK_MOVEMENT": [
        "MovementDrivers",
        "NewsTimeline",
        "SentimentPulse",
        "TechnicalMomentum",
        "Citations",
    ],
    "MARKET_OVERVIEW": [
        "MarketTrends",
        "SectorPerformance",
        "NewsHighlights",
        "RiskMetrics",
    ],
    "SENTIMENT_PULSE": [
        "SentimentMeter",
        "NewsTimeline",
        "KeyThemes",
        "Warnings",
    ],
    "EDUCATIONAL": [
        "EducationalExplainer",
        "Glossary",
        "ConceptCards",
        "References",
    ],
    "COMPARISON": [
        "ComparisonTable",
        "ChartComparison",
        "Strengths",
        "Weaknesses",
    ],
    "RESTRICTED_ADVISORY": [
        "SafeRefusal",
        "EducationalRedirect",
        "DisclaimerWarning",
    ],
    "GENERALIZED": [
        "ExecutiveSummary",
        "BasicExplainer",
        "RelatedContent",
    ],
    "MACROECONOMIC": [
        "MacroIndicators",
        "CentralBankActions",
        "RegionalImpact",
        "Citations",
    ],
}

SCHEMA_VERSION = "DQI-1.0"
SECTION_NAMES = ("fundamentals", "technicals", "sentiment", "valuation")
KEY_STAT_LABELS = {
    "Market Cap",
    "Current Price",
    "High / Low",
    "Stock P/E",
    "P/E Ratio (TTM)",
    "PEG Ratio",
    "Price to Book",
    "Price/Book",
    "Book Value",
    "Dividend Yield",
    "ROCE",
    "ROE",
    "Face Value",
    "EPS (TTM)",
    "Annual Revenue",
    "Net Profit Margin",
    "Debt/Equity Ratio",
}


def _confidence_score(report: Optional[Dict[str, Any]]) -> int:
    if not isinstance(report, dict):
        return 0
    confidence = report.get("confidence") or {}
    if isinstance(confidence, dict):
        return int(confidence.get("confidence_score") or 0)
    return 0


def _is_populated(report: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(report, dict) or not report:
        return False
    if report.get("status") == "skipped":
        return False
    if _confidence_score(report) > 0:
        return True
    return any(bool(report.get(key)) for key in ("summary", "financial_health", "trend_analysis", "momentum_analysis", "key_themes"))


def _section(
    *,
    name: str,
    report: Optional[Dict[str, Any]],
    synthesis: str = "",
    freshness: Optional[str],
    skipped_reason: Optional[str] = None,
) -> Dict[str, Any]:
    populated = _is_populated(report) or bool(synthesis)
    report_status = report.get("status") if isinstance(report, dict) else None
    status = "available" if populated else "skipped" if skipped_reason or report_status == "skipped" else "unavailable"
    warning = skipped_reason or (report.get("summary") if isinstance(report, dict) and report_status == "skipped" else None) or (None if populated else "Insufficient verified data was returned for this section.")
    return {
        "status": status,
        "data": report if isinstance(report, dict) else {},
        "synthesis": synthesis or "",
        "confidence": _confidence_score(report),
        "warnings": [warning] if warning else [],
        "data_freshness": freshness,
        "source_quality": "Tier 1" if name in ("fundamentals", "technicals") and populated else "Tier 2" if populated else "Unavailable",
        "retrieval_status": "verified" if populated else "missing",
    }


def extract_key_statistics_from_context(context: Optional[List[Any]]) -> Dict[str, str]:
    """Recover legacy key metrics from yfinance/Screener context for frontend compatibility."""
    stats: Dict[str, str] = {}
    for raw in context or []:
        for line in str(raw).splitlines():
            line = line.strip().lstrip("-* ").strip()
            if ": " not in line:
                continue
            label, value = line.split(": ", 1)
            label = label.strip()
            if label in KEY_STAT_LABELS and value.strip() and value.strip() != "N/A":
                stats[label] = value.strip()
    return stats


def extract_peer_comparison_from_context(context: Optional[List[Any]]) -> str:
    """Recover peer comparison markdown emitted by market_data for valuation display."""
    required_rows = ("Market Cap", "P/E Ratio", "ROE")
    for raw in context or []:
        text = str(raw).strip()
        if "| Metric |" not in text:
            continue
        if all(row in text for row in required_rows):
            return text
    return ""


def key_statistics_markdown(stats: Dict[str, str]) -> str:
    if not stats:
        return ""
    lines = ["### Screener Key Statistics", "| Metric | Value |", "| :--- | :--- |"]
    for label, value in stats.items():
        lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def build_sections(
    *,
    intent: str,
    final_report: Optional[Dict[str, Any]],
    fundamental_report: Optional[Dict[str, Any]],
    technical_report: Optional[Dict[str, Any]],
    sentiment_report: Optional[Dict[str, Any]],
    data_freshness: Optional[str],
    context: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    final_report = final_report or {}
    key_statistics = extract_key_statistics_from_context(context)
    peer_comparison = final_report.get("peer_comparison") or extract_peer_comparison_from_context(context)
    enriched_fundamental_report = dict(fundamental_report or {})
    if key_statistics:
        enriched_fundamental_report["key_statistics"] = key_statistics
    if peer_comparison:
        enriched_fundamental_report["peer_comparison"] = peer_comparison
    skip_fundamentals = None
    skip_technicals = None
    skip_sentiment = None
    skip_valuation = None

    if intent in ("EDUCATIONAL", "RESTRICTED_ADVISORY", "MACROECONOMIC"):
        skip_fundamentals = "Analysis skipped for this query type."
        skip_technicals = "Analysis skipped for this query type."
        skip_sentiment = "Analysis skipped for this query type." if intent == "EDUCATIONAL" else None
        skip_valuation = "Analysis skipped for this query type."
    elif intent == "STOCK_MOVEMENT":
        skip_valuation = "Peer valuation is not required for movement-focused queries."

    return {
        "fundamentals": _section(
            name="fundamentals",
            report=enriched_fundamental_report,
            synthesis="\n\n".join(
                part for part in [
                    final_report.get("fundamental_synthesis", ""),
                    key_statistics_markdown(key_statistics),
                ] if part
            ),
            freshness=data_freshness,
            skipped_reason=skip_fundamentals,
        ),
        "technicals": _section(
            name="technicals",
            report=technical_report,
            synthesis=final_report.get("technical_synthesis", ""),
            freshness=data_freshness,
            skipped_reason=skip_technicals,
        ),
        "sentiment": _section(
            name="sentiment",
            report=sentiment_report,
            synthesis=final_report.get("sentiment_synthesis", ""),
            freshness=data_freshness,
            skipped_reason=skip_sentiment,
        ),
        "valuation": _section(
            name="valuation",
            report={
                "scenario_analysis": final_report.get("scenario_analysis", {}),
                "investment_thesis": final_report.get("investment_thesis", []),
                "risks": final_report.get("risk_analysis", []),
                "peer_comparison": peer_comparison,
            },
            synthesis="\n\n".join(
                part for part in [
                    peer_comparison,
                    "\n".join(final_report.get("investment_thesis", []) or []),
                ] if part
            ),
            freshness=data_freshness,
            skipped_reason=skip_valuation,
        ),
    }


def extract_citations_from_context(context: Optional[List[Any]]) -> List[Dict[str, str]]:
    citations: List[Dict[str, str]] = []
    for ctx in context or []:
        ctx_str = str(ctx).strip()
        if ctx_str.startswith("[") and " - " in ctx_str:
            try:
                date_part, rest = ctx_str.split("] ", 1)
                source_part, title_desc = rest.split(" - ", 1)
                title = title_desc.split(": ", 1)[0]
                citations.append({
                    "source_name": source_part.strip(),
                    "metric": title.strip()[:120],
                    "value": date_part[1:].strip(),
                    "trust_tier": "Tier 2",
                })
            except Exception:
                continue
        elif "financial snapshot" in ctx_str.lower() or "screener" in ctx_str.lower():
            citations.append({
                "source_name": "yFinance/Screener",
                "metric": ctx_str.splitlines()[0][:120],
                "value": "live market context",
                "trust_tier": "Tier 1",
            })
    return citations[:20]


def build_response(
    *,
    intent_data: Dict[str, Any],
    final_report: Optional[Dict[str, Any]],
    ticker: Optional[str] = None,
    query: str = "",
    execution_logs: Optional[List[Dict[str, Any]]] = None,
    ui_blocks_override: Optional[List[str]] = None,
    data_freshness: Optional[str] = None,
    generation_time_ms: int = 0,
    fundamental_report: Optional[Dict[str, Any]] = None,
    technical_report: Optional[Dict[str, Any]] = None,
    sentiment_report: Optional[Dict[str, Any]] = None,
    context: Optional[List[Any]] = None,
    warnings: Optional[List[str]] = None,
) -> UnifiedResponseEnvelope:
    """
    Transforms LangGraph output into UnifiedResponseEnvelope.
    
    Args:
        intent_data: Output from intent_classifier node (contains primary_intent, secondary_intent, etc.)
        final_report: Output from judge node (FinalEducationalReport as dict)
        ticker: Stock ticker symbol if applicable
        query: Original user query
        execution_logs: Execution logs from debug_logger if available
        ui_blocks_override: Custom UI blocks if provided
        data_freshness: Data freshness timestamp
        generation_time_ms: Total execution time in milliseconds
    
    Returns:
        UnifiedResponseEnvelope ready to send to frontend
    """
    
    # Extract intent details
    primary_intent = intent_data.get("primary_intent", "GENERALIZED")
    secondary_intent = intent_data.get("secondary_intent", "NONE")
    intent_confidence = intent_data.get("intent_confidence", 0.5)
    query_risk_level = intent_data.get("query_risk_level", "LOW")
    query_risk_score = intent_data.get("query_risk_score", 0.0)
    complexity_level = intent_data.get("complexity_level", "LIGHT")
    classification_reasoning = intent_data.get("classification_reasoning", "")
    
    # Determine UI blocks
    ui_blocks = ui_blocks_override or UI_BLOCKS_BY_INTENT.get(primary_intent, ["ExecutiveSummary"])
    
    # Build intent metadata
    intent_meta = IntentMeta(
        primary_intent=primary_intent,
        secondary_intent=secondary_intent if secondary_intent != "NONE" else None,
        intent_confidence=intent_confidence,
        query_risk_level=query_risk_level,
        query_risk_score=query_risk_score,
        complexity_level=complexity_level,
        classification_reasoning=classification_reasoning,
    )
    
    # Build response metadata
    if data_freshness is None:
        data_freshness = datetime.utcnow().isoformat()
    
    response_meta = ResponseMeta(
        report_id=str(uuid.uuid4()),
        ticker=ticker,
        data_freshness=data_freshness,
        generation_time_ms=generation_time_ms,
        created_at=datetime.utcnow().isoformat(),
    )
    
    # Extract summary and data from final report
    summary = ""
    data_payload: Dict[str, Any] = {}
    confidence_metrics: Optional[ConfidenceMetrics] = None
    citations = extract_citations_from_context(context)
    response_warnings = list(warnings or [])
    if final_report:
        final_report = dict(final_report)
        peer_comparison = final_report.get("peer_comparison") or extract_peer_comparison_from_context(context)
        if peer_comparison:
            final_report["peer_comparison"] = peer_comparison
    
    if final_report:
        summary = final_report.get("executive_summary", "Analysis completed")
        
        # Build data payload with all report sections
        data_payload = {
            "schema_version": SCHEMA_VERSION,
            "outlook": final_report.get("outlook_label", "Neutral Outlook"),
            "conviction": final_report.get("conviction_level", "Low Confidence Scenario"),
            "fundamentals": final_report.get("fundamental_synthesis", ""),
            "technicals": final_report.get("technical_synthesis", ""),
            "sentiment": final_report.get("sentiment_synthesis", ""),
            "company_overview": final_report.get("company_overview", ""),
            "investment_thesis": final_report.get("investment_thesis", []),
            "scenario_analysis": final_report.get("scenario_analysis", {}),
            "risks": final_report.get("risk_analysis", []),
            "peer_comparison": final_report.get("peer_comparison", ""),
        }
        
        # Try to extract confidence metrics
        if isinstance(final_report.get("overall_confidence_score"), int):
            confidence_metrics = ConfidenceMetrics(
                confidence_score=final_report["overall_confidence_score"],
                uncertainty_level="Low" if final_report["overall_confidence_score"] > 70 else "Moderate" if final_report["overall_confidence_score"] > 40 else "High",
                confidence_reasoning=f"Synthesis confidence based on input quality and cross-analyst agreement.",
                missing_data_points=[],
            )
    else:
        response_warnings.append("Judge synthesis was unavailable; rendering partial analyst outputs.")
        data_payload = {"schema_version": SCHEMA_VERSION}

    if primary_intent == "RESTRICTED_ADVISORY":
        summary = (
            "I cannot provide personalized investment advice or specific trade recommendations. "
            "However, this response can still provide educational context, risk factors, valuation considerations, "
            "and market evidence without making a buy or sell call."
        )
        response_warnings.append("Query contains advisory-risk language; response restricted to educational context.")

    sections = build_sections(
        intent=primary_intent,
        final_report=final_report,
        fundamental_report=fundamental_report,
        technical_report=technical_report,
        sentiment_report=sentiment_report,
        data_freshness=data_freshness,
        context=context,
    )

    for section_name, section in sections.items():
        if section["status"] != "available":
            response_warnings.extend(section.get("warnings", []))
    
    # Log response building
    logger.info(
        f"Built UnifiedResponseEnvelope: intent={primary_intent}, "
        f"ui_blocks={len(ui_blocks)}, confidence={confidence_metrics.confidence_score if confidence_metrics else 'N/A'}"
    )
    
    # Construct the unified envelope
    envelope = UnifiedResponseEnvelope(
        intent=intent_meta,
        meta=response_meta,
        summary=summary or "Analysis completed",
        data=data_payload,
        sections=sections,
        confidence=confidence_metrics,
        warnings=list(dict.fromkeys(response_warnings)),
        citations=citations,
        ui_blocks=ui_blocks,
        debug={
            "schema_version": SCHEMA_VERSION,
            "execution_logs": execution_logs or [],
            "retrieval_sources": [str(c)[:200] for c in (context or [])],
            "section_status": {name: section["status"] for name, section in sections.items()},
        },
    )
    
    return envelope
