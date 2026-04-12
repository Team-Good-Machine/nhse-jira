import nhse_jira


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
