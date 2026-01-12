import sys
import argparse
from datetime import datetime

from backend.agents.orchestrator import Oracle
from backend.config.settings import settings


def cmd_daily(args):
    print("\nGenerating daily macro brief...\n")

    oracle = Oracle()
    state = oracle.run_daily_brief()

    print("\n" + "=" * 60)
    print("DAILY BRIEF COMPLETE")
    print("=" * 60)
    print(f"\nReport: {settings.reports_dir}/daily/{state.date}.md")

    if args.show:
        print("\n" + state.markdown_report)


def cmd_research(args):
    query = " ".join(args.query)

    print(f"\n{'=' * 60}")
    print(f"ORACLE RESEARCH: {query}")
    print("=" * 60 + "\n")

    oracle = Oracle()
    state = oracle.run_research(query)

    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)

    print(f"\nThesis: {state.thesis}")
    print(f"\nConfidence: {state.confidence:.0%}")

    print("\nRecommendations:")
    for i, rec in enumerate(state.recommendations, 1):
        if isinstance(rec, dict):
            print(f"  {i}. [{rec.get('conviction', 'MEDIUM')}] {rec.get('trade', '')}")
            print(f"     Rationale: {rec.get('rationale', '')}")
        else:
            print(f"  {i}. {rec}")

    print("\nRisk Factors:")
    for risk in state.risk_factors:
        print(f"  - {risk}")

    print(f"\nSources ({len(state.sources)}):")
    for source in state.sources[:5]:
        print(f"  - {source}")


def cmd_status(args):
    import os

    print(f"""
╔══════════════════════════════════════════════════════════╗
║     ORACLE - Macro Research Agent                        ║
║     Version: {settings.app_version}                                        ║
╠══════════════════════════════════════════════════════════╣
║  Configuration                                           ║
║    Environment: {settings.environment:<38}║
║    Reports Dir: {settings.reports_dir:<38}║
║    LLM Provider: {settings.llm_provider:<37}║
║    Model: {settings.model_primary:<45}║
╠══════════════════════════════════════════════════════════╣
║  API Keys                                                ║
║    FRED API: {"Configured" if settings.fred_api_key else "Not Set":<44}║
║    Tavily API: {"Configured" if settings.tavily_api_key else "Not Set":<42}║
║    Alpha Vantage: {"Configured" if settings.alpha_vantage_api_key else "Not Set":<38}║
║    Anthropic: {"Configured" if settings.anthropic_api_key else "Not Set":<43}║
╠══════════════════════════════════════════════════════════╣
║  Schedule                                                ║
║    Daily Brief: {settings.daily_brief_time} ET                               ║
║    Weekly Report: {settings.weekly_report_day.capitalize()} {settings.weekly_report_time} ET                   ║
╚══════════════════════════════════════════════════════════╝
""")

    daily_dir = os.path.join(settings.reports_dir, "daily")
    weekly_dir = os.path.join(settings.reports_dir, "weekly")

    daily_count = len(os.listdir(daily_dir)) if os.path.exists(daily_dir) else 0
    weekly_count = len(os.listdir(weekly_dir)) if os.path.exists(weekly_dir) else 0

    print(f"  Reports: {daily_count} daily, {weekly_count} weekly")


def cmd_server(args):
    from backend.main import start_server

    start_server()


def cmd_view(args):
    import os

    report_type = args.type or "daily"
    date = args.date or datetime.now().strftime("%Y-%m-%d")

    filepath = os.path.join(settings.reports_dir, report_type, f"{date}.md")

    if os.path.exists(filepath):
        with open(filepath) as f:
            print(f.read())
    else:
        print(f"Report not found: {filepath}")

        report_dir = os.path.join(settings.reports_dir, report_type)
        if os.path.exists(report_dir):
            files = sorted(os.listdir(report_dir), reverse=True)
            if files:
                print(f"\nAvailable reports:")
                for f in files[:10]:
                    print(f"  - {f}")


def cmd_test_email(args):
    """Test email delivery."""
    import asyncio

    from backend.delivery.email import email_delivery

    print("\nTesting email delivery...")
    print(f"  Enabled: {email_delivery.enabled}")
    print(f"  Delivery Method: {email_delivery.delivery_method}")
    print(f"  From: {email_delivery.from_addr}")
    print(f"  To: {email_delivery.to_addr}")

    if not email_delivery.enabled:
        print("\n⚠️  Email is disabled. Set ENABLE_EMAIL=true in .env")
        return

    # Generate a test report
    print("\nGenerating test report...")
    oracle = Oracle()
    state = oracle.run_daily_brief()

    print(f"Generated test report: {state.date}")

    # Send it
    print("\nSending test email...")
    success = asyncio.run(email_delivery.send_premarket_report(state.date))

    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email")


def cmd_scheduler(args):
    """Start the automated report scheduler."""
    from backend.scheduler.scheduler import start_scheduler, get_scheduler_status

    if args.status:
        status = get_scheduler_status()
        print("\nScheduler Status:")
        print(f"  Running: {status['running']}")
        for job in status["jobs"]:
            print(f"  - {job['name']}: {job['next_run']}")
        return

    if args.stop:
        from backend.scheduler.scheduler import stop_scheduler

        stop_scheduler()
        print("Scheduler stopped")
        return

    print("\nStarting automated report scheduler...")
    print(f"  Premarket: {settings.premarket_time} ET")
    print(f"  Post-market: {settings.postmarket_time} ET")
    print(f"  Timezone: {settings.scheduler_timezone}")
    print(f"  Email enabled: {settings.enable_email}")

    start_scheduler()
    print("\n✅ Scheduler started! Reports will be sent automatically.")
    print("\nPress Ctrl+C to stop")

    # Keep running
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        from backend.scheduler.scheduler import stop_scheduler

        stop_scheduler()
        print("\nScheduler stopped")


def main():
    parser = argparse.ArgumentParser(
        prog="oracle",
        description="Oracle - Macro Research Agent for Hedge Fund Trading",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    daily_parser = subparsers.add_parser("daily", help="Generate daily macro brief")
    daily_parser.add_argument(
        "--show", action="store_true", help="Print report to stdout"
    )
    daily_parser.set_defaults(func=cmd_daily)

    research_parser = subparsers.add_parser(
        "research", help="Run on-demand research query"
    )
    research_parser.add_argument("query", nargs="+", help="Research query")
    research_parser.set_defaults(func=cmd_research)

    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)

    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.set_defaults(func=cmd_server)

    view_parser = subparsers.add_parser("view", help="View a report")
    view_parser.add_argument("--type", choices=["daily", "weekly"], default="daily")
    view_parser.add_argument("--date", help="Report date (YYYY-MM-DD)")
    view_parser.set_defaults(func=cmd_view)

    email_parser = subparsers.add_parser("test-email", help="Test email delivery")
    email_parser.set_defaults(func=cmd_test_email)

    scheduler_parser = subparsers.add_parser(
        "scheduler", help="Start automated report scheduler"
    )
    scheduler_parser.add_argument(
        "--status", action="store_true", help="Show scheduler status"
    )
    scheduler_parser.add_argument(
        "--stop", action="store_true", help="Stop the scheduler"
    )
    scheduler_parser.set_defaults(func=cmd_scheduler)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
