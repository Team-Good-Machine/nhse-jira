from unittest.mock import MagicMock
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

    nhse_jira.api_post(
        session,
        "https://jira.example.com",
        "issue/MAV-1/transitions",
        json={"transition": {"id": "5"}},
    )

    session.post.assert_called_once_with(
        "https://jira.example.com/rest/api/2/issue/MAV-1/transitions",
        json={"transition": {"id": "5"}},
    )
