import logging

logger = logging.getLogger(__name__)


async def test_hub_alive(hub_url, hub, admin_request):
    """Test that the hub is alive and responding to requests."""
    response = await admin_request("/info")
    logger.info(f"test_hub_alive: {response}")
    assert response["version"] is not None