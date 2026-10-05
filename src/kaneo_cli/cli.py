"""Command-line interface for Kaneo."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .client import ApiClient, ApiError, client_from_environment


def _payload(args: argparse.Namespace, *, include_project: bool = False) -> dict[str, Any]:
    """Build a Kaneo task payload from parsed command-line arguments.

    Args:
        args: Parsed arguments containing optional task fields.
        include_project: Whether to include the parsed project identifier.

    Returns:
        A mapping containing only task fields whose values were provided.

    Examples:
        Input: a namespace with ``title="Fix bug"`` and ``priority="high"``.
        Output: ``{"title": "Fix bug", "priority": "high"}``.
    """
    values = {
        "title": getattr(args, "title", None),
        "description": getattr(args, "description", None),
        "projectId": getattr(args, "project_id", None) if include_project else None,
        "columnId": getattr(args, "column_id", None),
        "status": getattr(args, "status", None),
        "priority": getattr(args, "priority", None),
        "dueDate": getattr(args, "due_date", None),
    }
    return {key: value for key, value in values.items() if value is not None}


def _emit(value: Any, as_json: bool) -> None:
    """Print a command result in human-readable or compact JSON form.

    Args:
        value: Scalar, mapping, or sequence returned by an API operation.
        as_json: Whether to use compact JSON output.

    Examples:
        Input: ``{"id": "task-1"}`` and ``as_json=True``.
        Output: one line containing ``{"id":"task-1"}``.
    """
    if as_json:
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    elif isinstance(value, (dict, list)):
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(value)


def _run(args: argparse.Namespace, client: ApiClient) -> Any:
    """Dispatch parsed resource arguments to the matching API operation.

    Args:
        args: Parsed command-line namespace with resource and verb fields.
        client: API client used to perform the selected operation.

    Returns:
        The operation result, ready for output formatting.

    Raises:
        ApiError: If no supported command is selected.

    Examples:
        Input: ``Namespace(resource="workspace", verb="list")``.
        Output: the list returned by ``client.list_workspaces()``.
    """
    if args.resource == "workspace":
        return client.list_workspaces()
    if args.resource == "project":
        return client.list_projects(args.workspace_id)
    if args.resource == "task" and args.verb == "list":
        return client.list_tasks(args.project_id, args.page, args.limit)
    if args.resource == "task" and args.verb == "show":
        return client.get_task(args.task_id)
    if args.resource == "task" and args.verb == "create":
        return client.create_task(args.project_id, _payload(args))
    if args.resource == "task" and args.verb == "update":
        return client.update_task(args.task_id, _payload(args))
    if args.resource == "comment":
        return client.create_task_comment(args.task_id, args.content)
    raise ApiError("No command selected")


def _add_json(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``--json`` output option to a subparser.

    Args:
        parser: Subparser that should accept machine-readable output.

    Examples:
        Input: an ``ArgumentParser`` for ``task list``.
        Output: the parser accepts ``--json`` and sets ``args.json`` to ``True``.
    """
    parser.add_argument("--json", action="store_true", help="emit compact JSON for scripts")


def _add_task_fields(parser: argparse.ArgumentParser, required_title: bool = False) -> None:
    """Add common task creation and update options to a subparser.

    Args:
        parser: Subparser that should accept task fields.
        required_title: Whether ``--title`` must be supplied.

    Examples:
        Input: a task-create parser with ``required_title=True``.
        Output: parsed arguments include ``title``, ``description``, and other
        optional task fields, with ``title`` required.
    """
    parser.add_argument("--title", required=required_title, help="task title")
    parser.add_argument("--description", help="task description")
    parser.add_argument("--column-id", help="Kaneo column ID")
    parser.add_argument("--status", help="Kaneo task status column slug")
    parser.add_argument("--priority", help="task priority")
    parser.add_argument("--due-date", help="due date in the server's accepted format")


def build_parser() -> argparse.ArgumentParser:
    """Build the Kaneo argument parser.

    Returns:
        A parser containing workspace, project, task, and comment subcommands.

    Examples:
        Input: no arguments.
        Output: a parser that accepts ``task list --project-id project-1``.
    """
    parser = argparse.ArgumentParser(
        prog="kaneo", description="Manage a self-hosted Kaneo instance"
    )
    parser.add_argument(
        "--no-tls-verify",
        action="store_true",
        help=(
            "disable TLS certificate and hostname verification (INSECURE; only use "
            "for trusted self-hosted deployments with private certificates)"
        ),
    )
    resources = parser.add_subparsers(dest="resource", required=True)

    workspace = resources.add_parser("workspace", help="workspace operations")
    workspace.set_defaults(verb="list")
    workspace_sub = workspace.add_subparsers(dest="verb", required=True)
    workspace_sub.add_parser("list", help="list workspaces")
    _add_json(workspace_sub.choices["list"])

    project = resources.add_parser("project", help="project operations")
    project_sub = project.add_subparsers(dest="verb", required=True)
    project_list = project_sub.add_parser("list", help="list projects in a workspace")
    project_list.add_argument("--workspace-id", required=True)
    _add_json(project_list)

    task = resources.add_parser("task", help="task operations")
    task_sub = task.add_subparsers(dest="verb", required=True)
    task_list = task_sub.add_parser("list", help="list tasks in a project")
    task_list.add_argument("--project-id", required=True)
    task_list.add_argument("--page", type=int, default=1)
    task_list.add_argument("--limit", type=int, default=50)
    _add_json(task_list)
    task_show = task_sub.add_parser("show", help="show one task")
    task_show.add_argument("task_id")
    _add_json(task_show)
    task_create = task_sub.add_parser("create", help="create a task")
    task_create.add_argument("--project-id", required=True)
    _add_task_fields(task_create, required_title=True)
    _add_json(task_create)
    task_update = task_sub.add_parser("update", help="update a task")
    task_update.add_argument("task_id")
    _add_task_fields(task_update)
    _add_json(task_update)

    comment = resources.add_parser("comment", help="task comment operations")
    comment_sub = comment.add_subparsers(dest="verb", required=True)
    comment_create = comment_sub.add_parser("create", help="add a comment to a task")
    comment_create.add_argument("--task-id", required=True)
    comment_create.add_argument("--content", required=True)
    _add_json(comment_create)
    return parser


def main(argv: list[str] | None = None, client: ApiClient | None = None) -> int:
    """Run the CLI and return a process exit status.

    Args:
        argv: Optional argument list; defaults to the process command line.
        client: Optional client, primarily useful for embedding and tests.

    Returns:
        ``0`` for success or ``1`` when an API error is reported.

    Examples:
        Input: ``["workspace", "list"]`` with an injected client.
        Output: ``0`` after printing the workspace response.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = _run(
            args,
            client or client_from_environment(verify_tls=not args.no_tls_verify),
        )
        _emit(result, args.json)
    except ApiError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
