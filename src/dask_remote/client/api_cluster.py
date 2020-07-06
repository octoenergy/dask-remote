from typing import Optional

from ..cluster_base import RemoteSchedulerCluster
from .api_client import ApiClient


class ApiCluster(RemoteSchedulerCluster):
    _api_client: Optional[ApiClient] = None

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
        super().__init__(asynchronous=asynchronous, loop=loop, security=security)

    @property
    def api_client(self) -> ApiClient:
        if self._api_client is None:
            self._api_client = ApiClient(self.url)
            if self.user and self.password:
                self._api_client.set_proxy_credentials(self.user, self.password)
        return self._api_client

    @property
    def scheduler_address(self) -> str:
        if self.override_scheduler_address:
            return self.override_scheduler_address
        return self.api_client.get_scheduler_address()

    @property
    def dashboard_link(self) -> str:
        if self.override_dashboard_link:
            return self.override_dashboard_link
        return self.api_client.get_dashboard_link()

    def scale(self, n) -> None:
        self.api_client.set_scale(n)

    def adapt(self, minimum, maximum) -> None:
        self.api_client.set_adapt(minimum, maximum)
