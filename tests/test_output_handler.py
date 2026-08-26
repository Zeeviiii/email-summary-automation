"""Tests for src.output_handler.OutputHandler."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.output_handler import OutputHandler


@pytest.fixture
def handler_factory(tmp_path):
    """Build an OutputHandler writing into an isolated temp directory."""

    def _make(**overrides):
        config = {"output_dir": str(tmp_path / "summaries"), "format": "txt"}
        config.update(overrides)
        return OutputHandler(config)

    return _make


class TestInitialisation:
    def test_creates_output_directory(self, tmp_path):
        target = tmp_path / "new_dir"
        assert not target.exists()

        OutputHandler({"output_dir": str(target)})

        assert target.is_dir()

    def test_existing_directory_is_reused(self, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()
        (target / "keep.txt").write_text("data", encoding="utf-8")

        OutputHandler({"output_dir": str(target)})

        assert (target / "keep.txt").read_text(encoding="utf-8") == "data"

    def test_defaults_applied_when_config_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        handler = OutputHandler({})

        assert handler.output_dir == "summaries"
        assert handler.format == "txt"
        assert handler.send_email is False


class TestSaveSummary:
    def test_txt_written_with_summary_text(self, handler_factory, sample_emails):
        handler = handler_factory(format="txt")

        path = handler.save_summary("Two emails today.", sample_emails)

        assert path.endswith(".txt")
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            assert f.read() == "Two emails today."

    def test_hebrew_summary_round_trips(self, handler_factory, sample_emails):
        handler = handler_factory(format="txt")
        summary = "התקבלו שני מיילים חדשים."

        path = handler.save_summary(summary, sample_emails)

        with open(path, encoding="utf-8") as f:
            assert f.read() == summary

    def test_json_structure_and_email_count(self, handler_factory, sample_emails):
        handler = handler_factory(format="json")

        path = handler.save_summary("Summary body", sample_emails)

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["email_count"] == 2
        assert data["summary"] == "Summary body"
        assert len(data["emails"]) == 2
        assert data["emails"][0]["subject"] == "Quarterly report"
        assert data["emails"][1]["subject"] == "עדכון משמרת"

    def test_json_omits_email_bodies(self, handler_factory, sample_emails):
        """Only metadata is persisted — bodies must not leak into the file."""
        handler = handler_factory(format="json")

        path = handler.save_summary("Summary", sample_emails)

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assert set(data["emails"][0]) == {"subject", "from", "date"}

    def test_html_contains_summary_and_count(self, handler_factory, sample_emails):
        handler = handler_factory(format="html")

        path = handler.save_summary("Digest text", sample_emails)

        assert path.endswith(".html")
        with open(path, encoding="utf-8") as f:
            html = f.read()

        assert "Digest text" in html
        assert "<!DOCTYPE html>" in html
        assert 'dir="rtl"' in html

    def test_unknown_format_falls_back_to_txt(self, handler_factory, sample_emails):
        handler = handler_factory(format="pdf")

        path = handler.save_summary("Fallback", sample_emails)

        assert path.endswith(".txt")

    def test_empty_email_list_still_writes_file(self, handler_factory):
        handler = handler_factory(format="json")

        path = handler.save_summary("Nothing new.", [])

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["email_count"] == 0
        assert data["emails"] == []

    def test_saved_file_lands_in_configured_directory(
        self, handler_factory, sample_emails
    ):
        handler = handler_factory()

        path = handler.save_summary("Body", sample_emails)

        assert os.path.dirname(path) == handler.output_dir


class TestSendSummaryEmail:
    def test_returns_false_when_sending_disabled(self, handler_factory, valid_config):
        handler = handler_factory(send_email=False)

        result = handler.send_summary_email("Body", valid_config["email"])

        assert result is False

    def test_returns_false_without_recipient(self, handler_factory, valid_config):
        handler = handler_factory(send_email=True, recipient_email=None)

        result = handler.send_summary_email("Body", valid_config["email"])

        assert result is False

    @patch("src.output_handler.smtplib.SMTP_SSL")
    def test_sends_and_returns_true(self, mock_smtp, handler_factory, valid_config):
        server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = server
        handler = handler_factory(send_email=True, recipient_email="to@example.com")

        result = handler.send_summary_email("Body", valid_config["email"])

        assert result is True
        server.login.assert_called_once()
        server.send_message.assert_called_once()

    @patch("src.output_handler.smtplib.SMTP_SSL")
    def test_derives_smtp_host_from_imap_host(
        self, mock_smtp, handler_factory, valid_config
    ):
        mock_smtp.return_value.__enter__.return_value = MagicMock()
        handler = handler_factory(send_email=True, recipient_email="to@example.com")

        handler.send_summary_email("Body", valid_config["email"])

        assert mock_smtp.call_args[0][0] == "smtp.gmail.com"

    @patch("src.output_handler.smtplib.SMTP_SSL")
    def test_smtp_failure_returns_false_not_raise(
        self, mock_smtp, handler_factory, valid_config
    ):
        mock_smtp.side_effect = OSError("connection refused")
        handler = handler_factory(send_email=True, recipient_email="to@example.com")

        result = handler.send_summary_email("Body", valid_config["email"])

        assert result is False
