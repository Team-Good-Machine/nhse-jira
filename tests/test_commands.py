from unittest.mock import MagicMock

import nhse_jira
import pytest


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

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-5902"])

        output = capsys.readouterr().out
        assert "MAV-5902" in output
        assert "Fix login bug" in output
        assert "Alice" in output

    def test_fetches_epic_name(self, capsys):
        issue = {
            "key": "MAV-100",
            "fields": {
                "summary": "Child ticket",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
                "description": "Desc",
                "comment": {"comments": []},
                "customfield_10005": "MAV-50",
            },
        }
        epic = {
            "key": "MAV-50",
            "fields": {"summary": "Improve national reporting"},
        }
        session = MagicMock()
        session.get.return_value.ok = True
        session.get.return_value.json.side_effect = [issue, epic]

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-100"], epic_field="customfield_10005")

        output = capsys.readouterr().out
        assert "MAV-50" in output
        assert "Improve national reporting" in output


def _issue(key, summary="A summary"):
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "status": {"name": "Open"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "description": "Description",
            "comment": {"comments": []},
        },
    }


class TestCmdViewMultiple:
    def test_two_keys_prints_both(self, capsys):
        search = {"issues": [_issue("MAV-1", "First"), _issue("MAV-2", "Second")]}
        session = _mock_session(search)

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-1", "MAV-2"])

        output = capsys.readouterr().out
        assert "MAV-1" in output
        assert "First" in output
        assert "MAV-2" in output
        assert "Second" in output

    def test_three_keys_make_one_http_request(self):
        search = {"issues": [_issue("MAV-1"), _issue("MAV-2"), _issue("MAV-3")]}
        session = _mock_session(search)

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-1", "MAV-2", "MAV-3"])

        assert session.get.call_count == 1

    def test_single_key_still_uses_issue_endpoint(self):
        session = _mock_session(_issue("MAV-5902"))

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-5902"])

        assert session.get.call_count == 1
        url = session.get.call_args[0][0]
        assert url.endswith("/rest/api/2/issue/MAV-5902")

    def test_output_preserves_command_line_order(self, capsys):
        # Jira returns reversed; CLI asked for MAV-1, MAV-2, MAV-3
        search = {
            "issues": [
                _issue("MAV-3", "Third"),
                _issue("MAV-1", "First"),
                _issue("MAV-2", "Second"),
            ]
        }
        session = _mock_session(search)

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-1", "MAV-2", "MAV-3"])

        out = capsys.readouterr().out
        # find heading positions
        pos_1 = out.find("MAV-1: First")
        pos_2 = out.find("MAV-2: Second")
        pos_3 = out.find("MAV-3: Third")
        assert 0 <= pos_1 < pos_2 < pos_3, f"got order: {pos_1=} {pos_2=} {pos_3=}\n{out}"

    def test_unknown_key_reported_valid_still_print(self, capsys):
        # Jira finds MAV-1 but not MAV-99999
        search = {"issues": [_issue("MAV-1", "Real ticket")]}
        session = _mock_session(search)

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-1", "MAV-99999"])

        captured = capsys.readouterr()
        assert "MAV-1" in captured.out
        assert "Real ticket" in captured.out
        assert "MAV-99999" in captured.err

    def test_three_keys_use_search_endpoint_with_jql_in(self):
        search = {"issues": [_issue("MAV-1"), _issue("MAV-2"), _issue("MAV-3")]}
        session = _mock_session(search)

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-1", "MAV-2", "MAV-3"])

        url, kwargs = session.get.call_args[0], session.get.call_args[1]
        assert url[0].endswith("/rest/api/2/search")
        jql = kwargs["params"]["jql"]
        assert "key in" in jql
        assert "MAV-1" in jql and "MAV-2" in jql and "MAV-3" in jql


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

    def test_with_extra_fields(self, capsys):
        data = {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "First",
                        "status": {"name": "Done"},
                        "customfield_10595": {"value": "Triaged"},
                    },
                },
            ]
        }
        session = _mock_session(data)
        extra_fields = [("Clinical Safety", "customfield_10595", "option")]

        nhse_jira.cmd_list(
            session, "https://jira.example.com", "MAV",
            jql="status = Done", extra_fields=extra_fields,
        )

        output = capsys.readouterr().out
        assert "Triaged" in output


class TestCmdReleaseFields:
    def test_with_extra_fields(self, capsys):
        data = {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "First",
                        "status": {"name": "Done"},
                        "customfield_22907": "9/9 - Done",
                    },
                },
            ]
        }
        session = _mock_session(data)
        extra_fields = [("Progress", "customfield_22907", "string")]

        nhse_jira.cmd_release(
            session, "https://jira.example.com", "MAV", "7.9.0",
            extra_fields=extra_fields,
        )

        output = capsys.readouterr().out
        assert "MAV-1" in output
        assert "9/9 - Done" in output


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


