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

metrics_prefix = os.getenv('JUPYTERHUB_METRICS_PREFIX', 'jupyterhub')

USER_GROUP = Gauge(
    'user_group',
    'Get user group memberships',
    ['user', 'user_group'],
    namespace=metrics_prefix,
)


def get_service_token():
    """Get the service token"""
    token = os.environ.get("JUPYTERHUB_API_TOKEN")
    return token


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


async def get_user_groups(hub_url, **kwargs):
    """
    Get the user groups from the JupyterHub API
    """
    token = get_service_token()
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
    argparser = argparse.ArgumentParser(description="User groups exporter")
    argparser.add_argument(
        "--port",
        default=9090,
        type=int,
        help="Port to listen on",
    )
    argparser.add_argument(
        "--interval",
        default=60,
        type=float,
        help="Interval to update user groups (minutes)",
    )
    args = argparser.parse_args()

    hub_url = "http://127.0.0.1:8000"

    start_http_server(args.port)

    loop = IOLoop.current()
    callback =  partial(get_user_groups, hub_url)
    # Set up immediate one-off callback to get user groups
    loop.add_callback(callback)
    # Set up a periodic callback to update the user groups
    pc = PeriodicCallback(callback, args.interval * 60 * 1000)  # convert to milliseconds
    pc.start()
    try:
        loop.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
