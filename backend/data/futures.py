"""
Futures-specific data for traders.
Includes micro e-minis, VIX futures, bond futures, and commodity futures.
Enhanced with gamma regime analysis, dealer positioning, and term structure.
"""

import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf

    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

logger = logging.getLogger(__name__)

# Key futures contracts relevant to macro/futures traders
FUTURES_CONTRACTS = {
    "MES": "Micro E-mini S&P 500",
    "MNQ": "Micro E-mini Nasdaq-100",
    "MYM": "Micro E-mini Dow",
    "M2K": "Micro E-mini Russell 2000",
    "ES": "E-mini S&P 500",
    "NQ": "E-mini Nasdaq-100",
    "YM": "E-mini Dow",
    "RTY": "E-mini Russell 2000",
    "VIX": "VIX Index",
    "VXM": "Micro VIX",
    "ZN": "10-Year T-Note",
    "ZB": "30-Year T-Bond",
    "ZF": "5-Year T-Note",
    "ZT": "2-Year T-Note",
    "CL": "Crude Oil WTI",
    "NG": "Natural Gas",
    "RB": "RBOB Gasoline",
    "HO": "Heating Oil",
    "GC": "Gold",
    "SI": "Silver",
    "HG": "Copper",
    "PL": "Platinum",
    "PA": "Palladium",
    "ZC": "Corn",
    "ZS": "Soybeans",
    "ZW": "Wheat",
    "ZL": "Soybean Oil",
    "ZM": "Soybean Meal",
    "6E": "Euro",
    "6B": "British Pound",
    "6J": "Japanese Yen",
    "6A": "Australian Dollar",
    "6C": "Canadian Dollar",
    "6S": "Swiss Franc",
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
}

# Futures term structure contracts by symbol
# Yahoo Finance only provides front month futures data
TERM_STRUCTURE_CONTRACTS = {
    "ES": ["ES=F"],
    "NQ": ["NQ=F"],
    "ZN": ["ZN=F"],
    "GC": ["GC=F"],
    "CL": ["CL=F"],
    "SI": ["SI=F"],
    "NG=F": ["NG=F"],
}


