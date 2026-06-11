"""
Production security middleware:
- JWT authentication dependency
- Rate limiting with tier-based limits
- Input validation & sanitization
- Comprehensive error handling
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.session import get_session
from src.models.user import User
from src.core.security import verify_token
from jose import JWTError
from typing import Optional
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

class RateLimitConfig:
    """Rate limit configuration by user tier."""
    # Free tier: 10 requests per minute
    FREE_LIMIT = "10/minute"
    # Premium tier: 100 requests per minute
    PREMIUM_LIMIT = "100/minute"
    # Admin/System: Unlimited (no limit applied)
    ADMIN_LIMIT = "1000/minute"

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Validate JWT token and retrieve current user from database.
    
    Dependencies:
    - HTTPBearer token extraction
    - JWT verification
    - Database lookup
    
    Raises:
        HTTPException: 401 if token invalid/expired
        HTTPException: 404 if user not found
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    
    try:
        token_data = verify_token(token)
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        result = await session.execute(
            select(User).where(User.id == token_data.sub)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Database lookup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Optional authentication - returns user if token provided, None otherwise.
    Useful for endpoints that work for both authenticated and public users.
    """
    if credentials is None:
        return None
    
    return await get_current_user(credentials, session)

def get_user_rate_limit(user: User) -> str:
    """
    Determine rate limit based on user tier.
    
    Args:
        user: User object with is_premium flag
    
    Returns:
        Rate limit string (e.g., "10/minute" or "100/minute")
    """
    if user.is_premium:
        return RateLimitConfig.PREMIUM_LIMIT
    return RateLimitConfig.FREE_LIMIT

async def validate_ticker(ticker: str) -> str:
    """
    Validate and sanitize ticker symbol.
    
    Args:
        ticker: Ticker string to validate
    
    Returns:
        Uppercase sanitized ticker
    
    Raises:
        ValueError: If ticker is invalid
    """
    ticker = ticker.upper().strip()
    
    # Validate: 1-15 characters supporting global and Indian (NSE) tickers
    if not ticker or len(ticker) > 15:
        raise ValueError(f"Invalid ticker: {ticker}")
    
    import re
    if not re.match(r"^[A-Z0-9&\-._]+$", ticker):
        raise ValueError(f"Ticker must contain only letters, numbers, and symbols like & or -: {ticker}")
    
    return ticker

async def validate_query(query: str, max_length: int = 500) -> str:
    """
    Validate and sanitize user query.
    Enforces the single-company constraint.
    """
    query = query.strip()
    
    if not query or len(query) == 0:
        raise ValueError("Query cannot be empty")
    
    if len(query) > max_length:
        raise ValueError(f"Query exceeds {max_length} character limit")
    
    # Remove potentially dangerous characters (but allow & for stocks like M&M)
    dangerous_chars = ["<", ">", ";", "$", "`", "|"]
    for char in dangerous_chars:
        if char in query:
            raise ValueError(f"Query contains invalid character: {char}")
            
    # Check if user query references multiple companies
    query_lower = query.lower()
    
    # Try to load the indian_tickers.json mapping to check how many unique companies are matched
    import json
    import os
    import re
    
    json_path = "c:\\Users\\sunny\\OneDrive\\Desktop\\Sentinews.AI\\backend\\src\\indian_tickers.json"
    matched_tickers = set()
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                ticker_map = json.load(f)
            
            # Clean common connectors to split composite checks
            cleaned_query = query_lower
            for connector in [" vs ", " versus ", " compared to ", " compare ", " and ", " or "]:
                cleaned_query = cleaned_query.replace(connector, " ")
            
            # Check each name key in the mapping (longer keys first to prevent partial match splits)
            sorted_keys = sorted(ticker_map.keys(), key=len, reverse=True)
            temp_query = cleaned_query
            for name_key in sorted_keys:
                pattern = rf"\b{re.escape(name_key)}\b"
                if re.search(pattern, temp_query):
                    matched_tickers.add(ticker_map[name_key])
                    temp_query = re.sub(pattern, " ", temp_query)
        except Exception as e:
            logger.warning(f"Error parsing indian_tickers.json during query validation: {e}")
            
    # Check for multiple all-caps words that look like stock tickers
    all_caps_words = re.findall(r"\b[A-Z]{2,10}\b", query)
    skip_words = {"THE", "IS", "AND", "FOR", "OF", "IN", "TO", "A", "AN", "AT", "BY", "VS", "OR", "BUY", "NSE", "BSE"}
    for word in all_caps_words:
        if word not in skip_words:
            matched_tickers.add(word)
            
    # Check for comparison indicators with one or more matched tickers
    comparison_indicators = [" vs ", " versus ", " compare ", " comparison ", " compared to "]
    has_comparison_word = any(indicator in query_lower for indicator in comparison_indicators)
    
    if len(matched_tickers) > 1 or (has_comparison_word and len(matched_tickers) >= 1):
        raise ValueError("Please proceed with only one stock or company at a time.")
    
    return query

async def handle_rate_limit_exceeded(request, exc):
    """
    Custom handler for rate limit exceeded errors.
    Returns proper JSON response instead of default HTML.
    """
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Free tier: 10/min, Premium: 100/min",
    )
