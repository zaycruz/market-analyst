import json
import urllib.request
import urllib.parse
from typing import Dict, Any


class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str = ""):
        if not api_key:
            raise ValueError(
                "Alpha Vantage API key is required. Set ALPHA_VANTAGE_API_KEY in your .env file. "
                "Get a free key at: https://www.alphavantage.co/support/#api-key"
            )
        self.api_key = api_key

    def _request(self, params: Dict[str, str]) -> Dict[str, Any]:
        params["apikey"] = self.api_key
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Oracle/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        params = {"function": "GLOBAL_QUOTE", "symbol": symbol}

        data = self._request(params)

        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%"),
                "volume": int(quote.get("06. volume", 0)),
                "latest_trading_day": quote.get("07. latest trading day"),
                "source": f"Alpha Vantage ({symbol})",
            }

        return {
            "symbol": symbol,
            "error": data.get("Note", "No data"),
            "source": "Alpha Vantage",
        }

    def get_market_overview(self) -> Dict[str, Dict]:
        symbols = ["SPY", "QQQ", "TLT", "GLD", "USO"]

        results = {}
        for symbol in symbols:
            results[symbol] = self.get_quote(symbol)

        return results
