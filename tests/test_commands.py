from unittest.mock import MagicMock
import pytest
import nhse_jira


def _mock_session(json_response):
    session = MagicMock()
    session.get.return_value.ok = True
    session.get.return_value.json.return_value = json_response
    return session


SAMPLE_ISSUE = {
    "key": "MAV-5902",
    "fields": {
        "summary": "Fix login bug",
        "status": {"name": "Open"},
        "assignee": {"displayName": "Alice"},
        "reporter": {"displayName": "Bob"},
        "description": "Description here",
        "comment": {"comments": []},
    },
}


class TestCmdView:
    def test_prints_formatted_issue(self, capsys):
        session = _mock_session(SAMPLE_ISSUE)

        nhse_jira.cmd_view(session, "https://jira.example.com", "MAV-5902")

        output = capsys.readouterr().out
        assert "MAV-5902" in output
        assert "Fix login bug" in output
        assert "Alice" in output
