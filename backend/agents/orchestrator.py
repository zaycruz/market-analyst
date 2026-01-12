import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config.settings import settings
from backend.data.alpha_vantage import AlphaVantageClient
from backend.data.cot import CotClient
from backend.data.fred import FredClient
from backend.data.futures import FuturesDataClient
from backend.data.tavily import TavilyClient
from backend.models.llm import LLMClient

logger = logging.getLogger(__name__)


REQUIRED_TRADE_FIELDS = ["name", "instrument", "entry", "stop", "target"]


class MarketState:
    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.market_status = "OPEN"

        self.economic_indicators: Dict = {}
        self.risk_indicators: Dict = {}
        self.regime_analysis = ""

        self.geopolitical_events: List[Dict] = []
        self.risk_factors: List[str] = []

        self.cot_report: Dict = {}
        self.positioning: Dict = {}

        self.market_data: Dict = {}

        # Futures-specific data
        self.futures_data: Dict = {}
        self.futures_positioning: Dict = {}
        self.gamma_regime: Dict = {}
        self.key_levels: Dict = {}

        self.executive_summary = ""
        self.regime: Dict = {"label": "TRANSITIONAL", "drivers": [], "falsifiers": []}
        self.trades: List[Dict] = []
        self.positioning_analysis: Dict = {}
        self.data_quality_issues: List[str] = []
        self.confidence = 0.5

        self.thesis = ""
        self.explanation = ""
        self.recommendations: List[Dict] = []

        self.markdown_report = ""
        self.sources: List[str] = []


class MacroEconomist:
    def __init__(self, api_key: str = ""):
        self.fred = FredClient(api_key)

    def analyze(self, state: MarketState) -> MarketState:
        print("  [Macro Economist] Fetching economic data...")

        snapshot = self.fred.get_economic_snapshot()
        state.economic_indicators = snapshot

        risk_indicators = self.fred.get_risk_indicators()
        state.risk_indicators = risk_indicators

        for series_id, data in snapshot.items():
            if "source" in data:
                state.sources.append(data["source"])

        state.regime_analysis = self._determine_regime(snapshot, risk_indicators)

        print(f"  [Macro Economist] Regime: {state.regime_analysis}")
        return state

    def _determine_regime(self, data: Dict, risk: Dict) -> str:
        vix = risk.get("VIXCLS", {}).get("value")
        hy_spread = risk.get("BAMLH0A0HYM2", {}).get("value")
        curve_10y2y = risk.get("T10Y2Y", {}).get("value")

        if vix and vix > 30:
            return "CRISIS - VIX elevated, risk-off dominant"
        if hy_spread and hy_spread > 5.0:
            return "RISK_OFF - Credit stress, HY spreads widening"
        if curve_10y2y and curve_10y2y < -0.5:
            return "RISK_OFF - Yield curve deeply inverted"

        gdp = data.get("GDP", {}).get("value")
        cpi = data.get("CPIAUCSL", {}).get("value")
        unemployment = data.get("UNRATE", {}).get("value")

        if cpi and cpi > 3.5:
            if unemployment and unemployment < 4.5:
                return "TRANSITIONAL - Late-cycle, inflationary pressures"
            return "RISK_OFF - Stagflationary risk"

        if gdp and gdp > 2.5:
            if vix and vix < 15:
                return "RISK_ON - Goldilocks, low vol expansion"
            return "RISK_ON - Early-to-mid cycle expansion"

        return "TRANSITIONAL - Mixed signals"


class GeopoliticalAnalyst:
    def __init__(self, api_key: str = ""):
        self.tavily = TavilyClient(api_key)

    def analyze(self, state: MarketState) -> MarketState:
        print("  [Geopolitical Analyst] Searching for market-moving events...")

        macro_events = self.tavily.search_macro_events()

        events = []
        for topic, results in macro_events.items():
            for result in results:
                events.append(
                    {
                        "topic": topic,
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:200],
                        "source": result.get("source", ""),
                    }
                )
                if "source" in result:
                    state.sources.append(result["source"])

        state.geopolitical_events = events

        print(f"  [Geopolitical Analyst] Found {len(events)} events")
        return state


