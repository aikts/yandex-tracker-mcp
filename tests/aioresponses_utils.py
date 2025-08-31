"""Utilities for type-safe aioresponses request verification."""

import json
from dataclasses import dataclass, field
from typing import Any

from aioresponses import CallbackResult
from yarl import URL


@dataclass
class CapturedRequest:
    """Captured HTTP request details."""

    url: URL
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    data: Any = None
    json_data: Any = None

    def assert_header(self, name: str, expected: str) -> None:
        """Assert that a header has the expected value."""
        assert name in self.headers, (
            f"Header '{name}' not found in request headers: {self.headers}"
        )
        assert self.headers[name] == expected, (
            f"Header '{name}' has value '{self.headers[name]}', expected '{expected}'"
        )

    def assert_headers(self, expected: dict[str, str]) -> None:
        """Assert that multiple headers have expected values."""
        for name, value in expected.items():
            self.assert_header(name, value)

    def assert_param(self, name: str, expected: Any) -> None:
        """Assert that a query parameter has the expected value."""
        assert name in self.params, (
            f"Param '{name}' not found in request params: {self.params}"
        )
        assert self.params[name] == expected, (
            f"Param '{name}' has value '{self.params[name]}', expected '{expected}'"
        )

    def assert_params(self, expected: dict[str, Any]) -> None:
        """Assert that multiple query parameters have expected values."""
        for name, value in expected.items():
            self.assert_param(name, value)

    def get_json_body(self) -> dict[str, Any]:
        """Get the request body as parsed JSON."""
        if self.json_data is not None:
            return self.json_data
        if self.data is not None:
            return json.loads(self.data)
        return {}

    def assert_json_body(self, expected: dict[str, Any]) -> None:
        """Assert that the JSON body matches expected value."""
        actual = self.get_json_body()
        assert actual == expected, (
            f"JSON body mismatch: expected {expected}, got {actual}"
        )

    def assert_json_field(self, name: str, expected: Any) -> None:
        """Assert that a specific field in the JSON body has expected value."""
        body = self.get_json_body()
        assert name in body, f"Field '{name}' not found in JSON body: {body}"
        assert body[name] == expected, (
            f"Field '{name}' has value '{body[name]}', expected '{expected}'"
        )


class RequestCapture:
    """Captures HTTP requests for later verification.

    Usage:
        capture = RequestCapture()
        with aioresponses() as m:
            m.get(url, payload=data, callback=capture.callback)
            # ... make request ...

        capture.assert_request_count(1)
        capture.last_request.assert_header("Authorization", "OAuth token")
    """

    def __init__(
        self, *, status: int = 200, payload: Any = None, body: str = ""
    ) -> None:
        """Initialize capture with response details.

        Args:
            status: HTTP status code to return
            payload: JSON payload to return (will be serialized)
            body: Raw body string to return
        """
        self._requests: list[CapturedRequest] = []
        self._status = status
        self._payload = payload
        self._body = body

    def callback(self, url: URL, **kwargs: Any) -> CallbackResult:
        """Callback to capture request details and return configured response."""
        # Extract headers from kwargs, handling different possible formats
        headers = kwargs.get("headers", {})
        if hasattr(headers, "items"):
            headers = dict(headers.items())

        self._requests.append(
            CapturedRequest(
                url=url,
                method=kwargs.get("method", "GET"),
                headers=headers,
                params=kwargs.get("params", {}),
                data=kwargs.get("data"),
                json_data=kwargs.get("json"),
            )
        )
        return CallbackResult(
            status=self._status, payload=self._payload, body=self._body
        )

    @property
    def requests(self) -> list[CapturedRequest]:
        """Get all captured requests."""
        return self._requests

    @property
    def last_request(self) -> CapturedRequest:
        """Get the last captured request."""
        assert self._requests, "No requests were captured"
        return self._requests[-1]

    @property
    def first_request(self) -> CapturedRequest:  # pragma: no cover
        """Get the first captured request."""
        assert self._requests, "No requests were captured"
        return self._requests[0]

    def assert_request_count(self, expected: int) -> None:
        """Assert the number of captured requests."""
        actual = len(self._requests)
        assert actual == expected, f"Expected {expected} requests, got {actual}"

    def assert_called(self) -> None:  # pragma: no cover
        """Assert that at least one request was made."""
        assert self._requests, "Expected at least one request, but none were captured"

    def assert_called_once(self) -> None:
        """Assert that exactly one request was made."""
        self.assert_request_count(1)
