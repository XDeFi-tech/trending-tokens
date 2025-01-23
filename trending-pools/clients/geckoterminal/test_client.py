import pytest

from .client import GeckoterminalClient


@pytest.fixture
def gecko_client() -> GeckoterminalClient:
    return GeckoterminalClient()


@pytest.mark.asyncio
# To run tests comment the line below
# @pytest.mark.skip(reason="makes actual http calls.")
async def test_get_trending_pools(gecko_client: GeckoterminalClient):
    page_1 = await gecko_client.get_trending_pools(page=1)
    assert page_1.get("data")
    assert len(page_1.get("data")) == 20


@pytest.mark.asyncio
# To run tests comment the line below
# @pytest.mark.skip(reason="makes actual http calls.")
async def test_get_token(gecko_client: GeckoterminalClient):
    vine_on_solana = await gecko_client.get_token(
        network="solana", address="6AJcP7wuLwmRYLBNbi825wgguaPsWzPBEHcHndpRpump"
    )
    assert vine_on_solana.get("data")
    assert (
        vine_on_solana.get("data").get("id")
        == "solana_6AJcP7wuLwmRYLBNbi825wgguaPsWzPBEHcHndpRpump"
    )
