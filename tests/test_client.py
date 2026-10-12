import ssl
from urllib.error import HTTPError

import kaneo_cli.client as client_module
from kaneo_cli.client import ApiClient, ApiError, HttpTransport, normalize_comment_content


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


def test_list_workspaces_uses_verified_organization_route():
    transport = FakeTransport([[{"id": "w1", "name": "Main"}]])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.list_workspaces() == [{"id": "w1", "name": "Main"}]
    assert transport.calls == [("GET", "/auth/organization/list", None, None)]


class _Response:
    def __init__(self, body=b'{"ok": true}'):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def test_http_transport_verifies_tls_by_default(monkeypatch):
    calls = []

    def fake_urlopen(request, *, timeout, context):
        calls.append((request, timeout, context))
        return _Response()

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    assert HttpTransport("https://kaneo.example/api", "secret").request("GET", "/health") == {
        "ok": True
    }
    assert calls[0][2].verify_mode == ssl.CERT_REQUIRED
    assert calls[0][2].check_hostname is True


def test_http_transport_can_explicitly_disable_tls_verification(monkeypatch):
    calls = []

    def fake_urlopen(request, *, timeout, context):
        calls.append((request, timeout, context))
        return _Response()

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    HttpTransport("https://kaneo.example/api", "secret", verify_tls=False).request(
        "GET", "/health"
    )
    assert calls[0][2].verify_mode == ssl.CERT_NONE
    assert calls[0][2].check_hostname is False


def test_http_transport_makes_reorder_conflict_actionable(monkeypatch):
    def fake_urlopen(*_args, **_kwargs):
        raise HTTPError("https://kaneo.example/api/task/reorder", 409, "Conflict", {}, None)

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    try:
        HttpTransport("https://kaneo.example/api", "secret").request("POST", "/task/reorder")
    except ApiError as error:
        assert "refresh the board and retry deliberately" in str(error)
    else:
        raise AssertionError("expected ApiError")


def test_api_client_passes_tls_setting_to_http_transport(monkeypatch):
    transports = []

    class RecordingTransport(HttpTransport):
        def __init__(self, *args, **kwargs):
            transports.append(kwargs["verify_tls"])
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(client_module, "HttpTransport", RecordingTransport)

    ApiClient("https://kaneo.example", "secret", verify_tls=False)
    assert transports == [False]


def test_create_task_uses_project_path_and_excludes_project_from_payload():
    created = {"id": "t1"}
    task = {"id": "t1", "projectId": "p1", "title": "Prepare"}
    transport = FakeTransport([created, task])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.create_task("p1", {"title": "Prepare"}) == task
    assert transport.calls == [
        ("POST", "/task/p1", None, {"title": "Prepare"}),
        ("GET", "/task/t1", None, None),
    ]


def test_create_task_comment_uses_comment_path():
    response = {"id": "c1", "content": "Ready"}
    transport = FakeTransport([response])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.create_task_comment("t1", "Ready") == response
    assert transport.calls == [("POST", "/comment/t1", None, {"content": "Ready"})]


def test_list_task_comments_uses_verified_comment_path():
    response = [{"id": "c1", "content": "Ready", "authorName": "Ada"}]
    transport = FakeTransport([response])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.list_task_comments("t1") == response
    assert transport.calls == [("GET", "/comment/t1", None, None)]


def test_list_task_activity_supports_full_and_bounded_feeds():
    activity = [{"id": "a1", "type": "status_changed", "eventData": {"oldStatus": "todo", "newStatus": "done"}}]
    transport = FakeTransport([activity, activity])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.list_task_activity("t1") == activity
    assert client.list_task_activity("t1", limit=10) == activity
    assert transport.calls == [
        ("GET", "/activity/t1", None, None),
        ("GET", "/activity/t1", {"limit": 10}, None),
    ]


def test_list_task_activity_rejects_invalid_limit_before_request():
    transport = FakeTransport([])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    try:
        client.list_task_activity("t1", limit=101)
    except ApiError as error:
        assert str(error) == "activity limit must be between 1 and 100"
    else:
        raise AssertionError("expected ApiError")
    assert transport.calls == []


def test_normalize_comment_content_only_decodes_literal_newline_pairs():
    assert normalize_comment_content(r"One\nTwo\nThree") == "One\nTwo\nThree"
    assert normalize_comment_content("One\nTwo") == "One\nTwo"
    assert normalize_comment_content(r"Path\\nname") == "Path\\\nname"


def test_update_task_status_to_top_uses_reorder_snapshot_and_reads_back():
    task = {"id": "t1", "projectId": "p1", "status": "todo", "position": 20}
    board = {
        "columns": [
            {"slug": "todo", "tasks": [task, {"id": "t2", "status": "todo", "position": 30}]},
            {"slug": "done", "tasks": [{"id": "t3", "status": "done", "position": 10}]},
        ]
    }
    updated = {**task, "status": "done", "position": 0}
    transport = FakeTransport([task, board, [{"id": "t1", "position": 0, "status": "done"}], updated])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.update_task_status("t1", "done", move_to_top=True) == updated
    assert transport.calls == [
        ("GET", "/task/t1", None, None),
        ("GET", "/task/tasks/p1", {"page": 1, "limit": 50}, None),
        (
            "POST",
            "/task/reorder",
            None,
            {
                "projectId": "p1",
                "tasks": [
                    {"id": "t1", "position": 0, "status": "done"},
                    {"id": "t3", "position": 1, "status": "done"},
                    {"id": "t2", "position": 0, "status": "todo"},
                ],
                "expectedTasks": [
                    {"id": "t1", "position": 20, "status": "todo"},
                    {"id": "t2", "position": 30, "status": "todo"},
                    {"id": "t3", "position": 10, "status": "done"},
                ],
            },
        ),
        ("GET", "/task/t1", None, None),
    ]


def test_update_task_status_to_top_reads_all_board_pages():
    task = {"id": "t1", "projectId": "p1", "status": "todo", "position": 20}
    first_page = {
        "columns": [{"slug": "todo", "tasks": [task]}],
        "pagination": {"page": 1, "totalPages": 2},
    }
    second_page = {
        "columns": [{"slug": "done", "tasks": [{"id": "t2", "status": "done", "position": 10}]}],
        "pagination": {"page": 2, "totalPages": 2},
    }
    updated = {**task, "status": "done", "position": 0}
    transport = FakeTransport([task, first_page, second_page, [], updated])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.update_task_status("t1", "done", move_to_top=True) == updated
    assert transport.calls[1] == ("GET", "/task/tasks/p1", {"page": 1, "limit": 50}, None)
    assert transport.calls[2] == ("GET", "/task/tasks/p1", {"page": 2, "limit": 50}, None)
    assert transport.calls[3][1] == "/task/reorder"


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


def test_update_task_status_uses_dedicated_endpoint_and_reads_back_task():
    updated = {"id": "t1", "title": "Prepare", "status": "feature-review"}
    transport = FakeTransport([{}, updated])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert client.update_task("t1", {"status": "feature-review"}) == updated
    assert transport.calls == [
        ("PUT", "/task/status/t1", None, {"status": "feature-review"}),
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
