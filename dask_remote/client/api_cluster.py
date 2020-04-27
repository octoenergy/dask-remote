from typing import Optional

from requests import HTTPError

from ..cluster_base import RemoteSchedulerCluster
from .api_client import ApiClient


class ApiCluster(RemoteSchedulerCluster):
    def __init__(
        self,
        url: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        override_scheduler_address: Optional[str] = None,
        override_dashboard_link: Optional[str] = None,
        asynchronous=False,
        loop=None,
        security=None,
    ):
        self.url = url
        self.user = user
        self.password = password
        self.override_scheduler_address = override_scheduler_address
        self.override_dashboard_link = override_dashboard_link
        self._api_client = None
        super().__init__(asynchronous=asynchronous, loop=loop, security=security)

    @property
    def api_client(self):
        if not self._api_client:
            self._api_client = ApiClient(self.url, user=self.user, password=self.password)
        return self._api_client

    @property
    def scheduler_address(self):
        if self.override_scheduler_address:
            return self.override_scheduler_address
        try:
            return self.api_client.get("/scheduler_address").message
        except (ValueError, HTTPError):
            return self.api_client.get("/scheduler_info").address

    @property
    def dashboard_link(self):
        if self.override_dashboard_link:
            return self.override_dashboard_link
        try:
            return self.api_client.get("/dashboard_link").message
        except (ValueError, HTTPError):
            return super().dashboard_link

    def scale(self, n):
        self.api_client.post("/scale/{n}", n=n)

    def adapt(self, minimum, maximum):
        self.api_client.post("/adapt", minimum=minimum, maximum=maximum)
