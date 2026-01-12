import os
from pathlib import Path


class Settings:
    def __init__(self):
        self._load_env()

        self.app_name = os.getenv("APP_NAME", "Oracle")
        self.app_version = os.getenv("APP_VERSION", "0.1.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))

        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite:///./data/market_oracle.db"
        )

        self.llm_provider = os.getenv("LLM_PROVIDER", "anthropic")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.model_primary = os.getenv("MODEL_PRIMARY", "claude-sonnet-4-20250514")
        self.model_fast = os.getenv("MODEL_FAST", "claude-3-5-sonnet-20241022")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))

        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")

        self.cache_ttl_research = int(os.getenv("CACHE_TTL_RESEARCH", "3600"))
        self.cache_ttl_cot = int(os.getenv("CACHE_TTL_COT", "86400"))
        self.cache_ttl_economic = int(os.getenv("CACHE_TTL_ECONOMIC", "1800"))

        self.scheduler_timezone = os.getenv("SCHEDULER_TIMEZONE", "America/New_York")
        self.daily_brief_time = os.getenv("DAILY_BRIEF_TIME", "06:30")
        self.weekly_report_time = os.getenv("WEEKLY_REPORT_TIME", "17:00")
        self.weekly_report_day = os.getenv("WEEKLY_REPORT_DAY", "sunday")

        # Premarket and Post-market scheduling
        self.premarket_time = os.getenv("PREMIUM_TIME", "06:30")  # Morning report
        self.postmarket_time = os.getenv(
            "POSTMARKET_TIME", "16:30"
        )  # 4:30 PM evening report

        self.reports_dir = os.getenv("REPORTS_DIR", "./reports")

        self.enable_email = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
        self.email_delivery_method = os.getenv("EMAIL_DELIVERY_METHOD", "auto")
        self.email_output_dir = os.getenv("EMAIL_OUTPUT_DIR", "./email_reports")
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.email_from = os.getenv("EMAIL_FROM", "oracle@local")
        self.email_to = os.getenv("EMAIL_TO", "")
        self.email_subject_prefix = os.getenv("EMAIL_SUBJECT_PREFIX", "[ORACLE]")

    def _load_env(self):
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())


settings = Settings()
