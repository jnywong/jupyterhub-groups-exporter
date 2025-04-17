import logging

logger = logging.getLogger(__name__)


async def test_hub_alive(admin_request):
    """Test that the hub is alive and responding to requests."""
    try:
        response = await admin_request(path="hub/api/info")
    except Exception as e:
        raise RuntimeError("Hub is not alive")
    assert response["version"] is not None


async def test_groups_exporter_alive(admin_request):
    """Test that the hub is alive and responding to requests."""
    try:
        response = await admin_request(path="services/groups-exporter", parse_json=False)
    except Exception as e:
        logger.info(f"test_groups_exporter_alive: {e}")
        raise RuntimeError("JupyterHub groups exporter service is not alive")
    assert response is not None