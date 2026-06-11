"""
Financial analysis endpoints.
Main research endpoint that uses the LangGraph workflow to analyze stocks.
Includes rate limiting, database persistence, and citation support.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import time
import logging
from datetime import datetime
import json

from src.database.session import get_session
from src.models.user import User
from src.models.report import GeneratedReport
from src.core.middleware import (
    get_current_user,
    get_current_user_optional,
    validate_ticker,
    validate_query,
    limiter,
    RateLimitConfig,
)
from src.agents.graph import research_app
from src.core.config import settings
from src.core.debug_logger import start_workflow_logging, get_debug_summary
from src.services.response_builder import build_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["research"])

# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Stock analysis request."""
    query: str = Field(..., min_length=1, max_length=500)
    ticker: Optional[str] = Field(None, pattern=r"^[A-Z]{1,5}$")

class Citation(BaseModel):
    """Citation/source reference."""
    title: str
    source: str
    url: str
    published_at: str

class ScenarioAnalysis(BaseModel):
    bull_case: str
    base_case: str
    bear_case: str

class AnalysisResponse(BaseModel):
    """Complete educational analysis response."""
    report_id: str
    ticker: str
    company_name: Optional[str]
    
    outlook_label: str
    conviction_level: str
    
    executive_summary: str
    company_overview: str
    investment_thesis: List[str]
    
    fundamental_synthesis: str
    technical_synthesis: str
    sentiment_synthesis: str
    
    scenario_analysis: ScenarioAnalysis
    risk_analysis: List[str]
    
    citations: List[Citation] = []
    data_freshness: str
    overall_confidence_score: int
    sebi_disclaimer: str
    
    generation_time_ms: int
    created_at: str
    
    class Config:
        from_attributes = True

class AnalysisStatus(BaseModel):
    """Status check response."""
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    estimated_time_remaining_ms: Optional[int] = None

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(RateLimitConfig.FREE_LIMIT)
async def analyze_stock(
    request: Request,
    req_data: AnalysisRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """
    Analyze a stock using the full LangGraph workflow.
    
    Flow:
    1. Validate input
    2. Fetch real-time data (yfinance + NewsAPI)
    3. Run parallel analysis (Fundamental, Technical, Sentiment)
    4. Synthesize into final report
    5. Save to database
    6. Return complete analysis
    
    Rate limits:
    - Free tier: 10/minute
    - Premium tier: 100/minute
    """
    
    try:
        # Always use the smart Indian market extractor from retriever
        # This handles: "analyse tcs", "reliance", "TCS", "Tata Consultancy", etc.
        from src.agents.retriever import extract_ticker
        
        if req_data.ticker:
            # If user explicitly provided a ticker, use it directly (already validated by Pydantic)
            ticker = req_data.ticker.upper().strip()
        else:
            # Extract ticker from natural language query
            ticker = extract_ticker(req_data.query)
        
        query = await validate_query(req_data.query)
        
        user_email = current_user.email if current_user else "guest"
        logger.info(f"Analysis request: ticker={ticker}, user={user_email}")
        
        # Start timing and per-request debug capture
        start_time = time.time()
        start_workflow_logging()
        
        # Execute the research graph
        # This runs: Retriever → [Fundamental, Technical, Sentiment] in parallel → Judge
        result = await research_app.ainvoke({
            "query": query,
            "ticker": ticker,
            "intent": None,
            "context": [],
            "retrieval_intent": None,
            "data_freshness": None,
            "ui_blocks": [],
            "fundamental_report": {},
            "technical_report": {},
            "sentiment_report": {},
            "reflection_feedback": None,
            "iteration_count": 0,
            "final_report": {},
            "execution_logs": [],
        })
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        debug_summary = get_debug_summary()

        # Extract components from result
        final_report = result.get("final_report", {})
        
        if isinstance(final_report, str):
            # If judge returned string instead of JSON, wrap it
            final_report = {
                "executive_summary": "Analysis complete",
                "fundamental_section": final_report[:500],
                "technical_section": "",
                "sentiment_section": "",
                "conclusion": final_report,
                "risk_disclaimer": "This is AI-generated educational research, NOT investment advice.",
            }
        
        # Extract sentiment score
        sentiment_data = result.get("sentiment_report", {})
        sentiment_score = sentiment_data.get("sentiment_score", 0) if isinstance(sentiment_data, dict) else 0
        
        # Build citations (from context)
        citations = []
        for ctx in result.get("context", []):
            ctx_str = str(ctx).strip()
            if ctx_str.startswith("[") and " - " in ctx_str:
                try:
                    # Parse example format: "[2026-05-19] Google News - Article Title: Article Desc"
                    date_part, rest = ctx_str.split("] ", 1)
                    date_str = date_part[1:]  # strip leading '['
                    
                    source_part, title_desc = rest.split(" - ", 1)
                    
                    if ": " in title_desc:
                        title_str, _ = title_desc.split(": ", 1)
                    else:
                        title_str = title_desc
                    
                    citations.append(Citation(
                        title=title_str.strip(),
                        source=source_part.strip(),
                        url="",
                        published_at=date_str.strip(),
                    ))
                except Exception:
                    citations.append(Citation(
                        title=ctx_str[:120],
                        source="News Outlet",
                        url="",
                        published_at=datetime.utcnow().isoformat()[:10],
                    ))
            elif "overview" in ctx_str.lower() or "financial snapshot" in ctx_str.lower():
                citations.append(Citation(
                    title=f"yfinance Live Financial Database Node ({ticker.upper()})",
                    source="yfinance",
                    url=f"https://finance.yahoo.com/quote/{ticker.upper()}.NS",
                    published_at=datetime.utcnow().isoformat()[:10],
                ))
        
        final_data_freshness = None
        if isinstance(final_report, dict):
            final_data_freshness = result.get("data_freshness") or final_report.get("data_freshness")

        envelope = build_response(
            intent_data=result.get("intent") or {},
            final_report=final_report if isinstance(final_report, dict) else {},
            ticker=result.get("ticker") or ticker,
            query=query,
            execution_logs=debug_summary.get("nodes", []) if isinstance(debug_summary, dict) else [],
            ui_blocks_override=result.get("ui_blocks") or None,
            data_freshness=final_data_freshness,
            generation_time_ms=generation_time_ms,
            fundamental_report=result.get("fundamental_report") if isinstance(result.get("fundamental_report"), dict) else {},
            technical_report=result.get("technical_report") if isinstance(result.get("technical_report"), dict) else {},
            sentiment_report=result.get("sentiment_report") if isinstance(result.get("sentiment_report"), dict) else {},
            context=result.get("context") or [],
            warnings=[],
        )
        
        # Persist to database if authenticated user
        if current_user:
            await save_report_to_db(
                current_user.id,
                ticker,
                query,
                final_report,
                citations,
                sentiment_score,
                generation_time_ms,
                session,
            )
        
        return envelope.model_dump()
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again.",
        )

