from requests import HTTPError

from ..client_base import AuthClient


class ApiClient(AuthClient):
    def get_status(self) -> str:
        response = self.get("/status")
        return response["message"]

    def get_scheduler_address(self) -> str:
        try:
            response = self.get("/scheduler_address")
            return response["message"]
        except (KeyError, HTTPError):
            response = self.get("/scheduler_info")
            return response["address"]

    def get_dashboard_link(self) -> str:
        response = self.get("/dashboard_link")
        return response["message"]

    def get_scale(self) -> int:
        response = self.get("/scale")
        return int(response["message"])

    def set_scale(self, n: int) -> None:
        self.post("/scale", params={"n": n})

    def set_adapt(self, minimum: int, maximum: int) -> None:
        self.post("/adapt", params={"minimum": minimum, "maximum": maximum})
