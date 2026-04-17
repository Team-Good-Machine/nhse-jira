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

    def test_shows_fix_version(self):
        output = nhse_jira.format_issue(self._make_issue(
            fixVersions=[{"name": "7.8.0"}]
        ))
        assert "7.8.0" in output

    def test_shows_multiple_fix_versions(self):
        output = nhse_jira.format_issue(self._make_issue(
            fixVersions=[{"name": "7.8.0"}, {"name": "7.9.0"}]
        ))
        assert "7.8.0" in output
        assert "7.9.0" in output

    def test_no_fix_version(self):
        output = nhse_jira.format_issue(self._make_issue(fixVersions=[]))
        assert "None" in output

    def test_shows_option_custom_field(self):
        custom_fields = {
            "metadata": {
                "Clinical Severity": {
                    "field": "customfield_37401",
                    "format": "option",
                },
            },
        }
        issue = self._make_issue(
            customfield_37401={"value": "Low", "id": "51010"},
        )
        output = nhse_jira.format_issue(issue, custom_fields=custom_fields)
        assert "Clinical Severity" in output
        assert "Low" in output

    def test_option_custom_field_null_value(self):
        custom_fields = {
            "metadata": {
                "Clinical Severity": {
                    "field": "customfield_37401",
                    "format": "option",
                },
            },
        }
        issue = self._make_issue(customfield_37401=None)
        output = nhse_jira.format_issue(issue, custom_fields=custom_fields)
        assert "Clinical Severity" in output

    def test_no_custom_fields_config(self):
        output = nhse_jira.format_issue(self._make_issue())
        assert "MAV-5902" in output

    def test_shows_string_section(self):
        custom_fields = {
            "sections": {
                "Test Summary": {
                    "field": "customfield_37407",
                    "format": "string",
                },
            },
        }
        issue = self._make_issue(
            customfield_37407="Automation evidence for end to end testing.",
        )
        output = nhse_jira.format_issue(issue, custom_fields=custom_fields)
        assert "Test Summary" in output
        assert "Automation evidence for end to end testing." in output

    def test_string_section_null_skipped(self):
        custom_fields = {
            "sections": {
                "Test Summary": {
                    "field": "customfield_37407",
                    "format": "string",
                },
            },
        }
        issue = self._make_issue(customfield_37407=None)
        output = nhse_jira.format_issue(issue, custom_fields=custom_fields)
        assert "Test Summary" not in output


class TestFormatIssueEpic:
    def _make_issue(self, **overrides):
        issue = {
            "key": "MAV-100",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
                "description": "Desc",
                "comment": {"comments": []},
            },
        }
        issue["fields"].update(overrides)
        return issue

    def test_shows_epic_link(self):
        issue = self._make_issue(customfield_10005="MAV-2730")
        output = nhse_jira.format_issue(issue, epic_field="customfield_10005")
        assert "Epic" in output
        assert "MAV-2730" in output

    def test_no_epic_when_field_is_null(self):
        issue = self._make_issue(customfield_10005=None)
        output = nhse_jira.format_issue(issue, epic_field="customfield_10005")
        assert "Epic" not in output

    def test_no_epic_when_field_absent(self):
        issue = self._make_issue()
        output = nhse_jira.format_issue(issue, epic_field="customfield_10005")
        assert "Epic" not in output

    def test_no_epic_when_no_epic_field_configured(self):
        issue = self._make_issue(customfield_10005="MAV-2730")
        output = nhse_jira.format_issue(issue)
        assert "Epic" not in output

    def test_custom_epic_field(self):
        issue = self._make_issue(customfield_99999="MAV-500")
        output = nhse_jira.format_issue(issue, epic_field="customfield_99999")
        assert "MAV-500" in output


