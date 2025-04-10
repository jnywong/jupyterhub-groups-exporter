import pathlib
import secrets
import sys
import os

c = get_config()  # noqa

n_users = 5
c.Authenticator.allowed_users = {f"test-{i}" for i in range(n_users)}
c.JupyterHub.load_groups = {
    'group-0': {
        'users': list(c.Authenticator.allowed_users),
    },
}

c.Authenticator.admin_users = {'admin'}
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"

c.JupyterHub.last_activity_interval = 3
c.JupyterHub.ip = '127.0.0.1'
c.JupyterHub.hub_ip = '127.0.0.1'
c.JupyterHub.port = 8000
c.JupyterHub.cleanup_proxy = True
c.JupyterHub.cleanup_servers = True

c.JupyterHub.load_roles = [
    {
        "name": "pytest",
        "scopes": [
            "servers",
            "admin:users",
            "read:hub",
        ],
        "services": ["pytest"],
    },
    {
        "name": "groups-exporter",
        "scopes": [
            "users",
            "groups",
        ],
        "services": ["groups-exporter"],
    },
]

service_port = 9090
service_interval = 1  # minutes
c.JupyterHub.services = [
    {
        "name": "pytest",
        "api_token": os.environ["TEST_ADMIN_TOKEN"],
    },
    {
        "name": "groups-exporter",
        # "api_token": os.environ["TEST_GROUPS_TOKEN"],
        "url": f"http://{c.JupyterHub.ip}:{service_port}",
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_groups_exporter.groups_exporter",
            "--port",
            f"{service_port}",
            "--interval",
            f"{service_interval}",
        ],
    },
]
