"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import os
import json
import logging

from prometheus_client import Gauge, start_http_server
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop, PeriodicCallback
from functools import partial


logger = logging.getLogger(__name__)

async def api_request(hub_url, path, token=None, parse_json=True, **kwargs):
    """Make an API request to the Hub, parsing JSON responses"""
    hub_url = hub_url.rstrip("/")
    headers = kwargs.setdefault("headers", {})
    headers["Authorization"] = f"token {token}"

    path = path.lstrip("/")
    url = f"{hub_url}/hub/api/{path}"
    logger.info(f"api_request: {url}, {kwargs}")
    client = AsyncHTTPClient()
    try:
        resp = await client.fetch(url, **kwargs)
    except Exception as e:
        logger.info(f"Error fetching {url}: {e}")
    else:
        if not parse_json:
            return resp
        if resp.body:
            return json.loads(resp.body.decode("utf8"))
        else:
            return None


async def get_user_groups(hub_url, token, metrics_prefix, **kwargs):
    """
    Get the user groups from the JupyterHub API
    """
    USER_GROUP = Gauge(
    'user_group',
    'Get user group memberships',
    ['user', 'user_group'],
    namespace=metrics_prefix,
)
    response = await api_request(
        hub_url,
        path="groups",
        token=token,
    )
    if response:
        USER_GROUP.clear()  # Clear previous metrics
        for group in response:
            for user in group["users"]:
                USER_GROUP.labels(user_group=f"{group['name']}", user=f"{user}").set(1)


def main():
    argparser = argparse.ArgumentParser(description="JupyterHub user groups exporter for Prometheus.")
    argparser.add_argument(
        "--port",
        default=9090,
        type=int,
        help="Port to listen on for the groups exporter.",
    )
    argparser.add_argument(
        "--update_exporter_interval",
        default=3600,
        type=int,
        help="Time interval between each update of the JupyterHub groups exporter (seconds).",
    )
    argparser.add_argument(
        "--hub_url",
        default="http://127.0.0.1:8000",
        type=str,
        help="JupyterHub URL.",
    )
    argparser.add_argument(
        "--api_token",
        default=os.environ.get("JUPYTERHUB_API_TOKEN"),
        type=str,
        help="Token to talk to the JupyterHub API.",
    )
    argparser.add_argument(
        "--jupyterhub_metrics_prefix",
        default=os.environ.get("JUPYTERHUB_METRICS_PREFIX", "jupyterhub"),
        type=str,
        help="Prefix for the JupyterHub metrics for Prometheus.",
    )
    argparser.add_argument(
        "--jupyterhub_service_prefix",
        default=os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "jupyterhub"),
        type=str,
        help="Prometheus prefix/namespace for JupyterHub metrics.",
    )
    args = argparser.parse_args()

    start_http_server(args.port)

    loop = IOLoop.current()
    callback =  partial(get_user_groups, args.hub_url, args.api_token, args.metrics_prefix)
    # Set up immediate one-off callback to get user groups
    loop.add_callback(callback)
    # Set up a periodic callback to update the user groups
    pc = PeriodicCallback(callback, args.update_exporter_interval * 1000)  # convert to milliseconds
    pc.start()
    try:
        loop.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
