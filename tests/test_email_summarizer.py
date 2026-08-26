"""Tests for src.email_summarizer.EmailSummarizer.

No live AI calls are made — both provider clients are patched.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.email_summarizer import EmailSummarizer


@pytest.fixture
def anthropic_summarizer(valid_config):
    """A summarizer wired to a mocked Anthropic client."""
    with patch("anthropic.Anthropic") as mock_client:
        summarizer = EmailSummarizer(valid_config["summarization"])
        summarizer.client = mock_client.return_value
        yield summarizer


@pytest.fixture
def openai_summarizer(valid_config):
    """A summarizer wired to a mocked OpenAI client."""
    config = dict(valid_config["summarization"])
    config["provider"] = "openai"
    config["openai_api_key"] = "sk-test"
    with patch("openai.OpenAI") as mock_client:
        summarizer = EmailSummarizer(config)
        summarizer.client = mock_client.return_value
        yield summarizer


def anthropic_reply(text):
    """Shape a mock matching the Anthropic messages API response."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


def openai_reply(text):
    """Shape a mock matching the OpenAI chat completions response."""
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    return response


class TestProviderSelection:
    def test_anthropic_provider_initialises(self, anthropic_summarizer):
        assert anthropic_summarizer.provider == "anthropic"
        assert anthropic_summarizer.model == "claude-3-5-sonnet-20241022"

    def test_openai_provider_initialises(self, openai_summarizer):
        assert openai_summarizer.provider == "openai"
        assert openai_summarizer.model == "gpt-4-turbo-preview"

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported provider"):
            EmailSummarizer({"provider": "gemini"})

    def test_settings_read_from_config(self, anthropic_summarizer):
        assert anthropic_summarizer.max_tokens == 500
        assert anthropic_summarizer.temperature == 0.3
        assert anthropic_summarizer.summary_language == "he"

    def test_defaults_applied_when_absent(self):
        with patch("anthropic.Anthropic"):
            summarizer = EmailSummarizer({"provider": "anthropic"})

        assert summarizer.max_tokens == 500
        assert summarizer.temperature == 0.3
        assert summarizer.summary_language == "he"


class TestCreateSummaryPrompt:
    def test_includes_every_email_subject(self, anthropic_summarizer, sample_emails):
        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "Quarterly report" in prompt
        assert "עדכון משמרת" in prompt

    def test_includes_sender_and_date(self, anthropic_summarizer, sample_emails):
        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "boss@example.com" in prompt
        assert "12 Aug 2026" in prompt

    def test_numbers_each_email(self, anthropic_summarizer, sample_emails):
        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "#1" in prompt
        assert "#2" in prompt

    def test_hebrew_instruction_for_he_language(
        self, anthropic_summarizer, sample_emails
    ):
        anthropic_summarizer.summary_language = "he"

        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "אנא סכם את המיילים הבאים בעברית" in prompt

    def test_english_instruction_for_en_language(
        self, anthropic_summarizer, sample_emails
    ):
        anthropic_summarizer.summary_language = "en"

        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "in English" in prompt

    def test_unknown_language_falls_back_to_english(
        self, anthropic_summarizer, sample_emails
    ):
        anthropic_summarizer.summary_language = "fr"

        prompt = anthropic_summarizer._create_summary_prompt(sample_emails)

        assert "in English" in prompt

    def test_long_body_is_truncated_to_1000_chars(self, anthropic_summarizer):
        emails = [{"subject": "Big", "from": "a@b.c", "body": "x" * 5000}]

        prompt = anthropic_summarizer._create_summary_prompt(emails)

        assert prompt.count("x") == 1000

    def test_missing_fields_get_placeholders(self, anthropic_summarizer):
        prompt = anthropic_summarizer._create_summary_prompt([{}])

        assert "ללא נושא" in prompt
        assert "לא ידוע" in prompt


class TestSummarizeEmails:
    def test_empty_list_returns_none_without_calling_api(self, anthropic_summarizer):
        result = anthropic_summarizer.summarize_emails([])

        assert result is None
        anthropic_summarizer.client.messages.create.assert_not_called()

    def test_anthropic_returns_summary_text(self, anthropic_summarizer, sample_emails):
        anthropic_summarizer.client.messages.create.return_value = anthropic_reply(
            "סיכום של שני מיילים."
        )

        result = anthropic_summarizer.summarize_emails(sample_emails)

        assert result == "סיכום של שני מיילים."

    def test_openai_returns_summary_text(self, openai_summarizer, sample_emails):
        openai_summarizer.client.chat.completions.create.return_value = openai_reply(
            "Summary of two emails."
        )

        result = openai_summarizer.summarize_emails(sample_emails)

        assert result == "Summary of two emails."

    def test_anthropic_called_with_configured_model_and_limits(
        self, anthropic_summarizer, sample_emails
    ):
        anthropic_summarizer.client.messages.create.return_value = anthropic_reply("ok")

        anthropic_summarizer.summarize_emails(sample_emails)

        kwargs = anthropic_summarizer.client.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert kwargs["max_tokens"] == 500
        assert kwargs["temperature"] == 0.3

    def test_openai_sends_system_and_user_messages(
        self, openai_summarizer, sample_emails
    ):
        openai_summarizer.client.chat.completions.create.return_value = openai_reply(
            "ok"
        )

        openai_summarizer.summarize_emails(sample_emails)

        kwargs = openai_summarizer.client.chat.completions.create.call_args.kwargs
        roles = [m["role"] for m in kwargs["messages"]]
        assert roles == ["system", "user"]

    def test_api_error_does_not_leak_exception(
        self, anthropic_summarizer, sample_emails
    ):
        anthropic_summarizer.client.messages.create.side_effect = RuntimeError(
            "rate limited"
        )

        result = anthropic_summarizer.summarize_emails(sample_emails)

        assert result is None
