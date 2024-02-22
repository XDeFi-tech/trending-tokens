from typing import NamedTuple
import json
import time
from decimal import Decimal
import aiohttp
import asyncio
import json
import logging

log = logging.getLogger("trending-tokens")

global_assets = []
global_ids = []

async def get_request(url, nbRetry=1, headers = None, debug=False):
    if nbRetry == 0:
        raise Exception(
            f"get_request Max retry in request exceeded for {url}"
        )
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            loop = asyncio.get_event_loop()
            start_time = loop.time()
            async with session.get(url, ssl=False) as resp:
                if debug:
                    log.warning(f"Response status for {url}: {resp.status}, time elapsed: {loop.time() - start_time}")
                if resp.status > 299:
                    log.warning(f"GET request failed for {url} with status code: {resp.status}. Response text: {await resp.text(encoding='utf-8')}")
                return await resp.json(content_type=resp.content_type)
    except json.JSONDecodeError as e:
        log.error(e)
        raise e
    except Exception as e:
        log.warning(f"Retry request..., error : {e}")
        await get_request(url, nbRetry - 1)

class AssetInfo(NamedTuple):
    id: str
    chain: str
    address: str
    decimals: int
    symbol: str
    liquidity: str
    volume24: str

BASE_URL = "https://api.geckoterminal.com/api/v2"

TRENDING_POOLS = "/networks/trending_pools?page={page}"

TOKEN = "/networks/{network}/tokens/{address}"

supported_chains = ["solana", "eth", "bsc", "avax"]

def find_asset_info(token_id):
    for token in global_assets:
        if token["id"] == token_id:
            return token

async def parse_pool(p):
    base_token_id = None
    try:
        if Decimal(p["attributes"]["reserve_in_usd"]) < Decimal(1e5):
            log.error(f"Not including pool {p['attributes']['name']}. Not enough liquidity.")
            return
        base_token_id = p["relationships"]["base_token"]["data"]["id"]
        chain, address = base_token_id.split("_")
        if chain not in supported_chains:
            log.warning(f"Not including pool {p['attributes']['name']}. Chain {chain} not supported.")
            return
        if address == "So11111111111111111111111111111111111111112":
            base_token_id = p["relationships"]["quote_token"]["data"]["id"]
        if base_token_id in global_ids:
            # Update volume and liquidity
            shitcoin = find_asset_info(base_token_id)
            shitcoin["liquidity"] = p["attributes"]["reserve_in_usd"]
            shitcoin["volume24"] = p["attributes"]["volume_usd"]["h24"]
            if Decimal(shitcoin["volume24"]) < Decimal(1e4):
                return
            return shitcoin
        chain, address = base_token_id.split("_")
        asset_details = (await get_request(BASE_URL + TOKEN.format(network=chain, address=address)))["data"]
        return AssetInfo(
            id=base_token_id, 
            chain=chain, 
            address=address, 
            decimals=asset_details["attributes"]["decimals"], 
            symbol=asset_details["attributes"]["symbol"],
            liquidity=p["attributes"]["reserve_in_usd"],
            volume24=p["attributes"]["volume_usd"]["h24"],
        )._asdict()
    except Exception as e:
        log.error(f"error: {e}, id: {base_token_id}")

async def process_pools(pools):
    return await asyncio.gather(*[parse_pool(p) for p in pools])

async def run_async():
    tic = time.time()
    i = 1
    res = (await get_request(BASE_URL + TRENDING_POOLS.format(page=i)))["data"]
    assets = await process_pools(res)
    # while len(res) > 0 and i < 2:
    #     i += 1
    #     print(i)
    #     res = (await get_request(BASE_URL + TRENDING_POOLS.format(page=i)))["data"]
    #     assets += await process_pools(res)
    assets = list(filter(lambda x: x is not None, assets))
    log.warning(f"Assets length: {len(assets)}")
    if len(assets) > 0:
        with open("assets.json", "w") as outfile:
            json.dump(assets, outfile)
    toc = time.time()
    log.warning(f"Fetching trending assets took: {toc-tic}s")

def load_existing_tokens():
    with open("assets.json") as json_file:
        try:
            tmp_assets = json.load(json_file)
            return list(map(lambda x: x["id"], tmp_assets)), tmp_assets
        except: 
            return [], []

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    # global_ids, global_assets = load_existing_tokens()
    loop.run_until_complete(run_async())
