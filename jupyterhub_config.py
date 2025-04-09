import pathlib
import secrets
import sys
import os

c = get_config()  # noqa

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
        "name": "groups-exporter",
        "scopes": [
            "users",
            "groups",
        ],
        "services": ["groups-exporter"],
    },
]

here = pathlib.Path(__file__).parent
token_file = here.joinpath("service-token")
if token_file.exists():
    with token_file.open("r") as f:
        token = f.read()
else:
    token = secrets.token_hex(16)
    with token_file.open("w") as f:
        f.write(token)

service_port = 9090
service_interval = 1  # minutes
c.JupyterHub.services = [
    {
        "name": "groups-exporter",
        "api_token": token,
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
