# nhse-jira CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight CLI for interacting with the NHSE self-hosted Jira instance (Server 10.3.15, REST API v2) with Bearer token auth.

**Architecture:** Single Python script (`nhse-jira`) using `uv run` shebang for zero-install execution. Pure functions for config, normalization, and formatting (easily testable). Thin API layer using `requests.Session`. CLI wiring via `argparse`. Config from `~/.config/nhse-jira/config.yml`, token from `~/.netrc`.

**Tech Stack:** Python 3.12+, uv, requests, PyYAML, pytest

---

## File Structure

```
nhse-jira                     # executable script (uv run shebang)
pyproject.toml                # test runner config + dev dependencies
tests/
  conftest.py                 # imports nhse-jira script as a module
  test_config.py              # config + token loading
  test_normalize.py           # issue key + JQL normalization
  test_format.py              # output formatting (view, table, release)
  test_api.py                 # API client (mocked HTTP)
  test_commands.py            # command functions (mocked HTTP)
  test_cli.py                 # argument parsing
```

---

### Task 1: Project scaffolding and test infrastructure

**Files:**
- Create: `pyproject.toml`
- Create: `nhse-jira`
- Create: `tests/conftest.py`
- Create: `tests/test_scaffold.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "nhse-jira"
version = "0.1.0"
requires-python = ">=3.12"

[dependency-groups]
dev = ["pytest", "requests", "pyyaml"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create the script skeleton `nhse-jira`**

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "pyyaml"]
# ///


def main():
    pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Make the script executable**

Run: `chmod +x nhse-jira`

- [ ] **Step 4: Create `tests/conftest.py` to import the script as a module**

```python
import importlib.util
import sys
from pathlib import Path

_script_path = Path(__file__).parent.parent / "nhse-jira"
_spec = importlib.util.spec_from_file_location("nhse_jira", _script_path)
nhse_jira = importlib.util.module_from_spec(_spec)
sys.modules["nhse_jira"] = nhse_jira
_spec.loader.exec_module(nhse_jira)
```

- [ ] **Step 5: Write a smoke test `tests/test_scaffold.py`**

```python
import nhse_jira


def test_module_imports():
    assert hasattr(nhse_jira, "main")
```

- [ ] **Step 6: Run the test**

Run: `uv run --group dev pytest tests/test_scaffold.py -v`
Expected: PASS — 1 test passes

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml nhse-jira tests/conftest.py tests/test_scaffold.py
git commit -m "scaffold: project setup with test infrastructure"
```

---

### Task 2: Config loading

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests in `tests/test_config.py`**

```python
import pytest
import nhse_jira


def test_load_config_reads_yaml(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text("server: https://example.com\nproject: TEST\n")

    config = nhse_jira.load_config(config_file)

    assert config["server"] == "https://example.com"
    assert config["project"] == "TEST"


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(SystemExit, match="Config file not found"):
        nhse_jira.load_config(tmp_path / "nonexistent.yml")


def test_load_token_from_netrc(tmp_path):
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text("machine example.com login _ password secret-token\n")
    netrc_file.chmod(0o600)

    token = nhse_jira.load_token("https://example.com", netrc_file)

    assert token == "secret-token"


def test_load_token_missing_entry_raises(tmp_path):
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text("machine other.com login _ password tok\n")
    netrc_file.chmod(0o600)

    with pytest.raises(SystemExit, match="No .netrc entry"):
        nhse_jira.load_token("https://example.com", netrc_file)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_config.py -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'load_config'`

- [ ] **Step 3: Implement `load_config` and `load_token` in `nhse-jira`**

Add to `nhse-jira` before `main()`:

```python
import sys
import netrc as netrc_mod
from pathlib import Path
from urllib.parse import urlparse

import yaml


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "nhse-jira" / "config.yml"
DEFAULT_NETRC_PATH = Path.home() / ".netrc"


def load_config(config_path=DEFAULT_CONFIG_PATH):
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        raise SystemExit(f"Config file not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_token(server_url, netrc_path=DEFAULT_NETRC_PATH):
    hostname = urlparse(server_url).hostname
    try:
        nrc = netrc_mod.netrc(str(netrc_path))
    except FileNotFoundError:
        print(
            f"Error: No .netrc file found at {netrc_path}\n"
            "Create a Personal Access Token in Jira and add it:\n"
            f"  machine {hostname} login _ password <your-token>",
            file=sys.stderr,
        )
        raise SystemExit(f"No .netrc entry for {hostname}")
    auth = nrc.authenticators(hostname)
    if auth is None:
        print(
            f"Error: No .netrc entry for {hostname}\n"
            "Add this line to your ~/.netrc:\n"
            f"  machine {hostname} login _ password <your-token>",
            file=sys.stderr,
        )
        raise SystemExit(f"No .netrc entry for {hostname}")
    return auth[2]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_config.py -v`
