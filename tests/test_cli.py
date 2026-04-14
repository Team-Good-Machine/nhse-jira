import nhse_jira


class TestResolveFields:
    SAMPLE_CUSTOM_FIELDS = {
        "metadata": {
            "Clinical Severity": {
                "field": "customfield_37401",
                "format": "option",
            },
            "Clinical Safety": {
                "field": "customfield_10595",
                "format": "option",
            },
            "Checklist Progress": {
                "field": "customfield_22907",
                "format": "string",
            },
        },
        "sections": {
            "Test Summary": {
                "field": "customfield_37407",
                "format": "string",
            },
        },
    }

    def test_resolves_by_label_case_insensitive(self):
        result = nhse_jira.resolve_fields(
            ["clinical severity"], self.SAMPLE_CUSTOM_FIELDS
        )
        assert result == [("Clinical Severity", "customfield_37401", "option")]

    def test_resolves_multiple_fields(self):
        result = nhse_jira.resolve_fields(
            ["clinical safety", "checklist progress"], self.SAMPLE_CUSTOM_FIELDS
        )
        assert len(result) == 2
        assert result[0] == ("Clinical Safety", "customfield_10595", "option")
        assert result[1] == ("Checklist Progress", "customfield_22907", "string")

    def test_resolves_from_sections_too(self):
        result = nhse_jira.resolve_fields(
            ["test summary"], self.SAMPLE_CUSTOM_FIELDS
        )
        assert result == [("Test Summary", "customfield_37407", "string")]

    def test_resolves_standard_field_assignee(self):
        result = nhse_jira.resolve_fields(["assignee"], self.SAMPLE_CUSTOM_FIELDS)
        assert result == [("Assignee", "assignee", "user")]

    def test_resolves_mix_of_standard_and_custom(self):
        result = nhse_jira.resolve_fields(
            ["assignee", "clinical safety"], self.SAMPLE_CUSTOM_FIELDS
        )
        assert result[0] == ("Assignee", "assignee", "user")
        assert result[1] == ("Clinical Safety", "customfield_10595", "option")

    def test_unknown_field_raises(self):
        import pytest
        with pytest.raises(SystemExit, match="Unknown field"):
            nhse_jira.resolve_fields(["nonexistent"], self.SAMPLE_CUSTOM_FIELDS)

    def test_empty_fields_returns_empty(self):
        result = nhse_jira.resolve_fields([], self.SAMPLE_CUSTOM_FIELDS)
        assert result == []

    def test_none_fields_returns_empty(self):
        result = nhse_jira.resolve_fields(None, self.SAMPLE_CUSTOM_FIELDS)
        assert result == []


class TestParserFields:
    def test_list_fields_flag(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--mine", "--fields", "clinical safety,checklist progress"])
        assert args.fields == "clinical safety,checklist progress"

    def test_list_no_fields_default(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--mine"])
        assert args.fields is None

    def test_release_fields_flag(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["release", "7.9.0", "--fields", "clinical safety"])
        assert args.fields == "clinical safety"


class TestParserHelp:
    def test_view_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["view", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira view 5902" in output

    def test_list_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["list", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira list --mine" in output
        assert "nhse-jira list" in output

    def test_transition_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["transition", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira transition 5902" in output

    def test_release_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["release", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira release" in output

    def test_releases_help_has_examples(self, capsys):
        parser = nhse_jira.build_parser()
        try:
            parser.parse_args(["releases", "--help"])
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert "nhse-jira releases" in output
