from clients.geckoterminal.client import GeckoterminalClient
from clients.dextools.client import DexToolsClient

gecko_client = GeckoterminalClient()
dextools_client = DexToolsClient()


async def get_processed_pools():
    gecko_client_pools = await gecko_client.fetch_pools()
    await gecko_client.process_pools(gecko_client_pools)

    # dextools_chain = "solana"
    # dextools_client_pools = await dextools_client.get_all_pools(chain=dextools_chain)
    # await dextools_client.process_pools(dextools_client_pools, chain=dextools_chain)