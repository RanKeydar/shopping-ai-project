import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


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

    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = timeout  # seconds

    def set_auth_token(self, token: Optional[str]) -> None:
        """
        Optional helper: set/remove Authorization header.
        Later you can call this from auth_service after login.
        """
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _parse_body(self, response: requests.Response) -> Any:
        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            if not response.content:
                return None
            return response.json()

        return response.text

    def _handle_response(self, response: requests.Response) -> Any:
        body = self._parse_body(response)

        if response.ok:
            return body

        message = "Request failed"
        if isinstance(body, dict):
            message = (
                str(body.get("detail"))
                if body.get("detail") is not None
                else str(body.get("message"))
                if body.get("message") is not None
                else message
            )
        elif isinstance(body, str) and body.strip():
            message = body.strip()[:300]

        raise APIClientError(
            APIErrorDetail(
                status_code=response.status_code,
                message=message,
                data=body,
            )
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int | tuple[int, int]] = None,
    ) -> Any:
        try:
            logger.debug(f"{method} {endpoint} params={params} json={json}")
            response = self.session.request(
                method=method,
                url=self._build_url(endpoint),
                params=params,
                json=json,
                timeout=timeout if timeout is not None else self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"API connection error: {method} {endpoint} -> {e}")
            raise APIConnectionError(f"Connection error: {e}") from e

    # Public helpers
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int | tuple[int, int]] = None,
    ) -> Any:
        return self._request("GET", endpoint, params=params, timeout=timeout)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int | tuple[int, int]] = None,
    ) -> Any:
        return self._request("POST", endpoint, json=data, timeout=timeout)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int | tuple[int, int]] = None,
    ) -> Any:
        return self._request("PUT", endpoint, json=data, timeout=timeout)

    def delete(
        self,
        endpoint: str,
        timeout: Optional[int | tuple[int, int]] = None,
    ) -> Any:
        return self._request("DELETE", endpoint, timeout=timeout)


# ---------- Singleton instance ----------

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
api = APIClient(BASE_URL)