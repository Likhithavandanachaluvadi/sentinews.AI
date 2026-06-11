from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

# ==========================================
# Core Confidence & Evidence Structures
# ==========================================

class EvidenceCitation(BaseModel):
    """Represents a validated citation for a factual claim."""
    source_name: str = Field(description="Name of the source (e.g., 'yFinance', 'Screener.in', 'Reuters')")
    metric: str = Field(description="The exact metric or fact cited")
    value: str = Field(description="The value of the metric")
    trust_tier: Literal["Tier 1", "Tier 2", "Tier 3"] = Field(
        description="Tier 1: Primary data (NSE, RBI, SEC). Tier 2: Reputable media (Reuters). Tier 3: Opinion/Blogs"
    )

class ConfidenceMetrics(BaseModel):
    """Standardized confidence scoring for all agents."""
    confidence_score: int = Field(ge=0, le=100, description="Confidence score from 0 to 100")
    uncertainty_level: Literal["Low", "Moderate", "High"] = Field(description="Level of uncertainty due to missing or conflicting data")
    confidence_reasoning: str = Field(description="Explanation of why this confidence level was chosen")
    missing_data_points: List[str] = Field(default_factory=list, description="List of important data points that were missing from context")

# ==========================================
# Specific Analyst Output Schemas
# ==========================================

class FundamentalOutput(BaseModel):
    summary: str = Field(description="Executive summary of fundamental health")
    financial_health: str = Field(description="Analysis of revenue, profit, margins, and debt")
    competitive_moat: str = Field(description="Analysis of competitive advantages")
    key_factors: List[str] = Field(description="Key fundamental drivers")
    citations: List[EvidenceCitation] = Field(description="Evidence supporting fundamental claims")
    confidence: ConfidenceMetrics

class TechnicalOutput(BaseModel):
    summary: str = Field(description="Summary of programmatic technical indicators")
    trend_analysis: str = Field(description="Analysis of SMAs, MACD, and price action")
    momentum_analysis: str = Field(description="Analysis of RSI and volume trends")
    key_levels: str = Field(description="Support and resistance levels")
    citations: List[EvidenceCitation] = Field(description="Evidence based on programmatic technical data")
    confidence: ConfidenceMetrics

class SentimentOutput(BaseModel):
    summary: str = Field(description="Summary of recent news and social sentiment")
    sentiment_score: int = Field(ge=0, le=100, description="0 (Extremely Negative) to 100 (Extremely Positive)")
    key_themes: List[str] = Field(description="Recurring themes in recent news")
    citations: List[EvidenceCitation] = Field(description="Citations of specific news articles")
    confidence: ConfidenceMetrics

# ==========================================
# Verifier & Reflection Output Schemas
# ==========================================

class VerificationOutput(BaseModel):
    """Output of the Verifier Agent acting as a reliability gate."""
    is_valid: bool = Field(description="True if all claims are supported and no SEBI violations exist")
    contradictions_found: List[str] = Field(default_factory=list, description="Contradictions between different analyst reports")
    hallucinations_detected: List[str] = Field(default_factory=list, description="Claims made without supporting evidence in context")
    sebi_violations: List[str] = Field(default_factory=list, description="Uses of banned words like BUY, SELL, GUARANTEED")
    feedback_for_reflection: str = Field(description="Instructions for analysts if re-run is needed")

# ==========================================
# Final Judge / Synthesis Schema
# ==========================================

class ScenarioAnalysis(BaseModel):
    bull_case: str = Field(description="Optimistic educational scenario")
    base_case: str = Field(description="Most likely educational scenario")
    bear_case: str = Field(description="Pessimistic educational scenario")

class FinalEducationalReport(BaseModel):
    """The final SEBI-compliant educational intelligence report."""
    outlook_label: Literal[
        "Positive Long-Term Outlook", 
        "Neutral Outlook", 
        "Elevated Risk Outlook", 
        "Constructive Momentum", 
        "Weak Momentum"
    ] = Field(description="SEBI-safe educational outlook label")
    
    conviction_level: Literal["High Conviction", "Moderate Conviction", "Low Confidence Scenario"]
    
    executive_summary: str = Field(description="Crisp, high-impact summary of the educational analysis")
    
    company_overview: str
    investment_thesis: List[str] = Field(description="Key educational drivers (3-5 bullet points)")
    
    fundamental_synthesis: str
    technical_synthesis: str
    sentiment_synthesis: str
    
    scenario_analysis: ScenarioAnalysis
    
    risk_analysis: List[str] = Field(description="Major risks that could cause the thesis to fail")
    
    data_freshness: str = Field(description="Timestamp of when the latest data was retrieved")
    overall_confidence_score: int = Field(ge=0, le=100)
    
    sebi_disclaimer: str = Field(
        default="This is AI-generated educational research for informational purposes only. It does NOT constitute SEBI-registered investment advice. Past performance is not indicative of future results."
    )


# ==========================================
# Unified Response Envelope
# ==========================================

class IntentMeta(BaseModel):
    """Intent and risk metadata for the response."""
    primary_intent: str
    secondary_intent: Optional[str] = "NONE"
    intent_confidence: float
    query_risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    query_risk_score: float = 0.0
    complexity_level: Literal["LIGHT", "DEEP"]
    classification_reasoning: str

class ResponseMeta(BaseModel):
    """Operational metadata for the response."""
    report_id: str
    ticker: Optional[str] = None
    data_freshness: str
    generation_time_ms: int
    created_at: str

class UnifiedResponseEnvelope(BaseModel):
    """
    The SINGLE predictable JSON structure returned by ALL API responses.
    
    The frontend only needs to handle this one shape.
    The `ui_blocks` list tells the frontend EXACTLY which components to render.
    
    Example ui_blocks by intent:
      STOCK_ANALYSIS:  ["ExecutiveSummary", "ConfidenceGauge", "FundamentalCard", "TechnicalCard", "SentimentCard", "ScenarioCards", "RiskFactors", "Citations"]
      STOCK_MOVEMENT:  ["MovementDrivers", "NewsTimeline", "SentimentPulse"]
      EDUCATIONAL:     ["EducationalExplainer", "Glossary"]
      RESTRICTED_ADVISORY: ["SafeRefusal", "EducationalRedirect"]
    """
    intent: IntentMeta
    meta: ResponseMeta
    summary: str = Field(description="Plain-language summary of the response")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic payload — content varies by intent")
    sections: Dict[str, Any] = Field(default_factory=dict, description="Stable report sections; every expected section is always present")
    confidence: Optional[ConfidenceMetrics] = None
    warnings: List[str] = Field(default_factory=list)
    citations: List[EvidenceCitation] = Field(default_factory=list)
    ui_blocks: List[str] = Field(
        description="Ordered list of UI component names the frontend should render"
    )
    debug: Optional[Dict[str, Any]] = Field(default=None, description="Internal debugging dashboard payload")
    sebi_disclaimer: str = Field(
        default="This is AI-generated educational research for informational purposes only. "
                "It does NOT constitute SEBI-registered investment advice. "
                "Past performance is not indicative of future results."
    )
