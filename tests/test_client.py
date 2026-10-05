from kaneo_cli.client import ApiClient, ApiError


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append((method, path, params, payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_list_projects_uses_workspace_query():
    transport = FakeTransport([[{"id": "p1", "name": "Roadmap"}]])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.list_projects("w1") == [{"id": "p1", "name": "Roadmap"}]
    assert transport.calls == [("GET", "/project", {"workspaceId": "w1"}, None)]


def test_list_tasks_returns_board_response_with_pagination():
    board = {"columns": [{"id": "todo", "tasks": [{"id": "t1"}]}], "pagination": {"page": 1}}
    transport = FakeTransport([board])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.list_tasks("p1", page=2, limit=25) == board
    assert transport.calls == [("GET", "/task/tasks/p1", {"page": 2, "limit": 25}, None)]


def test_update_task_reads_existing_and_preserves_unrelated_fields():
    existing = {
        "id": "t1",
        "title": "Old",
        "description": "Keep",
        "projectId": "p1",
        "priority": "high",
    }
    updated = {**existing, "title": "New"}
    transport = FakeTransport([existing, {"ok": True}, updated])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.update_task("t1", {"title": "New"}) == updated
    assert transport.calls == [
        ("GET", "/task/t1", None, None),
        ("PUT", "/task/t1", None, existing | {"title": "New"}),
        ("GET", "/task/t1", None, None),
    ]


def test_api_error_has_actionable_message_without_secret():
    transport = FakeTransport([ApiError("Kaneo returned 401: check KANEO_API_KEY")])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    try:
        client.list_workspaces()
    except ApiError as error:
        assert str(error) == "Kaneo returned 401: check KANEO_API_KEY"
    else:
        raise AssertionError("expected ApiError")
