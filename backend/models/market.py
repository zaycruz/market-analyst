from typing import Dict, List, Optional


class MarketState:
    date: str
    market_status: str

    economic_indicators: Optional[Dict] = None
    regime_analysis: Optional[str] = None

    geopolitical_events: Optional[List[Dict]] = None
    risk_factors: Optional[List[str]] = None

    cot_report: Optional[Dict] = None
    positioning: Optional[Dict] = None
    credit_spreads: Optional[Dict] = None

    commodity_data: Optional[Dict] = None
    supply_demand: Optional[Dict] = None

    market_snapshot: Optional[Dict] = None
    thesis: Optional[str] = None
    recommendations: Optional[List[str]] = None
    confidence: Optional[float] = None

    markdown_report: Optional[str] = None


class EconomicIndicator:
    series: str
    value: float
    prior: Optional[float] = None
    expected: Optional[float] = None
    source: str


class GeopoliticalEvent:
    event: str
    impact: str
    affected_assets: List[str]
    trading_implication: str
    source: str
    date: str


class Recommendation:
    trade_idea: str
    direction: str
    conviction: str
    rationale: str
    ticker: Optional[str] = None
    target: Optional[float] = None


class ReportMetadata:
    date: str
    type: str
    title: str
    sources: List[str]
    generated_at: str
    confidence: float
