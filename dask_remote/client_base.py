from typing import Optional

from requests import Session, auth


# Default connection timeout at 10''
DEFAULT_TIMEOUT = 10.0

# Default JSON response back
DEFAULT_HEADERS = {"Accept": "application/json"}


class ClientError(Exception):
    ...


class JSONClient:
    """Base class for JSON clients."""

    _conn: Optional[Session] = None

    def __init__(
        self, base_url: str, default_timeout: float = None, default_headers: dict = None
    ) -> None:
        self._url = base_url
        self._timeout = default_timeout or DEFAULT_TIMEOUT
        self._headers = default_headers or DEFAULT_HEADERS

    @property
    def conn(self) -> Session:
        if self._conn is None:
            self._conn = Session()
            self._conn.headers.update(self._headers)
        return self._conn

    # Public HTTP methods:

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        return self._request(method="GET", path=path, params=params)

    def post(self, path: str, params: Optional[dict] = None, data: Optional[dict] = None) -> dict:
        return self._request(method="POST", path=path, params=params, data=data)

    # Private methods:

    def _request(
        self, method: str, path: str, params: Optional[dict] = None, data: Optional[dict] = None,
    ) -> dict:
        url = self._url.rstrip("/") + "/" + path.lstrip("/")
        response = self.conn.request(
            method, url, params=params, json=data, headers=self._headers, timeout=self._timeout
        )

        response.raise_for_status()
        if "application/json" != response.headers.get("content-type", ""):
            raise ClientError(f"No JSON content returned: {response.text}")

        return response.json()


class AuthClient(JSONClient):
    """Base class for authenticated clients (basic auth)."""

    def set_proxy_credentials(self, username: str, password: str) -> None:
        """Set reverse-proxy credentials."""
        proxy_auth = auth.HTTPBasicAuth(username, password)
        proxy_auth(self.conn)
