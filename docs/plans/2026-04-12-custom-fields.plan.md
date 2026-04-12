# Config-Driven Custom Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display project-specific custom fields in issue view, driven by config so the script stays generic.

**Architecture:** Custom fields are defined in `config.yml` under `custom_fields` with three rendering types: `string` (plain text), `option` (Jira option object with `.value`), and `checklist` (Smart Checklist stringified Java object parsed via regex). `format_issue` receives the config and renders metadata fields inline and section fields as blocks below the description.

**Tech Stack:** Python, PyYAML, regex, pytest

---

## File Structure

```
nhse-jira                      # modify: add custom field rendering + checklist parser
tests/test_format.py           # modify: add custom field formatting tests
tests/test_config.py           # modify: test config loading with custom_fields
```

---

### Task 1: Config loading supports custom_fields

The config parser already works. This task ensures `custom_fields` is passed through correctly and the tool doesn't break when it's absent (backwards compatibility).

**Files:**
- Modify: `tests/test_config.py`
- No changes to `nhse-jira` needed (yaml.safe_load already passes through all keys)

- [ ] **Step 1: Write failing tests in `tests/test_config.py`**

```python
def test_load_config_with_custom_fields(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        "server: https://example.com\n"
        "project: TEST\n"
        "custom_fields:\n"
        "  metadata:\n"
        "    Clinical Severity:\n"
        "      field: customfield_37401\n"
        "      format: option\n"
    )

    config = nhse_jira.load_config(config_file)

    assert config["custom_fields"]["metadata"]["Clinical Severity"]["field"] == "customfield_37401"
    assert config["custom_fields"]["metadata"]["Clinical Severity"]["format"] == "option"


def test_load_config_without_custom_fields(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text("server: https://example.com\nproject: TEST\n")

    config = nhse_jira.load_config(config_file)

    assert config.get("custom_fields") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_config.py -v`
Expected: Both new tests PASS immediately (yaml.safe_load handles this). If so, good — no code change needed. This confirms backwards compatibility.

- [ ] **Step 3: Commit**

```bash
git add tests/test_config.py
git commit -m "test: verify config loading supports custom_fields"
```

---

### Task 2: Render option-type custom fields as metadata

Option fields (Clinical Severity, Clinical Safety) are Jira objects like `{"value": "Low", "id": "51010"}`. Render them as metadata lines after Fix Version.

**Files:**
- Modify: `tests/test_format.py`
- Modify: `nhse-jira`

- [ ] **Step 1: Write failing tests in `tests/test_format.py`**

Add a new test class at the end of the `TestFormatIssue` class:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_format.py::TestFormatIssue::test_shows_option_custom_field -v`
Expected: FAIL — `format_issue() got an unexpected keyword argument 'custom_fields'`

- [ ] **Step 3: Implement custom field rendering in `format_issue`**

Change `format_issue` signature and add metadata rendering after the Fix Version line. In `nhse-jira`:

Change `def format_issue(issue):` to `def format_issue(issue, custom_fields=None):` and add after the Fix Version line in the `lines` list:

```python
def format_issue(issue, custom_fields=None):
    key = issue["key"]
    fields = issue["fields"]
    summary = fields["summary"]
    status = fields["status"]["name"]
    assignee = fields.get("assignee")
    assignee_name = assignee["displayName"] if assignee else "Unassigned"
    reporter = fields["reporter"]["displayName"]
    description = fields.get("description") or "No description"
    fix_versions = fields.get("fixVersions", [])
    fix_version_str = ", ".join(v["name"] for v in fix_versions) if fix_versions else "None"

    lines = [
        f"{BOLD}{key}: {summary}{RESET}",
        f"{CYAN}Status:{RESET}      {status}",
        f"{CYAN}Assignee:{RESET}    {assignee_name}",
        f"{CYAN}Reporter:{RESET}    {reporter}",
        f"{CYAN}Fix Version:{RESET} {fix_version_str}",
    ]

    # Custom metadata fields
    if custom_fields:
        for label, cfg in custom_fields.get("metadata", {}).items():
            raw = fields.get(cfg["field"])
            value = _format_custom_value(raw, cfg.get("format", "string"))
            lines.append(f"{CYAN}{label}:{RESET} {value}")

    lines.append("")
    lines.append(description)

    # ... rest unchanged (comments)
```

Also add the helper function `_format_custom_value` before `format_issue`:

```python
def _format_custom_value(raw, fmt):
    if raw is None:
        return "None"
    if fmt == "option":
        return raw.get("value", str(raw)) if isinstance(raw, dict) else str(raw)
    return str(raw)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_format.py -v`
Expected: PASS — all tests pass including existing ones (backwards compatible via `custom_fields=None` default)

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_format.py
git commit -m "feat: render option-type custom fields in issue view"
```

---

### Task 3: Render string-type custom fields as sections

String fields (Test Summary) are plain text shown as a section below the description, similar to how comments are shown.

**Files:**
- Modify: `tests/test_format.py`
- Modify: `nhse-jira`

- [ ] **Step 1: Write failing tests in `tests/test_format.py`**

