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
from yarl import URL


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
)

async def update_user_group_info(session: aiohttp.ClientSession, headers: dict, hub_url: str, USER_GROUP: Gauge):
    """
    Update the prometheus exporter with user group memberships from the JupyterHub API.
    """
    url = URL(f"{hub_url}").with_path("hub/api/groups")

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            try:
                data = await response.json()
                USER_GROUP.clear()  # Clear previous prometheus metrics
                for group in data:
                    for user in group["users"]:
                        USER_GROUP.labels(usergroup=f"{group['name']}", username=f"{user}").set(1)
                logger.info(f"Updated user group info from {url}.")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
        else:
            logger.error(f"Failed to fetch user group info from {url}. Status code: {response.status}")


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
        default=f"http://{os.environ.get('HUB_SERVICE_HOST')}:{os.environ.get('HUB_SERVICE_PORT')}",
        type=str,
        help="JupyterHub service URL, e.g. http://localhost:8000 for local development.",
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
    'JupyterHub username and user group membership information.',
    ['username', 'usergroup'],
    namespace=args.jupyterhub_metrics_prefix,
    )

    start_http_server(args.port)
    logger.info(f"Starting JupyterHub user groups Prometheus exporter on port {args.port} with an update interval of {args.update_exporter_interval} seconds.")

    headers = {"Authorization": f"token {args.api_token}"}
    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession() as session:
        while True:
            await update_user_group_info(session, headers, args.hub_url, USER_GROUP)
            await asyncio.sleep(args.update_exporter_interval)


if __name__ == "__main__":
    asyncio.run(main())
