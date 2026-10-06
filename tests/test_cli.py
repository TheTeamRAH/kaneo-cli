from test_client import FakeTransport

from kaneo_cli.cli import main
from kaneo_cli.client import ApiClient


def test_cli_version_reports_package_version(capsys):
    try:
        main(["--version"])
    except SystemExit as error:
        assert error.code == 0

    assert capsys.readouterr().out == "kaneo-cli 0.1.0\n"


def test_cli_task_update_emits_compact_stable_json(capsys):
    existing = {"id": "t1", "title": "Old", "projectId": "p1"}
    transport = FakeTransport([existing, {}, {"id": "t1", "projectId": "p1", "title": "New"}])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert main(["task", "update", "t1", "--title", "New", "--json"], client=client) == 0
    assert capsys.readouterr().out == '{"id":"t1","projectId":"p1","title":"New"}\n'


def test_cli_task_comment_list_emits_json(capsys):
    comments = [{"id": "c1", "content": "Ready", "authorName": "Ada"}]
    transport = FakeTransport([comments])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert main(["comment", "list", "--task-id", "t1", "--json"], client=client) == 0
    assert transport.calls == [("GET", "/comment/t1", None, None)]
    assert capsys.readouterr().out == '[{"authorName":"Ada","content":"Ready","id":"c1"}]\n'


def test_cli_task_create_uses_project_path_without_project_body_field(capsys):
    transport = FakeTransport([
        {"id": "t1"},
        {"id": "t1", "projectId": "p1", "title": "Prepare"},
    ])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert main(
        ["task", "create", "--project-id", "p1", "--title", "Prepare", "--json"],
        client=client,
    ) == 0
    assert transport.calls == [
        ("POST", "/task/p1", None, {"title": "Prepare"}),
        ("GET", "/task/t1", None, None),
    ]
    assert capsys.readouterr().out == '{"id":"t1","projectId":"p1","title":"Prepare"}\n'


def test_cli_task_status_is_sent_as_api_status_for_create_and_update():
    transport = FakeTransport([
        {"id": "t1"},
        {"id": "t1", "status": "feature-review"},
        {},
        {"id": "t1", "title": "Prepare", "status": "feature-review"},
    ])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert main(
        [
            "task",
            "create",
            "--project-id",
            "p1",
            "--title",
            "Prepare",
            "--status",
            "feature-review",
        ],
        client=client,
    ) == 0
    assert main(
        ["task", "update", "t1", "--status", "feature-review"],
        client=client,
    ) == 0

    assert transport.calls[0] == ("POST", "/task/p1", None, {
        "title": "Prepare",
        "status": "feature-review",
    })
    assert transport.calls[2] == ("PUT", "/task/status/t1", None, {
        "status": "feature-review",
    })
    assert transport.calls[3] == ("GET", "/task/t1", None, None)


def test_cli_reports_missing_key_without_traceback(capsys, monkeypatch):
    monkeypatch.delenv("KANEO_API_KEY", raising=False)

    assert main(["workspace", "list"]) == 1
    assert "KANEO_API_KEY" in capsys.readouterr().err


def test_cli_no_tls_verify_is_explicit_and_passed_to_client(monkeypatch):
    received = []

    def fake_client_from_environment(*, verify_tls):
        received.append(verify_tls)
        return ApiClient("https://kaneo.example/api", "secret", transport=FakeTransport([[]]))

    monkeypatch.setattr("kaneo_cli.cli.client_from_environment", fake_client_from_environment)

    assert main(["--no-tls-verify", "workspace", "list"]) == 0
    assert received == [False]
