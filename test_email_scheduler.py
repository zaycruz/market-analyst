#!/usr/bin/env python3
"""
Test script to verify email and scheduling configuration.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_configuration():
    """Test that all configuration is properly set up."""
    print("Testing Configuration...")
    print("=" * 50)

    try:
        from backend.config.settings import settings

        print("✅ Settings loaded successfully")

        # Check email configuration
        print("\n📧 Email Configuration:")
        print(f"  Enabled: {settings.enable_email}")
        print(
            f"  Delivery Method: {getattr(settings, 'email_delivery_method', 'auto')}"
        )
        print(
            f"  Output Dir: {getattr(settings, 'email_output_dir', './email_reports')}"
        )
        print(f"  From: {settings.email_from}")
        print(f"  To: {settings.email_to}")

        if not settings.enable_email:
            print("  ⚠️  Email is disabled - set ENABLE_EMAIL=true in .env")
        else:
            print("  ✅ Email is enabled")

        # Check scheduling configuration
        print("\n⏰ Scheduling Configuration:")
        print(f"  Timezone: {settings.scheduler_timezone}")
        print(f"  Premarket: {getattr(settings, 'premarket_time', '06:30')}")
        print(f"  Post-market: {getattr(settings, 'postmarket_time', '16:30')}")

        # Test email module
        print("\n📨 Testing Email Module:")
        try:
            from backend.delivery.email import email_delivery

            print("  ✅ Email delivery module imported successfully")
            print(f"  ✅ Email delivery instance created: {email_delivery.enabled}")
        except ImportError as e:
            print(f"  ❌ Failed to import email module: {e}")
            return False

        # Test scheduler module
        print("\n📅 Testing Scheduler Module:")
        try:
            from backend.scheduler.scheduler import report_scheduler

            print("  ✅ Scheduler module imported successfully")
            status = report_scheduler.get_status()
            print(f"  ✅ Scheduler status: {status}")
        except ImportError as e:
            print(f"  ❌ Failed to import scheduler module: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def test_email_sending():
    """Test sending a sample email."""
    print("\nTesting Email Sending...")
    print("=" * 50)

    try:
        import asyncio
        from backend.delivery.email import email_delivery

        if not email_delivery.enabled:
            print("⚠️  Email is disabled. Enable it in .env first.")
            return False

        if email_delivery.delivery_method == "file":
            print("📁 File-based delivery mode - reports will be saved to directory")
            return True

        # Generate a test report first
        print("Generating test report...")
        from backend.agents.orchestrator import Oracle

        oracle = Oracle()
        state = oracle.run_daily_brief()
        print(f"✅ Generated test report for {state.date}")

        # Try to send
        print("Attempting to send email...")
        success = asyncio.run(email_delivery.send_premarket_report(state.date))

        if success:
            print("✅ Email sent successfully!")
        else:
            print("❌ Failed to send email")

        return success

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def test_scheduler():
    """Test scheduler functionality."""
    print("\nTesting Scheduler...")
    print("=" * 50)

    try:
        from backend.scheduler.scheduler import report_scheduler

        print("Starting scheduler...")
        report_scheduler.start()

        print("Getting scheduler status...")
        status = report_scheduler.get_status()

        print(f"✅ Scheduler running: {status['running']}")
        print(f"✅ Jobs: {len(status['jobs'])}")

        for job in status["jobs"]:
            print(f"  - {job['name']}: {job['next_run']}")

        report_scheduler.stop()
        print("✅ Scheduler stopped successfully")

        return True

    except Exception as e:
        print(f"❌ Error testing scheduler: {e}")
        return False


if __name__ == "__main__":
    print("Oracle - Email & Scheduler Configuration Test")
    print("=" * 60)

    # Run tests
    config_ok = test_configuration()

    if config_ok:
        print("\n" + "=" * 60)
        print("Would you like to run additional tests?")
        print("1. Test email sending (requires real SMTP)")
        print("2. Test scheduler (safe)")
        print("3. Skip additional tests")

        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            test_email_sending()
        elif choice == "2":
            test_scheduler()
    else:
        print("\n❌ Configuration test failed. Please fix the errors above.")
        sys.exit(1)
