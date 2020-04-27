from typing import Optional

import requests

from .api import cluster_api

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
        url = self.url.rstrip("/") + endpoint
        model = self.GET_ENDPOINTS[endpoint]

        response = requests.get(url, auth=self.auth)
        response.raise_for_status()

        return model(**response.json())

    def post(self, endpoint: str, **kwargs):
        if endpoint not in self.POST_ENDPOINTS:
            raise ValueError("Unknown endpoint '{method}'")
        url = self.url.rstrip("/") + endpoint.format(**kwargs)
        model = self.POST_ENDPOINTS[endpoint]

        response = requests.post(url, auth=self.auth)
        response.raise_for_status()

        return model(**response.json())