class FuturesDataClient:
    """Client for fetching futures data from various sources."""

    def __init__(self, alpha_vantage_key: str = "", forex_key: str = ""):
        self.alpha_vantage_key = alpha_vantage_key
        self.forex_key = forex_key
        self.yahoo_base = "https://query1.finance.yahoo.com/v8/finance/chart"

    def get_futures_overview(self) -> Dict[str, Dict]:
        """Get overview of key futures contracts."""
        futures_data = {}

        # Get equity index futures (from Yahoo Finance)
        futures_data["equity_index"] = self._get_yahoo_futures(
            [
                "ES=F",  # E-mini S&P 500
                "NQ=F",  # E-mini Nasdaq
                "YM=F",  # E-mini Dow
                "RTY=F",  # Russell 2000
            ]
        )

        # Get treasury futures
        futures_data["treasury"] = self._get_yahoo_futures(
            [
                "ZN=F",  # 10-Year T-Note
                "ZB=F",  # 30-Year T-Bond
                "ZF=F",  # 5-Year T-Note
                "ZT=F",  # 2-Year T-Note
            ]
        )

        # Get commodity futures
        futures_data["commodities"] = self._get_yahoo_futures(
            [
                "GC=F",  # Gold
                "SI=F",  # Silver
                "CL=F",  # Crude Oil
                "NG=F",  # Natural Gas
            ]
        )

        # Get VIX
        futures_data["volatility"] = self._get_yahoo_futures(["^VIX"])

        return futures_data

    def _get_yahoo_futures(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch futures data from Yahoo Finance."""
        results = {}

        for symbol in symbols:
            clean_symbol = symbol.replace("^", "").replace("=F", "")
            friendly_name = FUTURES_CONTRACTS.get(clean_symbol, clean_symbol)

            try:
                url = f"{self.yahoo_base}/{symbol}?interval=1d&range=5d"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))

                if "chart" in data and "result" in data["chart"]:
                    result = data["chart"]["result"][0]
                    meta = result.get("meta", {})
                    quotes = result.get("indicators", {}).get("quote", [{}])[0]

                    # Get latest close
                    closes = quotes.get("close", [])
                    latest_close = None
                    for c in reversed(closes):
                        if c is not None:
                            latest_close = c
                            break

                    # Get previous close
                    prev_close = None
                    for c in closes[:-1]:
                        if c is not None:
                            prev_close = c
                            break

                    change = None
                    if latest_close and prev_close:
                        change = latest_close - prev_close

                    results[clean_symbol] = {
                        "name": friendly_name,
                        "symbol": clean_symbol,
                        "price": latest_close,
                        "change": change,
                        "source": f"Yahoo Finance ({symbol})",
                    }

            except Exception as e:
                logger.debug(f"Could not fetch {symbol}: {e}")
                results[clean_symbol] = {
                    "name": friendly_name,
                    "symbol": clean_symbol,
                    "error": str(e),
                    "source": f"Yahoo Finance ({symbol})",
                }

        return results

    def get_term_structure(self, symbol: str) -> Dict[str, Any]:
        """
        Get futures term structure (contango/backwardation).

        Estimates term structure from historical price trends since Yahoo Finance
        only provides front month futures data. For full curve, use CME Group API.
        """
        symbol_lookup = f"{symbol}=F" if not symbol.endswith("=F") else symbol

        if HAS_YFINANCE:
            try:
                # Fetch historical data to estimate term structure from price action
                data = yf.download(
                    symbol_lookup, period="3mo", interval="1d", progress=False
                )

                if data is not None and not data.empty and "Close" in data.columns:
                    recent_prices = data["Close"].dropna()
                    current_price = recent_prices.iloc[-1]
                    one_month_price = (
                        recent_prices.iloc[-22] if len(recent_prices) > 22 else None
                    )
                    three_month_price = (
                        recent_prices.iloc[-66] if len(recent_prices) > 66 else None
                    )

                    # Estimate term structure from price trends
                    structure_notes = []

                    if one_month_price and three_month_price:
                        # Use price trend to estimate contango/backwardation
                        if current_price > three_month_price > one_month_price:
                            structure = "BACKWARDATION"
                            structure_notes.append(
                                "Futures in backwardation - near-term premium"
                            )
                            spread = (
                                (one_month_price - three_month_price)
                                / three_month_price
                                * 100
                            )
                        elif current_price < three_month_price < one_month_price:
                            structure = "CONTANGO"
                            structure_notes.append(
                                "Futures in contango - carry favors longs"
                            )
                            spread = (
                                (three_month_price - one_month_price)
                                / one_month_price
                                * 100
                            )
                        else:
                            structure = "FLAT"
                            structure_notes.append("Flat term structure")
                            spread = 0

                        return {
                            "symbol": symbol,
                            "name": FUTURES_CONTRACTS.get(symbol, symbol),
                            "current_price": float(current_price),
                            "one_month_ago": float(one_month_price)
                            if one_month_price
                            else None,
                            "three_months_ago": float(three_month_price)
                            if three_month_price
                            else None,
                            "spread_pct": spread,
                            "contango": structure == "CONTANGO",
                            "backwardation": structure == "BACKWARDATION",
                            "structure": structure,
                            "notes": structure_notes,
                            "source": "Yahoo Finance via yfinance (estimated from price trends)",
                            "limitation": "Front month only - use CME API for full curve",
                        }
            except Exception as e:
                logger.debug(f"Could not fetch term structure for {symbol}: {e}")

        # Fallback when data unavailable
        return {
            "symbol": symbol,
            "name": FUTURES_CONTRACTS.get(symbol, symbol),
            "current_price": None,
            "one_month_ago": None,
            "three_months_ago": None,
            "spread_pct": None,
            "contango": None,
            "backwardation": None,
            "structure": "UNKNOWN",
            "notes": ["Term structure requires CME Group API for full contract curve"],
            "source": "N/A",
        }

    def get_market_gamma(self) -> Dict[str, Any]:
        """
        Calculate market gamma exposure from available data.

        Gamma analysis measures how dealer positioning affects market dynamics:
        - Long Gamma: Dealers buy dips, sell rips (stabilizes market)
        - Short Gamma: Dealers sell dips, buy rips (amplifies moves)
        """
        # Get VIX and market data
        futures_data = self.get_futures_overview()
        volatility = futures_data.get("volatility", {})
        vix_data = volatility.get("VIX", {})
        vix_price = vix_data.get("price")

        if not vix_price:
            return {
                "vix_level": None,
                "gamma_regime": "UNKNOWN",
                "sput_risk": "UNKNOWN",
                "dealer_positioning": "UNKNOWN",
                "notes": ["Could not fetch VIX data for gamma analysis"],
            }

        # Calculate gamma exposure based on VIX and market conditions
        gamma_regime, sput_risk, dealer_pos, notes = self._calculate_gamma_from_vix(
            vix_price
        )

        # Fetch SPY/ES for additional context if yfinance is available
        if HAS_YFINANCE:
            try:
                spy_data = yf.download("SPY", period="1mo", progress=False)
                if not spy_data.empty:
                    spy_close = spy_data["Close"].iloc[-1]
                    spy_prev = spy_data["Close"].iloc[-2]
                    spy_vol = (
                        spy_data["Close"].pct_change().tail(5).std() * 252**0.5
                    )  # Annualized

                    notes.append(f"SPY realized vol: {spy_vol:.1f}%")
                    notes.append(f"SPY price: ${spy_close:.2f}")

                    # Adjust gamma based on realized vs implied
                    if spy_vol < vix_price * 0.8:
                        notes.append("Realized vol < implied vol - options overpriced")
                        gamma_regime = (
                            "SHORT" if gamma_regime == "NEUTRAL" else gamma_regime
                        )
                    elif spy_vol > vix_price * 1.2:
                        notes.append("Realized vol > implied vol - options underpriced")
                        gamma_regime = (
                            "LONG" if gamma_regime == "NEUTRAL" else gamma_regime
                        )
            except Exception as e:
                logger.debug(f"Could not fetch SPY data: {e}")

        return {
            "vix_level": vix_price,
            "gamma_regime": gamma_regime,  # LONG, NEUTRAL, SHORT
            "sput_risk": sput_risk,  # LOW, MEDIUM, HIGH
            "dealer_positioning": dealer_pos,  # LONG_GAMMA, SHORT_GAMMA, FLAT
            "notes": notes,
        }

    def _calculate_gamma_from_vix(self, vix: float) -> tuple:
        """
        Estimate gamma exposure from VIX level.

        Logic:
        - VIX < 15: Low vol environment, dealers likely short gamma (selling vol)
        - VIX 15-25: Normal vol, neutral gamma
        - VIX > 25: High vol, dealers likely long gamma (bought protection)
        - VIX > 35: Crisis mode, extreme gamma exposure
        """
        notes = []

        if vix < 12:
            # Very low vol - dealers selling options aggressively
            gamma = "SHORT"
            sput = "HIGH"  # Short puts are risky in low vol regime
            dealer = "SHORT_GAMMA"
            notes.append("VIX < 12: Options sellers dominating, short gamma regime")
            notes.append("Risk: Vol spike would cause rapid dealer hedging")

        elif vix < 18:
            # Low to normal vol
            gamma = "NEUTRAL_SLIGHT_SHORT"
            sput = "MEDIUM"
            dealer = "FLAT_SLIGHT_SHORT"
            notes.append("VIX 12-18: Normal volatility, balanced positioning")

        elif vix < 25:
            # Normal vol
            gamma = "NEUTRAL"
            sput = "MEDIUM"
            dealer = "FLAT"
            notes.append("VIX 18-25: Standard volatility environment")

        elif vix < 35:
            # Elevated vol
            gamma = "NEUTRAL_SLIGHT_LONG"
            sput = "LOW"
            dealer = "FLAT_SLIGHT_LONG"
            notes.append("VIX 25-35: Elevated volatility, some dealers long gamma")

        else:
            # Crisis mode
            gamma = "LONG"
            sput = "LOW"
            dealer = "LONG_GAMMA"
            notes.append(
                "VIX > 35: Crisis volatility, dealers likely long gamma (protection)"
            )

        # Normalize gamma regime to 3 categories
        gamma_normalized = gamma
        if "SLIGHT" in gamma:
            gamma_normalized = "NEUTRAL"

        return gamma_normalized, sput, dealer, notes

    def get_futures_positioning(self) -> Dict[str, Any]:
        """Get futures-specific positioning analysis with dynamic levels."""
        futures_data = self.get_futures_overview()

        # Calculate dynamic key levels from price data
        key_levels = self._calculate_key_levels(futures_data)

        # Get gamma analysis for dealer positioning
        gamma_analysis = self.get_market_gamma()

        # Extract dealer positioning from gamma analysis
        dealer_gamma = gamma_analysis.get("dealer_positioning", "FLAT")

        return {
            "equity_index_sentiment": self._get_sentiment(
                futures_data.get("equity_index", {})
            ),
            "treasury_positioning": self._analyze_treasury_positioning(
                futures_data.get("treasury", {})
            ),
            "commodity_positioning": self._analyze_commodity_positioning(
                futures_data.get("commodities", {})
            ),
            "currency_positioning": "NEUTRAL",  # Would need FX data
            "dealer_gamma": dealer_gamma,
            "gamma_regime": gamma_analysis.get("gamma_regime"),
            "key_levels": key_levels,
            "seasonality": self._get_current_seasonality(),
            "gamma_notes": gamma_analysis.get("notes", []),
        }

    def _analyze_treasury_positioning(self, treasury_data: Dict) -> str:
        """Analyze treasury futures positioning."""
        zn = treasury_data.get("ZN", {})
        zn_price = zn.get("price")

        if zn_price is None:
            return "NEUTRAL"

        # Simple logic: ZN < 108 = bearish (yields high), ZN > 112 = bullish (yields low)
        if zn_price < 108:
            return "BEARISH_BIAS"
        elif zn_price > 112:
            return "BULLISH_BIAS"
        else:
            return "NEUTRAL"

    def _analyze_commodity_positioning(self, commodity_data: Dict) -> str:
        """Analyze commodity futures positioning."""
        gc = commodity_data.get("GC", {})
        cl = commodity_data.get("CL", {})

        gc_price = gc.get("price")
        cl_price = cl.get("price")

        signals = []

        if gc_price:
            if gc_price > 2700:
                signals.append("GOLD_BULLISH")
            elif gc_price < 2400:
                signals.append("GOLD_BEARISH")

        if cl_price:
            if cl_price > 75:
                signals.append("CRUDE_BULLISH")
            elif cl_price < 65:
                signals.append("CRUDE_BEARISH")

        if signals:
            return "_".join(signals)
        return "NEUTRAL"

    def _get_current_seasonality(self) -> Dict[str, str]:
        """Get current seasonality based on time of year."""
        month = datetime.now().month

        seasonality = {}

        # Equity seasonality (general patterns)
        if month in [1, 4, 5, 10, 11]:
            seasonality["equity"] = "SEASONALLY_BULLISH"
        elif month in [9]:
            seasonality["equity"] = "SEASONALLY_BEARISH"
        else:
            seasonality["equity"] = "NEUTRAL"

        # Treasury seasonality
        if month in [1, 2, 6, 12]:
            seasonality["treasury"] = "SEASONALLY_BULLISH"
        elif month in [3, 8]:
            seasonality["treasury"] = "SEASONALLY_BEARISH"
        else:
            seasonality["treasury"] = "NEUTRAL"

        # Energy seasonality
        if month in [12, 1, 2]:  # Winter
            seasonality["energy"] = "SEASONALLY_STRONG_WINTER"
        elif month in [6, 7, 8]:  # Summer driving season
            seasonality["energy"] = "SEASONALLY_STRONG_SUMMER"
        else:
            seasonality["energy"] = "NEUTRAL"

        return seasonality

    def _calculate_key_levels(self, futures_data: Dict) -> Dict[str, Any]:
        """Calculate dynamic support/resistance levels from price data."""
        key_levels = {}

        # Equity index levels
        equity = futures_data.get("equity_index", {})
        es_data = equity.get("ES", {})
        es_price = es_data.get("price")

        if es_price and isinstance(es_price, (int, float)):
            # Use 2% bands for support/resistance
            es_support = [
                round(es_price * 0.98, 0),
                round(es_price * 0.96, 0),
                round(es_price * 0.94, 0),
            ]
            es_resistance = [
                round(es_price * 1.02, 0),
                round(es_price * 1.04, 0),
                round(es_price * 1.06, 0),
            ]
            key_levels["ES_support"] = [int(s) for s in es_support]
            key_levels["ES_resistance"] = [int(r) for r in es_resistance]
            key_levels["ES_current"] = es_price
        else:
            key_levels["ES_support"] = [5800, 5750, 5700]
            key_levels["ES_resistance"] = [5900, 5950, 6000]

        # Treasury futures levels
        treasury = futures_data.get("treasury", {})
        zn_data = treasury.get("ZN", {})
        zn_price = zn_data.get("price")

        if zn_price and isinstance(zn_price, (int, float)):
            # 1% bands for treasuries
            zn_support = [
                round(zn_price * 0.99, 1),
                round(zn_price * 0.98, 1),
                round(zn_price * 0.97, 1),
            ]
            zn_resistance = [
                round(zn_price * 1.01, 1),
                round(zn_price * 1.02, 1),
                round(zn_price * 1.03, 1),
            ]
            key_levels["ZN_support"] = [float(s) for s in zn_support]
            key_levels["ZN_resistance"] = [float(r) for r in zn_resistance]
            key_levels["ZN_current"] = zn_price
        else:
            key_levels["ZN_support"] = [108.0, 106.0, 104.0]
            key_levels["ZN_resistance"] = [112.0, 114.0, 116.0]

        # VIX levels
        volatility = futures_data.get("volatility", {})
        vix_data = volatility.get("VIX", {})
        vix_price = vix_data.get("price")
        if vix_price:
            key_levels["VIX_current"] = vix_price

        key_levels["VIX_support"] = 14.0
        key_levels["VIX_resistance"] = 22.0

        return key_levels

    def _get_sentiment(self, market_data: Dict) -> str:
        """Determine market sentiment from price action."""
        for symbol, data in market_data.items():
            if not isinstance(data, dict):
                continue

            price = data.get("price")
            change = data.get("change")

            if price and change is not None:
                if change > 0.5:
                    return "BULLISH"
                elif change < -0.5:
                    return "BEARISH"
                else:
                    return "NEUTRAL"

        return "NEUTRAL"
