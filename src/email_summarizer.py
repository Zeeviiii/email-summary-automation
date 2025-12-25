"""
Email Summarizer Module
Handles summarization of emails using AI
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSummarizer:
    """Summarizes emails using AI"""

    def __init__(self, config: Dict):
        """
        Initialize email summarizer

        Args:
            config: Summarization configuration dictionary
        """
        self.provider = config.get('provider', 'anthropic')
        self.max_tokens = config.get('max_tokens', 500)
        self.temperature = config.get('temperature', 0.3)
        self.summary_language = config.get('summary_language', 'he')

        # Initialize AI client based on provider
        if self.provider == 'openai':
            self._init_openai(config)
        elif self.provider == 'anthropic':
            self._init_anthropic(config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _init_openai(self, config: Dict):
        """Initialize OpenAI client"""
        try:
            import openai
            self.api_key = config.get('openai_api_key')
            self.model = config.get('openai_model', 'gpt-4-turbo-preview')
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("Initialized OpenAI client")
        except ImportError:
            logger.error("OpenAI package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    def _init_anthropic(self, config: Dict):
        """Initialize Anthropic client"""
        try:
            import anthropic
            self.api_key = config.get('anthropic_api_key')
            self.model = config.get('anthropic_model', 'claude-3-5-sonnet-20241022')
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Initialized Anthropic client")
        except ImportError:
            logger.error("Anthropic package not installed. Run: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            raise

    def _create_summary_prompt(self, emails: List[Dict]) -> str:
        """
        Create prompt for email summarization

        Args:
            emails: List of email dictionaries

        Returns:
            Formatted prompt string
        """
        language_instructions = {
            'he': 'אנא סכם את המיילים הבאים בעברית.',
            'en': 'Please summarize the following emails in English.',
            'es': 'Por favor, resume los siguientes correos en español.'
        }

        instruction = language_instructions.get(
            self.summary_language,
            language_instructions['en']
        )

        prompt = f"""{instruction}

עבור כל מייל, ספק:
1. נושא המייל
2. שולח המייל
3. תאריך
4. סיכום תוכן (2-3 משפטים)
5. נקודות פעולה (אם יש)

מיילים לסיכום:
---
"""

        for i, email_data in enumerate(emails, 1):
            prompt += f"""
מייל #{i}:
נושא: {email_data.get('subject', 'ללא נושא')}
מאת: {email_data.get('from', 'לא ידוע')}
תאריך: {email_data.get('date', 'לא ידוע')}

תוכן:
{email_data.get('body', '')[:1000]}...

---
"""

        prompt += """
אנא ספק סיכום מסודר וברור של כל המיילים.
בסוף, ספק סיכום כללי של נושאי המיילים העיקריים ונקודות הפעולה החשובות.
"""

        return prompt

    def _summarize_with_openai(self, prompt: str) -> str:
        """
        Summarize using OpenAI

        Args:
            prompt: Prompt text

        Returns:
            Summary text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes emails clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            summary = response.choices[0].message.content
            logger.info("Successfully generated summary with OpenAI")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            raise

    def _summarize_with_anthropic(self, prompt: str) -> str:
        """
        Summarize using Anthropic Claude

        Args:
            prompt: Prompt text

        Returns:
            Summary text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = response.content[0].text
            logger.info("Successfully generated summary with Anthropic")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary with Anthropic: {e}")
            raise

    def summarize_emails(self, emails: List[Dict]) -> Optional[str]:
        """
        Summarize a list of emails

        Args:
            emails: List of email dictionaries

        Returns:
            Summary text or None if failed
        """
        if not emails:
            logger.warning("No emails to summarize")
            return None

        logger.info(f"Summarizing {len(emails)} emails")

        try:
            # Create prompt
            prompt = self._create_summary_prompt(emails)

            # Generate summary based on provider
            if self.provider == 'openai':
                summary = self._summarize_with_openai(prompt)
            elif self.provider == 'anthropic':
                summary = self._summarize_with_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return summary

        except Exception as e:
            logger.error(f"Failed to summarize emails: {e}")
            return None

    def create_summary_report(self, emails: List[Dict], summary: str) -> str:
        """
        Create a formatted summary report

        Args:
            emails: List of email dictionaries
            summary: AI-generated summary

        Returns:
            Formatted report
        """
        report = f"""
{'=' * 80}
סיכום מיילים - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 80}

מספר מיילים שנסרקו: {len(emails)}

{summary}

{'=' * 80}
נוצר על ידי מערכת אוטומציה לסיכום מיילים
{'=' * 80}
"""
        return report
