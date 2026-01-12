#!/usr/bin/env python3
"""
Setup script to configure automated email reports for Oracle.
Generates .env file with credential-free email and scheduling settings.
"""

import os


def create_env_config():
    """Create .env file with email and scheduling configuration."""

    env_content = """# Application Configuration
APP_NAME=Oracle
APP_VERSION=0.1.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Database
DATABASE_URL=sqlite:///./data/market_oracle.db
DATABASE_POOL_SIZE=10

# LLM Configuration
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MODEL_PRIMARY=claude-sonnet-4-20250514
MODEL_FAST=claude-3-5-sonnet-20241022
TEMPERATURE=0.7
MAX_TOKENS=4096

# Optional: Ollama for local LLM (set LLM_PROVIDER=ollama to use)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Data Source API Keys
TAVILY_API_KEY=your_tavily_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
FRED_API_KEY=your_fred_api_key_here

# Rate Limiting (requests per minute)
API_RATE_LIMIT=60
API_BURST=10

# Caching Configuration
CACHE_TTL_RESEARCH=3600  # 1 hour for research results
CACHE_TTL_COT=86400  # 24 hours for COT data
CACHE_TTL_ECONOMIC=1800  # 30 minutes for economic data

# Scheduler Configuration (automated reports)
SCHEDULER_TIMEZONE=America/New_York
PREMIUM_TIME=06:30  # Premarket report time (morning)
POSTMARKET_TIME=16:30  # Post-market report time (4:30 PM)

# Report Configuration
REPORTS_DIR=./reports
DAILY_REPORT_LENGTH=800
WEEKLY_REPORT_LENGTH=1500
ENABLE_CITATIONS=true

# Email Delivery (credential-free - NO passwords required!)
ENABLE_EMAIL=true
EMAIL_DELIVERY_METHOD=auto  # Options: auto, sendmail, file, smtp
# - auto: Use sendmail if available, otherwise save to file
# - sendmail: Use local sendmail command (no credentials needed)
# - file: Save reports to email_reports/ directory (no email at all)
# - smtp: Use SMTP server (requires username/password)
EMAIL_OUTPUT_DIR=./email_reports  # Where to save reports for file-based delivery
EMAIL_FROM=oracle@local
EMAIL_TO=your_email@example.com
EMAIL_SUBJECT_PREFIX=[ORACLE]

# Slack Integration (optional)
ENABLE_SLACK=false
SLACK_WEBHOOK_URL=

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_DIR=./backups
BACKUP_SCHEDULE=daily
BACKUP_RETENTION_DAYS=30

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
"""

    # Check if .env already exists
    if os.path.exists(".env"):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != "y":
            print("Cancelled. Please edit .env manually.")
            return False

    with open(".env", "w") as f:
        f.write(env_content)

    print("✅ Created .env file with credential-free email configuration")
    print("\n📧 Delivery Methods (NO passwords required!):")
    print("  1. auto      - Use sendmail if available, otherwise save to file")
    print("  2. sendmail  - Use local sendmail (works on most servers)")
    print("  3. file      - Save reports to ./email_reports/ directory")
    print("  4. smtp      - Use SMTP server (requires credentials)")
    print()
    print("🚀 Next steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Test delivery: python -m backend.cli.main test-email")
    print("  3. Start scheduler: python -m backend.cli.main scheduler")
    print()
    print("💡 Tip: On Linux servers, sendmail is usually pre-installed!")

    return True


if __name__ == "__main__":
    create_env_config()
