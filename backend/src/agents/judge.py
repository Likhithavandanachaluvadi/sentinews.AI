"""
Chief Investment Officer / Judge Node
Synthesizes the expert analyst reports into a SEBI-compliant educational report.
Uses strictly typed Pydantic output.

CRITICAL FIXES:
- Properly detects report content before saying "null"
- Never says a report is null if data is present
- Synthesizes partial outputs correctly
- Logs all decisions for debugging
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import ResearchState
from src.agents.schemas import FinalEducationalReport
from src.core.config import settings
from src.core.debug_logger import debug_logger, NodeStatus
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

llm = ChatGroq(
    temperature=0.2,
    model_name="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY
) if settings.GROQ_API_KEY else None

judge_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Principal Financial Educator and Systems Architect.
Your task is to synthesize the verified specialist analyst reports (Fundamental, Technical, and Sentiment) into a single, cohesive educational research report.

CRITICAL RULES:
1. NO INVESTMENT ADVICE. Do not use words like "BUY", "SELL", or "TARGET PRICE". 
2. Use safe educational outlooks (e.g. "Positive Long-Term Outlook").
3. DO NOT hallucinate numbers. Use the numbers provided in the reports.
4. Output MUST conform exactly to the provided JSON schema.
5. Provide a balanced scenario analysis (Bull, Base, Bear).
6. If any section is missing data, say "Insufficient data available for this analysis".
7. NEVER say a section is null if ANY data was provided for it.

If the Verifier found contradictions, explain them in the risk analysis or executive summary.
"""),
    ("user", """SPECIALIST ANALYST REPORTS:

FUNDAMENTAL REPORT:
{fundamental_report}

TECHNICAL REPORT:
{technical_report}

SENTIMENT REPORT:
{sentiment_report}

VERIFIER FEEDBACK:
{verifier_feedback}

Original User Query: {query}

IMPORTANT: Check if reports have ANY content before deciding they are "null".
If summary or any field exists, the report is NOT null.
""")
])

def is_report_populated(report: dict) -> bool:
    """Check if a report has actual content (not just empty dict)."""
    if not report:
        return False
    if report.get("content"):
        return True
    
    # Check for key fields that indicate actual content
    # key_fields = ["summary", "confidence", "key_themes", "trend_analysis"]
    key_fields = [
    "summary",
    "content",
    "confidence",
    "key_themes",
    "trend_analysis"
]
    for field in key_fields:
        if field in report and report[field]:
            # Special check: confidence object should have a score
            if field == "confidence":
                if isinstance(report[field], dict) and report[field].get("confidence_score", 0) > 0:
                    return True
            else:
                return True
    
    return False


def _fallback_final_report(state: ResearchState, reason: str) -> dict:
    """Build a SEBI-safe partial synthesis when the judge LLM is unavailable."""
    fund_report = state.get("fundamental_report") or {}
    tech_report = state.get("technical_report") or {}
    sent_report = state.get("sentiment_report") or {}
    populated = [r for r in (fund_report, tech_report, sent_report) if is_report_populated(r)]
    confidence_scores = [
        int((r.get("confidence") or {}).get("confidence_score") or 0)
        for r in populated
        if isinstance(r, dict)
    ]
    overall_conf = int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 20
    return {
        "outlook_label": "Neutral Outlook",
        "conviction_level": "Low Confidence Scenario",
        "executive_summary": (
            "A partial educational analysis is available. Some synthesis components "
            f"could not be completed: {reason}"
        ),
        "company_overview": fund_report.get("summary") or "Company overview is unavailable from verified data.",
        "investment_thesis": [
            item for item in [
                fund_report.get("summary"),
                tech_report.get("summary"),
                sent_report.get("summary"),
            ] if item
        ][:5],
        "fundamental_synthesis": fund_report.get("summary") or "Insufficient data available for this analysis.",
        "technical_synthesis": tech_report.get("summary") or "Insufficient data available for this analysis.",
        "sentiment_synthesis": sent_report.get("summary") or "Insufficient data available for this analysis.",
        "scenario_analysis": {
            "bull_case": "Constructive outcomes depend on verified fundamentals, market conditions, and execution.",
            "base_case": "Use available evidence as educational context, not personalized investment advice.",
            "bear_case": "Missing or stale data materially reduces confidence in the analysis.",
        },
        "risk_analysis": [reason, "Partial data can omit material risks and recent events."],
        "data_freshness": state.get("data_freshness") or datetime.utcnow().isoformat(),
        "overall_confidence_score": overall_conf,
        "sebi_disclaimer": "This is AI-generated educational research for informational purposes only. It does NOT constitute SEBI-registered investment advice. Past performance is not indicative of future results.",
    }