class FlowAnalyst:
    def __init__(self):
        self.cot = CotClient()

    def analyze(self, state: MarketState) -> MarketState:
        print("  [Flow Analyst] Analyzing COT positioning data...")

        cot_data = self.cot.get_latest_report()
        positioning = self.cot.get_positioning_summary()
        crowded = self.cot.get_crowded_trades()

        state.cot_report = cot_data
        state.positioning = positioning

        for asset, data in cot_data.items():
            if isinstance(data, dict) and "source" in data:
                state.sources.append(data["source"])
                break

        print(f"  [Flow Analyst] {len(crowded)} crowded trades identified")
        return state


class CommoditySpecialist:
    def __init__(self, api_key: str = ""):
        self.av = AlphaVantageClient(api_key)

    def analyze(self, state: MarketState) -> MarketState:
        print("  [Commodity Specialist] Fetching market data...")

        market_data = self.av.get_market_overview()
        state.market_data = market_data

        for symbol, data in market_data.items():
            if "source" in data:
                state.sources.append(data["source"])

        print(f"  [Commodity Specialist] Analyzed {len(market_data)} assets")
        return state


class FuturesSpecialist:
    """Specialized analysis for futures traders."""

    def __init__(self):
        self.futures = FuturesDataClient()

    def analyze(self, state: MarketState) -> MarketState:
        print("  [Futures Specialist] Analyzing futures markets...")

        # Get futures overview
        futures_data = self.futures.get_futures_overview()
        state.futures_data = futures_data

        # Get futures-specific positioning
        futures_positioning = self.futures.get_futures_positioning()
        state.futures_positioning = futures_positioning

        # Get gamma regime
        gamma_analysis = self.futures.get_market_gamma()
        state.gamma_regime = gamma_analysis
        state.futures_data = gamma_analysis

        # Extract key levels
        if "key_levels" in futures_positioning:
            state.key_levels = futures_positioning["key_levels"]

        print("  [Futures Specialist] Analyzed equity, treasury, and commodity futures")
        return state


class SynthesisAgent:
    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str = "",
        model: str = "claude-sonnet-4-20250514",
    ):
        self.llm = LLMClient(provider, api_key, model)

    def synthesize(self, state: MarketState) -> MarketState:
        print("  [Synthesis Agent] Generating thesis and recommendations...")

        result = self.llm.synthesize_research(
            economic_data=state.economic_indicators,
            geopolitical_events=state.geopolitical_events,
            positioning_data=state.positioning,
            commodity_data=state.market_data,
            market_data=state.risk_indicators,
            futures_data=state.futures_data,
            futures_positioning=state.futures_positioning,
            gamma_regime=state.gamma_regime,
            key_levels=state.key_levels,
        )

        state.executive_summary = result.get("executive_summary", "")
        state.regime = result.get(
            "regime", {"label": "TRANSITIONAL", "drivers": [], "falsifiers": []}
        )
        state.trades = result.get("trades", [])
        state.positioning_analysis = result.get("positioning_analysis", {})
        state.risk_factors = result.get("risk_factors", [])
        state.confidence = result.get("confidence", 0.5)
        state.data_quality_issues = result.get("data_quality_issues", [])

        state.thesis = result.get("executive_summary", "")
        state.recommendations = state.trades

        state.sources = list(set(state.sources))

        print(f"  [Synthesis Agent] Regime: {state.regime.get('label', 'UNKNOWN')}")
        print(f"  [Synthesis Agent] Trades: {len(state.trades)}")
        print(f"  [Synthesis Agent] Confidence: {state.confidence:.0%}")
        return state


