"""HTTP client for the Kaneo REST API."""

from __future__ import annotations

import json
import os
import ssl
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    """An actionable error returned by or raised while calling Kaneo.

    Examples:
        Input: an HTTP 401 response.
        Output: ``ApiError("Kaneo returned 401: check KANEO_API_KEY (...)")``.
    """


class Transport(Protocol):
    """Protocol implemented by HTTP and test transports.

    Examples:
        Input: ``request("GET", "/task/task-1")``.
        Output: a decoded JSON mapping such as ``{"id": "task-1"}``.
    """

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """Send one request through a transport implementation.

        Args:
            method: HTTP method such as ``"GET"`` or ``"POST"``.
            path: API-relative path.
            params: Optional query parameters.
            payload: Optional JSON object to send as the request body.

        Returns:
            The decoded response value, or ``None`` for an empty response.

        Examples:
            Input: ``{"method": "GET", "path": "/task/task-1"}``.
            Output: ``{"id": "task-1", "title": "Fix bug"}``.
        """
        ...


class HttpTransport:
    """Small urllib transport that sends bearer-authenticated JSON requests.

    Args:
        base_url: API base URL, with or without a trailing slash.
        api_key: Bearer token used for authentication.
        timeout: Request timeout in seconds.
        verify_tls: Whether to verify TLS certificates and hostnames.

    Examples:
        Input: ``HttpTransport("https://kaneo.example/api", "token")``.
        Output: a transport ready to return decoded JSON mappings.
    """

    def __init__(
        self, base_url: str, api_key: str, timeout: float = 30.0, verify_tls: bool = True
    ) -> None:
        """Initialize transport settings and its TLS context.

        Args:
            base_url: API base URL.
            api_key: Bearer token used for authentication.
            timeout: Request timeout in seconds.
            verify_tls: Whether to verify TLS certificates and hostnames.

        Examples:
            Input: ``base_url="http://localhost:1337/api"`` and ``timeout=10``.
            Output: a configured transport with a 10-second timeout.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_tls = verify_tls
        self.ssl_context = ssl.create_default_context()
        if not verify_tls:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """Send a request and decode its JSON response.

        Args:
            method: HTTP method to use.
            path: API-relative request path.
            params: Optional query parameters.
            payload: Optional JSON object for the request body.

        Returns:
            The decoded JSON value, or ``None`` when the response is empty.

        Raises:
            ApiError: If the server cannot be reached, returns an HTTP error, or
                returns invalid JSON.

        Examples:
            Input: ``request("GET", "/task/task-1")``.
            Output: ``{"id": "task-1", "title": "Fix bug"}``.
        """
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
            with urlopen(request, timeout=self.timeout, context=self.ssl_context) as response:
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
    """Typed operations used by the Kaneo CLI.

    Args:
        base_url: Kaneo server URL, with or without ``/api``.
        api_key: Bearer token used to authenticate requests.
        transport: Optional transport replacement for tests or embedding.
        verify_tls: Whether the default transport verifies TLS.

    Examples:
        Input: ``ApiClient("http://localhost:1337", "token")``.
        Output: a client whose API base URL is ``http://localhost:1337/api``.
    """

    base_url: str
    api_key: str
    transport: Transport | None = None
    verify_tls: bool = True

    def __post_init__(self) -> None:
        """Normalize the API URL and create the default transport if needed.

        Examples:
            Input: ``base_url="http://localhost:1337/"``.
            Output: ``base_url`` becomes ``"http://localhost:1337/api"``.
        """
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url += "/api"
        if self.transport is None:
            self.transport = HttpTransport(self.base_url, self.api_key, verify_tls=self.verify_tls)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Forward an API request to the configured transport.

        Args:
            method: HTTP method to use.
            path: API-relative request path.
            **kwargs: Optional transport arguments such as ``params`` or
                ``payload``.

        Returns:
            The decoded transport response.

        Examples:
            Input: ``_request("GET", "/task/task-1")``.
            Output: ``{"id": "task-1"}`` from the transport.
        """
        return self.transport.request(method, path, **kwargs)  # type: ignore[union-attr]

    def list_workspaces(self) -> Any:
        """Return the workspaces visible to the authenticated user.

        Returns:
            A decoded list or response mapping supplied by Kaneo.

        Examples:
            Input: no arguments.
            Output: ``[{"id": "workspace-1", "name": "Personal"}]``.
        """
        return self._request("GET", "/auth/organization/list")

    def list_projects(self, workspace_id: str) -> Any:
        """Return projects belonging to ``workspace_id``.

        Args:
            workspace_id: Kaneo workspace identifier.

        Returns:
            A decoded list or response mapping supplied by Kaneo.

        Examples:
            Input: ``workspace_id="workspace-1"``.
            Output: ``[{"id": "project-1", "name": "Website"}]``.
        """
        return self._request("GET", "/project", params={"workspaceId": workspace_id})

    def list_tasks(self, project_id: str, page: int = 1, limit: int = 50) -> Any:
        """Return the task board and pagination for a project.

        Args:
            project_id: Kaneo project identifier.
            page: One-based page number.
            limit: Maximum number of tasks to request.

        Returns:
            The decoded task board response from Kaneo.

        Examples:
            Input: ``project_id="project-1", page=1, limit=50``.
            Output: ``{"tasks": [{"id": "task-1"}], "page": 1}``.
        """
        return self._request(
            "GET", f"/task/tasks/{project_id}", params={"page": page, "limit": limit}
        )

    def get_task(self, task_id: str) -> Any:
        """Return one task by ID.

        Args:
            task_id: Kaneo task identifier.

        Returns:
            The decoded task object supplied by Kaneo.

        Examples:
            Input: ``task_id="task-1"``.
            Output: ``{"id": "task-1", "title": "Fix bug"}``.
        """
        return self._request("GET", f"/task/{task_id}")

    def create_task(self, project_id: str, payload: dict[str, Any]) -> Any:
        """Create a task and read it back when an ID is returned.

        Args:
            project_id: Kaneo project identifier.
            payload: Task fields accepted by the server.

        Returns:
            The created task when the response includes an ID, otherwise the
            server's decoded response.

        Examples:
            Input: ``project_id="project-1", payload={"title": "Fix bug"}``.
            Output: ``{"id": "task-1", "title": "Fix bug"}``.
        """
        created = self._request("POST", f"/task/{project_id}", payload=payload)
        if isinstance(created, dict) and created.get("id"):
            return self.get_task(str(created["id"]))
        return created

    def update_task(self, task_id: str, changes: dict[str, Any]) -> Any:
        """Apply task changes using the narrow status route when appropriate.

        Status-only changes use Kaneo's dedicated status endpoint. All other
        changes retain the full-object update behavior required by Kaneo.

        Args:
            task_id: Kaneo task identifier.
            changes: Task fields to replace or update.

        Returns:
            The task read back after the mutation.

        Raises:
            ApiError: If Kaneo does not return an existing task object for a
                full-object update.

        Examples:
            Input: ``task_id="task-1", changes={"title": "New title"}``.
            Output: ``{"id": "task-1", "title": "New title"}``.
        """
        if set(changes) == {"status"}:
            return self.update_task_status(task_id, changes["status"])
        existing = self.get_task(task_id)
        if not isinstance(existing, dict):
            raise ApiError("Kaneo returned no task object to update")
        payload = {**existing, **changes}
        self._request("PUT", f"/task/{task_id}", payload=payload)
        return self.get_task(task_id)

    def update_task_status(self, task_id: str, status: Any) -> Any:
        """Set a task's status through Kaneo's dedicated endpoint.

        Args:
            task_id: Kaneo task identifier.
            status: Status column slug accepted by the server.

        Returns:
            The task read back after the status mutation.

        Examples:
            Input: ``task_id="task-1", status="done"``.
            Output: ``{"id": "task-1", "status": "done"}``.
        """
        self._request("PUT", f"/task/status/{task_id}", payload={"status": status})
        return self.get_task(task_id)

    def create_task_comment(self, task_id: str, content: str) -> Any:
        """Add a comment to a task.

        Args:
            task_id: Kaneo task identifier.
            content: Comment text.

        Returns:
            The decoded response supplied by Kaneo.

        Examples:
            Input: ``task_id="task-1", content="Investigating this."``.
            Output: ``{"id": "comment-1", "content": "Investigating this."}``.
        """
        return self._request("POST", f"/comment/{task_id}", payload={"content": content})


def client_from_environment(*, verify_tls: bool = True) -> ApiClient:
    """Construct a client from environment settings.

    Args:
        verify_tls: Whether to verify the server certificate and hostname.

    Returns:
        A client configured from ``KANEO_API_URL`` and ``KANEO_API_KEY``.

    Raises:
        ApiError: If ``KANEO_API_KEY`` is not set.

    Examples:
        Input: ``KANEO_API_URL="http://localhost:1337"`` and a configured API key.
        Output: an ``ApiClient`` targeting ``http://localhost:1337/api``.
    """
    key = os.getenv("KANEO_API_KEY")
    if not key:
        raise ApiError("KANEO_API_KEY is required; set it in the environment")
    return ApiClient(
        os.getenv("KANEO_API_URL", "http://localhost:1337"), key, verify_tls=verify_tls
    )