class TestFormatIssueLinks:
    def _make_issue(self, issuelinks):
        return {
            "key": "MAV-100",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
                "description": "Desc",
                "comment": {"comments": []},
                "issuelinks": issuelinks,
            },
        }

    def test_shows_outward_link(self):
        issue = self._make_issue([{
            "type": {"inward": "is depended on by", "outward": "depends on"},
            "outwardIssue": {
                "key": "MAV-200",
                "fields": {
                    "summary": "Add indexes",
                    "status": {"name": "Backlog"},
                    "issuetype": {"name": "Task"},
                },
            },
        }])
        output = nhse_jira.format_issue(issue)
        assert "depends on" in output
        assert "MAV-200" in output
        assert "Backlog" in output
        assert "Add indexes" in output

    def test_shows_inward_link(self):
        issue = self._make_issue([{
            "type": {"inward": "is blocked by", "outward": "blocks"},
            "inwardIssue": {
                "key": "MAV-300",
                "fields": {
                    "summary": "Fix the widget",
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Bug"},
                },
            },
        }])
        output = nhse_jira.format_issue(issue)
        assert "is blocked by" in output
        assert "MAV-300" in output
        assert "In Progress" in output
        assert "Fix the widget" in output

    def test_shows_issue_type_badge(self):
        issue = self._make_issue([
            {
                "type": {"inward": "relates to", "outward": "relates to"},
                "outwardIssue": {
                    "key": "MAV-400",
                    "fields": {
                        "summary": "A story",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Story"},
                    },
                },
            },
            {
                "type": {"inward": "relates to", "outward": "relates to"},
                "outwardIssue": {
                    "key": "MAV-401",
                    "fields": {
                        "summary": "A bug",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Bug"},
                    },
                },
            },
            {
                "type": {"inward": "relates to", "outward": "relates to"},
                "outwardIssue": {
                    "key": "MAV-402",
                    "fields": {
                        "summary": "A task",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Task"},
                    },
                },
            },
        ])
        output = nhse_jira.format_issue(issue)
        assert "[S]" in output
        assert "[B]" in output
        assert "[T]" in output

    def test_unknown_issue_type_gets_generic_badge(self):
        issue = self._make_issue([{
            "type": {"inward": "relates to", "outward": "relates to"},
            "outwardIssue": {
                "key": "MAV-500",
                "fields": {
                    "summary": "An epic",
                    "status": {"name": "Open"},
                    "issuetype": {"name": "Epic"},
                },
            },
        }])
        output = nhse_jira.format_issue(issue)
        assert "[E]" in output
        assert "MAV-500" in output

    def test_no_links_section_when_empty(self):
        issue = self._make_issue([])
        output = nhse_jira.format_issue(issue)
        assert "Links" not in output

    def test_no_links_section_when_absent(self):
        issue = self._make_issue([])
        del issue["fields"]["issuelinks"]
        output = nhse_jira.format_issue(issue)
        assert "Links" not in output


class TestFormatChecklist:
    SAMPLE_CHECKLIST = [
        'Checklist(id=1, issueId=2, _items=['
        'Item(id=10, checklistId=1, value=First item done, rank=0, '
        'status=Status(id=4, rank=4, statusState=CHECKED, name=DONE, color=GREEN, '
        'default=true, global=true, projectIds=[]), quotes=[], assignees=[], '
        'history=null, mandatory=false, description=null, weight=null), '
        'Item(id=11, checklistId=1, value=Second item in progress, rank=1, '
        'status=Status(id=2, rank=2, statusState=UNCHECKED, name=TO DO, color=GRAY, '
        'default=true, global=true, projectIds=[]), quotes=[], assignees=[], '
        'history=null, mandatory=false, description=null, weight=null)'
        '])'
    ]

    def test_parses_items_with_status(self):
        output = nhse_jira._format_checklist(self.SAMPLE_CHECKLIST)
        assert "First item done" in output
        assert "Second item in progress" in output
        assert "DONE" in output
        assert "TO DO" in output

    def test_empty_checklist(self):
        output = nhse_jira._format_checklist([])
        assert output == "No items"

    def test_none_checklist(self):
        output = nhse_jira._format_checklist(None)
        assert output == "No items"


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

    def test_extra_fields_option_type(self):
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
        extra_fields = [("Clinical Safety", "customfield_10595", "option")]
        output = nhse_jira.format_issue_table(data, extra_fields=extra_fields)
        assert "MAV-1" in output
        assert "Triaged" in output

    def test_extra_fields_string_type(self):
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
        extra_fields = [("Progress", "customfield_22907", "string")]
        output = nhse_jira.format_issue_table(data, extra_fields=extra_fields)
        assert "9/9 - Done" in output

    def test_extra_fields_null_value(self):
        data = {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "First",
                        "status": {"name": "Done"},
                        "customfield_10595": None,
                    },
                },
            ]
        }
        extra_fields = [("Clinical Safety", "customfield_10595", "option")]
        output = nhse_jira.format_issue_table(data, extra_fields=extra_fields)
        assert "None" in output

    def test_extra_fields_assignee(self):
        data = {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "First",
                        "status": {"name": "Done"},
                        "assignee": {"displayName": "Alice"},
                    },
                },
            ]
        }
        extra_fields = [("Assignee", "assignee", "user")]
        output = nhse_jira.format_issue_table(data, extra_fields=extra_fields)
        assert "Alice" in output

    def test_extra_fields_assignee_null(self):
        data = {
            "issues": [
                {
                    "key": "MAV-1",
                    "fields": {
                        "summary": "First",
                        "status": {"name": "Done"},
                        "assignee": None,
                    },
                },
            ]
        }
        extra_fields = [("Assignee", "assignee", "user")]
        output = nhse_jira.format_issue_table(data, extra_fields=extra_fields)
        assert "Unassigned" in output

    def test_extra_fields_default_unchanged(self):
        """Existing behaviour: no extra_fields still works."""
        data = {
            "issues": [
                {"key": "MAV-1", "fields": {"summary": "First", "status": {"name": "Done"}}},
            ]
        }
        output = nhse_jira.format_issue_table(data)
        assert "MAV-1" in output
        assert "Done" in output


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
