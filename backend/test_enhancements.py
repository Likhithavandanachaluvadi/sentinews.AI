#!/usr/bin/env python3
"""
Quick Test Script for Enhanced Fundamental Analysis
Tests the new screener.com metrics and market data pipeline
"""

import asyncio
import json
import sys
from typing import Dict, Any

# Test configurations
TEST_TICKERS = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
BACKEND_URL = "http://localhost:"

async def test_market_data_import():
    """Test if market data service loads correctly"""
    print("\n=== Testing Market Data Service ===")
    try:
        from src.services.market_data import get_enhanced_market_context, _to_nse_ticker
        print("✓ Market data service imported successfully")
        
        # Test NSE ticker conversion
        test_conversions = [
            ("RELIANCE", "RELIANCE.NS"),
            ("M&M", "M&M.NS"),
            ("BAJAJ-AUTO", "BAJAJ-AUTO.NS"),
            ("TCS", "TCS.NS"),
        ]
        
        for input_ticker, expected in test_conversions:
            result = _to_nse_ticker(input_ticker)
            assert result == expected, f"Expected {expected}, got {result}"
            print(f"✓ Ticker conversion: {input_ticker} → {result}")
        
        return True
    except Exception as e:
        print(f"✗ Market data service test failed: {e}")
        return False

async def test_screener_service_import():
    """Test if screener service loads correctly"""
    print("\n=== Testing Screener Service ===")
    try:
        from src.services.screener_service import ScreenerService, enrich_with_screener_metrics
        print("✓ Screener service imported successfully")
        
        # Check that key methods exist
        assert hasattr(ScreenerService, 'fetch_company_metrics')
        assert hasattr(ScreenerService, 'fetch_peer_comparison')
        assert hasattr(ScreenerService, 'fetch_enhanced_metrics')
        print("✓ All required screener methods exist")
        
        return True
    except Exception as e:
        print(f"✗ Screener service test failed: {e}")
        return False

async def test_enhanced_fundamental_prompt():
    """Test if enhanced fundamental prompt is correctly structured"""
    print("\n=== Testing Enhanced Fundamental Prompt ===")
    try:
        from src.agents.analysts import fundamental_prompt
        
        # Check that prompt is a ChatPromptTemplate
        assert fundamental_prompt is not None
        print("✓ Fundamental prompt loaded successfully")
        
        # Check that key metrics are mentioned in prompt
        prompt_str = str(fundamental_prompt)
        key_metrics = [
            "peg_ratio",
            "roce",
            "fcf_yield",
            "screener_key_statistics",
            "financial_health_analysis",
            "valuation_analysis",
            "competitive_position",
        ]
        
        for metric in key_metrics:
            assert metric in prompt_str.lower(), f"Metric {metric} not found in prompt"
            print(f"✓ Metric '{metric}' found in prompt")
        
        return True
    except Exception as e:
        print(f"✗ Fundamental prompt test failed: {e}")
        return False

async def test_retriever_import():
    """Test if updated retriever works"""
    print("\n=== Testing Retriever Node ===")
    try:
        from src.agents.retriever import retriever_node, extract_ticker
        print("✓ Retriever node imported successfully")
        
        # Test ticker extraction
        test_queries = [
            ("RELIANCE", "RELIANCE"),
            ("Tell me about Infosys", "INFY"),
            ("Should I invest in TCS?", "TCS"),
            ("Analyze Tata Consultancy Services", "TCS"),
        ]
        
        for query, expected_prefix in test_queries:
            ticker = extract_ticker(query)
            print(f"✓ Query extraction: '{query}' → {ticker}")
        
        return True
    except Exception as e:
        print(f"✗ Retriever test failed: {e}")
        return False

async def test_agent_imports():
    """Test if all agents import correctly"""
    print("\n=== Testing Agent Imports ===")
    try:
        from src.agents.graph import create_research_graph, research_app
        from src.agents.analysts import fundamental_node, technical_node, sentiment_node
        from src.agents.judge import judge_node
        print("✓ All agent modules imported successfully")
        
        # Check that research_app is compiled
        assert research_app is not None
        print("✓ Research graph compiled successfully")
        
        return True
    except Exception as e:
        print(f"✗ Agent import test failed: {e}")
        return False

async def test_sample_analysis():
    """Test running a sample analysis (requires backend running)"""
    print("\n=== Testing Sample Analysis (Requires Backend) ===")
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Try to call the backend
            response = await client.post(
                f"{BACKEND_URL}/api/v1/research/analyze",
                json={"query": "RELIANCE"},
                timeout=120
            )
            
            if response.status_code == 202:
                result = response.json()
                
                # Check response structure
                required_fields = [
                    "report_id", "ticker", "company_name",
                    "executive_summary", "fundamental_analysis",
                    "technical_analysis", "sentiment_analysis",
                    "conclusion", "sentiment_score"
                ]
                
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
                    print(f"✓ Response field present: {field}")
                
                # Check if fundamental analysis has new metrics
                fundamental = result.get("fundamental_analysis", "")
                new_metrics = ["peg_ratio", "roce", "fcf_yield", "screener"]
                
                found_metrics = [m for m in new_metrics if m.lower() in fundamental.lower()]
                if found_metrics:
                    print(f"✓ New metrics found in analysis: {found_metrics}")
                else:
                    print("⚠ No new metrics found (may use fallback data)")
                
                return True
            else:
                print(f"✗ Backend returned status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"⚠ Sample analysis test skipped (backend may not be running): {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("SENTINEWS AI - FUNDAMENTAL ANALYSIS ENHANCEMENT TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Run unit tests
    results["Market Data Import"] = await test_market_data_import()
    results["Screener Service Import"] = await test_screener_service_import()
    results["Fundamental Prompt"] = await test_enhanced_fundamental_prompt()
    results["Retriever Node"] = await test_retriever_import()
    results["Agent Imports"] = await test_agent_imports()
    
    # Run integration test (optional)
    results["Sample Analysis"] = await test_sample_analysis()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Fundamental analysis enhancements are working.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check logs above for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
