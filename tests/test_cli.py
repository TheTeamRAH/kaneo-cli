from test_client import FakeTransport

from kaneo_cli.cli import main
from kaneo_cli.client import ApiClient


def test_cli_task_update_emits_compact_stable_json(capsys):
    existing = {"id": "t1", "title": "Old", "projectId": "p1"}
    transport = FakeTransport([existing, {}, {"id": "t1", "projectId": "p1", "title": "New"}])
    client = ApiClient("https://kaneo.example/api", "secret", transport=transport)

    assert main(["task", "update", "t1", "--title", "New", "--json"], client=client) == 0
    assert capsys.readouterr().out == '{"id":"t1","projectId":"p1","title":"New"}\n'


def test_cli_reports_missing_key_without_traceback(capsys, monkeypatch):
    monkeypatch.delenv("KANEO_API_KEY", raising=False)

    assert main(["workspace", "list"]) == 1
    assert "KANEO_API_KEY" in capsys.readouterr().err
