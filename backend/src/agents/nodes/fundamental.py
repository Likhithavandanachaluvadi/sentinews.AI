from itertools import chain
import logging
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import ResearchState
from src.agents.schemas import FundamentalOutput
from src.core.config import settings
from src.core.debug_logger import debug_logger, NodeStatus

logger = logging.getLogger(__name__)

llm_analyst = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY
)if settings.GROQ_API_KEY else None

fundamental_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a SEBI-conscious Fundamental Analyst.
Analyze the provided company context strictly relying on the data provided.

RULES:
1. NEVER use the words BUY, SELL, or TARGET PRICE.
2. NEVER guarantee returns.
3. If data is missing for a section, explicitly mark it as "Data Unavailable" in the uncertainty/missing fields.
4. ONLY cite data actually present in the provided context. Do NOT hallucinate financial ratios or historical facts.
5. Provide a confidence score (0-100) based on the completeness and tier of the data sources.

You must format your response to exactly match the requested schema."""),
    ("user", "Company Query: {query}\n\nContext & Data:\n{context}")
])

async def fundamental_node(state: ResearchState) -> dict:
    """
    Generates fundamental analysis structured output.
    
    CRITICAL: Never returns None/null for fundamental_report.
    If analysis fails, returns a partial output with low confidence.
    """
    start_time = time.time()
    query = state.get("query", "")
    existing_report = state.get("fundamental_report")
    intent = state.get("intent") or {}
    primary_intent = intent.get("primary_intent", "GENERALIZED")
    secondary_intent = intent.get("secondary_intent", "NONE")
    ticker = state.get("ticker") or intent.get("extracted_ticker")
    has_stock_ticker = bool(ticker and str(ticker).strip())

    if primary_intent in ("EDUCATIONAL", "RESTRICTED_ADVISORY", "MACROECONOMIC", "SENTIMENT_PULSE", "MARKET_OVERVIEW") or (
        primary_intent == "STOCK_MOVEMENT" and secondary_intent != "FUNDAMENTAL" and not has_stock_ticker
    ):
        skipped = existing_report or {
            "status": "skipped",
            "summary": "Fundamental analysis skipped for this query type.",
            "financial_health": "Analysis skipped for this query type.",
            "competitive_moat": "Analysis skipped for this query type.",
            "key_factors": [],
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "Intent-aware workflow skipped deep fundamentals.",
                "missing_data_points": ["Fundamental workflow not required"],
            },
        }
        debug_logger.log_node_execution(
            node_name="fundamental",
            status=NodeStatus.SKIPPED,
            input_state={"query": query, "primary_intent": primary_intent},
            output_state={"status": "skipped"},
            execution_ms=0,
            missing_fields=["fundamental_report"],
        )
        return {"fundamental_report": skipped}
    
    if not llm_analyst:
        logger.warning("Groq API Key missing.")
        
        debug_logger.log_node_execution(
            node_name="fundamental",
            status=NodeStatus.FAILED,
            input_state={"query": query, "context_items": len(state.get("context", []))},
            output_state={"fundamental_report": None},
            execution_ms=0,
            error_message="LLM not available",
        )
        
        # Return existing report if available, never return None
        if existing_report:
            return {"fundamental_report": existing_report}
        
        # Fallback: minimal report with low confidence
        fallback = {
            "summary": "Fundamental analysis unavailable - LLM service offline",
            "financial_health": "Data Unavailable",
            "competitive_moat": "Data Unavailable",
            "key_factors": [],
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "LLM service unavailable",
                "missing_data_points": ["All fundamental data"],
            }
        }
        return {"fundamental_report": fallback}

    try:
        context_str = "\n".join(state.get("context", []))

        # Use structured output to enforce the FundamentalOutput schema
        structured_llm = llm_analyst.with_structured_output(FundamentalOutput)
        chain = fundamental_prompt | structured_llm

        report: FundamentalOutput = await chain.ainvoke({
            "query": query,
            "context": context_str,
        })
    #     structured_llm = llm_analyst
    #     chain = fundamental_prompt | structured_llm

    #     report = await chain.ainvoke({
    # "query": query,
    # "context": context_str,
    #     })
    #     execution_ms = int((time.time() - start_time) * 1000)
    #     confidence = 50  # Placeholder confidence score
        
        execution_ms = int((time.time() - start_time) * 1000)
        # derive confidence if available on the response
        try:
            confidence = int(report.confidence.confidence_score)  # type: ignore
        except Exception:
            confidence = 50

        debug_logger.log_node_execution(
            node_name="fundamental",
            status=NodeStatus.SUCCESS,
            input_state={"query": query, "context_items": len(state.get("context", []))},
            output_state={"confidence": confidence, "citations": len(getattr(report, 'citations', []) or [])},
            execution_ms=execution_ms,
            citations_count=len(getattr(report, 'citations', []) or []),
            confidence_score=confidence,
        )
        
        logger.info(f"Fundamental analysis completed. Confidence: {confidence}")

        # Store as dict in state
        try:
            report_dict = report.model_dump()
        except Exception:
            # fallback if report is already a dict-like or string
            try:
                report_dict = dict(report)
            except Exception:
                report_dict = {"summary": str(report)}

        return {"fundamental_report": report_dict}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        execution_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Fundamental analysis failed: {e}")
        
        debug_logger.log_node_execution(
            node_name="fundamental",
            status=NodeStatus.FAILED,
            input_state={"query": query, "context_items": len(state.get("context", []))},
            output_state={"error": str(e)},
            execution_ms=execution_ms,
            error_message=str(e),
        )
        
        # CRITICAL: Never return None. Return partial output with low confidence.
        if existing_report:
            return {"fundamental_report": existing_report}
        
        fallback = {
            "summary": "Fundamental analysis encountered an error",
            "financial_health": "Data Unavailable",
            "competitive_moat": "Data Unavailable",
            "key_factors": [],
            "citations": [],
            "confidence": {
                "confidence_score": 10,
                "uncertainty_level": "High",
                "confidence_reasoning": f"Analysis failed: {str(e)[:100]}",
                "missing_data_points": ["Error during analysis"],
            }
        }
        return {"fundamental_report": fallback}
