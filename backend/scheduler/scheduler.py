"""
Simple scheduler for Oracle reports using Python's built-in sched module.
No external dependencies required!
"""

import logging
import sched
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from backend.agents.orchestrator import Oracle
from backend.config.settings import settings
from backend.delivery.email import email_delivery

logger = logging.getLogger(__name__)


class SimpleScheduler:
    """Simple scheduler using Python's built-in sched module."""

    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.running = False
        self.oracle = Oracle()
        self.premarket_job = None
        self.postmarket_job = None
        self.lock = threading.Lock()

    def _parse_time(self, time_str: str) -> tuple:
        """Parse HH:MM time string to (hour, minute)."""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])

    def _get_next_run_time(self, hour: int, minute: int) -> float:
        """Calculate next run time for given hour and minute."""
        now = datetime.now()

        # Calculate target time today
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If already passed today, schedule for tomorrow
        if target <= now:
            target = target + timedelta(days=1)

        return target.timestamp()

    def generate_and_send_premarket(self):
        """Generate and send premarket report."""
        logger.info("Starting scheduled premarket report generation")
        try:
            state = self.oracle.run_daily_brief()
            logger.info(f"Generated premarket report for {state.date}")

            if settings.enable_email:
                import asyncio

                success = asyncio.run(email_delivery.send_premarket_report(state.date))
                if success:
                    logger.info("Premarket report sent successfully")
                else:
                    logger.error("Failed to send premarket report")
            else:
                logger.info("Email delivery disabled, skipping send")

        except Exception as e:
            logger.error(f"Error in premarket report generation: {e}")

    def generate_and_send_postmarket(self):
        """Generate and send post-market report."""
        logger.info("Starting scheduled post-market report generation")
        try:
            state = self.oracle.run_daily_brief()
            logger.info(f"Generated post-market report for {state.date}")

            if settings.enable_email:
                import asyncio

                success = asyncio.run(email_delivery.send_postmarket_report(state.date))
                if success:
                    logger.info("Post-market report sent successfully")
                else:
                    logger.error("Failed to send post-market report")
            else:
                logger.info("Email delivery disabled, skipping send")

        except Exception as e:
            logger.error(f"Error in post-market report generation: {e}")

    def _schedule_next_run(self, job_type: str):
        """Schedule the next run for a job."""
        with self.lock:
            if job_type == "premarket":
                hour, minute = self._parse_time(
                    getattr(settings, "premarket_time", "06:30")
                )
                next_time = self._get_next_run_time(hour, minute)

                self.premarket_job = self.scheduler.enterabs(
                    next_time, 1, self.generate_and_send_premarket
                )
                logger.info(
                    f"Scheduled premarket report for {datetime.fromtimestamp(next_time)}"
                )

            elif job_type == "postmarket":
                hour, minute = self._parse_time(
                    getattr(settings, "postmarket_time", "16:30")
                )
                next_time = self._get_next_run_time(hour, minute)

                self.postmarket_job = self.scheduler.enterabs(
                    next_time, 1, self.generate_and_send_postmarket
                )
                logger.info(
                    f"Scheduled post-market report for {datetime.fromtimestamp(next_time)}"
                )

    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        logger.info("Starting Oracle Report Scheduler")

        # Get schedule times
        premarket_time = getattr(settings, "premarket_time", "06:30")
        postmarket_time = getattr(settings, "postmarket_time", "16:30")

        print(f"""
╔══════════════════════════════════════════════════════════╗
║           ORACLE Report Scheduler Started                ║
╠══════════════════════════════════════════════════════════╣
║  📅 Schedule:                                            ║
║     • Premarket Report:    {premarket_time} ET (morning)             ║
║     • Post-market Report:  {postmarket_time} ET (4:30 PM)           ║
╠══════════════════════════════════════════════════════════╣
║  📧 Email Delivery:     {"Enabled" if settings.enable_email else "Disabled":<35}║
║  🌍 Timezone:           {settings.scheduler_timezone:<35}║
╚══════════════════════════════════════════════════════════╝
""")

        # Schedule first runs
        self._schedule_next_run("premarket")
        self._schedule_next_run("postmarket")

        # Start scheduler in background thread
        def run_scheduler():
            while self.running:
                self.scheduler.run(blocking=False)
                time.sleep(1)  # Check every second

        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()

        print("✅ Scheduler is running in background")
        print("\nWhat the scheduler will do:")
        print("━" * 60)
        self.print_next_runs()
        print("\nPress Ctrl+C to stop")

    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return

        self.running = False
        self.scheduler.cancel(self.premarket_job) if self.premarket_job else None
        self.scheduler.cancel(self.postmarket_job) if self.postmarket_job else None

        print("\n🛑 Scheduler stopped")
        logger.info("Scheduler stopped")

    def get_status(self) -> dict:
        """Get scheduler status."""
        premarket_time = getattr(settings, "premarket_time", "06:30")
        postmarket_time = getattr(settings, "postmarket_time", "16:30")

        return {
            "running": self.running,
            "premarket_time": premarket_time,
            "postmarket_time": postmarket_time,
            "email_enabled": settings.enable_email,
            "timezone": settings.scheduler_timezone,
        }

    def print_next_runs(self):
        """Print information about next scheduled runs."""
        premarket_time = getattr(settings, "premarket_time", "06:30")
        postmarket_time = getattr(settings, "postmarket_time", "16:30")

        hour, minute = self._parse_time(premarket_time)
        next_premarket = datetime.fromtimestamp(self._get_next_run_time(hour, minute))

        hour, minute = self._parse_time(postmarket_time)
        next_postmarket = datetime.fromtimestamp(self._get_next_run_time(hour, minute))

        print(f"📅 Next Scheduled Runs:")
        print(
            f"   1. Premarket Report:  {next_premarket.strftime('%Y-%m-%d at %I:%M %p ET')}"
        )
        print(
            f"   2. Post-market Report: {next_postmarket.strftime('%Y-%m-%d at %I:%M %p ET')}"
        )

        now = datetime.now()
        time_to_premarket = next_premarket - now
        time_to_postmarket = next_postmarket - now

        print(f"\n⏱️  Time Until Next Reports:")

        def format_timedelta(td):
            total_seconds = int(td.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{days} days, {hours} hours, {minutes} minutes"

        print(f"   • Premarket:  {format_timedelta(time_to_premarket)}")
        print(f"   • Post-market: {format_timedelta(time_to_postmarket)}")


# Singleton instance
report_scheduler = SimpleScheduler()


def start_scheduler():
    """Start the report scheduler."""
    report_scheduler.start()


def stop_scheduler():
    """Stop the report scheduler."""
    report_scheduler.stop()


def get_scheduler_status() -> dict:
    """Get scheduler status."""
    return report_scheduler.get_status()
