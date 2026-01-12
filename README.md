# Oracle - AI Macro Research Agent for Futures Trading

A self-hosted multi-agent AI system that conducts institutional-grade macro research for futures traders. Generates daily briefs with gamma-adjusted trade recommendations, dealer positioning analysis, and actionable trading levels.

## Features

### Core Capabilities
- **Daily Macro Brief** (6:30 AM ET): Institutional-grade research with regime assessment, 3-5 actionable futures trades, and gamma-aware position sizing
- **Weekly Positioning Report** (Sunday 5:00 PM ET): Comprehensive macro outlook with COT analysis and term structure
- **On-Demand Research**: CLI-triggered analysis on specific topics or markets

### Advanced Analysis
- **Gamma Regime Analysis**: VIX-based dealer gamma estimation (LONG/NEUTRAL/SHORT) with SPUT risk assessment
- **Dealer Positioning**: Estimates dealer flow direction from volatility regime
- **Futures Term Structure**: Contango/backwardation analysis from price trends
- **Dynamic Key Levels**: Real-time support/resistance calculation for ES, ZN, VIX
- **Seasonality**: Monthly seasonal biases for equity, treasury, and energy markets

### Data Sources
| Source | Data | Cost |
|--------|------|------|
| **Yahoo Finance** | Futures prices (ES, NQ, ZN, GC, CL, VIX) | Free |
| **CFTC COT** | Commitment of Traders positioning | Free |
| **FRED API** | Economic indicators (GDP, CPI, unemployment, yield spreads) | Free |
| **Tavily** | Web search for geopolitical/market news | $50-100/mo |
| **Anthropic** | LLM synthesis (Claude Sonnet) | $300-500/mo |

## Quick Start

```bash
# 1. Clone the repository
cd market-analyst

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run the test suite
python test_oracle.py

# 4. Generate a daily brief
python -m backend.cli.main daily

# 5. View the generated report
python -m backend.cli.main view --type daily

# 6. Run on-demand research
python -m backend.cli.main research "Gold outlook given current positioning"

# 7. Check system status
python -m backend.cli.main status

# 8. Start the API server
python -m backend.cli.main server
```

## CLI Commands

```bash
# Generate daily macro brief
python -m backend.cli.main daily
python -m backend.cli.main daily --show  # Print to stdout

# Run on-demand research query
python -m backend.cli.main research "Your research question"

# View a report
python -m backend.cli.main view --type daily
python -m backend.cli.main view --type daily --date 2026-01-06

# Check system status
python -m backend.cli.main status

# Start API server
python -m backend.cli.main server
```

## API Endpoints

