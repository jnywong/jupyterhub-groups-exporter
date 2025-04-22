FROM ubuntu:24.04

RUN apt-get update > /dev/null && \
    apt-get install --yes python3 python3-pip python3-venv tini > /dev/null && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY pyproject.toml /opt/jupyterhub_groups_exporter
COPY jupyterhub_groups_exporter /opt/jupyterhub_groups_exporter/jupyterhub_groups_exporter

WORKDIR /opt/jupyterhub_groups_exporter

RUN pip install -e .
RUN pip install  -e ".[test]"

ENTRYPOINT ["tini", "--"]
