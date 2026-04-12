import pytest
import nhse_jira


def test_load_config_reads_yaml(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text("server: https://example.com\nproject: TEST\n")

    config = nhse_jira.load_config(config_file)

    assert config["server"] == "https://example.com"
    assert config["project"] == "TEST"


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(SystemExit, match="Config file not found"):
        nhse_jira.load_config(tmp_path / "nonexistent.yml")


def test_load_token_from_netrc(tmp_path):
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text("machine example.com login _ password secret-token\n")
    netrc_file.chmod(0o600)

    token = nhse_jira.load_token("https://example.com", netrc_file)

    assert token == "secret-token"


def test_load_token_missing_entry_raises(tmp_path):
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text("machine other.com login _ password tok\n")
    netrc_file.chmod(0o600)

    with pytest.raises(SystemExit, match="No .netrc entry"):
        nhse_jira.load_token("https://example.com", netrc_file)


def test_load_config_with_custom_fields(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        "server: https://example.com\n"
        "project: TEST\n"
        "custom_fields:\n"
        "  metadata:\n"
        "    Clinical Severity:\n"
        "      field: customfield_37401\n"
        "      format: option\n"
    )

    config = nhse_jira.load_config(config_file)

    assert config["custom_fields"]["metadata"]["Clinical Severity"]["field"] == "customfield_37401"
    assert config["custom_fields"]["metadata"]["Clinical Severity"]["format"] == "option"


def test_load_config_without_custom_fields(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text("server: https://example.com\nproject: TEST\n")

    config = nhse_jira.load_config(config_file)

    assert config.get("custom_fields") is None
