import kubernetes_asyncio as kubernetes


async def _config_from_file(
    config_file=None, context=None, client_configuration=None, persist_config=True
):
    await kubernetes.config.load_kube_config(
        config_file=config_file,
        context=context,
        client_configuration=client_configuration,
        persist_config=persist_config,
    )


def _config_incluster():
    kubernetes.config.load_incluster_config()


async def k8s_config(in_cluster=False, config_file=None):
    if in_cluster:
        _config_incluster()
    else:
        await _config_from_file(config_file=config_file)


def get_AppsV1Api():
    configuration = kubernetes.client.Configuration()
    api_client = kubernetes.client.ApiClient(configuration)
    api_instance = kubernetes.client.AppsV1Api(api_client)
    return api_instance