Expected: PASS — all 4 tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_config.py
git commit -m "feat: config loading from YAML and token from .netrc"
```

---

### Task 3: Issue key and JQL normalization

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_normalize.py`

- [ ] **Step 1: Write failing tests in `tests/test_normalize.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_normalize.py -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'normalize_key'`

- [ ] **Step 3: Implement `normalize_key` and `normalize_jql` in `nhse-jira`**

Add to `nhse-jira`:

```python
import re


def normalize_key(key, default_project):
    if key.isdigit():
        return f"{default_project}-{key}"
    return key.upper()


def normalize_jql(jql, default_project):
    if not re.search(r"\bproject\s*=", jql, re.IGNORECASE):
        return f"project = {default_project} AND {jql}"
    return jql
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_normalize.py -v`
Expected: PASS — all 6 tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_normalize.py
git commit -m "feat: issue key and JQL normalization with project defaulting"
```

---

### Task 4: Output formatting

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_format.py`

- [ ] **Step 1: Write failing tests in `tests/test_format.py`**

```python
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
        assert "[MAV-1] First issue" in output
        assert "[MAV-2] Second issue" in output

    def test_empty_release(self):
        output = nhse_jira.format_release({"issues": []})
        assert output == "No issues found"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_format.py -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'format_issue'`

- [ ] **Step 3: Implement formatting functions in `nhse-jira`**

Add to `nhse-jira`:

```python
BOLD = "\033[1m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"


def format_issue(issue):
    key = issue["key"]
    fields = issue["fields"]
    summary = fields["summary"]
    status = fields["status"]["name"]
    assignee = fields.get("assignee")
    assignee_name = assignee["displayName"] if assignee else "Unassigned"
    reporter = fields["reporter"]["displayName"]
    description = fields.get("description") or "No description"

    lines = [
        f"{BOLD}{key}: {summary}{RESET}",
        f"{CYAN}Status:{RESET}   {status}",
        f"{CYAN}Assignee:{RESET} {assignee_name}",
        f"{CYAN}Reporter:{RESET} {reporter}",
        "",
        description,
    ]

    comments = fields.get("comment", {}).get("comments", [])
    if comments:
        last_3 = comments[-3:]
        lines.append("")
        lines.append(f"{BOLD}Comments ({len(last_3)}):{RESET}")
        for comment in last_3:
            author = comment["author"]["displayName"]
            body = comment["body"]
            lines.append(f"  {GREEN}{author}:{RESET} {body}")

    return "\n".join(lines)


def format_issue_table(data):
    issues = data["issues"]
    if not issues:
        return "No issues found"

    rows = []
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        status = issue["fields"]["status"]["name"]
        rows.append((key, summary, status))

    key_width = max(len(r[0]) for r in rows)
    status_width = max(len(r[2]) for r in rows)

    lines = []
    for key, summary, status in rows:
        lines.append(f"{CYAN}{key:<{key_width}}{RESET}  {summary}  {YELLOW}{status:<{status_width}}{RESET}")
    return "\n".join(lines)


def format_release(data):
    issues = data["issues"]
    if not issues:
        return "No issues found"
    lines = []
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        lines.append(f"{CYAN}[{key}]{RESET} {summary}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_format.py -v`
Expected: PASS — all 9 tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_format.py
git commit -m "feat: output formatting for view, list, and release"
```

---

### Task 5: API client

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing tests in `tests/test_api.py`**

Mocking `requests.Session` is unavoidable here since we can't hit the real Jira instance.

```python
from unittest.mock import MagicMock, patch
import pytest
import nhse_jira


def test_create_session_sets_bearer_header():
    session = nhse_jira.create_session("my-token")
    assert session.headers["Authorization"] == "Bearer my-token"


def test_api_get_calls_correct_url():
    session = MagicMock()
    session.get.return_value.ok = True
    session.get.return_value.json.return_value = {"key": "MAV-1"}

    result = nhse_jira.api_get(session, "https://jira.example.com", "issue/MAV-1")

    session.get.assert_called_once_with(
        "https://jira.example.com/rest/api/2/issue/MAV-1", params=None
    )
    assert result == {"key": "MAV-1"}


def test_api_get_passes_params():
    session = MagicMock()
    session.get.return_value.ok = True
    session.get.return_value.json.return_value = {"issues": []}

    nhse_jira.api_get(session, "https://jira.example.com", "search", params={"jql": "x"})

    session.get.assert_called_once_with(
        "https://jira.example.com/rest/api/2/search", params={"jql": "x"}
    )


