"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import time
import os
import json
import logging

from pathlib import Path
from prometheus_client import Gauge, start_http_server
from tornado.httpclient import HTTPClient


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


def api_request(hub_url, path, token=None, parse_json=True, **kwargs):
    """Make an API request to the Hub, parsing JSON responses"""
    hub_url = hub_url.rstrip("/")
    headers = kwargs.setdefault("headers", {})
    headers["Authorization"] = f"token {token}"

    path = path.lstrip("/")
    url = f"{hub_url}/hub/api/{path}"
    logger.info(f"api_request: {url}, {kwargs}")
    # resp = await AsyncHTTPClient().fetch(url, **kwargs)
    resp = HTTPClient().fetch(url, **kwargs)
    if not parse_json:
        return resp
    if resp.body:
        return json.loads(resp.body.decode("utf8"))
    else:
        return None


def get_user_groups(hub_url, **kwargs):
    """
    Get the user groups from the JupyterHub API
    """
    time.sleep(15)  # wait for JupyterHub to proxy routes on startup
    token = get_service_token()
    response = api_request(
        hub_url,
        path="groups",
        token=token,
    )
    return response


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
    while True:
        response = get_user_groups(hub_url)
        USER_GROUP.clear()  # Clear previous metrics
        for group in response:
            for user in group["users"]:
                USER_GROUP.labels(user_group=f"{group['name']}", user=f"{user}").set(1)
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
