import logging
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import ResearchState
from src.agents.schemas import TechnicalOutput
from src.core.config import settings
from src.core.debug_logger import debug_logger, NodeStatus

logger = logging.getLogger(__name__)

llm_analyst = ChatGroq(
    temperature=0.1,
    model_name="llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY
) if settings.GROQ_API_KEY else None

technical_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a SEBI-conscious Technical Analyst.
Analyze the programmatic technical indicators provided in the context.

RULES:
1. NEVER guess or calculate technical indicators yourself. Use ONLY the computed metrics provided in the Context.
2. NEVER use the words BUY, SELL, or TARGET PRICE. Instead use "Constructive Setup", "Weak Momentum", etc.
3. NEVER guarantee returns or price movements.
4. If technical data is missing, explicitly mark it as "Data Unavailable".
5. Provide a confidence score (0-100) based on the completeness of the programmatic data.

You must format your response to exactly match the requested schema."""),
    ("user", "Company Query: {query}\n\nTechnical Data Context:\n{context}")
])

async def technical_node(state: ResearchState) -> dict:
    """
    Generates technical analysis structured output.
    CRITICAL: Never returns None/null for technical_report.=
    If analysis fails, returns a partial output with low confidence.
    """
    start_time = time.time()
    query = state.get("query", "")
    existing_report = state.get("technical_report")
    intent = state.get("intent") or {}
    primary_intent = intent.get("primary_intent", "GENERALIZED")

    if primary_intent in ("EDUCATIONAL", "RESTRICTED_ADVISORY", "MACROECONOMIC", "SENTIMENT_PULSE"):
        skipped = existing_report or {
            "status": "skipped",
            "summary": "Technical analysis skipped for this query type.",
            "trend_analysis": "Analysis skipped for this query type.",
            "momentum_analysis": "Analysis skipped for this query type.",
            "key_levels": "Analysis skipped for this query type.",
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "Intent-aware workflow skipped technical analysis.",
                "missing_data_points": ["Technical workflow not required"],
            },
        }
        debug_logger.log_node_execution(
            node_name="technical",
            status=NodeStatus.SKIPPED,
            input_state={"query": query, "primary_intent": primary_intent},
            output_state={"status": "skipped"},
            execution_ms=0,
            missing_fields=["technical_report"],
        )
        return {"technical_report": skipped}
    
    if not llm_analyst:
        logger.warning("Groq API Key missing.")
        debug_logger.log_node_execution(
            node_name="technical",
            status=NodeStatus.FAILED,
            input_state={"query": query},
            output_state={},
            execution_ms=0,
            error_message="LLM not available",
        )
        if existing_report:
            return {"technical_report": existing_report}
        fallback = {
            "summary": "Technical analysis unavailable - LLM offline",
            "trend_analysis": "Data Unavailable",
            "momentum_analysis": "Data Unavailable",
            "key_levels": "Data Unavailable",
            "citations": [],
            "confidence": {
                "confidence_score": 0,
                "uncertainty_level": "High",
                "confidence_reasoning": "LLM service unavailable",
                "missing_data_points": ["All technical data"],
            }
        }
        return {"technical_report": fallback}

    try:
        context_str = "\n".join([str(c) for c in state.get("context", [])])
        
        # structured_llm = llm_analyst.with_structured_output(TechnicalOutput)
        structured_llm = llm_analyst.with_structured_output(TechnicalOutput)
        chain = technical_prompt | structured_llm

        report = await chain.ainvoke({
            "query": query,
            "context": context_str,
        })


        execution_ms = int((time.time() - start_time) * 1000)
        # confidence = report.confidence.confidence_score if report.confidence else 0
        confidence = report.confidence.confidence_score if report.confidence else 50
        debug_logger.log_node_execution(
            node_name="technical",
            status=NodeStatus.SUCCESS,
            input_state={"query": query},
            output_state={"confidence": confidence},
            execution_ms=execution_ms,
            confidence_score=confidence,
        )
        
        logger.info(f"Technical analysis completed. Confidence: {confidence}")
        # print("TECHNICAL REPORT =", str(report))
        print("TECHNICAL REPORT =", report.model_dump())
        return {"technical_report": report.model_dump()}
#         return {
#     "technical_report": {
#         "summary": str(report),
#         "trend_analysis": str(report),
#         "momentum_analysis": str(report),
#         "key_levels": str(report),
#         "citations": [],
#         "confidence": {
#             "confidence_score": 50,
#             "uncertainty_level": "Moderate",
#             "confidence_reasoning": "LLM response received",
#             "missing_data_points": []
#             print("TECHNICAL REPORT =", report.model_dump())
#         }
#     }
# }
    except Exception as e:
        execution_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Technical analysis failed: {e}")
        
        debug_logger.log_node_execution(
            node_name="technical",
            status=NodeStatus.FAILED,
            input_state={"query": query},
            output_state={},
            execution_ms=execution_ms,
            error_message=str(e),
        )
        
        if existing_report:
            return {"technical_report": existing_report}
        
        fallback = {
            "summary": "Technical analysis error",
            "trend_analysis": "Data Unavailable",
            "momentum_analysis": "Data Unavailable",
            "key_levels": "Data Unavailable",
            "citations": [],
            "confidence": {
                "confidence_score": 10,
                "uncertainty_level": "High",
                "confidence_reasoning": f"Error: {str(e)[:80]}",
                "missing_data_points": ["Error during analysis"],
            }
        }
        return {"technical_report": fallback}