class ReportGenerator:
    def __init__(self, reports_dir: str = "./reports"):
        self.reports_dir = reports_dir

    def generate_daily(self, state: MarketState) -> MarketState:
        print("  [Report Generator] Creating daily macro brief...")

        date_str = datetime.now().strftime("%B %d, %Y")
        timestamp = datetime.now().strftime("%H:%M:%S")

        report_parts = [
            f"# Daily Macro Brief - {date_str}",
            f"*Generated {timestamp} ET | Data as of market close*",
            "",
            "## EXECUTIVE SUMMARY",
            state.executive_summary or "Analysis pending.",
            "",
            f"**Regime: {state.regime.get('label', 'TRANSITIONAL')}**",
            "",
        ]

        drivers = state.regime.get("drivers", [])
        for driver in drivers:
            report_parts.append(f"- {driver}")

        report_parts.extend(["", "---", "", "## RISK DASHBOARD"])
        report_parts.append(self._format_risk_dashboard(state))

        report_parts.extend(["", "---", "", "## POSITIONING (COT)"])
        report_parts.append(self._format_positioning_table(state))

        report_parts.extend(["", "---", "", "## FUTURES TRADING LEVELS"])
        report_parts.append(self._format_futures_levels(state))

        report_parts.extend(["", "---", "", "## TRADE IDEAS"])
        report_parts.append(self._format_trades(state))

        report_parts.extend(["", "---", "", "## RISK FACTORS"])
        for i, risk in enumerate(state.risk_factors[:5], 1):
            report_parts.append(f"{i}. {risk}")

        falsifiers = state.regime.get("falsifiers", [])
        if falsifiers:
            report_parts.extend(["", "---", "", "## REGIME FALSIFIERS"])
            for falsifier in falsifiers:
                report_parts.append(f"- {falsifier}")

        report_parts.extend(
            [
                "",
                "---",
                "",
                f"**Confidence: {state.confidence * 10:.1f}/10**",
                "",
            ]
        )

        issues = state.data_quality_issues
        if issues:
            report_parts.append(f"*Data Quality Issues: {'; '.join(issues)}*")
        else:
            report_parts.append("*Data Quality Issues: None*")

        report_parts.extend(
            [
                "",
                "---",
                "*Report generated by Oracle - Macro Research Agent*",
            ]
        )

        state.markdown_report = "\n".join(report_parts)

        self._save_report(state.markdown_report, "daily", state.date)

        return state

    def _format_risk_dashboard(self, state: MarketState) -> str:
        lines = [
            "| Indicator | Value | Prior | Change | Signal |",
            "|-----------|-------|-------|--------|--------|",
        ]

        indicator_names = {
            "VIXCLS": "VIX",
            "BAMLC0A0CM": "IG Spread",
            "BAMLH0A0HYM2": "HY Spread",
            "T10Y2Y": "10Y-2Y",
            "T10Y3M": "10Y-3M",
        }

        for series_id, display_name in indicator_names.items():
            data = state.risk_indicators.get(series_id, {})
            if not data or "error" in data:
                lines.append(f"| {display_name} | N/A | N/A | N/A | - |")
                continue

            value = data.get("value")
            prior = data.get("prior_value")
            change = data.get("change")

            value_str = f"{value:.2f}" if value is not None else "N/A"
            prior_str = f"{prior:.2f}" if prior is not None else "N/A"

            if change is not None:
                change_str = f"{change:+.2f}"
            else:
                change_str = "N/A"

            signal = self._get_risk_signal(series_id, value, change)

            lines.append(
                f"| {display_name} | {value_str} | {prior_str} | {change_str} | {signal} |"
            )

        return "\n".join(lines)

    def _get_risk_signal(
        self, series_id: str, value: Optional[float], change: Optional[float]
    ) -> str:
        if value is None:
            return "-"

        if series_id == "VIXCLS":
            if value > 25:
                return "HIGH FEAR"
            elif value > 18:
                return "ELEVATED"
            elif value < 12:
                return "COMPLACENT"
            return "NORMAL"

        if series_id in ("BAMLC0A0CM", "BAMLH0A0HYM2"):
            if change and change > 0.1:
                return "WIDENING"
            elif change and change < -0.1:
                return "TIGHTENING"
            return "STABLE"

        if series_id in ("T10Y2Y", "T10Y3M"):
            if value < 0:
                return "INVERTED"
            elif value < 0.25:
                return "FLAT"
            return "NORMAL"

        return "-"

    def _format_positioning_table(self, state: MarketState) -> str:
        lines = [
            "| Asset | Net % OI | Percentile | WoW Change | Signal |",
            "|-------|----------|------------|------------|--------|",
        ]

        positioning = state.positioning_analysis or state.positioning

        for asset, data in positioning.items():
            if not isinstance(data, dict):
                continue

            net_pct = data.get("net_pct") or data.get("spec_net_pct", 0)
            percentile = data.get("percentile", "-")
            wow = data.get("wow_change", "-")
            signal = data.get("signal") or data.get("positioning", "NEUTRAL")

            if isinstance(net_pct, (int, float)):
                net_pct_str = f"{net_pct:.1f}%"
            else:
                net_pct_str = str(net_pct)

            if isinstance(percentile, (int, float)):
                percentile_str = f"{percentile}th"
            else:
                percentile_str = str(percentile)

            lines.append(
                f"| {asset} | {net_pct_str} | {percentile_str} | {wow} | {signal} |"
            )

        if len(lines) == 2:
            lines.append("| No positioning data available | - | - | - | - |")

        return "\n".join(lines)

    def _format_futures_levels(self, state: MarketState) -> str:
        """Format futures trading levels and key prices."""
        lines = []

        # Gamma regime
        gamma = state.gamma_regime or {}
        gamma_regime = gamma.get("gamma_regime", "NEUTRAL")
        sput_risk = gamma.get("sput_risk", "LOW")

        lines.append(f"**Gamma Regime:** {gamma_regime}  |  **SPUT Risk:** {sput_risk}")
        lines.append("")

        # Key levels table
        lines.append("| Contract | Current | Support | Resistance | Sentiment |")
        lines.append("|----------|---------|---------|------------|-----------|")

        key_levels = state.key_levels or {}

        # ES levels
        es_current = key_levels.get(
            "ES_current", key_levels.get("ES_support", [5800])[0]
        )
        es_support = key_levels.get("ES_support", [5800, 5750, 5700])
        es_resistance = key_levels.get("ES_resistance", [5900, 5950, 6000])

        # ZN levels
        zn_current = key_levels.get(
            "ZN_current", key_levels.get("ZN_support", [108])[0]
        )
        zn_support = key_levels.get("ZN_support", [108.0, 106.0, 104.0])
        zn_resistance = key_levels.get("ZN_resistance", [112.0, 114.0, 116.0])

        # VIX
        vix_current = key_levels.get("VIX_current", 15.5)

        # Get futures sentiment
        futures_pos = state.futures_positioning or {}

        equity_sentiment = futures_pos.get("equity_index_sentiment", "NEUTRAL")
        treasury_sentiment = (
            "BEARISH"
            if "LONG" in str(futures_pos.get("Treasury_positioning", ""))
            else "NEUTRAL"
        )

        # Format support as range
        es_support_str = f"{es_support[0]}-{es_support[-1]}"
        es_resistance_str = f"{es_resistance[0]}-{es_resistance[-1]}"
        zn_support_str = f"{zn_support[0]}-{zn_support[-1]}"
        zn_resistance_str = f"{zn_resistance[0]}-{zn_resistance[-1]}"

        lines.append(
            f"| ES (S&P 500) | {es_current:.0f} | {es_support_str} | {es_resistance_str} | {equity_sentiment} |"
        )
        lines.append(
            f"| ZN (10Y Note) | {zn_current:.1f} | {zn_support_str} | {zn_resistance_str} | {treasury_sentiment} |"
        )
        lines.append(
            f"| VIX | {vix_current:.1f} | 14.0 | 22.0 | {'ELEVATED' if vix_current > 18 else 'NORMAL'} |"
        )

        lines.append("")

        # Seasonality
        seasonality = futures_pos.get("seasonality", {})
        if seasonality:
            lines.append("**Seasonality:**")
            for market, season in seasonality.items():
                lines.append(f"- {market.title()}: {season}")

        return "\n".join(lines)

    def _format_trades(self, state: MarketState) -> str:
        lines = []
        valid_trade_count = 0

        for trade in state.trades:
            if not isinstance(trade, dict):
                continue

            missing_fields = [f for f in REQUIRED_TRADE_FIELDS if not trade.get(f)]
            if missing_fields:
                logger.warning(
                    f"Skipping trade missing required fields: {missing_fields}. Trade: {trade.get('name', 'unnamed')}"
                )
                continue

            valid_trade_count += 1
            lines.extend(
                [
                    f"### {valid_trade_count}. {trade.get('name', 'Unnamed Trade')}",
                    "",
                    "| Field | Value |",
                    "|-------|-------|",
                    f"| Instrument | {trade.get('instrument', 'N/A')} |",
                    f"| Direction | {trade.get('direction', 'N/A')} |",
                    f"| Entry | {trade.get('entry', 'N/A')} |",
                    f"| Stop | {trade.get('stop', 'N/A')} |",
                    f"| Target | {trade.get('target', 'N/A')} |",
                    f"| Size | {trade.get('size_pct', 'N/A')}% NAV |",
                    f"| Timeframe | {trade.get('timeframe', 'N/A')} |",
                    f"| Conviction | {trade.get('conviction', 'N/A')}/5 |",
                    "",
                    f"**Catalyst:** {trade.get('catalyst', 'Not specified')}",
                    "",
                    f"**Rationale:** {trade.get('rationale', 'Not specified')}",
                    "",
                ]
            )

        if not lines:
            return "No valid trade ideas generated."

        return "\n".join(lines)

    def _save_report(self, content: str, report_type: str, date: str):
        report_dir = os.path.join(self.reports_dir, report_type)
        os.makedirs(report_dir, exist_ok=True)

        filename = os.path.join(report_dir, f"{date}.md")

        with open(filename, "w") as f:
            f.write(content)

        print(f"  [Report Generator] Saved: {filename}")


