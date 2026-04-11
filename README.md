# nhse-jira

Lightweight CLI for the NHSE self-hosted Jira instance.

## Setup

### 1. Create a Personal Access Token

Go to https://nhsd-jira.digital.nhs.uk/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens

Click **Create token**, give it a name, and copy the value.

### 2. Add the token to ~/.netrc

```
machine nhsd-jira.digital.nhs.uk login _ password <your-token>
```

Make sure the file permissions are restricted:

```
chmod 600 ~/.netrc
```

### 3. Create the config file

```
mkdir -p ~/.config/nhse-jira
```

Create `~/.config/nhse-jira/config.yml`:

```yaml
server: https://nhsd-jira.digital.nhs.uk
project: MAV
```

### 4. Run it

```
./nhse-jira view MAV-5902
./nhse-jira view 5902
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (dependencies are fetched automatically on first run)
