from unittest.mock import patch
import nhse_jira


class TestCmdInit:
    def test_creates_config_file(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        netrc_path = tmp_path / ".netrc"

        with patch("builtins.input", side_effect=["", ""]), \
             patch("getpass.getpass", return_value="my-token"):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        config_file = config_dir / "config.yml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "https://nhsd-jira.digital.nhs.uk" in content
        assert "MAV" in content

    def test_creates_netrc_entry(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        netrc_path = tmp_path / ".netrc"

        with patch("builtins.input", side_effect=["", ""]), \
             patch("getpass.getpass", return_value="my-token"):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        content = netrc_path.read_text()
        assert "machine nhsd-jira.digital.nhs.uk" in content
        assert "my-token" in content
        assert netrc_path.stat().st_mode & 0o777 == 0o600

    def test_custom_server_and_project(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        netrc_path = tmp_path / ".netrc"

        with patch("builtins.input", side_effect=["https://jira.example.com", "PROJ"]), \
             patch("getpass.getpass", return_value="tok"):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        config_content = (config_dir / "config.yml").read_text()
        assert "https://jira.example.com" in config_content
        assert "PROJ" in config_content

        netrc_content = netrc_path.read_text()
        assert "machine jira.example.com" in netrc_content

    def test_appends_to_existing_netrc(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        netrc_path = tmp_path / ".netrc"
        netrc_path.write_text("machine other.com login x password y\n")
        netrc_path.chmod(0o600)

        with patch("builtins.input", side_effect=["", ""]), \
             patch("getpass.getpass", return_value="my-token"):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        content = netrc_path.read_text()
        assert "machine other.com" in content
        assert "machine nhsd-jira.digital.nhs.uk" in content

    def test_prints_pat_url(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        netrc_path = tmp_path / ".netrc"

        with patch("builtins.input", side_effect=["", ""]), \
             patch("getpass.getpass", return_value="tok"):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        output = capsys.readouterr().out
        assert "ViewProfile" in output

    def test_warns_if_config_exists(self, tmp_path, capsys):
        config_dir = tmp_path / ".config" / "nhse-jira"
        config_dir.mkdir(parents=True)
        (config_dir / "config.yml").write_text("server: https://old.com\nproject: OLD\n")
        netrc_path = tmp_path / ".netrc"

        with patch("builtins.input", side_effect=["n"]):
            nhse_jira.cmd_init(config_dir=config_dir, netrc_path=netrc_path)

        # Config unchanged when user declines
        assert "old.com" in (config_dir / "config.yml").read_text()
