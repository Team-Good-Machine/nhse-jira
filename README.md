# nhse-jira

Lightweight CLI for the NHSE self-hosted Jira instance.

## Installation

Symlink the script into a directory on your PATH:

```
mkdir -p ~/.local/bin
ln -s "$(pwd)/nhse-jira" ~/.local/bin/nhse-jira
```

If `~/.local/bin` isn't already on your PATH, add it to your shell config:

**zsh** (macOS default):
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

**bash**:
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

**fish**:
```
fish_add_path ~/.local/bin
```

Now `nhse-jira` works from any directory.

## Setup

```
nhse-jira init
```

This will walk you through:

1. Configuring the Jira server URL (default: `https://nhsd-jira.digital.nhs.uk`)
2. Creating a Personal Access Token (with a link to the token page)
3. Setting the default project (default: `MAV`)

Config is saved to `~/.config/nhse-jira/config.yml` and the token to `~/.netrc`.

## Commands

### View an issue

```
./nhse-jira view MAV-5902
./nhse-jira view 5902          # uses default project
```

### Search issues

```
./nhse-jira list "status = 'In Progress'"
./nhse-jira list --mine
./nhse-jira list --mine --status "In Progress"
./nhse-jira list --limit 10 "type = Bug"
./nhse-jira list --mine --fields "clinical safety,checklist progress"
```

### Transition an issue

```
./nhse-jira transition 5902              # list available transitions
./nhse-jira transition 5902 "In Progress"
./nhse-jira transition MAV-5902 Done
```

### List project versions

```
./nhse-jira releases
./nhse-jira releases --unreleased
```

### List issues in a release

```
./nhse-jira release 7.8.0
./nhse-jira release 7.9.0 --fields "clinical safety,checklist progress"
```

## Custom fields

Custom fields are configured in `~/.config/nhse-jira/config.yml`. The MAV project
comes pre-configured with fields for testing and clinical assurance (via `nhse-jira init`).

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

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (dependencies are fetched automatically on first run)
