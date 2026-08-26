"""Shared fixtures for the test suite."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def valid_config():
    """A minimal configuration that passes validation."""
    return {
        "email": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "email_address": "user@example.com",
            "password": "app-password",
            "folder": "INBOX",
            "days_to_check": 7,
            "max_emails": 50,
        },
        "summarization": {
            "provider": "anthropic",
            "anthropic_api_key": "test-key",
            "anthropic_model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "temperature": 0.3,
            "summary_language": "he",
        },
        "output": {
            "output_dir": "summaries",
            "format": "txt",
            "send_email": False,
        },
        "logging": {"level": "INFO"},
    }


@pytest.fixture
def config_file(tmp_path, valid_config):
    """Write valid_config to a real YAML file and return its path."""
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(valid_config), encoding="utf-8")
    return str(path)


@pytest.fixture
def sample_emails():
    """Two representative fetched emails, including Hebrew content."""
    return [
        {
            "subject": "Quarterly report",
            "from": "boss@example.com",
            "date": "Mon, 12 Aug 2026 09:00:00 +0300",
            "body": "Please review the attached numbers before Thursday.",
        },
        {
            "subject": "עדכון משמרת",
            "from": "shift@example.co.il",
            "date": "Tue, 13 Aug 2026 07:30:00 +0300",
            "body": "המשמרת הועברה לשעה 07:00.",
        },
    ]
