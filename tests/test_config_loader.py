"""Tests for src.config_loader.ConfigLoader."""

import pytest
import yaml

from src.config_loader import ConfigLoader


class TestLoadConfig:
    def test_loads_yaml_file(self, config_file):
        loader = ConfigLoader(config_file)
        config = loader.load_config()

        assert config["email"]["imap_server"] == "imap.gmail.com"
        assert config["summarization"]["provider"] == "anthropic"

    def test_missing_file_raises_file_not_found(self, tmp_path):
        loader = ConfigLoader(str(tmp_path / "does-not-exist.yaml"))

        with pytest.raises(FileNotFoundError):
            loader.load_config()

    def test_malformed_yaml_raises(self, tmp_path):
        path = tmp_path / "broken.yaml"
        path.write_text("email:\n  imap_server: [unclosed", encoding="utf-8")
        loader = ConfigLoader(str(path))

        with pytest.raises(yaml.YAMLError):
            loader.load_config()

    def test_reads_utf8_content(self, tmp_path, valid_config):
        valid_config["output"]["recipient_email"] = "משתמש@example.com"
        path = tmp_path / "config.yaml"
        path.write_text(
            yaml.safe_dump(valid_config, allow_unicode=True), encoding="utf-8"
        )

        config = ConfigLoader(str(path)).load_config()

        assert config["output"]["recipient_email"] == "משתמש@example.com"


class TestEnvOverrides:
    def test_env_var_overrides_yaml_value(self, config_file, monkeypatch):
        monkeypatch.setenv("EMAIL_ADDRESS", "override@example.com")

        config = ConfigLoader(config_file).load_config()

        assert config["email"]["email_address"] == "override@example.com"

    def test_yaml_value_kept_when_env_absent(self, config_file, monkeypatch):
        monkeypatch.delenv("EMAIL_ADDRESS", raising=False)

        config = ConfigLoader(config_file).load_config()

        assert config["email"]["email_address"] == "user@example.com"

    def test_api_key_override_applies_to_summarization(self, config_file, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")

        config = ConfigLoader(config_file).load_config()

        assert config["summarization"]["anthropic_api_key"] == "sk-ant-from-env"

    def test_empty_env_var_does_not_override(self, config_file, monkeypatch):
        monkeypatch.setenv("IMAP_SERVER", "")

        config = ConfigLoader(config_file).load_config()

        assert config["email"]["imap_server"] == "imap.gmail.com"


class TestValidateConfig:
    def _loader(self, config):
        loader = ConfigLoader()
        loader.config = config
        return loader

    def test_valid_config_passes(self, valid_config):
        assert self._loader(valid_config).validate_config() is True

    def test_unloaded_config_fails(self):
        assert ConfigLoader().validate_config() is False

    @pytest.mark.parametrize("section", ["email", "summarization", "output"])
    def test_missing_required_section_fails(self, valid_config, section):
        del valid_config[section]

        assert self._loader(valid_config).validate_config() is False

    @pytest.mark.parametrize("field", ["imap_server", "email_address", "password"])
    def test_missing_email_field_fails(self, valid_config, field):
        valid_config["email"][field] = ""

        assert self._loader(valid_config).validate_config() is False

    def test_anthropic_without_key_fails(self, valid_config):
        valid_config["summarization"]["anthropic_api_key"] = ""

        assert self._loader(valid_config).validate_config() is False

    def test_openai_without_key_fails(self, valid_config):
        valid_config["summarization"]["provider"] = "openai"
        valid_config["summarization"]["openai_api_key"] = ""

        assert self._loader(valid_config).validate_config() is False

    def test_openai_with_key_passes(self, valid_config):
        valid_config["summarization"]["provider"] = "openai"
        valid_config["summarization"]["openai_api_key"] = "sk-test"

        assert self._loader(valid_config).validate_config() is True

    @pytest.mark.parametrize("provider", ["gemini", "", None])
    def test_unknown_provider_fails(self, valid_config, provider):
        valid_config["summarization"]["provider"] = provider

        assert self._loader(valid_config).validate_config() is False


class TestSectionGetters:
    def test_getters_return_their_sections(self, config_file):
        loader = ConfigLoader(config_file)
        loader.load_config()

        assert loader.get_email_config()["imap_port"] == 993
        assert loader.get_summarization_config()["max_tokens"] == 500
        assert loader.get_output_config()["format"] == "txt"

    def test_missing_section_returns_empty_dict(self, valid_config):
        del valid_config["output"]
        loader = ConfigLoader()
        loader.config = valid_config

        assert loader.get_output_config() == {}

    def test_logging_config_has_default_level(self, valid_config):
        del valid_config["logging"]
        loader = ConfigLoader()
        loader.config = valid_config

        assert loader.get_logging_config() == {"level": "INFO"}
