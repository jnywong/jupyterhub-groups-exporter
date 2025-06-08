# jupyterhub-groups-exporter

An externally-managed JupyterHub service to export user group memberships to Prometheus.

## Overview

The `jupyterhub-groups-exporter` project provides a service that integrates with [Zero to JupyterHub documentation](https://z2jh.jupyter.org) to export user group memberships as Prometheus metrics. This enables JupyterHub administrators to monitor usage and costs segmented by user groups using visualization tools like Grafana.

## Features

- Exports user group memberships from JupyterHub to Prometheus.
- Supports integration with Kubernetes clusters via Helm charts.

## Installation

This repository provides packaged Helm charts for the `jupyterhub-groups-exporter` project. These charts are hosted in the [`gh-pages` branch](https://github.com/2i2c-org/jupyterhub-groups-exporter/tree/gh-pages) and made available as a Helm chart repository.

### Prerequisites

- Kubernetes cluster
- Helm installed ([Helm documentation](https://helm.sh/docs/intro/install/))

### Steps

1. Add the Helm chart repository:

   ```shell
   helm repo add jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter
   helm repo update
   ```

2. Install the Helm chart:

   ```shell
   helm install jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter --version <version>
   ```

## Usage

Once installed, the `jupyterhub-groups-exporter` service will interact with the JupyterHub API to retrieve user group memberships and expose them as Prometheus metrics. These metrics can then be queried with PromQL and visualized in Grafana dashboards.

### Configuration

The exporter supports the following argument options:

- `--port`: Port to listen on for the groups exporter. Default is `9090`.
- `--update_exporter_interval`: Time interval (in seconds) between each update of the JupyterHub groups exporter. Default is `3600`.
- `--allowed_groups`: List of allowed user groups to be exported. If not provided, all groups will be exported.
- `--default_group`: Default group to account usage against for users with multiple group memberships. Default is `"other"`.
- `--hub_url`: JupyterHub service URL, e.g., `http://localhost:8000` for local development. Default is constructed using environment variables `HUB_SERVICE_HOST` and `HUB_SERVICE_PORT`.
- `--api_token`: Token to authenticate with the JupyterHub API. Default is fetched from the environment variable `JUPYTERHUB_API_TOKEN`.
- `--jupyterhub_namespace`: Kubernetes namespace where the JupyterHub is deployed. Default is fetched from the environment variable `NAMESPACE`.
- `--jupyterhub_metrics_prefix`: Prefix/namespace for the JupyterHub metrics for Prometheus. Default is `"jupyterhub"`.
- `--log_level`: Logging level for the exporter service. Options are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Default is `"INFO"`.

## Contributing

Contributions to the `jupyterhub-groups-exporter` project are welcome! Please follow the standard GitHub workflow:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

## License

This project is licensed under the [BSD 3-Clause License](LICENSE).

## Resources

- [Helm Chart Repository](https://2i2c.org/jupyterhub-groups-exporter/)
- [Zero to JupyterHub Documentation](https://z2jh.jupyter.org)
