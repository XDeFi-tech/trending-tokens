import pytest

from .client import DexToolsClient


@pytest.fixture
def dextools_client() -> DexToolsClient:
    return DexToolsClient()


@pytest.mark.asyncio
# To run tests comment the line below
@pytest.mark.skip(reason="makes actual http calls.")
async def test_get_solana_pools(dextools_client: DexToolsClient):
    page_0 = await dextools_client.get_pools(chain="solana", page=0, page_size=50)
    assert page_0.get("statusCode") == 200
    assert page_0.get("data")
    assert page_0.get("data").get("page") == 0
    assert page_0.get("data").get("pageSize") == 50
    assert page_0.get("data").get("totalPages")
    assert page_0.get("data").get("results")
    assert len(page_0.get("data").get("results")) <= 50


@pytest.mark.asyncio
# To run tests comment the line below
@pytest.mark.skip(reason="makes actual http calls.")
async def test_get_pools_liquidity(dextools_client: DexToolsClient):
    res = await dextools_client.get_pools_liquidity(
        address="CCeZrfzcpf27VjDnVphDURV8dNqogbkihP9F5MTrMQCU", chain="solana"
    )
    pass

@pytest.mark.asyncio
# To run tests comment the line below
@pytest.mark.skip(reason="makes actual http calls.")
async def test_get_liquidity_pool_price_info(dextools_client: DexToolsClient):
    res = await dextools_client.get_liquidity_pool_price_info(
        address="CCeZrfzcpf27VjDnVphDURV8dNqogbkihP9F5MTrMQCU", chain="solana"
    )
    pass