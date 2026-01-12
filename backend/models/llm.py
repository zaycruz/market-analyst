import json
import re
import urllib.request
from typing import Any, Dict, List, Optional


RESEARCH_OUTPUT_SCHEMA = {
    "executive_summary": "string: 2-3 sentences for PM 30-second read",
    "regime": {
        "label": "RISK_ON | RISK_OFF | TRANSITIONAL | CRISIS",
        "drivers": ["string: bullet with metric + direction + evidence"],
        "falsifiers": ["string: If X happens, regime changes because Y"],
    },
    "trades": [
        {
            "name": "string: e.g. 'Short EUR/USD on Crowded Positioning Unwind'",
            "instrument": "string: e.g. '6E (CME Euro FX)' or 'EUR/USD spot'",
            "direction": "LONG | SHORT",
            "conviction": "integer 1-5",
            "timeframe": "string: e.g. '1-2 weeks'",
            "entry": "string: specific price level e.g. '1.0850-1.0900'",
            "stop": "string: specific price level e.g. '1.1050'",
            "target": "string: specific price level e.g. '1.0650'",
            "size_pct": "float 0.5-5.0: recommended position size as % of NAV",
            "catalyst": "string: specific event with date",
            "rationale": "string: data-driven reasoning with specific metrics",
        }
    ],
    "risk_factors": [
        "string: specific risk with trigger condition and affected positions"
    ],
    "positioning_analysis": {
        "asset_name": {
            "net_pct": "float: net position as % of open interest",
            "percentile": "integer 0-100: historical percentile",
            "signal": "CROWDED LONG | CROWDED SHORT | ELEVATED LONG | ELEVATED SHORT | NEUTRAL",
            "wow_change": "string: week-over-week change e.g. '+2.3%'",
        }
    },
    "confidence": "float 0.0-1.0",
    "data_quality_issues": ["string: any missing data or caveats"],
}


