from pathlib import Path

from scripts.check_env_contract import (
    parse_env_template,
    secret_placeholder_violations,
    settings_variables,
    validate_contract,
)


def test_repository_environment_contract_is_complete_and_safe():
    assert validate_contract() == []


def test_template_parser_rejects_duplicates_and_invalid_lines(tmp_path: Path):
    template = tmp_path / ".env.example"
    template.write_text(
        "VALID_NAME=one\nVALID_NAME=two\ninvalid-name=value\nMISSING_EQUALS\n",
        encoding="utf-8",
    )

    values, violations = parse_env_template(template)

    assert values == {"VALID_NAME": "one"}
    assert len(violations) == 3


def test_sensitive_template_values_must_be_placeholders():
    violations = secret_placeholder_violations(
        {
            "OPENAI_API_KEY": "real-looking-key",
            "TOSS_CLIENT_SECRET": "change-me",
            "DATABASE_URL": "postgresql+psycopg://user:unsafe@database/app",
        }
    )

    assert violations == [
        "OPENAI_API_KEY: sensitive template values must be empty or use change-me",
        "DATABASE_URL: template password must use change-me",
    ]


def test_settings_parser_reads_only_annotated_fields(tmp_path: Path):
    settings_file = tmp_path / "settings.py"
    settings_file.write_text(
        "class Settings:\n"
        "    model_config = {}\n"
        "    database_url: str = 'sqlite://'\n"
        "    _private: str = 'ignored'\n"
        "    def method(self):\n"
        "        return None\n",
        encoding="utf-8",
    )

    assert settings_variables(settings_file) == {"DATABASE_URL"}
