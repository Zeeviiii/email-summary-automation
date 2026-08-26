"""Tests for src.email_fetcher.EmailFetcher.

The IMAP connection is always mocked — these tests never touch the network.
"""

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from src.email_fetcher import EmailFetcher


@pytest.fixture
def fetcher(valid_config):
    return EmailFetcher(valid_config["email"])


def build_raw_email(subject="Hello", sender="a@example.com", body="Body text"):
    """Build a real RFC822 byte string the way an IMAP server would return it."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = "me@example.com"
    msg["Date"] = "Mon, 12 Aug 2026 09:00:00 +0300"
    msg.set_content(body)
    return msg.as_bytes()


class TestInitialisation:
    def test_reads_values_from_config(self, fetcher):
        assert fetcher.imap_server == "imap.gmail.com"
        assert fetcher.imap_port == 993
        assert fetcher.folder == "INBOX"
        assert fetcher.max_emails == 50

    def test_applies_defaults_for_missing_keys(self):
        fetcher = EmailFetcher({"imap_server": "imap.example.com"})

        assert fetcher.imap_port == 993
        assert fetcher.folder == "INBOX"
        assert fetcher.days_to_check == 7
        assert fetcher.connection is None


class TestConnect:
    @patch("src.email_fetcher.imaplib.IMAP4_SSL")
    def test_successful_connect_returns_true(self, mock_imap, fetcher):
        result = fetcher.connect()

        assert result is True
        mock_imap.assert_called_once_with("imap.gmail.com", 993)
        mock_imap.return_value.login.assert_called_once_with(
            "user@example.com", "app-password"
        )

    @patch("src.email_fetcher.imaplib.IMAP4_SSL")
    def test_bad_credentials_return_false_not_raise(self, mock_imap, fetcher):
        mock_imap.return_value.login.side_effect = OSError("auth failed")

        assert fetcher.connect() is False

    @patch("src.email_fetcher.imaplib.IMAP4_SSL")
    def test_unreachable_server_returns_false(self, mock_imap, fetcher):
        mock_imap.side_effect = OSError("host unreachable")

        assert fetcher.connect() is False

    def test_disconnect_without_connection_is_safe(self, fetcher):
        fetcher.disconnect()  # must not raise

    def test_disconnect_swallows_errors(self, fetcher):
        fetcher.connection = MagicMock()
        fetcher.connection.close.side_effect = OSError("already closed")

        fetcher.disconnect()  # must not raise


class TestDecodeHeaderValue:
    def test_plain_ascii_passes_through(self, fetcher):
        assert fetcher._decode_header_value("Simple subject") == "Simple subject"

    def test_empty_value_returns_empty_string(self, fetcher):
        assert fetcher._decode_header_value("") == ""
        assert fetcher._decode_header_value(None) == ""

    def test_decodes_utf8_base64_header(self, fetcher):
        # "שלום עולם" as an RFC 2047 base64-encoded header
        encoded = "=?utf-8?b?16nXnNeV150g16LXldec150=?="

        assert fetcher._decode_header_value(encoded) == "שלום עולם"

    def test_decodes_quoted_printable_header(self, fetcher):
        encoded = "=?utf-8?q?Caf=C3=A9_meeting?="

        assert fetcher._decode_header_value(encoded) == "Café meeting"

    def test_joins_multipart_header(self, fetcher):
        encoded = "=?utf-8?q?Part_one_?= and plain tail"

        result = fetcher._decode_header_value(encoded)

        assert "Part one" in result
        assert "plain tail" in result


class TestExtractBody:
    def test_extracts_plain_text_body(self, fetcher):
        msg = EmailMessage()
        msg.set_content("The quick brown fox.")

        assert fetcher._extract_body(msg) == "The quick brown fox."

    def test_strips_surrounding_whitespace(self, fetcher):
        msg = EmailMessage()
        msg.set_content("\n\n  padded body  \n\n")

        assert fetcher._extract_body(msg) == "padded body"

    def test_extracts_hebrew_body(self, fetcher):
        msg = EmailMessage()
        msg.set_content("המשמרת הועברה לשעה 07:00")

        assert fetcher._extract_body(msg) == "המשמרת הועברה לשעה 07:00"

    def test_multipart_prefers_plain_text_over_html(self, fetcher):
        msg = EmailMessage()
        msg.set_content("plain version")
        msg.add_alternative("<p>html version</p>", subtype="html")

        body = fetcher._extract_body(msg)

        assert "plain version" in body
        assert "html version" not in body

    def test_attachments_are_skipped(self, fetcher):
        msg = EmailMessage()
        msg.set_content("real body")
        msg.add_attachment(
            b"should-not-appear",
            maintype="text",
            subtype="plain",
            filename="notes.txt",
        )

        body = fetcher._extract_body(msg)

        assert "real body" in body
        assert "should-not-appear" not in body

    def test_empty_message_returns_empty_string(self, fetcher):
        msg = EmailMessage()

        assert fetcher._extract_body(msg) == ""


class TestFetchEmails:
    def _wire(self, fetcher, raw_emails, search_status="OK"):
        conn = MagicMock()
        ids = b" ".join(str(i).encode() for i in range(1, len(raw_emails) + 1))
        conn.search.return_value = (search_status, [ids])
        conn.fetch.side_effect = [("OK", [(b"header", raw)]) for raw in raw_emails]
        fetcher.connection = conn
        return conn

    def test_returns_parsed_email_dicts(self, fetcher):
        self._wire(fetcher, [build_raw_email(subject="Quarterly report")])

        emails = fetcher.fetch_emails()

        assert len(emails) == 1
        assert emails[0]["subject"] == "Quarterly report"
        assert emails[0]["from"] == "a@example.com"
        assert "Body text" in emails[0]["body"]

    def test_selects_configured_folder(self, fetcher):
        conn = self._wire(fetcher, [build_raw_email()])

        fetcher.fetch_emails()

        conn.select.assert_called_once_with("INBOX")

    def test_search_failure_returns_empty_list(self, fetcher):
        self._wire(fetcher, [build_raw_email()], search_status="NO")

        assert fetcher.fetch_emails() == []

    def test_no_matching_emails_returns_empty_list(self, fetcher):
        conn = MagicMock()
        conn.search.return_value = ("OK", [b""])
        fetcher.connection = conn

        assert fetcher.fetch_emails() == []

    def test_respects_max_emails_limit(self, fetcher):
        fetcher.max_emails = 2
        conn = MagicMock()
        conn.search.return_value = ("OK", [b"1 2 3 4 5"])
        conn.fetch.side_effect = [
            ("OK", [(b"h", build_raw_email(subject=f"Mail {i}"))]) for i in range(2)
        ]
        fetcher.connection = conn

        emails = fetcher.fetch_emails()

        assert len(emails) == 2
        assert conn.fetch.call_count == 2

    def test_skips_unparseable_email_and_continues(self, fetcher):
        conn = MagicMock()
        conn.search.return_value = ("OK", [b"1 2"])
        conn.fetch.side_effect = [
            OSError("fetch failed"),
            ("OK", [(b"h", build_raw_email(subject="Second"))]),
        ]
        fetcher.connection = conn

        emails = fetcher.fetch_emails()

        assert len(emails) == 1
        assert emails[0]["subject"] == "Second"

    def test_non_ok_fetch_status_is_skipped(self, fetcher):
        conn = MagicMock()
        conn.search.return_value = ("OK", [b"1"])
        conn.fetch.return_value = ("NO", [None])
        fetcher.connection = conn

        assert fetcher.fetch_emails() == []

    @patch("src.email_fetcher.imaplib.IMAP4_SSL")
    def test_connects_automatically_when_not_connected(self, mock_imap, fetcher):
        conn = mock_imap.return_value
        conn.search.return_value = ("OK", [b"1"])
        conn.fetch.return_value = ("OK", [(b"h", build_raw_email())])

        fetcher.fetch_emails()

        mock_imap.assert_called_once()

    @patch("src.email_fetcher.imaplib.IMAP4_SSL")
    def test_returns_empty_when_auto_connect_fails(self, mock_imap, fetcher):
        mock_imap.side_effect = OSError("unreachable")

        assert fetcher.fetch_emails() == []
