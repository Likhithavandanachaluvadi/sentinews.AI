"""
Hierarchical Intent Classifier for SentiNews Dynamic Query Intelligence System.

This is the ENTRY POINT of the entire agentic pipeline.
Every user query passes through this node first, determining:
  - primary_intent: The main category of the query
  - secondary_intent: A supporting sub-category for mixed queries
  - intent_confidence: How certain we are (0.0 - 1.0)
  - query_risk_level: SEBI compliance risk (LOW, MEDIUM, HIGH)
  - complexity_level: Whether to run LIGHT or DEEP analysis
  - requires_live_data: Whether live market APIs should be called
  - extracted_ticker: Best-guess ticker from the query text

ROUTING RULES:
  - confidence < LOW_CONFIDENCE_THRESHOLD (0.65) → GENERALIZED workflow
  - query_risk_level == HIGH → Safe Refusal (no analyst nodes invoked)
  - primary_intent == RESTRICTED_ADVISORY → Immediate educational redirect
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Literal, Optional
from src.core.config import settings
from src.agents.query_risk_scoring import score_advisory_risk, QueryRiskLevel
from src.core.debug_logger import debug_logger

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.65

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class IntentClassification(BaseModel):
    """
    Hierarchical intent output from the classifier.
    Drives ALL downstream routing decisions.
    """
    primary_intent: Literal[
        "STOCK_ANALYSIS",        # Full deep-dive: fundamentals + technical + sentiment
        "STOCK_MOVEMENT",        # Why did a stock move? → price + news focus
        "MARKET_OVERVIEW",       # Broad index/sector movement
        "MACROECONOMIC",         # Inflation, interest rates, RBI, GDP
        "SENTIMENT_PULSE",       # News/social sentiment for a company/sector
        "EDUCATIONAL",           # Explain financial concepts (RSI, PE ratio, etc.)
        "COMPARISON",            # Compare two or more stocks/sectors
        "RESTRICTED_ADVISORY",   # Direct investment advice ("Should I buy?", "Give me a tip")
        "GENERALIZED",           # Ambiguous / low-confidence fallback
    ] = Field(description="Primary classification of the user query")

    secondary_intent: Optional[Literal[
        "NEWS",                  # News-driven component
        "FUNDAMENTAL",           # Valuation or financial health sub-query
        "TECHNICAL",             # Chart/price action sub-query
        "MACRO",                 # Macro overlay needed
        "NONE",
    ]] = Field(default="NONE", description="Supporting secondary classification for mixed queries")

    intent_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score in the classification (0.0 = unknown, 1.0 = certain)"
    )

    query_risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description=(
            "LOW: Educational/analytical query. "
            "MEDIUM: Borderline advisory language. "
            "HIGH: Direct investment advice request, guarantees, or SEBI-restricted language."
        )
    )

    query_risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Pattern-based advisory risk score used to tune compliance strictness"
    )

    complexity_level: Literal["LIGHT", "DEEP"] = Field(
        description=(
            "LIGHT: Simple factual/movement query. Run only 1-2 relevant agents. "
            "DEEP: Full synthesis required. Run all analyst nodes."
        )
    )

    requires_live_data: bool = Field(
        description="False for EDUCATIONAL queries — no live API calls needed"
    )

    extracted_ticker: Optional[str] = Field(
        default=None,
        description="Best-guess NSE ticker symbol extracted from the query (e.g. TCS, RELIANCE). None if not applicable."
    )

    classification_reasoning: str = Field(
        description="Short 1-2 sentence explanation of why this classification was chosen"
    )


# ---------------------------------------------------------------------------
# LLM Setup
# ---------------------------------------------------------------------------

llm_classifier = ChatGroq(
    temperature=0.0,   # Zero temperature: classification must be deterministic
    model_name="llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY
) if settings.GROQ_API_KEY else None

CLASSIFIER_SYSTEM_PROMPT = """You are a specialized Financial Query Intent Classifier for an Indian stock market AI platform.

