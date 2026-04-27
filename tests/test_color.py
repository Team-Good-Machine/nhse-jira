import os
import sys
from unittest.mock import patch

import nhse_jira


class TestShouldUseColor:
    """_should_use_color() checks TTY status and NO_COLOR env var."""

    def test_false_when_stdout_is_not_a_tty(self):
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert nhse_jira._should_use_color() is False

    def test_true_when_stdout_is_a_tty(self):
        with patch.object(sys.stdout, "isatty", return_value=True), \
             patch.dict(os.environ, {}, clear=True):
            assert nhse_jira._should_use_color() is True

    def test_false_when_no_color_env_set(self):
        with patch.object(sys.stdout, "isatty", return_value=True), \
             patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert nhse_jira._should_use_color() is False

    def test_false_when_no_color_is_empty_string(self):
        """NO_COLOR spec: presence of the variable is enough, value doesn't matter."""
        with patch.object(sys.stdout, "isatty", return_value=True), \
             patch.dict(os.environ, {"NO_COLOR": ""}):
            assert nhse_jira._should_use_color() is False


class TestColorInOutput:
    """Formatting functions respect the colour setting."""

    def _make_issue_table_data(self):
        return {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "Test issue",
                        "status": {"name": "Done"},
                    },
                },
            ]
        }

    def test_no_ansi_codes_when_color_disabled(self):
        output = nhse_jira.format_issue_table(
            self._make_issue_table_data(), colors=nhse_jira.Colors.disabled()
        )
        assert "\033[" not in output

    def test_ansi_codes_present_when_color_enabled(self):
        output = nhse_jira.format_issue_table(
            self._make_issue_table_data(), colors=nhse_jira.Colors.enabled()
        )
        assert "\033[" in output
