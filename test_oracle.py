#!/usr/bin/env python3

import sys
import os


def test_imports():
    print("Testing imports...")

    from backend.config.settings import settings

    assert settings.app_name == "Oracle"
    print("  [PASS] Settings imported")

    from backend.data.fred import FredClient
    from backend.data.tavily import TavilyClient
    from backend.data.cot import CotClient
    from backend.data.alpha_vantage import AlphaVantageClient

    print("  [PASS] Data clients imported")

    from backend.models.llm import LLMClient

    print("  [PASS] LLM client imported")

    from backend.agents.orchestrator import Oracle, MarketState

    print("  [PASS] Orchestrator imported")

    return True


def test_data_clients():
    print("\nTesting data clients...")

    from backend.config.settings import settings
    from backend.data.fred import FredClient

    fred = FredClient(api_key=settings.fred_api_key)
    result = fred.get_series("FEDFUNDS", limit=1)
    assert "value" in result and result["value"] is not None
    print(f"  [PASS] FRED: Fed Funds Rate = {result['value']}")

    from backend.data.cot import CotClient

    cot = CotClient()
    report = cot.get_latest_report()
    assert len(report) > 0
    print(f"  [PASS] COT: {len(report)} assets")

    from backend.data.alpha_vantage import AlphaVantageClient

    av = AlphaVantageClient(api_key=settings.alpha_vantage_api_key)
    quote = av.get_quote("SPY")
    assert "price" in quote and quote["price"] > 0
    print(f"  [PASS] Alpha Vantage: SPY = ${quote['price']}")

    from backend.data.tavily import TavilyClient

    tavily = TavilyClient(api_key=settings.tavily_api_key)
    results = tavily.search("Federal Reserve", max_results=2)
    assert len(results) > 0
    print(f"  [PASS] Tavily: {len(results)} results")

    return True


def test_llm_client():
    print("\nTesting LLM client...")

    from backend.config.settings import settings
    from backend.models.llm import LLMClient

    llm = LLMClient(
        provider="anthropic",
        api_key=settings.anthropic_api_key,
        model=settings.model_primary,
    )

    response = llm.generate("In one word, what color is the sky?", max_tokens=10)
    assert len(response) > 0
    print(f"  [PASS] LLM response: {response.strip()}")

    return True


def test_orchestrator():
    print("\nTesting orchestrator...")

    from backend.agents.orchestrator import Oracle, MarketState

    oracle = Oracle()
    print("  [PASS] Oracle instantiated")

    state = MarketState()
    assert state.date is not None
    print("  [PASS] MarketState created")

    return True


def test_full_pipeline():
    print("\nTesting full pipeline (daily brief)...")

    from backend.agents.orchestrator import Oracle

    oracle = Oracle()
    state = oracle.run_daily_brief()

    assert state.thesis is not None and len(state.thesis) > 0
    print(f"  [PASS] Thesis generated: {state.thesis[:50]}...")

    assert state.confidence > 0
    print(f"  [PASS] Confidence: {state.confidence:.0%}")

    assert len(state.recommendations) > 0
    print(f"  [PASS] Recommendations: {len(state.recommendations)}")

    assert len(state.sources) > 0
    print(f"  [PASS] Sources: {len(state.sources)}")

    assert len(state.markdown_report) > 0
    print(f"  [PASS] Report: {len(state.markdown_report)} chars")

    from backend.config.settings import settings

    report_path = f"{settings.reports_dir}/daily/{state.date}.md"
    assert os.path.exists(report_path)
    print(f"  [PASS] Report saved: {report_path}")

    return True


def main():
    print("=" * 60)
    print("ORACLE - Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Data Clients", test_data_clients),
        ("LLM Client", test_llm_client),
        ("Orchestrator", test_orchestrator),
        ("Full Pipeline", test_full_pipeline),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