class LLMClient:
    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str = "",
        model: str = "claude-sonnet-4-20250514",
    ):
        if not api_key:
            key_name = (
                "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
            )
            raise ValueError(
                f"LLM API key is required. Set {key_name} in your .env file. "
                f"Provider: {provider}"
            )
        self.provider = provider
        self.api_key = api_key
        self.model = model

    def generate(
        self, prompt: str, max_tokens: int = 4096, temperature: float = 0.3
    ) -> str:
        if self.provider == "anthropic":
            return self._anthropic_generate(prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return self._openai_generate(prompt, max_tokens, temperature)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. Use 'anthropic' or 'openai'."
            )

    def _anthropic_generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        url = "https://api.anthropic.com/v1/messages"

        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
                content = data.get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "")
                return ""

        except Exception as e:
            return f"LLM Error: {str(e)}"

    def _openai_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"

        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""

        except Exception as e:
            return f"LLM Error: {str(e)}"

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        schema_prompt = f"""{prompt}

## REQUIRED OUTPUT SCHEMA
You MUST output valid JSON matching this exact structure:
```json
{json.dumps(schema, indent=2)}
```

## CRITICAL CONSTRAINTS
- Output ONLY valid JSON, no markdown, no explanation, no preamble
- Every field in the schema is required unless explicitly marked optional
- If you cannot determine a field value, set it to null and add explanation to data_quality_issues
- DO NOT invent data - use null for unknown values
- Numeric fields must be numbers, not strings
- conviction must be integer 1-5
- size_pct must be float 0.5-5.0
- regime.label must be exactly one of: RISK_ON, RISK_OFF, TRANSITIONAL, CRISIS
- direction must be exactly: LONG or SHORT
"""

        response = self.generate(schema_prompt, max_tokens, temperature)
        result = self._extract_json(response)

        if result is None:
            return {
                "executive_summary": "Failed to parse LLM response",
                "regime": {"label": "TRANSITIONAL", "drivers": [], "falsifiers": []},
                "trades": [],
                "risk_factors": [],
                "positioning_analysis": {},
                "confidence": 0.0,
                "data_quality_issues": [
                    f"LLM response was not valid JSON: {response[:500]}"
                ],
            }

        return result

    def synthesize_research(
        self,
        economic_data: Dict,
        geopolitical_events: List,
        positioning_data: Dict,
        commodity_data: Dict,
        market_data: Optional[Dict] = None,
        futures_data: Optional[Dict] = None,
        futures_positioning: Optional[Dict] = None,
        gamma_regime: Optional[Dict] = None,
        key_levels: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        prompt = f"""You are the Chief Investment Strategist at a macro hedge fund. Your PM trades FUTURES and needs actionable intelligence.

## CRITICAL CONTEXT: FUTURES TRADER
- The trader primarily trades: Equity Index (ES, NQ, MES, MNQ), Treasury (ZN, ZF, ZT), Volatility (VIX), and Commodities (GC, CL, NG)
- Trades are primarily SHORT-TERM (day to few weeks)
- Position sizing is critical: recommend % of notional or contract count
- Key levels (support/resistance) are essential for trade execution
- Gamma regime and dealer positioning affects trade structure

## MARKET DATA
{json.dumps(market_data or {}, indent=2)}

## FUTURES DATA (Yahoo Finance)
{json.dumps(futures_data or {}, indent=2)}

## FUTURES POSITIONING & SENTIMENT
{json.dumps(futures_positioning or {}, indent=2)}

## GAMMA/DEALER POSITIONING
{json.dumps(gamma_regime or {}, indent=2)}

## KEY TRADING LEVELS
{json.dumps(key_levels or {}, indent=2)}

## ECONOMIC INDICATORS (FRED)
{json.dumps(economic_data, indent=2)}

## GEOPOLITICAL EVENTS & NEWS
{json.dumps(geopolitical_events, indent=2)}

## COT POSITIONING DATA
{json.dumps(positioning_data, indent=2)}

## COMMODITY DATA
{json.dumps(commodity_data, indent=2)}

## YOUR TASK
Synthesize this data into institutional-quality futures trading research.

### REGIME ASSESSMENT
- Determine current market regime: RISK_ON, RISK_OFF, TRANSITIONAL, or CRISIS
- List 3-5 key drivers with specific metrics (e.g., "VIX at 18.5, below 20 threshold")
- List 2-3 falsifiers: conditions that would change your regime call

### FUTURES TRADE RECOMMENDATIONS
Generate 3-5 specific, actionable futures trades. For EACH trade you MUST specify:
- name: Descriptive trade name (e.g., "Long ES on Dip Below 5800")
- instrument: Exact futures contract (e.g., "ES (E-mini S&P 500)", "ZN (10Y T-Note)", "VIX")
- direction: LONG or SHORT
- conviction: 1-5 integer (5 = highest conviction)
- timeframe: Expected holding period (e.g., "intraday", "1-3 days", "1-2 weeks")
- entry: Specific entry price zone or range
- stop: Specific stop-loss level
- target: Specific profit target
- size_pct: Recommended position size as % of NAV (typically 0.5-3.0 for futures)
- catalyst: Specific upcoming event or technical trigger
- rationale: Data-driven reasoning citing specific metrics from the input data

### FUTURES-SPECIFIC ANALYSIS
For each futures market, provide:
- sentiment: BULLISH, BEARISH, or NEUTRAL based on positioning and technicals
- term_structure: CONTANGO, BACKWARDATION, or FLAT (if known)
- key_level: Most important support or resistance for the day
- dealer_positioning: What are dealers likely doing (long/short)

### CRITICAL RULES FOR FUTURES
1. Entry/stop/target MUST be specific price levels near current market prices
2. Consider contract specifications (multiplier, tick size) in rationale
3. Account for gamma regime in trade structure (smaller size in high gamma)
4. Note any roll considerations for contracts near expiration
5. Include weekend risk assessment if holding overnight
6. conviction is INTEGER 1-5, not a string or decimal
7. size_pct is FLOAT between 0.5 and 3.0 (futures have leverage)
8. If data is missing for a field, set to null and add to data_quality_issues
9. Be specific: "ES at 5850" not "equities elevated"
10. Include both long and short ideas to show balanced view
"""

        return self.generate_with_schema(
            prompt, RESEARCH_OUTPUT_SCHEMA, max_tokens=8000, temperature=0.3
        )