When running the server (`python -m backend.cli.main server`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/reports/daily/{date}` | GET | Get daily report |
| `/api/reports/weekly/{date}` | GET | Get weekly report |
| `/api/reports/recent` | GET | List recent reports |
| `/api/reports/generate/daily` | POST | Generate new daily report |
| `/api/research` | POST | Run research query |

## Project Structure

```
market-analyst/
├── backend/
│   ├── main.py              # HTTP API server
│   ├── agents/
│   │   └── orchestrator.py  # Agent coordination and state management
│   ├── cli/
│   │   └── main.py          # Command-line interface
│   ├── config/
│   │   └── settings.py      # Configuration and environment
│   ├── data/
│   │   ├── fred.py          # FRED economic data
│   │   ├── tavily.py        # Web search for news/events
│   │   ├── alpha_vantage.py # Market data
│   │   ├── cot.py           # CFTC COT positioning
│   │   └── futures.py       # Futures data, gamma & term structure
│   ├── models/
│   │   ├── llm.py           # LLM client with schema validation
│   │   └── market.py        # Data models
│   ├── delivery/
│   │   └── email.py         # Email delivery
│   ├── scheduler/
│   │   └── scheduler.py     # Automated report scheduling
│   └── storage/
│       └── database.py      # SQLite persistence
├── reports/
│   ├── daily/               # Generated daily briefs
│   └── weekly/              # Generated weekly reports
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── test_oracle.py           # Test suite
└── README.md               # This file
```

## Configuration

Edit `.env` file with your API keys:

```bash
# LLM Configuration (required for synthesis)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here

# Data Sources
FRED_API_KEY=your_key_here           # Free from https://fred.stlouisfed.org
TAVILY_API_KEY=your_key_here         # From https://tavily.com
ALPHA_VANTAGE_API_KEY=your_key_here   # Free from https://www.alphavantage.co

# Schedule (optional)
DAILY_BRIEF_TIME=06:30
WEEKLY_REPORT_TIME=17:00
WEEKLY_REPORT_DAY=sunday
```

## Agent Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Oracle (Orchestrator)                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │   Macro    │  │Geopolitical│  │    Flow    │  │   Futures  │   │
│  │ Economist  │  │  Analyst   │  │  Analyst   │  │ Specialist │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘   │
│        │               │               │               │          │
│        └───────────────┼───────────────┼───────────────┘          │
│                        │               │                          │
│  ┌────────────┐        │               │                          │
│  │ Commodity  │        │               │                          │
│  │ Specialist │────────┴───────────────┘                          │
│  └─────┬──────┘                                                  │
│        │                                                         │
│        └─────────────────┬───────────────────────────────────────┘
│                          │
│                   ┌──────▼──────┐
│                   │  Synthesis  │
│                   │    Agent    │
│                   └──────┬──────┘
│                          │
│                   ┌──────▼──────┐
│                   │   Report    │
│                   │  Generator  │
│                   └─────────────┘
└────────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities
- **Macro Economist**: FRED economic data, regime determination, risk indicators
- **Geopolitical Analyst**: Tavily news search, market-moving events
- **Flow Analyst**: CFTC COT positioning, crowded trades identification
- **Futures Specialist**: Futures data, gamma regime, term structure, key levels
- **Commodity Specialist**: Alpha Vantage market data, cross-asset analysis
- **Synthesis Agent**: Combines all inputs into actionable trade recommendations
- **Report Generator**: Markdown reports with tables, risk dashboards, and trade sheets

## Sample Report Output

```markdown
# Daily Macro Brief - January 11, 2026

## EXECUTIVE SUMMARY
Markets in TRANSITIONAL regime with VIX at 14.5 signaling complacency while yield curve 
flattening and positioning extremes in gold suggest vulnerability.

**Regime: TRANSITIONAL**

- VIX at 14.5 near support, suggesting market complacency
- 10Y-2Y spread compressed to 0.64, indicating yield curve flattening
- Gold positioning at extreme 46.63% speculative net long
- ES trading mid-range between 6840 and 7119

---

## FUTURES TRADING LEVELS
**Gamma Regime:** NEUTRAL  |  **SPUT Risk:** MEDIUM

| Contract | Current | Support | Resistance | Sentiment |
|----------|---------|---------|------------|-----------|
| ES (S&P 500) | 6980 | 6840-6561 | 7119-7398 | BEARISH |
| ZN (10Y Note) | 112.3 | 111.2-109.0 | 113.5-115.7 | NEUTRAL |
| VIX | 14.5 | 14.0 | 22.0 | NORMAL |

---

## TRADE IDEAS

### 1. Short Gold on Crowded Positioning

| Field | Value |
|-------|-------|
| Instrument | GC (COMEX Gold Futures) |
| Direction | SHORT |
| Entry | 2650-2680 |
| Stop | 2720 |
| Target | 2550-2580 |
| Size | 2.0% NAV |
| Timeframe | 2-3 weeks |
| Conviction | 5/5 |

**Rationale:** COT data shows speculative longs at extreme 46.63%, historically bearish 
contrarian signal. Fed policy normalization at 3.72% reduces gold appeal.

---

**Confidence: 7.5/10**
```

## Testing

```bash
# Run full test suite
python test_oracle.py

# Expected output:
# RESULTS: 5 passed, 0 failed
```

## Cost Estimate

| Component | Monthly Cost |
|-----------|-------------|
| Anthropic API (Claude Sonnet) | $300-500 |
| Tavily API | $50-100 |
| Alpha Vantage | $0-25 |
| FRED API | Free |
| Yahoo Finance | Free |
| CFTC COT | Free |
| **Total** | **$350-625/month** |

API keys required. See `.env.example` for configuration.

## License

MIT
