import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


# ---------- Exceptions ----------

@dataclass
class APIErrorDetail:
    status_code: int
    message: str
    data: Any = None  # raw parsed response (json/text) if available


class APIClientError(Exception):
    """Raised when backend returns non-2xx response."""

    def __init__(self, detail: APIErrorDetail):
        self.detail = detail
        super().__init__(f"API Error {detail.status_code}: {detail.message}")


class APIConnectionError(Exception):
    """Raised when request fails due to network/timeout/DNS/connection errors."""

    def __init__(self, message: str):
        super().__init__(message)


# ---------- Client ----------

class APIClient:
    """
    Centralized HTTP client for communicating with backend API.
    - Uses requests.Session for connection pooling
    - Unified parsing (json/text) and error handling
    - Easy to add auth headers later
    """

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout  # seconds

    def set_auth_token(self, token: Optional[str]) -> None:
        """
        Optional helper: set/remove Authorization header.
        Later you can call this from auth_service after login.
        """
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            # Remove header if exists
            self.session.headers.pop("Authorization", None)

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _parse_body(self, response: requests.Response) -> Any:
        # 204 No Content
        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # If body is empty but marked as json, this might still throw; guard it.
            if not response.content:
                return None
            return response.json()

        # fallback: plain text (or html)
        return response.text

    def _handle_response(self, response: requests.Response) -> Any:
        body = self._parse_body(response)

        if response.ok:
            return body

        # Build a helpful message
        message = "Request failed"
        if isinstance(body, dict):
            # common patterns: {"detail": "..."} or {"message": "..."}
            message = (
                str(body.get("detail"))
                if body.get("detail") is not None
                else str(body.get("message")) if body.get("message") is not None
                else message
            )
        elif isinstance(body, str) and body.strip():
            message = body.strip()[:300]  # keep it short

        raise APIClientError(
            APIErrorDetail(status_code=response.status_code, message=message, data=body)
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = self.session.request(
                method=method,
                url=self._build_url(endpoint),
                params=params,
                json=json,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            # Includes: ConnectionError, Timeout, TooManyRedirects, etc.
            raise APIConnectionError(f"Connection error: {e}") from e

    # Public helpers
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, json=data)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PUT", endpoint, json=data)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)


# ---------- Singleton instance ----------

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
api = APIClient(BASE_URL)