Your ONLY task is to analyze the user's query and output a structured intent classification JSON.

CLASSIFICATION RULES:

PRIMARY INTENT DEFINITIONS:
- STOCK_ANALYSIS: Full company deep-dive ("Analyse Infosys", "Give me a research report on TCS")
- STOCK_MOVEMENT: Why did a stock move today? ("Why did Zomato fall?", "Why is Reliance up 5%?")
- MARKET_OVERVIEW: Broad market/index ("How is Nifty doing?", "What happened to small-caps today?")
- MACROECONOMIC: Macro/policy questions ("What is RBI doing with rates?", "Impact of US Fed on Indian markets")
- SENTIMENT_PULSE: Purely news/social sentiment ("What is the sentiment around HDFC?")
- EDUCATIONAL: Financial concept questions ("What is RSI?", "Explain PE ratio", "How does inflation affect stocks?")
- COMPARISON: Comparing stocks/sectors ("TCS vs Infosys", "IT vs Pharma sector comparison")
- RESTRICTED_ADVISORY: DIRECT investment advice ("Should I buy HDFC?", "Which stock will go up tomorrow?", "Give me a tip", "Guaranteed multibagger")
- GENERALIZED: When truly unclear after analysis

RISK LEVEL RULES:
- HIGH: Query contains "should I buy/sell", "guaranteed", "sure shot", "tip", "multibagger today", asking for direct trade signals
- MEDIUM: Query uses language like "is it worth investing", "is it a good time", borderline advisory
- LOW: Analytical, educational, or movement analysis queries

COMPLEXITY RULES:
- DEEP: Stock analysis, comparison queries
- LIGHT: Movement queries, educational, macro, sentiment-only, market overview

LIVE DATA RULES:
- requires_live_data = false ONLY for EDUCATIONAL intent
- requires_live_data = true for everything else