Add to `TestFormatIssue`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_format.py::TestFormatIssue::test_shows_string_section -v`
Expected: FAIL — "Test Summary" not in output

- [ ] **Step 3: Implement section rendering in `format_issue`**

Add after comments in `format_issue`, before the final `return "\n".join(lines)`:

```python
    # Custom sections
    if custom_fields:
        for label, cfg in custom_fields.get("sections", {}).items():
            raw = fields.get(cfg["field"])
            if raw is None:
                continue
            fmt = cfg.get("format", "string")
            if fmt == "checklist":
                value = _format_checklist(raw)
            else:
                value = str(raw)
            lines.append("")
            lines.append(f"{BOLD}{label}:{RESET}")
            lines.append(value)

    return "\n".join(lines)
```

Also add a stub for `_format_checklist` (implemented in Task 4):

```python
def _format_checklist(raw):
    return str(raw)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_format.py -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_format.py
git commit -m "feat: render string-type custom fields as sections"
```

---

### Task 4: Parse and render Smart Checklist

The Smart Checklist field (`customfield_22905`) is a list containing a stringified Java object. Extract items using regex and render as a checklist with status markers.

**Files:**
- Modify: `tests/test_format.py`
- Modify: `nhse-jira`

- [ ] **Step 1: Write failing tests in `tests/test_format.py`**

Add a new test class:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_format.py::TestFormatChecklist -v`
Expected: FAIL — output doesn't contain parsed items (stub just returns str())

- [ ] **Step 3: Implement `_format_checklist` in `nhse-jira`**

Replace the stub:

```python
def _format_checklist(raw):
    if not raw:
        return "No items"
    items = []
    for entry in raw:
        matches = re.findall(
            r"value=(.*?), rank=\d+, status=Status\([^)]*name=(\w[\w ]*)",
            entry,
        )
        for value, status in matches:
            if status == "DONE":
                marker = f"{GREEN}[DONE]{RESET}"
            else:
                marker = f"{YELLOW}[{status}]{RESET}"
            items.append(f"  {marker} {value}")
    return "\n".join(items) if items else "No items"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_format.py -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add nhse-jira tests/test_format.py
git commit -m "feat: parse and render Smart Checklist items"
```

---

### Task 5: Wire custom fields through cmd_view and update config

Pass `custom_fields` from the loaded config through `cmd_view` into `format_issue`. Update the default MAV config to include the five custom fields.

**Files:**
- Modify: `nhse-jira`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write failing test in `tests/test_commands.py`**

Update `SAMPLE_ISSUE` to include a custom field, and add a test:

```python
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

        nhse_jira.cmd_view(session, "https://jira.example.com", "MAV-100", custom_fields=custom_fields)

        output = capsys.readouterr().out
        assert "Clinical Severity" in output
        assert "High" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_commands.py::TestCmdViewCustomFields -v`
Expected: FAIL — `cmd_view() got an unexpected keyword argument 'custom_fields'`

- [ ] **Step 3: Update `cmd_view` and `main` in `nhse-jira`**

Update `cmd_view`:

```python
def cmd_view(session, base_url, issue_key, custom_fields=None):
    data = api_get(session, base_url, f"issue/{issue_key}")
    print(format_issue(data, custom_fields=custom_fields))
```

Update the `main()` function's view branch:

```python
    if args.command == "view":
        issue_key = normalize_key(args.issue, project)
        cmd_view(session, base_url, issue_key, custom_fields=config.get("custom_fields"))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest -v`
Expected: PASS — all tests pass

- [ ] **Step 5: Update the default config in `cmd_init`**

In `cmd_init`, after writing the basic config, also write the MAV custom fields when the project is MAV. Update the config writing section:

```python
    config_content = f"server: {server}\nproject: {project}\n"
    if project.upper() == "MAV":
        config_content += (
            "custom_fields:\n"
            "  metadata:\n"
            "    Clinical Severity:\n"
            "      field: customfield_37401\n"
            "      format: option\n"
            "    Clinical Safety:\n"
            "      field: customfield_10595\n"
            "      format: option\n"
            "    Checklist Progress:\n"
            "      field: customfield_22907\n"
            "      format: string\n"
            "  sections:\n"
            "    Test Summary:\n"
            "      field: customfield_37407\n"
            "      format: string\n"
            "    Smart Checklist:\n"
            "      field: customfield_22905\n"
            "      format: checklist\n"
        )
    config_file.write_text(config_content)
```

- [ ] **Step 6: Commit**

```bash
git add nhse-jira tests/test_commands.py
git commit -m "feat: wire custom fields through cmd_view and default MAV config"
```

---

### Task 6: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add custom fields section to README**

Add after the Commands section and before Requirements:

```markdown
## Custom fields

Custom fields are configured in `~/.config/nhse-jira/config.yml`. The MAV project
comes pre-configured with fields for testing and clinical assurance.

Three display formats are supported:

- `option` — Jira select fields (shown as metadata, e.g. "Clinical Severity: Low")
- `string` — plain text (shown as a section below the description)
- `checklist` — Smart Checklist (parsed and shown as a checklist with status markers)

Fields under `metadata` appear in the header. Fields under `sections` appear after the description.

```yaml
custom_fields:
  metadata:
    Clinical Severity:
      field: customfield_37401
      format: option
  sections:
    Test Summary:
      field: customfield_37407
      format: string
    Smart Checklist:
      field: customfield_22905
      format: checklist
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document custom fields configuration"
```
