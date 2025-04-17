import aiohttp
import inspect
import json
import logging
import os
import psutil
import pytest
import secrets
import shutil
import signal
import time

from pathlib import Path
from unittest import mock
from functools import partial
from tempfile import TemporaryDirectory
from subprocess import Popen
from yarl import URL

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
def hub_url():
    # hardcoded for now, but might want to override
    return "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
async def hub(hub_url, request, admin_token):
    """Start JupyterHub, set up to use admin and service tokens"""
    jupyterhub_config = Path.cwd().joinpath("tests/jupyterhub_config.py")
    with TemporaryDirectory() as td:
        shutil.copy(jupyterhub_config, Path(td).joinpath("jupyterhub_config.py"))
        hub = Popen(["jupyterhub", "--debug"], cwd=td)

        def cleanup():
            if hub.poll() is None:
                try:
                    kill_proc_tree(hub.pid)
                except psutil.ProcessLookupError:
                    pass
            logger.info("terminating hub")
            hub.terminate()

        request.addfinalizer(cleanup)

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                await api_request(hub_url=hub_url, path="hub/api/info", token=admin_token)
                logger.info("hub started")
            except Exception as e:
                logger.info(f"hub: {e}")
                if hub.poll() is not None:
                    raise RuntimeError("hub failed to start")
                time.sleep(1)
                continue
            else:
                break

        yield hub


async def api_request(hub_url:str, path:str, token:str=None, parse_json:bool=True):
    """Make an API request to the Hub, parsing JSON responses"""
    headers = {"Authorization": f"token {token}"}
    hub_url = URL(hub_url)
    url = hub_url.with_path(f"{path}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                try:
                    if parse_json:
                        return await resp.json()
                    else:
                        return await resp.text()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON response: {e}")
                    raise


@pytest.fixture
def admin_request(hub, hub_url, admin_token):
    """make an API request to a path with an admin token"""
    return partial(api_request, hub_url, token=admin_token)


def kill_proc_tree(pid, sig=signal.SIGKILL, include_parent=True,
                   timeout=None, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callback function which is
    called as soon as a child terminates.
    """
    assert pid != os.getpid(), "won't kill myself"
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        try:
            p.send_signal(sig)
            logger.info(f"terminating {p}")
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    logger.info(f"{len(gone)} processes killed, {len(alive)} still alive.")
