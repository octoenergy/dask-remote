from string import Formatter
from typing import Optional

import requests

from ..runner.api import cluster_api

_api_app = cluster_api()
_api_get_endpoints = {
    route.path: route.response_model
    for route in _api_app.routes
    if getattr(route, "response_model", None) and "GET" in route.methods
}
_api_post_endpoints = {
    route.path: route.response_model
    for route in _api_app.routes
    if getattr(route, "response_model", None) and "POST" in route.methods
}


class ApiClient:
    GET_ENDPOINTS = _api_get_endpoints
    POST_ENDPOINTS = _api_post_endpoints

    def __init__(self, url: str, user: Optional[str] = None, password: Optional[str] = None):
        self.url = url
        self.user = user
        self.password = password

    @property
    def auth(self):
        if self.user or self.password:
            auth = (self.user, self.password)
        else:
            auth = None
        return auth

    def get(self, endpoint: str):
        if endpoint not in self.GET_ENDPOINTS:
            raise ValueError("Unknown endpoint '{method}'")
        model = self.GET_ENDPOINTS[endpoint]
        url = self.url.rstrip("/") + endpoint

        response = requests.get(url, auth=self.auth)
        response.raise_for_status()

        return model(**response.json())

    @staticmethod
    def _format_endpoint(endpoint: str, **kwargs):
        """
        Insert kwargs into query string.

        _format_endpoint("/scale/{n}", n=1, param='a') returns "/scale/1", {param='a'},
        which in turn is used to construct the query "/scale/1?param=a"
        """
        refs = {fn for _, fn, _, _ in Formatter().parse(endpoint) if fn is not None}
        return endpoint.format(**kwargs), {k: v for k, v in kwargs.items() if k not in refs}

    def post(self, endpoint: str, **kwargs):
        if endpoint not in self.POST_ENDPOINTS:
            raise ValueError("Unknown endpoint '{method}'")
        model = self.POST_ENDPOINTS[endpoint]
        endpoint, kwargs = self._format_endpoint(endpoint, **kwargs)
        url = self.url.rstrip("/") + endpoint

        response = requests.post(url, auth=self.auth, params=kwargs)
        response.raise_for_status()

        return model(**response.json())
