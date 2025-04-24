"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import asyncio
import logging
import os

import aiohttp
import backoff
from prometheus_client import Gauge, start_http_server
from yarl import URL

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M",
)


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=8, logger=logger)
async def update_user_group_info(
    session: aiohttp.ClientSession, hub_url: URL, USER_GROUP: Gauge
):
    """
    Update the prometheus exporter with user group memberships from the JupyterHub API.
    """
    url = hub_url / "hub/api/groups"

    async with session.get(url) as response:
        data = await response.json()
        USER_GROUP.clear()  # Clear previous prometheus metrics
        for group in data:
            for user in group["users"]:
                USER_GROUP.labels(usergroup=f"{group['name']}", username=f"{user}").set(
                    1
                )
        logger.info(f"Updated user_group_info with data from API call to {url}.")


async def main():
    argparser = argparse.ArgumentParser(
        description="JupyterHub user groups exporter for Prometheus."
    )
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
        default="http://localhost:8000",
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
        "user_group_info",
        "JupyterHub username and user group membership information.",
        ["username", "usergroup"],
        namespace=args.jupyterhub_metrics_prefix,
    )

    start_http_server(args.port)
    logger.info(
        f"Starting JupyterHub user groups Prometheus exporter on port {args.port} with an update interval of {args.update_exporter_interval} seconds."
    )

    hub_url = URL(args.hub_url)
    headers = {"Authorization": f"token {args.api_token}"}

    asyncio.get_event_loop()
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            await update_user_group_info(session, hub_url, USER_GROUP)
            await asyncio.sleep(args.update_exporter_interval)


if __name__ == "__main__":
    asyncio.run(main())
