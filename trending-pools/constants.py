import os

BASE_URL = "https://api.geckoterminal.com/api/v2"

TRENDING_POOLS_URL = "/networks/trending_pools?page={page}"

TOKEN_URL = "/networks/{network}/tokens/{address}"

supported_chains = ["solana", "eth", "bsc", "avax"]

ASSETS_PATH = os.path.dirname(__file__) + "/assets.json"
