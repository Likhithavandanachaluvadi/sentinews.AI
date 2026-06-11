import logging
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import ResearchState
from src.agents.schemas import SentimentOutput
from src.core.config import settings
from src.core.debug_logger import debug_logger, NodeStatus

logger = logging.getLogger(__name__)

llm_analyst = ChatGroq(
    temperature=0.1,
    model_name="llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY
) if settings.GROQ_API_KEY else None

sentiment_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a SEBI-conscious Sentiment Analyst.
Analyze the provided news and social sentiment context.

RULES:
1. NEVER use the words BUY, SELL, or TARGET PRICE.
2. Maintain objectivity. Rate sentiment based strictly on the language in the provided news headlines.
3. If news data is missing, explicitly mark it as "Data Unavailable".
4. Provide a confidence score (0-100). If the only sources are Tier 3 (blogs) or missing, lower your confidence.

You must format your response to exactly match the requested schema."""),
    ("user", "Company Query: {query}\n\nNews Context:\n{context}")
])

async def sentiment_node(state: ResearchState) -> dict:
    """
    Generates sentiment analysis structured output.
    CRITICAL: Never returns None/null for sentiment_report.
    If analysis fails, returns a partial output with low confidence.
    """
    start_time = time.time()
    query = state.get("query", "")
    existing_report = state.get("sentiment_report")
    intent = state.get("intent") or {}
    primary_intent = intent.get("primary_intent", "GENERALIZED")

    if primary_intent in ("EDUCATIONAL", "RESTRICTED_ADVISORY", "MACROECONOMIC", "MARKET_OVERVIEW"):
        skipped = existing_report or {
            "status": "skipped",
            "summary": "Sentiment analysis skipped for this query type.",
            "sentiment_score": 50,
            "key_themes": [],
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "Intent-aware workflow skipped sentiment retrieval.",
                "missing_data_points": ["Sentiment workflow not required"],
            },
        }
        debug_logger.log_node_execution(
            node_name="sentiment",
            status=NodeStatus.SKIPPED,
            input_state={"query": query, "primary_intent": primary_intent},
            output_state={"status": "skipped"},
            execution_ms=0,
            missing_fields=["sentiment_report"],
        )
        return {"sentiment_report": skipped}
    
    if not llm_analyst:
        logger.warning("Groq API Key missing.")
        debug_logger.log_node_execution(
            node_name="sentiment",
            status=NodeStatus.FAILED,
            input_state={"query": query},
            output_state={},
            execution_ms=0,
            error_message="LLM not available",
        )
        if existing_report:
            return {"sentiment_report": existing_report}
        fallback = {
            "summary": "Sentiment analysis unavailable - LLM offline",
            "sentiment_score": 50,
            "key_themes": [],
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "LLM service unavailable",
                "missing_data_points": ["All news data"],
            }
        }
        return {"sentiment_report": fallback}

    try:
        context_str = "\n".join([str(c) for c in state.get("context", []) if "News" in str(c) or "[" in str(c)])
        if not context_str.strip():
            context_str = "No recent news available."
            
        structured_llm = llm_analyst.with_structured_output(SentimentOutput)
        chain = sentiment_prompt | structured_llm

        report: SentimentOutput = await chain.ainvoke({
            "query": query,
            "context": context_str,
        })
        
        execution_ms = int((time.time() - start_time) * 1000)
        confidence = report.confidence.confidence_score if report.confidence else 0
        
        debug_logger.log_node_execution(
            node_name="sentiment",
            status=NodeStatus.SUCCESS,
            input_state={"query": query},
            output_state={"confidence": confidence},
            execution_ms=execution_ms,
            confidence_score=confidence,
        )
        
        logger.info(f"Sentiment analysis completed. Confidence: {confidence}")
        return {"sentiment_report": report.model_dump()}

    except Exception as e:
        execution_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Sentiment analysis failed: {e}")
        
        debug_logger.log_node_execution(
            node_name="sentiment",
            status=NodeStatus.FAILED,
            input_state={"query": query},
            output_state={},
            execution_ms=execution_ms,
            error_message=str(e),
        )
        
        if existing_report:
            return {"sentiment_report": existing_report}
        
        fallback = {
            "summary": "Sentiment analysis error",
            "sentiment_score": 50,
            "key_themes": [],
            "citations": [],
            "confidence": {
                "confidence_score": 10,
                "uncertainty_level": "High",
                "confidence_reasoning": f"Error: {str(e)[:80]}",
                "missing_data_points": ["Error during analysis"],
            }
        }
        return {"sentiment_report": fallback}
