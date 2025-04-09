import os
import json
import inspect
import asyncio
import secrets
import shutil
import time
import psutil
import pytest
import logging

from pathlib import Path
from unittest import mock
from functools import partial
from tempfile import TemporaryDirectory
from subprocess import Popen
from tornado.httpclient import AsyncHTTPClient, HTTPClient

logger = logging.getLogger(__name__)


def pytest_collection_modifyitems(items):
    """This function is automatically run by pytest passing all collected test
    functions.

    We use it to add asyncio marker to all async tests and assert we don't use
    test functions that are async generators which wouldn't make sense.
    """
    for item in items:
        if inspect.iscoroutinefunction(item.obj):
            item.add_marker("asyncio")
        assert not inspect.isasyncgenfunction(item.obj)


@pytest.fixture(scope="session")
def admin_token():
    """Generate a token to use for admin requests"""
    token = secrets.token_hex(16)
    # jupyterhub subprocess loads this from the environment
    with mock.patch.dict(os.environ, {"TEST_ADMIN_TOKEN": token}):
        yield token


@pytest.fixture(scope="session")
def groups_token():
    """Generate a token to use for groups exporter service requests"""
    token = secrets.token_hex(16)
    # jupyterhub subprocess loads this from the environment
    with mock.patch.dict(os.environ, {"TEST_GROUPS_TOKEN": token}):
        yield token


@pytest.fixture(scope="session")
def hub_url():
    # hardcoded for now, but might want to override
    return "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def hub(hub_url, request, admin_token):
    """Start JupyterHub, set up to use our tokens"""
    jupyterhub_config = Path.cwd().joinpath("tests/jupyterhub_config.py")
    with TemporaryDirectory() as td:
        shutil.copy(jupyterhub_config, Path(td).joinpath("jupyterhub_config.py"))
        hub = Popen(["jupyterhub", "--debug"], cwd=td)

        def cleanup():
            if hub.poll() is None:
                try:
                    for p in psutil.Process(hub.pid).children():
                        logger.info(f"terminating {p}")
                        p.terminate()
                except psutil.ProcessLookupError:
                    pass
            logger.info("terminating hub")
            hub.terminate()

        request.addfinalizer(cleanup)

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                HTTPClient().fetch(hub_url + "/hub/api")
            except Exception as e:
                logger.info(f"hub: {e}")
                if hub.poll() is not None:
                    raise RuntimeError("hub failed to start")
                time.sleep(1)
                continue
            else:
                break

        yield hub


async def api_request(hub_url, path, token=None, parse_json=True, **kwargs):
    """Make an API request to the Hub, parsing JSON responses"""
    hub_url = hub_url.rstrip("/")
    headers = kwargs.setdefault("headers", {})
    headers["Authorization"] = f"token {token}"

    path = path.lstrip("/")
    url = f"{hub_url}/hub/api/{path}"
    logger.info(f"api_request: {url}, {kwargs}")
    resp = await AsyncHTTPClient().fetch(url, **kwargs)
    if not parse_json:
        return resp
    if resp.body:
        return json.loads(resp.body.decode("utf8"))
    else:
        return None


@pytest.fixture
def admin_request(hub, hub_url, admin_token):
    """make an API request to a path with an admin token"""
    return partial(api_request, hub_url, token=admin_token)