async def judge_node(state: ResearchState) -> dict:
    """
    Synthesizes the verified reports into a final educational JSON report.
    
    CRITICAL: Properly detects which reports are populated before synthesis.
    """
    start_time = time.time()
    
    if not llm:
        logger.warning("Groq API Key missing.")
        
        debug_logger.log_node_execution(
            node_name="judge",
            status=NodeStatus.FAILED,
            input_state={},
            output_state={},
            execution_ms=0,
            error_message="LLM not available",
        )
        
        return {"final_report": _fallback_final_report(state, "Judge LLM service unavailable")}
    
    try:
        # ===== STEP 1: DETECT POPULATED REPORTS =====
        fund_report = state.get("fundamental_report", {})
        tech_report = state.get("technical_report", {})
        sent_report = state.get("sentiment_report", {})
        
        fund_populated = is_report_populated(fund_report)
        tech_populated = is_report_populated(tech_report)
        sent_populated = is_report_populated(sent_report)
        
        logger.info(
            f"Judge report detection: Fund={fund_populated}, Tech={tech_populated}, Sent={sent_populated}"
        )
        
        # ===== STEP 2: PREPARE REPORTS FOR SYNTHESIS =====
        fund_report_json = json.dumps(fund_report, indent=2)
        tech_report_json = json.dumps(tech_report, indent=2)
        sent_report_json = json.dumps(sent_report, indent=2)
        ver_feedback = json.dumps(state.get("reflection_feedback", {}), indent=2)
        
        # ===== STEP 3: INVOKE JUDGE =====
        structured_llm = llm.with_structured_output(FinalEducationalReport)
        chain = judge_prompt | structured_llm
        
        report: FinalEducationalReport = await chain.ainvoke({
            "fundamental_report": fund_report_json,
            "technical_report": tech_report_json,
            "sentiment_report": sent_report_json,
            "verifier_feedback": ver_feedback,
            "query": state.get("query", ""),
        })
        
        # ===== STEP 4: CALCULATE OVERALL CONFIDENCE =====
        overall_conf = 50
        confs = []
        
        if fund_populated and "confidence" in fund_report:
            fund_conf = fund_report["confidence"].get("confidence_score", 0)
            if fund_conf:
                confs.append(fund_conf)
        
        if tech_populated and "confidence" in tech_report:
            tech_conf = tech_report["confidence"].get("confidence_score", 0)
            if tech_conf:
                confs.append(tech_conf)
        
        if sent_populated and "confidence" in sent_report:
            sent_conf = sent_report["confidence"].get("confidence_score", 0)
            if sent_conf:
                confs.append(sent_conf)
        
        if confs:
            overall_conf = sum(confs) // len(confs)
        
        report.overall_confidence_score = overall_conf
        report.data_freshness = datetime.utcnow().isoformat()
        
        # ===== STEP 5: DEBUG LOGGING =====
        execution_ms = int((time.time() - start_time) * 1000)
        
        sections_populated = []
        if fund_populated:
            sections_populated.append("fundamentals")
        if tech_populated:
            sections_populated.append("technicals")
        if sent_populated:
            sections_populated.append("sentiment")
        
        sections_missing = []
        if not fund_populated:
            sections_missing.append("fundamentals")
        if not tech_populated:
            sections_missing.append("technicals")
        if not sent_populated:
            sections_missing.append("sentiment")
        
        debug_logger.log_synthesis_result(
            outlook_label=report.outlook_label,
            conviction_level=report.conviction_level,
            overall_confidence=overall_conf,
            sections_populated=sections_populated,
            sections_missing=sections_missing,
            synthesis_quality="high" if len(sections_populated) >= 2 else "partial",
        )
        
        debug_logger.log_node_execution(
            node_name="judge",
            status=NodeStatus.SUCCESS,
            input_state={
                "query": state.get("query", "")[:50],
                "reports_available": {
                    "fundamental": fund_populated,
                    "technical": tech_populated,
                    "sentiment": sent_populated,
                }
            },
            output_state={
                "outlook": report.outlook_label,
                "confidence": overall_conf,
                "sections": sections_populated,
            },
            execution_ms=execution_ms,
            confidence_score=overall_conf,
        )
        
        logger.info(
            f"Judge synthesis completed. Outlook: {report.outlook_label} | "
            f"Conviction: {report.conviction_level} | Confidence: {overall_conf}% | "
            f"Sections: {len(sections_populated)} populated"
        )
        
        return {"final_report": report.model_dump()}
        
    except Exception as e:
        execution_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Judge synthesis failed: {e}")
        
        debug_logger.log_node_execution(
            node_name="judge",
            status=NodeStatus.FAILED,
            input_state={},
            output_state={},
            execution_ms=execution_ms,
            error_message=str(e),
        )
        
        return {"final_report": _fallback_final_report(state, f"Judge synthesis failed: {str(e)[:120]}")}