class Oracle:
    def __init__(self):
        self.macro_economist = MacroEconomist(settings.fred_api_key)
        self.geopolitical_analyst = GeopoliticalAnalyst(settings.tavily_api_key)
        self.flow_analyst = FlowAnalyst()
        self.commodity_specialist = CommoditySpecialist(settings.alpha_vantage_api_key)
        self.futures_specialist = FuturesSpecialist()
        self.synthesis_agent = SynthesisAgent(
            settings.llm_provider,
            settings.anthropic_api_key or settings.openai_api_key,
            settings.model_primary,
        )
        self.report_generator = ReportGenerator(settings.reports_dir)

    def run_daily_brief(self) -> MarketState:
        print("\n" + "=" * 60)
        print("ORACLE - Daily Macro Brief Generation")
        print("=" * 60 + "\n")

        state = MarketState()

        print("Step 1/6: Economic Analysis")
        state = self.macro_economist.analyze(state)

        print("\nStep 2/6: Geopolitical Analysis")
        state = self.geopolitical_analyst.analyze(state)

        print("\nStep 3/6: Flow Analysis")
        state = self.flow_analyst.analyze(state)

        print("\nStep 4/6: Market Data")
        state = self.commodity_specialist.analyze(state)

        print("\nStep 5/6: Futures Analysis")
        state = self.futures_specialist.analyze(state)

        print("\nStep 6/6: Synthesis & Report Generation")
        state = self.synthesis_agent.synthesize(state)
        state = self.report_generator.generate_daily(state)

        print("\n" + "=" * 60)
        print("REPORT COMPLETE")
        print("=" * 60)
        print(f"\nRegime: {state.regime.get('label', 'UNKNOWN')}")
        print(f"Confidence: {state.confidence:.0%}")
        print(f"Trade Ideas: {len(state.trades)}")
        print(f"Sources: {len(state.sources)}")
        print(f"Report saved to: {settings.reports_dir}/daily/{state.date}.md")

        return state

    def run_research(self, query: str) -> MarketState:
        print(f"\n[Oracle] Running research: {query}\n")

        state = MarketState()
        state = self.macro_economist.analyze(state)
        state = self.flow_analyst.analyze(state)
        state = self.synthesis_agent.synthesize(state)

        return state
