import json
import urllib.request
import urllib.parse
from typing import Dict, List, Any
from datetime import datetime, timedelta


class FredClient:
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str = ""):
        if not api_key:
            raise ValueError(
                "FRED API key is required. Set FRED_API_KEY in your .env file. "
                "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        self.api_key = api_key

    def _request(self, endpoint: str, params: Dict[str, str]) -> Dict[str, Any]:
        params["api_key"] = self.api_key
        params["file_type"] = "json"

        url = f"{self.BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Oracle/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def get_series(self, series_id: str, limit: int = 10) -> Dict[str, Any]:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        params = {
            "series_id": series_id,
            "observation_start": start_date,
            "observation_end": end_date,
            "sort_order": "desc",
            "limit": str(limit),
        }

        data = self._request("series/observations", params)

        if "error" in data:
            return {
                "series": series_id,
                "value": None,
                "error": data["error"],
                "source": f"FRED (series: {series_id})",
            }

        observations = data.get("observations", [])
        if not observations:
            return {
                "series": series_id,
                "value": None,
                "error": "No observations",
                "source": f"FRED (series: {series_id})",
            }

        latest = observations[0]
        prior = observations[1] if len(observations) > 1 else None

        try:
            value = float(latest["value"]) if latest["value"] != "." else None
            prior_value = (
                float(prior["value"]) if prior and prior["value"] != "." else None
            )
        except (ValueError, TypeError):
            value = None
            prior_value = None

        return {
            "series": series_id,
            "value": value,
            "date": latest.get("date"),
            "prior_value": prior_value,
            "prior_date": prior.get("date") if prior else None,
            "change": value - prior_value if value and prior_value else None,
            "source": f"FRED (series: {series_id})",
        }

    def get_economic_snapshot(self) -> Dict[str, Dict]:
        indicators = {
            "GDP": "Gross Domestic Product",
            "CPIAUCSL": "Consumer Price Index",
            "UNRATE": "Unemployment Rate",
            "FEDFUNDS": "Federal Funds Rate",
            "T10Y2Y": "10Y-2Y Treasury Spread",
            "T10Y3M": "10Y-3M Treasury Spread",
            "DGS10": "10-Year Treasury Rate",
            "DEXUSEU": "USD/EUR Exchange Rate",
            "DCOILWTICO": "WTI Crude Oil Price",
            "VIXCLS": "CBOE Volatility Index (VIX)",
            "BAMLC0A0CM": "ICE BofA US Corporate IG Spread",
            "BAMLH0A0HYM2": "ICE BofA US High Yield Spread",
        }

        results = {}
        for series_id, name in indicators.items():
            data = self.get_series(series_id)
            data["name"] = name
            results[series_id] = data

        return results

    def get_risk_indicators(self) -> Dict[str, Dict]:
        indicators = {
            "VIXCLS": "CBOE Volatility Index (VIX)",
            "BAMLC0A0CM": "ICE BofA US Corporate IG Spread",
            "BAMLH0A0HYM2": "ICE BofA US High Yield Spread",
            "T10Y2Y": "10Y-2Y Treasury Spread",
            "T10Y3M": "10Y-3M Treasury Spread",
        }

        results = {}
        for series_id, name in indicators.items():
            data = self.get_series(series_id)
            data["name"] = name
            results[series_id] = data

        return results