@router.get("/history")
async def get_analysis_history(
    ticker: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """
    Get user's analysis history with optional ticker filter.
    Supports pagination.
    """
    try:
        query = select(GeneratedReport).where(
            GeneratedReport.user_id == current_user.id
        )
        
        if ticker:
            query = query.where(GeneratedReport.ticker == ticker.upper())
        
        # Total count
        count_result = await session.execute(
            select(GeneratedReport).where(GeneratedReport.user_id == current_user.id)
        )
        total = len(count_result.scalars().all())
        
        # Paginated results
        results = await session.execute(
            query.order_by(GeneratedReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        reports = results.scalars().all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "reports": [
                {
                    "report_id": str(r.id),
                    "ticker": r.ticker,
                    "query": r.query,
                    "sentiment_score": r.sentiment_score,
                    "created_at": r.created_at.isoformat(),
                    "generation_time_ms": r.generation_time_ms,
                }
                for r in reports
            ]
        }
        
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analysis history",
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def save_report_to_db(
    user_id: str,
    ticker: str,
    query: str,
    final_report: Dict,
    citations: List[Citation],
    sentiment_score: int,
    generation_time_ms: int,
    session: AsyncSession,
):
    """Save analysis report to database (background task)."""
    try:
        report = GeneratedReport(
            user_id=user_id,
            ticker=ticker,
            query=query,
            final_report=json.dumps(final_report),
            fundamental_report=final_report.get("fundamental_section"),
            technical_report=final_report.get("technical_section"),
            sentiment_report=final_report.get("sentiment_section"),
            citations=[c.model_dump() for c in citations],
            sentiment_score=sentiment_score,
            generation_time_ms=generation_time_ms,
        )
        
        session.add(report)
        await session.commit()
        logger.info(f"Report saved for {ticker}")
        
    except Exception as e:
        logger.error(f"Failed to save report: {e}")

def generate_report_id() -> str:
    """Generate unique report ID."""
    import uuid
    return str(uuid.uuid4())

def extract_company_name(report: Dict) -> Optional[str]:
    """Extract company name from report."""
    # Try to extract from executive summary
    text = report.get("executive_summary", "")
    if text and len(text) > 0:
        # Simple heuristic: first capitalized word
        words = text.split()
        for w in words:
            if w[0].isupper() and len(w) > 1:
                return w.rstrip(".,;:")
    return None
