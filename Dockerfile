FROM ubuntu:24.04 AS base

RUN apt-get update > /dev/null && \
    apt-get install --yes python3 python3-pip python3-venv > /dev/null && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . /opt/jupyterhub_groups_exporter

WORKDIR /opt/jupyterhub_groups_exporter

RUN pip install -e .

FROM base AS dev

RUN pip install  -e ".[test]"

CMD ["python", "-m", "jupyterhub_groups_exporter.groups_exporter", "--update_exporter_interval", "10"]

FROM base AS prod

CMD ["python", "-m", "jupyterhub_groups_exporter.groups_exporter", "--update_exporter_interval", "3600"]

