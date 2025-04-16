"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import os
import json
import logging
import asyncio
import aiohttp

from prometheus_client import Gauge, start_http_server

logger = logging.getLogger(__name__)


async def update_user_group_info(session, headers, hub_url, USER_GROUP):
    """
    Get the user groups from the JupyterHub API
    """
    path = "groups"
    url = f"{hub_url}/hub/api/{path}"

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            try:
                data = await response.json()
                logger.info(f"api_response: {data}")
                USER_GROUP.clear()  # Clear previous metrics
                for group in data:
                    for user in group["users"]:
                        USER_GROUP.labels(usergroup=f"{group['name']}", username=f"{user}").set(1)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
        else:
            logger.error(f"Failed to fetch user group info from JupyterHub API. Status code: {response.status}")


async def main():
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
        help="Prefix/namespace for the JupyterHub metrics for Prometheus.",
    )

    args = argparser.parse_args()

    USER_GROUP = Gauge(
    'user_group_info',
    'Username and user group membership information.',
    ['username', 'usergroup'],
    namespace=args.jupyterhub_metrics_prefix,
    )

    start_http_server(args.port)

    headers = {"Authorization": f"token {args.api_token}"}
    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession() as session:
        while True:
            response = await update_user_group_info(session, headers, args.hub_url, USER_GROUP)
            await asyncio.sleep(args.update_exporter_interval)


if __name__ == "__main__":
    asyncio.run(main())
