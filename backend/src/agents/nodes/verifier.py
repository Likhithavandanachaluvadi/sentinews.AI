import logging
import json
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import ResearchState
from src.agents.schemas import VerificationOutput
from src.core.config import settings
from src.core.debug_logger import debug_logger, NodeStatus

logger = logging.getLogger(__name__)

llm_verifier = ChatGroq(
    temperature=0.0,  # Zero temperature for strict verification
    model_name="llama-3.3-70b-versatile", # Use the best model for verification
    api_key=settings.GROQ_API_KEY
) if settings.GROQ_API_KEY else None

verifier_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the SEBI Compliance & Reliability Verifier.
Your job is to read the outputs from the Fundamental, Technical, and Sentiment analysts and cross-check them against each other and the original context.

RULES FOR REJECTION (is_valid = False):
1. SEBI Violations: If ANY analyst uses words like "BUY", "SELL", "TARGET PRICE", or guarantees returns.
2. Contradictions: If the Fundamental analyst says the company is highly profitable, but the Technical analyst claims it's going bankrupt, you must flag it.
3. Hallucinations: If a specific financial number (e.g., "Revenue is 500 Cr") is cited but is NOT present in the provided context.

If there are any violations, set is_valid to False and provide feedback_for_reflection.
If everything is clean, objective, and SEBI-compliant, set is_valid to True.
"""),
    ("user", "Query: {query}\n\nOriginal Context:\n{context}\n\n---\n\nFundamental Report:\n{fundamental}\n\nTechnical Report:\n{technical}\n\nSentiment Report:\n{sentiment}")
])

async def verifier_node(state: ResearchState) -> dict:
    """
    Acts as a reliability gate, checking for hallucinations and compliance.
    
    CRITICAL: Never nulls out report sections. Downgrade confidence instead.
    If a report has issues, flag it but preserve the output with warnings.
    """
    start_time = time.time()
    
    if not llm_verifier:
        logger.warning("Groq API Key missing. Skipping verification.")
        
        debug_logger.log_node_execution(
            node_name="verifier",
            status=NodeStatus.SKIPPED,
            input_state={},
            output_state={},
            execution_ms=0,
            error_message="Verifier LLM not available",
        )
        
        # Fallback bypass - never null out reports
        return {"reflection_feedback": None}

    try:
        context_str = "\n".join([str(c) for c in state.get("context", [])])
        
        # Read the reports - NEVER null check here, use empty dicts
        fund_report = json.dumps(state.get("fundamental_report", {}))
        tech_report = json.dumps(state.get("technical_report", {}))
        sent_report = json.dumps(state.get("sentiment_report", {}))
        
        structured_llm = llm_verifier.with_structured_output(VerificationOutput)
        chain = verifier_prompt | structured_llm

        verification: VerificationOutput = await chain.ainvoke({
            "query": state.get("query", ""),
            "context": context_str,
            "fundamental": fund_report,
            "technical": tech_report,
            "sentiment": sent_report
        })
        
        execution_ms = int((time.time() - start_time) * 1000)
        
        # Log verification results
        debug_logger.log_verifier_feedback(
            is_valid=verification.is_valid,
            contradictions=verification.contradictions_found or [],
            hallucinations=verification.hallucinations_detected or [],
            sebi_violations=verification.sebi_violations or [],
            feedback=verification.feedback_for_reflection or "No issues found",
        )
        
        debug_logger.log_node_execution(
            node_name="verifier",
            status=NodeStatus.SUCCESS if verification.is_valid else NodeStatus.PARTIAL,
            input_state={"query": state.get("query", "")},
            output_state={
                "is_valid": verification.is_valid,
                "issues_found": len(verification.contradictions_found or []) + len(verification.hallucinations_detected or []),
            },
            execution_ms=execution_ms,
            validation_errors=verification.hallucinations_detected or [],
        )
        
        logger.info(
            f"Verification completed. Is Valid: {verification.is_valid} | "
            f"Contradictions: {len(verification.contradictions_found or [])} | "
            f"Hallucinations: {len(verification.hallucinations_detected or [])} | "
            f"SEBI Violations: {len(verification.sebi_violations or [])}"
        )
        
        # Store feedback in state. The graph will use this to determine if it should reflect or proceed.
        return {"reflection_feedback": verification.model_dump()}

    except Exception as e:
        execution_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Verification failed: {e}")
        
        debug_logger.log_node_execution(
            node_name="verifier",
            status=NodeStatus.FAILED,
            input_state={},
            output_state={},
            execution_ms=execution_ms,
            error_message=str(e),
        )
        
        # On failure, allow pass-through to prevent pipeline blockage
        # Never null out reports - they are valuable even if unverified
        return {"reflection_feedback": None}