def test_api_get_raises_on_error():
    session = MagicMock()
    session.get.return_value.ok = False
    session.get.return_value.status_code = 404
    session.get.return_value.json.return_value = {"errorMessages": ["Issue not found"]}

    with pytest.raises(nhse_jira.JiraError, match="404.*Issue not found"):
        nhse_jira.api_get(session, "https://jira.example.com", "issue/NOPE-1")


def test_api_post_calls_correct_url():
    session = MagicMock()
    session.post.return_value.ok = True
    session.post.return_value.status_code = 204
    session.post.return_value.content = b""

    nhse_jira.api_post(session, "https://jira.example.com", "issue/MAV-1/transitions", json={"transition": {"id": "5"}})

    session.post.assert_called_once_with(
        "https://jira.example.com/rest/api/2/issue/MAV-1/transitions",
        json={"transition": {"id": "5"}},
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_api.py -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'create_session'`

- [ ] **Step 3: Implement API client in `nhse-jira`**

Add to `nhse-jira`:

```python
import requests


class JiraError(Exception):
    pass


def create_session(token):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    session.headers["Content-Type"] = "application/json"
    return session


def _handle_error(resp):
    try:
        body = resp.json()
        messages = body.get("errorMessages", [])
        msg = "; ".join(messages) if messages else resp.text
    except Exception:
        msg = resp.text
    raise JiraError(f"HTTP {resp.status_code}: {msg}")


def api_get(session, base_url, path, params=None):
    resp = session.get(f"{base_url}/rest/api/2/{path}", params=params)
    if not resp.ok:
        _handle_error(resp)
    return resp.json()


def api_post(session, base_url, path, json=None):
    resp = session.post(f"{base_url}/rest/api/2/{path}", json=json)
    if not resp.ok:
        _handle_error(resp)
    if resp.content:
        return resp.json()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_api.py -v`
Expected: PASS — all 5 tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_api.py
git commit -m "feat: API client with session, get, post, and error handling"
```

---

### Task 6: View command

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_commands.py`

- [ ] **Step 1: Write failing test in `tests/test_commands.py`**

```python
from unittest.mock import MagicMock
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_commands.py::TestCmdView -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'cmd_view'`

- [ ] **Step 3: Implement `cmd_view` in `nhse-jira`**

```python
def cmd_view(session, base_url, issue_key):
    data = api_get(session, base_url, f"issue/{issue_key}")
    print(format_issue(data))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_commands.py::TestCmdView -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_commands.py
git commit -m "feat: view command - fetch and display issue details"
```

---

### Task 7: List command

**Files:**
- Modify: `nhse-jira`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write failing tests — append to `tests/test_commands.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_commands.py::TestBuildListJql tests/test_commands.py::TestCmdList -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'build_list_jql'`

- [ ] **Step 3: Implement `build_list_jql` and `cmd_list` in `nhse-jira`**

```python
def build_list_jql(jql="", mine=False, status=None):
    parts = []
    if mine:
        parts.append("assignee = currentUser()")
    if status:
        parts.append(f"status = '{status}'")
    if jql:
        parts.append(jql)
    if not parts:
        return "ORDER BY updated DESC"
    return " AND ".join(parts)


def cmd_list(session, base_url, project, jql="", mine=False, status=None, limit=50):
    query = build_list_jql(jql=jql, mine=mine, status=status)
    query = normalize_jql(query, project)
    data = api_get(session, base_url, "search", params={"jql": query, "maxResults": limit, "fields": "summary,status"})
    print(format_issue_table(data))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_commands.py -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_commands.py
git commit -m "feat: list command with JQL, --mine, and --status support"
```

---

### Task 8: Transition command

**Files:**
- Modify: `nhse-jira`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write failing tests — append to `tests/test_commands.py`**

```python
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
```

Add `import pytest` at the top of the file if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_commands.py::TestCmdTransition -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'cmd_transition'`

- [ ] **Step 3: Implement `cmd_transition` in `nhse-jira`**

```python
def cmd_transition(session, base_url, issue_key, target_status):
    data = api_get(session, base_url, f"issue/{issue_key}/transitions")
    transitions = data["transitions"]

    match = None
    for t in transitions:
        if t["to"]["name"].lower() == target_status.lower():
            match = t
            break

    if match is None:
        available = [t["to"]["name"] for t in transitions]
        print(
            f"Error: Cannot transition {issue_key} to '{target_status}'\n"
            f"Available transitions: {', '.join(available)}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    api_post(session, base_url, f"issue/{issue_key}/transitions", json={"transition": {"id": match["id"]}})
    print(f"Transitioned {issue_key} to {target_status}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_commands.py -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_commands.py
git commit -m "feat: transition command with available-transitions fallback"
```

---

### Task 9: Release command

**Files:**
- Modify: `nhse-jira`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write failing tests — append to `tests/test_commands.py`**

```python
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
        assert "[MAV-10]" in output
        assert "Add feature X" in output
        assert "[MAV-11]" in output
        assert "Fix bug Y" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_commands.py::TestCmdRelease -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'cmd_release'`

- [ ] **Step 3: Implement `cmd_release` in `nhse-jira`**

```python
def cmd_release(session, base_url, project, version_name):
    jql = f'project = {project} AND fixVersion = "{version_name}" ORDER BY key ASC'
    data = api_get(session, base_url, "search", params={"jql": jql, "maxResults": 200, "fields": "summary"})
    print(format_release(data))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_commands.py -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_commands.py
git commit -m "feat: release command - list issues by fixVersion"
```

---

### Task 10: CLI argument parsing and main entry point

**Files:**
- Modify: `nhse-jira`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests in `tests/test_cli.py`**

```python
import nhse_jira


class TestBuildParser:
    def test_view_command(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["view", "MAV-5902"])
        assert args.command == "view"
        assert args.issue == "MAV-5902"

    def test_view_bare_number(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["view", "5902"])
        assert args.issue == "5902"

    def test_list_with_jql(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "status = Open"])
        assert args.command == "list"
        assert args.jql == "status = Open"

    def test_list_mine(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--mine"])
        assert args.mine is True

    def test_list_status_filter(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--status", "In Progress"])
        assert args.status == "In Progress"

    def test_list_limit(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--limit", "10", "--mine"])
        assert args.limit == 10

    def test_list_default_limit(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["list", "--mine"])
        assert args.limit == 50

    def test_transition_command(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["transition", "5902", "In Progress"])
        assert args.command == "transition"
        assert args.issue == "5902"
        assert args.status == "In Progress"

    def test_release_command(self):
        parser = nhse_jira.build_parser()
        args = parser.parse_args(["release", "7.8.0"])
        assert args.command == "release"
        assert args.version == "7.8.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_cli.py -v`
Expected: FAIL — `AttributeError: module 'nhse_jira' has no attribute 'build_parser'`

- [ ] **Step 3: Implement `build_parser` and update `main` in `nhse-jira`**

```python
import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog="nhse-jira", description="CLI for NHSE Jira")
    subparsers = parser.add_subparsers(dest="command", required=True)

    view_parser = subparsers.add_parser("view", help="View issue details")
    view_parser.add_argument("issue", help="Issue key or number")

    list_parser = subparsers.add_parser("list", help="Search issues with JQL")
    list_parser.add_argument("jql", nargs="?", default="", help="JQL query")
    list_parser.add_argument("--mine", action="store_true", help="Only my issues")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")

    trans_parser = subparsers.add_parser("transition", help="Transition an issue")
    trans_parser.add_argument("issue", help="Issue key or number")
    trans_parser.add_argument("status", help="Target status name")

    release_parser = subparsers.add_parser("release", help="List issues in a release")
    release_parser.add_argument("version", help="Version name")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    config = load_config()
    token = load_token(config["server"])
    session = create_session(token)
    base_url = config["server"]
    project = config["project"]

    if args.command == "view":
        issue_key = normalize_key(args.issue, project)
        cmd_view(session, base_url, issue_key)
    elif args.command == "list":
        cmd_list(session, base_url, project, jql=args.jql, mine=args.mine, status=args.status, limit=args.limit)
    elif args.command == "transition":
        issue_key = normalize_key(args.issue, project)
        cmd_transition(session, base_url, issue_key, args.status)
    elif args.command == "release":
        cmd_release(session, base_url, project, args.version)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_cli.py -v`
Expected: PASS — all 9 tests pass

- [ ] **Step 5: Run full test suite**

Run: `uv run --group dev pytest -v`
Expected: PASS — all tests pass, output clean

- [ ] **Step 6: Commit**

```bash
git add nhse-jira tests/test_cli.py
git commit -m "feat: CLI argument parsing and main entry point"
```

- [ ] **Step 7: Verify the script runs**

Run: `./nhse-jira --help`
Expected: Shows usage with view, list, transition, release subcommands

- [ ] **Step 8: Delete scaffold test**

Remove `tests/test_scaffold.py` — it served its purpose and is now redundant.

```bash
git rm tests/test_scaffold.py
git commit -m "chore: remove scaffold test"
```
