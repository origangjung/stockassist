from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MONITORING = ROOT / "infrastructure" / "monitoring"


def load_yaml(name: str) -> dict:
    with (MONITORING / name).open(encoding="utf-8") as source:
        value = yaml.safe_load(source)
    assert isinstance(value, dict)
    return value


def test_prometheus_routes_alerts_to_internal_alertmanager():
    config = load_yaml("prometheus.yml")
    targets = config["alerting"]["alertmanagers"][0]["static_configs"][0]["targets"]
    assert targets == ["alertmanager:9093"]
    assert "/etc/prometheus/alert_rules.yml" in config["rule_files"]


def test_default_alertmanager_is_fail_safe_and_suppresses_warning_noise():
    config = load_yaml("alertmanager.yml")
    assert config["route"]["receiver"] == "stockpilot-local"
    receiver = config["receivers"][0]
    assert receiver == {"name": "stockpilot-local"}
    inhibition = config["inhibit_rules"][0]
    assert 'alertname="StockPilotApiUnavailable"' in inhibition["source_matchers"]
    assert 'severity="warning"' in inhibition["target_matchers"]
    assert inhibition["equal"] == ["service"]


def test_all_alerts_have_service_and_severity_routing_labels():
    config = load_yaml("alert_rules.yml")
    rules = config["groups"][0]["rules"]
    assert len(rules) == 4
    assert all(rule["labels"]["service"] == "stockpilot-api" for rule in rules)
    assert {rule["labels"]["severity"] for rule in rules} == {"critical", "warning"}


def test_slack_example_uses_a_secret_file_and_contains_no_webhook():
    path = MONITORING / "alertmanager.slack.example.yml"
    text = path.read_text(encoding="utf-8")
    config = yaml.safe_load(text)
    assert config["global"]["slack_api_url_file"] == "/run/secrets/slack_webhook_url"
    assert "hooks.slack.com" not in text
