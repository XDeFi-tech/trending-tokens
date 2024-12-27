import os
from datetime import datetime, timedelta

BASE_URL = "https://public-api.dextools.io/standard/v2"

TRENDING_POOLS_URL = "/pool/{chain}/pools/trending"

TOKEN_URL = "/token/{chain}"

supported_chains = [
    "solana",
    "ether",
    "bsc",
    "avalanche",
    "optimism",
    "polygon",
    "arbitrum",
]

ASSETS_PATH = os.path.dirname(__file__) + "/assets.json"

LIQUIDITY_THRESHOLD = 2e4

VOLUME_THRESHOLD = 1e4

FILE_LOGS = os.getenv("FILE_LOGS", 0)

# Assets, if trending, to exclude from list of shitcoins
POPULAR_QUOTE_ASSETS = {
    "ETH.WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "ARBITRUM.WETH": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    "SOL.USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "ETH.ETH": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "ARBITRUM.USDC": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
    "SOL.SOL": "So11111111111111111111111111111111111111112",
    "ETH.USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "BSC.USDT": "0x55d398326f99059ff775485246999027b3197955",
}

EXCLUSION_LIST = list(POPULAR_QUOTE_ASSETS.values())

# Get from time and current time
two_hours_ago = datetime.now() - timedelta(hours=1)
FROM_TIME: str = two_hours_ago.strftime("%Y-%m-%d %H:%M:%S")

now = datetime.now()
TO_TIME: str = now.strftime("%Y-%m-%d %H:%M:%S")