TICKER EXTRACTION:
- Extract the NSE ticker if identifiable from company name or abbreviation
- Common mappings: Reliance→RELIANCE, TCS→TCS, Zomato→ZOMATO, HDFC Bank→HDFCBANK, Infosys→INFY
- Return null if no specific company is mentioned
"""

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", CLASSIFIER_SYSTEM_PROMPT),
    ("user", "User Query: {query}\n\nClassify this query now.")
])


# ---------------------------------------------------------------------------
# Node Function
# ---------------------------------------------------------------------------

async def intent_classifier_node(state: dict) -> dict:
    """
    LangGraph node: Classifies the user query and populates intent fields in state.
    This is always the FIRST node in the graph.
    
    Performs:
    1. Query risk scoring (SEBI compliance check)
    2. Intent classification via LLM
    3. Ticker extraction
    4. Comprehensive debug logging
    """
    query = state.get("query", "")

    # Hard-coded fast path: empty query
    if not query.strip():
        logger.warning("Empty query received by intent classifier.")
        return {
            "intent": IntentClassification(
                primary_intent="GENERALIZED",
                secondary_intent="NONE",
                intent_confidence=0.0,
                query_risk_level="LOW",
                query_risk_score=0.0,
                complexity_level="LIGHT",
                requires_live_data=False,
                extracted_ticker=None,
                classification_reasoning="Empty query received.",
            ).model_dump()
        }

    # ========== STEP 1: QUERY RISK SCORING ==========
    risk_level, risk_score, detected_patterns = score_advisory_risk(query)
    
    debug_logger.log_intent_classification(
        query=query,
        primary_intent="<pending>",
        secondary_intent=None,
        intent_confidence=0.0,
        query_risk_level=risk_level.value,
        complexity_level="<pending>",
        extracted_ticker=None,
        reasoning=f"Risk Score: {risk_score:.2f}, Patterns: {len(detected_patterns)}"
    )

    if not llm_classifier:
        logger.warning("Groq API key missing — defaulting to GENERALIZED intent.")
        classification = IntentClassification(
            primary_intent="GENERALIZED",
            secondary_intent="NONE",
            intent_confidence=0.5,
            query_risk_level=risk_level.value,
            query_risk_score=risk_score,
            complexity_level="DEEP",
            requires_live_data=True,
            extracted_ticker=None,
            classification_reasoning="LLM unavailable, using safe GENERALIZED fallback.",
        )
        
        debug_logger.log_intent_classification(
            query=query,
            primary_intent=classification.primary_intent,
            secondary_intent=classification.secondary_intent,
            intent_confidence=classification.intent_confidence,
            query_risk_level=classification.query_risk_level,
            complexity_level=classification.complexity_level,
            extracted_ticker=classification.extracted_ticker,
            reasoning=classification.classification_reasoning
        )
        
        return {"intent": classification.model_dump()}

    try:
        # ========== STEP 2: LLM INTENT CLASSIFICATION ==========
        structured_llm = llm_classifier.with_structured_output(IntentClassification)
        chain = classifier_prompt | structured_llm

        classification: IntentClassification = await chain.ainvoke({"query": query})

        # ========== STEP 3: RISK LEVEL OVERRIDE ==========
        # If pattern-based risk scoring detected HIGH risk, enforce it
        if risk_level == QueryRiskLevel.HIGH:
            classification.query_risk_level = "HIGH"
            classification.query_risk_score = risk_score
            classification.primary_intent = "RESTRICTED_ADVISORY"
            logger.warning(
                f"High-risk query detected: '{query[:60]}...'\n"
                f"Detected patterns: {', '.join(detected_patterns[:3])}"
            )

        # Low confidence override
        if classification.intent_confidence < LOW_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Low confidence ({classification.intent_confidence:.2f}) for query '{query}'. "
                "Routing to GENERALIZED workflow."
            )
            classification.primary_intent = "GENERALIZED"
            classification.complexity_level = "DEEP"

        classification.query_risk_score = max(classification.query_risk_score, risk_score)

        # Override ticker with explicitly provided one if available
        if state.get("ticker") and not classification.extracted_ticker:
            classification.extracted_ticker = state["ticker"]

        # ========== DEBUG LOGGING ==========
        debug_logger.log_intent_classification(
            query=query,
            primary_intent=classification.primary_intent,
            secondary_intent=classification.secondary_intent,
            intent_confidence=classification.intent_confidence,
            query_risk_level=classification.query_risk_level,
            complexity_level=classification.complexity_level,
            extracted_ticker=classification.extracted_ticker,
            reasoning=classification.classification_reasoning
        )

        logger.info(
            f"Intent classified: primary={classification.primary_intent}, "
            f"secondary={classification.secondary_intent}, "
            f"risk={classification.query_risk_level}, "
            f"complexity={classification.complexity_level}, "
            f"confidence={classification.intent_confidence:.2f}, "
            f"ticker={classification.extracted_ticker}"
        )

        return {"intent": classification.model_dump()}

    except Exception as e:
        logger.error(f"Intent classification failed: {e}. Using safe GENERALIZED fallback.")
        fallback = IntentClassification(
            primary_intent="GENERALIZED",
            secondary_intent="NONE",
            intent_confidence=0.4,
            query_risk_level=risk_level.value,
            query_risk_score=risk_score,
            complexity_level="DEEP",
            requires_live_data=True,
            extracted_ticker=state.get("ticker"),
            classification_reasoning=f"Classification error: {str(e)[:100]}",
        )
        
        debug_logger.log_intent_classification(
            query=query,
            primary_intent=fallback.primary_intent,
            secondary_intent=fallback.secondary_intent,
            intent_confidence=fallback.intent_confidence,
            query_risk_level=fallback.query_risk_level,
            complexity_level=fallback.complexity_level,
            extracted_ticker=fallback.extracted_ticker,
            reasoning=fallback.classification_reasoning
        )
        
        return {"intent": fallback.model_dump()}
