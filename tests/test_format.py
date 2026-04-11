import nhse_jira


class TestFormatIssue:
    def _make_issue(self, **overrides):
        issue = {
            "key": "MAV-5902",
            "fields": {
                "summary": "Fix login bug",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
                "description": "The login page is broken",
                "comment": {"comments": []},
            },
        }
        issue["fields"].update(overrides)
        return issue

    def test_includes_key_and_summary(self):
        output = nhse_jira.format_issue(self._make_issue())
        assert "MAV-5902" in output
        assert "Fix login bug" in output

    def test_includes_status_assignee_reporter(self):
        output = nhse_jira.format_issue(self._make_issue())
        assert "In Progress" in output
        assert "Alice" in output
        assert "Bob" in output

    def test_includes_description(self):
        output = nhse_jira.format_issue(self._make_issue())
        assert "The login page is broken" in output

    def test_unassigned_when_assignee_null(self):
        output = nhse_jira.format_issue(self._make_issue(assignee=None))
        assert "Unassigned" in output

    def test_shows_last_3_comments(self):
        comments = [
            {"author": {"displayName": f"User{i}"}, "body": f"Comment {i}"}
            for i in range(5)
        ]
        issue = self._make_issue(comment={"comments": comments})
        output = nhse_jira.format_issue(issue)
        assert "User2" in output
        assert "User3" in output
        assert "User4" in output
        assert "User0" not in output


class TestFormatIssueTable:
    def test_formats_rows(self):
        data = {
            "issues": [
                {"key": "MAV-1", "fields": {"summary": "First", "status": {"name": "Done"}}},
                {"key": "MAV-2", "fields": {"summary": "Second", "status": {"name": "Open"}}},
            ]
        }
        output = nhse_jira.format_issue_table(data)
        assert "MAV-1" in output
        assert "First" in output
        assert "Done" in output
        assert "MAV-2" in output
        assert "Second" in output

    def test_empty_result(self):
        output = nhse_jira.format_issue_table({"issues": []})
        assert output == "No issues found"


class TestFormatRelease:
    def test_formats_issue_list(self):
        data = {
            "issues": [
                {"key": "MAV-1", "fields": {"summary": "First issue"}},
                {"key": "MAV-2", "fields": {"summary": "Second issue"}},
            ]
        }
        output = nhse_jira.format_release(data)
        assert "MAV-1" in output
        assert "First issue" in output
        assert "MAV-2" in output
        assert "Second issue" in output

    def test_empty_release(self):
        output = nhse_jira.format_release({"issues": []})
        assert output == "No issues found"
