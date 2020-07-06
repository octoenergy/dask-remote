from distributed.deploy.adaptive import Adaptive


class StatelessAdaptive(Adaptive):
    """Perform cluster scaling to the recommended number of workers.

    This is used for scaling via K8S Deployment, since we are not currently able
    to follow recommendations on which workers to retire.
    """

    async def recommendations(self, target: int) -> dict:
        recommendation = await super(Adaptive, self).recommendations(target)
        recommendation.update(n=target)
        return recommendation

    async def scale_down(self, n, workers):
        self.cluster.scale(n)

    async def scale_up(self, n):
        self.cluster.scale(n)
