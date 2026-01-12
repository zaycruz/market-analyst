import csv
import io
import json
import logging
import os
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CotClient:
    FUTURES_ONLY_URL = "https://www.cftc.gov/dea/newcot/deafut.txt"

    ASSET_MAPPINGS = {
        "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE": "Crude Oil",
        "GOLD - COMMODITY EXCHANGE INC.": "Gold",
        "EURO FX - CHICAGO MERCANTILE EXCHANGE": "EUR/USD",
        "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE": "S&P 500",
        "10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE": "10-Year Treasury",
        "CRUDE OIL, LIGHT SWEET": "Crude Oil",
        "GOLD": "Gold",
        "EURO FX": "EUR/USD",
        "E-MINI S&P 500": "S&P 500",
        "10-YEAR U.S. TREASURY NOTES": "10-Year Treasury",
        "10 YEAR U.S. TREASURY NOTES": "10-Year Treasury",
    }

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or "/tmp/cot_cache"
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None

    def _get_cache_path(self) -> str:
        os.makedirs(self.cache_dir, exist_ok=True)
        return os.path.join(self.cache_dir, "cot_data.json")

    def _is_cache_valid(self) -> bool:
        if self._cache_timestamp is None:
            return False

        now = datetime.now()
        cache_age = now - self._cache_timestamp

        if cache_age > timedelta(days=7):
            return False

        if now.weekday() >= 4:
            friday_4pm = now.replace(hour=16, minute=0, second=0, microsecond=0)
            if now.weekday() > 4:
                days_since_friday = now.weekday() - 4
                friday_4pm = friday_4pm - timedelta(days=days_since_friday)
            if self._cache_timestamp < friday_4pm and now >= friday_4pm:
                return False

        return True

    def _load_cache(self) -> bool:
        try:
            cache_path = self._get_cache_path()
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    cached = json.load(f)
                    self._cache = cached.get("data", {})
                    timestamp_str = cached.get("timestamp")
                    if timestamp_str:
                        self._cache_timestamp = datetime.fromisoformat(timestamp_str)
                    return True
        except Exception:
            pass
        return False

    def _save_cache(self) -> None:
        try:
            cache_path = self._get_cache_path()
            with open(cache_path, "w") as f:
                json.dump(
                    {
                        "data": self._cache,
                        "timestamp": self._cache_timestamp.isoformat()
                        if self._cache_timestamp
                        else None,
                    },
                    f,
                )
        except Exception:
            pass

    def _fetch_cot_data(self) -> str:
        try:
            req = urllib.request.Request(
                self.FUTURES_ONLY_URL,
                headers={"User-Agent": "Oracle/1.0 (Market Research Tool)"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch CFTC COT data: {str(e)}")

    def _parse_int(self, s: str) -> int:
        try:
            return int(s.strip().replace(",", "").replace('"', ""))
        except (ValueError, AttributeError):
            return 0

    def _parse_cot_row(self, row: List[str]) -> Optional[Dict[str, Any]]:
        if len(row) < 10:
            return None

        market_name = row[0].strip()

        if market_name.startswith("Market") or not market_name:
            return None

        our_asset_name = None
        for cftc_name, our_name in self.ASSET_MAPPINGS.items():
            if cftc_name.lower() in market_name.lower():
                our_asset_name = our_name
                break

        if not our_asset_name:
            return None

        date_str = row[2].strip() if len(row) > 2 else ""
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            report_date = datetime.now().strftime("%Y-%m-%d")

        open_interest = self._parse_int(row[7]) if len(row) > 7 else 0
        noncomm_long = self._parse_int(row[8]) if len(row) > 8 else 0
        noncomm_short = self._parse_int(row[9]) if len(row) > 9 else 0
        comm_long = self._parse_int(row[11]) if len(row) > 11 else 0
        comm_short = self._parse_int(row[12]) if len(row) > 12 else 0

        noncomm_net = noncomm_long - noncomm_short
        comm_net = comm_long - comm_short

        if open_interest <= 0:
            logger.warning(
                f"Skipping {our_asset_name}: invalid open_interest={open_interest}"
            )
            return None

        if abs(noncomm_net) > open_interest:
            logger.warning(
                f"Skipping {our_asset_name}: noncomm_net ({noncomm_net}) exceeds open_interest ({open_interest})"
            )
            return None

        if abs(comm_net) > open_interest:
            logger.warning(
                f"Skipping {our_asset_name}: comm_net ({comm_net}) exceeds open_interest ({open_interest})"
            )
            return None

        return {
            "asset": our_asset_name,
            "cftc_name": market_name,
            "date": report_date,
            "open_interest": open_interest,
            "noncommercial_long": noncomm_long,
            "noncommercial_short": noncomm_short,
            "noncommercial_net": noncomm_net,
            "commercial_long": comm_long,
            "commercial_short": comm_short,
            "commercial_net": comm_net,
        }

    def _analyze_positioning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        noncomm_net = data.get("noncommercial_net", 0)
        comm_net = data.get("commercial_net", 0)
        open_interest = data.get("open_interest", 1) or 1

        spec_net_pct = noncomm_net / open_interest * 100

        if spec_net_pct > 30:
            positioning = "Speculative longs at extreme - CROWDED"
            signal = "BEARISH - Contrarian"
        elif spec_net_pct > 15:
            positioning = "Speculative longs elevated"
            signal = "CAUTIOUS - Longs crowded"
        elif spec_net_pct < -30:
            positioning = "Speculative shorts at extreme - CROWDED"
            signal = "BULLISH - Contrarian"
        elif spec_net_pct < -15:
            positioning = "Speculative shorts elevated"
            signal = "CAUTIOUS - Shorts crowded"
        elif comm_net > 0 and abs(comm_net) > open_interest * 0.1:
            positioning = "Commercials net long - Smart money bullish"
            signal = "BULLISH"
        elif comm_net < 0 and abs(comm_net) > open_interest * 0.1:
            positioning = "Commercials net short - Smart money bearish"
            signal = "BEARISH"
        else:
            positioning = "Balanced positioning"
            signal = "NEUTRAL"

        data["positioning"] = positioning
        data["signal"] = signal
        data["spec_net_pct"] = round(spec_net_pct, 2)
        data["source"] = "CFTC Commitment of Traders Report"

        return data

    def _refresh_data(self) -> Dict[str, Dict[str, Any]]:
        raw_data = self._fetch_cot_data()

        parsed_data: Dict[str, Dict[str, Any]] = {}

        reader = csv.reader(io.StringIO(raw_data))
        for row in reader:
            parsed = self._parse_cot_row(row)
            if parsed:
                asset_name = parsed["asset"]
                if asset_name not in parsed_data:
                    analyzed = self._analyze_positioning(parsed)
                    parsed_data[asset_name] = analyzed

        if not parsed_data:
            raise RuntimeError(
                "Failed to parse any COT data from CFTC. "
                "The data format may have changed."
            )

        self._cache = parsed_data
        self._cache_timestamp = datetime.now()
        self._save_cache()

        return parsed_data

    def get_latest_report(self, asset: str = "") -> Dict[str, Any]:
        try:
            if not self._cache:
                self._load_cache()

            if not self._cache or not self._is_cache_valid():
                self._refresh_data()

            if asset:
                if asset in self._cache:
                    return self._cache[asset]
                for cached_asset in self._cache:
                    if asset.lower() in cached_asset.lower():
                        return self._cache[cached_asset]
                return {
                    "error": f"Asset '{asset}' not found in COT data. "
                    f"Available: {list(self._cache.keys())}"
                }

            return self._cache

        except Exception as e:
            return {
                "error": f"Failed to get COT data: {str(e)}",
                "source": "CFTC Commitment of Traders Report",
            }

    def get_positioning_summary(self) -> Dict[str, Dict]:
        data = self.get_latest_report()

        if "error" in data:
            return {"error": data["error"]}

        summary = {}
        for asset_name, info in data.items():
            if isinstance(info, dict) and "positioning" in info:
                summary[asset_name] = {
                    "positioning": info["positioning"],
                    "signal": info["signal"],
                    "spec_net_pct": info.get("spec_net_pct", 0),
                    "date": info.get("date"),
                    "source": info.get("source", "CFTC COT"),
                }

        return summary

    def get_crowded_trades(self) -> List[Dict[str, Any]]:
        data = self.get_latest_report()

        if "error" in data:
            return [{"error": data["error"]}]

        crowded = []
        for asset_name, info in data.items():
            if isinstance(info, dict) and "CROWDED" in info.get("positioning", ""):
                crowded.append(
                    {
                        "asset": asset_name,
                        "positioning": info["positioning"],
                        "signal": info["signal"],
                        "spec_net_pct": info.get("spec_net_pct", 0),
                        "risk": "HIGH - Vulnerable to reversal",
                        "date": info.get("date"),
                    }
                )

        return crowded

    def get_asset_history(self, asset: str, weeks: int = 4) -> Dict[str, Any]:
        return {
            "error": "Historical COT data not yet implemented. "
            "Would require parsing CFTC historical compressed files.",
            "asset": asset,
            "weeks_requested": weeks,
        }
