import nhse_jira


class TestNormalizeKey:
    def test_bare_number_gets_project_prefix(self):
        assert nhse_jira.normalize_key("5902", "MAV") == "MAV-5902"

    def test_full_key_unchanged(self):
        assert nhse_jira.normalize_key("MAV-5902", "MAV") == "MAV-5902"

    def test_lowercase_key_uppercased(self):
        assert nhse_jira.normalize_key("mav-5902", "MAV") == "MAV-5902"


class TestNormalizeJql:
    def test_adds_project_when_missing(self):
        result = nhse_jira.normalize_jql("status = 'In Progress'", "MAV")
        assert result == "project = MAV AND status = 'In Progress'"

    def test_preserves_existing_project_clause(self):
        jql = "project = OTHER AND status = Done"
        assert nhse_jira.normalize_jql(jql, "MAV") == jql

    def test_case_insensitive_project_detection(self):
        jql = "PROJECT = OTHER AND status = Done"
        assert nhse_jira.normalize_jql(jql, "MAV") == jql
