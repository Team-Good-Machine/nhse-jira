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


SAMPLE_SEARCH = {
    "issues": [
        {"key": "MAV-1", "fields": {"summary": "First", "status": {"name": "Done"}}},
        {"key": "MAV-2", "fields": {"summary": "Second", "status": {"name": "Open"}}},
    ]
}


class TestBuildListJql:
    def test_mine_flag(self):
        result = nhse_jira.build_list_jql(mine=True)
        assert result == "assignee = currentUser()"

    def test_status_flag(self):
        result = nhse_jira.build_list_jql(status="In Progress")
        assert result == "status = 'In Progress'"

    def test_mine_and_status(self):
        result = nhse_jira.build_list_jql(mine=True, status="Done")
        assert "assignee = currentUser()" in result
        assert "status = 'Done'" in result
        assert " AND " in result

    def test_raw_jql(self):
        result = nhse_jira.build_list_jql(jql="type = Bug")
        assert result == "type = Bug"

    def test_empty_defaults_to_order_by(self):
        result = nhse_jira.build_list_jql()
        assert "ORDER BY" in result


class TestCmdList:
    def test_prints_table(self, capsys):
        session = _mock_session(SAMPLE_SEARCH)

        nhse_jira.cmd_list(session, "https://jira.example.com", "MAV", jql="status = Open")

        output = capsys.readouterr().out
        assert "MAV-1" in output
        assert "First" in output


SAMPLE_TRANSITIONS = {
    "transitions": [
        {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "21", "name": "Done", "to": {"name": "Done"}},
        {"id": "31", "name": "Reopen", "to": {"name": "Open"}},
    ]
}


class TestCmdTransition:
    def test_successful_transition(self, capsys):
        session = MagicMock()
        session.get.return_value.ok = True
        session.get.return_value.json.return_value = SAMPLE_TRANSITIONS
        session.post.return_value.ok = True
        session.post.return_value.status_code = 204
        session.post.return_value.content = b""

        nhse_jira.cmd_transition(session, "https://jira.example.com", "MAV-5902", "In Progress")

        session.post.assert_called_once()
        output = capsys.readouterr().out
        assert "MAV-5902" in output
        assert "In Progress" in output

    def test_invalid_transition_shows_available(self, capsys):
        session = MagicMock()
        session.get.return_value.ok = True
        session.get.return_value.json.return_value = SAMPLE_TRANSITIONS

        with pytest.raises(SystemExit):
            nhse_jira.cmd_transition(session, "https://jira.example.com", "MAV-5902", "Nonexistent")

        output = capsys.readouterr().err
        assert "In Progress" in output
        assert "Done" in output
        assert "Open" in output

    def test_no_status_lists_available(self, capsys):
        session = MagicMock()
        session.get.return_value.ok = True
        session.get.return_value.json.return_value = SAMPLE_TRANSITIONS

        nhse_jira.cmd_transition(session, "https://jira.example.com", "MAV-5902", None)

        session.post.assert_not_called()
        output = capsys.readouterr().out
        assert "MAV-5902" in output
        assert "In Progress" in output
        assert "Done" in output
        assert "Open" in output


SAMPLE_RELEASE_SEARCH = {
    "issues": [
        {"key": "MAV-10", "fields": {"summary": "Add feature X"}},
        {"key": "MAV-11", "fields": {"summary": "Fix bug Y"}},
    ]
}


class TestCmdRelease:
    def test_prints_release_issues(self, capsys):
        session = _mock_session(SAMPLE_RELEASE_SEARCH)

        nhse_jira.cmd_release(session, "https://jira.example.com", "MAV", "7.8.0")

        output = capsys.readouterr().out
        assert "MAV-10" in output
        assert "Add feature X" in output
        assert "MAV-11" in output
        assert "Fix bug Y" in output


SAMPLE_VERSIONS = [
    {
        "name": "7.7.0",
        "released": True,
        "releaseDate": "2026-03-01",
    },
    {
        "name": "7.8.0",
        "released": False,
    },
    {
        "name": "7.9.0",
        "released": False,
    },
]


class TestCmdReleases:
    def test_lists_all_versions(self, capsys):
        session = _mock_session(SAMPLE_VERSIONS)

        nhse_jira.cmd_releases(session, "https://jira.example.com", "MAV")

        output = capsys.readouterr().out
        assert "7.7.0" in output
        assert "7.8.0" in output
        assert "7.9.0" in output

    def test_shows_release_status(self, capsys):
        session = _mock_session(SAMPLE_VERSIONS)

        nhse_jira.cmd_releases(session, "https://jira.example.com", "MAV")

        output = capsys.readouterr().out
        assert "Released" in output
        assert "Unreleased" in output

    def test_shows_release_date(self, capsys):
        session = _mock_session(SAMPLE_VERSIONS)

        nhse_jira.cmd_releases(session, "https://jira.example.com", "MAV")

        output = capsys.readouterr().out
        assert "2026-03-01" in output

    def test_unreleased_filter(self, capsys):
        session = _mock_session(SAMPLE_VERSIONS)

        nhse_jira.cmd_releases(session, "https://jira.example.com", "MAV", unreleased=True)

        output = capsys.readouterr().out
        assert "7.7.0" not in output
        assert "7.8.0" in output
        assert "7.9.0" in output
