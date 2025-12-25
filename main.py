#!/usr/bin/env python3
"""
Email Summary Automation - Main Script

This script automates the process of:
1. Fetching emails from IMAP server
2. Summarizing them using AI
3. Saving/sending the summary
"""

import sys
import logging
import schedule
import time
from datetime import datetime

from src.config_loader import ConfigLoader
from src.logger_setup import setup_logger
from src.email_fetcher import EmailFetcher
from src.email_summarizer import EmailSummarizer
from src.output_handler import OutputHandler

logger = logging.getLogger(__name__)


class EmailSummaryAutomation:
    """Main automation class"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize automation

        Args:
            config_path: Path to configuration file
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = None
        self.email_fetcher = None
        self.email_summarizer = None
        self.output_handler = None

    def initialize(self) -> bool:
        """
        Initialize all components

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load configuration
            self.config = self.config_loader.load_config()

            # Setup logging
            setup_logger(self.config_loader.get_logging_config())
            logger.info("=" * 80)
            logger.info("Email Summary Automation - Starting")
            logger.info("=" * 80)

            # Validate configuration
            if not self.config_loader.validate_config():
                logger.error("Configuration validation failed")
                return False

            # Initialize components
            logger.info("Initializing components...")

            self.email_fetcher = EmailFetcher(
                self.config_loader.get_email_config()
            )

            self.email_summarizer = EmailSummarizer(
                self.config_loader.get_summarization_config()
            )

            self.output_handler = OutputHandler(
                self.config_loader.get_output_config()
            )

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def run_summary(self):
        """Execute email summary process"""
        try:
            logger.info("-" * 80)
            logger.info(f"Starting email summary process - {datetime.now()}")
            logger.info("-" * 80)

            # Fetch emails
            logger.info("Step 1/4: Fetching emails...")
            with self.email_fetcher as fetcher:
                emails = fetcher.fetch_emails()

            if not emails:
                logger.warning("No emails found to summarize")
                return

            logger.info(f"Fetched {len(emails)} emails")

            # Summarize emails
            logger.info("Step 2/4: Generating summary...")
            summary = self.email_summarizer.summarize_emails(emails)

            if not summary:
                logger.error("Failed to generate summary")
                return

            # Create formatted report
            logger.info("Step 3/4: Creating report...")
            report = self.email_summarizer.create_summary_report(emails, summary)

            # Save summary
            logger.info("Step 4/4: Saving summary...")
            filepath = self.output_handler.save_summary(report, emails)

            logger.info(f"Summary saved successfully: {filepath}")

            # Send email if configured
            if self.output_handler.send_email:
                logger.info("Sending summary via email...")
                self.output_handler.send_summary_email(
                    report,
                    self.config_loader.get_email_config()
                )

            logger.info("-" * 80)
            logger.info("Email summary process completed successfully")
            logger.info("-" * 80)

        except Exception as e:
            logger.error(f"Error during summary process: {e}", exc_info=True)

    def run_scheduled(self):
        """Run automation on schedule"""
        automation_config = self.config_loader.get_automation_config()

        if not automation_config.get('enabled', False):
            logger.info("Scheduled automation is disabled")
            logger.info("Running one-time summary and exiting...")
            self.run_summary()
            return

        schedule_time = automation_config.get('schedule', '09:00')
        logger.info(f"Scheduling daily summary at {schedule_time}")

        schedule.every().day.at(schedule_time).do(self.run_summary)

        logger.info("Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

    def run_once(self):
        """Run summary once and exit"""
        logger.info("Running one-time email summary...")
        self.run_summary()


def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════╗
    ║   Email Summary Automation System          ║
    ║   אוטומציה לסיכום מיילים                  ║
    ╚════════════════════════════════════════════╝
    """)

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
Usage: python main.py [options]

Options:
  --once          Run summary once and exit
  --schedule      Run on schedule (based on config)
  -h, --help      Show this help message

If no option is provided, runs in scheduled mode by default.

Configuration:
  Edit config/config.yaml to configure email settings,
  AI provider, and scheduling options.
            """)
            return

        config_path = "config/config.yaml"
        mode = sys.argv[1] if len(sys.argv) > 1 else "--schedule"
    else:
        config_path = "config/config.yaml"
        mode = "--once"  # Default to once mode

    # Initialize automation
    automation = EmailSummaryAutomation(config_path)

    if not automation.initialize():
        print("❌ Failed to initialize automation. Check logs for details.")
        sys.exit(1)

    # Run automation based on mode
    if mode == '--once':
        automation.run_once()
    elif mode == '--schedule':
        automation.run_scheduled()
    else:
        print(f"Unknown option: {mode}")
        print("Use --help for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