class TestMainViewArgs:
    def _patch_main_deps(self, monkeypatch):
        monkeypatch.setattr(nhse_jira, "load_config", lambda: {"server": "https://jira.example.com", "project": "MAV"})
        monkeypatch.setattr(nhse_jira, "load_token", lambda server: "fake")
        monkeypatch.setattr(nhse_jira, "create_session", lambda token: MagicMock())

    def test_numeric_multi_keys_use_default_project(self, monkeypatch):
        self._patch_main_deps(monkeypatch)
        monkeypatch.setattr("sys.argv", ["nhse-jira", "view", "1", "2", "3"])
        captured = {}

        def fake_view(session, base_url, issue_keys, **kwargs):
            captured["keys"] = issue_keys

        monkeypatch.setattr(nhse_jira, "cmd_view", fake_view)
        nhse_jira.main()

        assert captured["keys"] == ["MAV-1", "MAV-2", "MAV-3"]

    def test_mixed_numeric_and_full_keys(self, monkeypatch):
        self._patch_main_deps(monkeypatch)
        monkeypatch.setattr("sys.argv", ["nhse-jira", "view", "1", "OTHER-99"])
        captured = {}

        def fake_view(session, base_url, issue_keys, **kwargs):
            captured["keys"] = issue_keys

        monkeypatch.setattr(nhse_jira, "cmd_view", fake_view)
        nhse_jira.main()

        assert captured["keys"] == ["MAV-1", "OTHER-99"]


class TestMainJiraErrorHandling:
    def test_jira_error_prints_message_to_stderr(self, capsys, monkeypatch):
        """JiraError should produce a clean error message, not a traceback."""
        monkeypatch.setattr("sys.argv", ["nhse-jira", "release", "v99.0.0"])
        monkeypatch.setattr(nhse_jira, "load_config", lambda: {"server": "https://jira.example.com", "project": "MAV"})
        monkeypatch.setattr(nhse_jira, "load_token", lambda server: "fake")
        monkeypatch.setattr(nhse_jira, "create_session", lambda token: MagicMock())

        def fake_release(*a, **kw):
            raise nhse_jira.JiraError("HTTP 400: The value 'v99.0.0' does not exist for the field 'fixVersion'.")

        monkeypatch.setattr(nhse_jira, "cmd_release", fake_release)

        with pytest.raises(SystemExit) as exc_info:
            nhse_jira.main()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "v99.0.0" in err
        assert "Traceback" not in err


class TestCmdEdit:
    def test_updates_summary_via_put(self, capsys):
        session = MagicMock()
        session.put.return_value.ok = True
        session.put.return_value.status_code = 204
        session.put.return_value.content = b""

        nhse_jira.cmd_edit(session, "https://jira.example.com", "MAV-5902", summary="New title")

        session.put.assert_called_once()
        call_args = session.put.call_args
        assert "issue/MAV-5902" in call_args[0][0]
        assert call_args[1]["json"] == {"fields": {"summary": "New title"}}

        output = capsys.readouterr().out
        assert "MAV-5902" in output

    def test_no_fields_prints_error(self, capsys):
        session = MagicMock()

        with pytest.raises(SystemExit):
            nhse_jira.cmd_edit(session, "https://jira.example.com", "MAV-5902")

        output = capsys.readouterr().err
        assert "Nothing to update" in output


class TestParserEdit:
    def test_edit_title_flag(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["edit", "MAV-5902", "--title", "New title"])
        assert args.issue == "MAV-5902"
        assert args.title == "New title"

    def test_edit_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["edit", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira edit" in output


class TestCmdViewCustomFields:
    def test_passes_custom_fields_to_format(self, capsys):
        issue = {
            "key": "MAV-100",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "assignee": None,
                "reporter": {"displayName": "Bob"},
                "description": "Desc",
                "comment": {"comments": []},
                "fixVersions": [],
                "customfield_37401": {"value": "High", "id": "1"},
            },
        }
        session = _mock_session(issue)
        custom_fields = {
            "metadata": {
                "Clinical Severity": {
                    "field": "customfield_37401",
                    "format": "option",
                },
            },
        }

        nhse_jira.cmd_view(session, "https://jira.example.com", ["MAV-100"], custom_fields=custom_fields)

        output = capsys.readouterr().out
        assert "Clinical Severity" in output
        assert "High" in output
