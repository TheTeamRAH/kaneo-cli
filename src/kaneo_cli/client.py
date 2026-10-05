"""HTTP client for the Kaneo REST API."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    """An actionable error returned by or raised while calling Kaneo."""


class Transport(Protocol):
    """Protocol implemented by HTTP and test transports."""

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any: ...


class HttpTransport:
    """Small urllib transport that sends bearer-authenticated JSON requests."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """Send a request and decode its JSON response."""
        query = ""
        if params:
            from urllib.parse import urlencode

            query = "?" + urlencode(params)
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.base_url + path + query,
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as error:
            detail = error.read().decode(errors="replace")[:300]
            hint = (
                "check KANEO_API_KEY"
                if error.code in (401, 403)
                else "check the request and server"
            )
            raise ApiError(f"Kaneo returned {error.code}: {hint} ({detail})") from error
        except URLError as error:
            raise ApiError(f"Unable to reach Kaneo at {self.base_url}: {error.reason}") from error
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise ApiError("Kaneo returned an invalid JSON response") from error


@dataclass
class ApiClient:
    """Typed operations used by the Kaneo CLI."""

    base_url: str
    api_key: str
    transport: Transport | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url += "/api"
        if self.transport is None:
            self.transport = HttpTransport(self.base_url, self.api_key)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.transport.request(method, path, **kwargs)  # type: ignore[union-attr]

    def list_workspaces(self) -> Any:
        """Return workspaces visible to the authenticated user."""
        return self._request("GET", "/workspace")

    def list_projects(self, workspace_id: str) -> Any:
        """Return projects belonging to ``workspace_id``."""
        return self._request("GET", "/project", params={"workspaceId": workspace_id})

    def list_tasks(self, project_id: str, page: int = 1, limit: int = 50) -> Any:
        """Return the task board and pagination for a project."""
        return self._request(
            "GET", f"/task/tasks/{project_id}", params={"page": page, "limit": limit}
        )

    def get_task(self, task_id: str) -> Any:
        """Return one task by ID."""
        return self._request("GET", f"/task/{task_id}")

    def create_task(self, payload: dict[str, Any]) -> Any:
        """Create a task and read it back when an ID is returned."""
        created = self._request("POST", "/task", payload=payload)
        if isinstance(created, dict) and created.get("id"):
            return self.get_task(str(created["id"]))
        return created

    def update_task(self, task_id: str, changes: dict[str, Any]) -> Any:
        """Apply changes to a full task object and read back the exact task."""
        existing = self.get_task(task_id)
        if not isinstance(existing, dict):
            raise ApiError("Kaneo returned no task object to update")
        payload = {**existing, **changes}
        self._request("PUT", f"/task/{task_id}", payload=payload)
        return self.get_task(task_id)

    def create_task_comment(self, task_id: str, content: str) -> Any:
        """Add a comment to a task."""
        return self._request("POST", f"/task/{task_id}/comment", payload={"content": content})


def client_from_environment() -> ApiClient:
    """Construct a client from ``KANEO_API_KEY`` and ``KANEO_API_URL``."""
    key = os.getenv("KANEO_API_KEY")
    if not key:
        raise ApiError("KANEO_API_KEY is required; set it in the environment")
    return ApiClient(os.getenv("KANEO_API_URL", "http://localhost:1337"), key)
