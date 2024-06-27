import os

BASE_URL = "https://api.geckoterminal.com/api/v2"

TRENDING_POOLS_URL = "/networks/trending_pools?page={page}"

TOKEN_URL = "/networks/{network}/tokens/{address}"

supported_chains = [
    "solana",
    "eth",
    "bsc",
    "avax",
    "optimism",
    "polygon_pos",
    "cro",
    "ftm",
    "aurora",
    "arbitrum",
    "xdai",
    "klaytn",
    "canto",
]

ASSETS_PATH = os.path.dirname(__file__) + "/assets.json"

LIQUIDITY_THRESHOLD = 4e4

VOLUME_THRESHOLD = 1.5e4

FILE_LOGS = os.getenv("FILE_LOGS", 0)

# Assets, if trending, to exclude from list of shitcoins
POPULAR_QUOTE_ASSETS = {
    "ETH.WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "ARBITRUM.WETH": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    "SOL.USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "ETH.ETH": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "ARBITRUM.USDC": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
    "SOL.SOL": "So11111111111111111111111111111111111111112",
}
