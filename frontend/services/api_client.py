import os
from typing import Any, Dict, Optional

import requests


class APIClient:
    """
    Centralized HTTP client for communicating with backend API.
    Keeps session alive and handles errors consistently.
    """

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout  # seconds

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _handle_response(self, response: requests.Response) -> Any:
        # 204 No Content is a successful response with empty body
        if response.status_code == 204:
            return None

        # Success responses
        if response.ok:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        # Error responses
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        raise Exception(f"API Error {response.status_code}: {error_data}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self.session.get(
                self._build_url(endpoint),
                params=params,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise Exception(f"Connection error: {e}")

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self.session.post(
                self._build_url(endpoint),
                json=data,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise Exception(f"Connection error: {e}")

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self.session.put(
                self._build_url(endpoint),
                json=data,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise Exception(f"Connection error: {e}")

    def delete(self, endpoint: str) -> Any:
        try:
            response = self.session.delete(
                self._build_url(endpoint),
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise Exception(f"Connection error: {e}")


BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
api = APIClient(BASE_URL)
