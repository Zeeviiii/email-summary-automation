"""
Configuration Loader Module
Handles loading and validation of configuration
"""

import yaml
import os
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages configuration"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize config loader

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None

    def load_config(self) -> Dict:
        """
        Load configuration from YAML file

        Returns:
            Configuration dictionary
        """
        # Load environment variables from .env file
        load_dotenv()

        if not os.path.exists(self.config_path):
            logger.error(f"Configuration file not found: {self.config_path}")
            logger.info("Please copy config/config.example.yaml to config/config.yaml and fill in your details")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # Override with environment variables if set
            self._apply_env_overrides()

            logger.info(f"Successfully loaded configuration from {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration"""
        env_mappings = {
            'EMAIL_ADDRESS': ('email', 'email_address'),
            'EMAIL_PASSWORD': ('email', 'password'),
            'IMAP_SERVER': ('email', 'imap_server'),
            'OPENAI_API_KEY': ('summarization', 'openai_api_key'),
            'ANTHROPIC_API_KEY': ('summarization', 'anthropic_api_key'),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value and section in self.config:
                self.config[section][key] = value
                logger.debug(f"Applied environment override for {section}.{key}")

    def validate_config(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.config:
            logger.error("Configuration not loaded")
            return False

        # Check required sections
        required_sections = ['email', 'summarization', 'output']
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False

        # Validate email config
        email_config = self.config['email']
        required_email_fields = ['imap_server', 'email_address', 'password']
        for field in required_email_fields:
            if not email_config.get(field):
                logger.error(f"Missing required email configuration: {field}")
                return False

        # Validate summarization config
        summary_config = self.config['summarization']
        provider = summary_config.get('provider')

        if provider == 'openai':
            if not summary_config.get('openai_api_key'):
                logger.error("OpenAI API key not configured")
                return False
        elif provider == 'anthropic':
            if not summary_config.get('anthropic_api_key'):
                logger.error("Anthropic API key not configured")
                return False
        else:
            logger.error(f"Invalid summarization provider: {provider}")
            return False

        logger.info("Configuration validation successful")
        return True

    def get_email_config(self) -> Dict:
        """Get email configuration section"""
        return self.config.get('email', {})

    def get_summarization_config(self) -> Dict:
        """Get summarization configuration section"""
        return self.config.get('summarization', {})

    def get_automation_config(self) -> Dict:
        """Get automation configuration section"""
        return self.config.get('automation', {})

    def get_output_config(self) -> Dict:
        """Get output configuration section"""
        return self.config.get('output', {})

    def get_logging_config(self) -> Dict:
        """Get logging configuration section"""
        return self.config.get('logging', {'level': 'INFO'})
