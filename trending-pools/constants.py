import os

BASE_URL = "https://api.geckoterminal.com/api/v2"

TRENDING_POOLS_URL = "/networks/trending_pools?page={page}"

TOKEN_URL = "/networks/{network}/tokens/{address}"

supported_chains = ["solana", "eth", "bsc", "avax", "optimism", "polygon_pos", "cro", "ftm", "aurora", "arbitrum", "xdai", "klaytn", "canto"]

ASSETS_PATH = os.path.dirname(__file__) + "/assets.json"

LIQUIDITY_THRESHOLD = 4e4

VOLUME_THRESHOLD = 1.5e4

FILE_LOGS = os.getenv("FILE_LOGS", 0)
