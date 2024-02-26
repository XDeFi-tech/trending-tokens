from decimal import Decimal
import asyncio
from asset import AssetInfo
import logging
from typing import Dict, Optional
from constants import supported_chains, BASE_URL, TOKEN_URL, TRENDING_POOLS_URL, ASSETS_PATH, LIQUIDITY_THRESHOLD, VOLUME_THRESHOLD, FILE_LOGS
from helpers import get_request, load_existing_tokens, write_json, parse_token_id

log = logging.getLogger(__name__)
if FILE_LOGS:
    log.addHandler(logging.FileHandler("output.log"))

def find_asset_info(token_id, global_assets):
    for token in global_assets:
        if token["id"] == token_id:
            return token

async def parse_pool(p: Dict) -> Optional[Dict]:
    base_token_id = None
    try:
        if Decimal(p["attributes"]["reserve_in_usd"]) < Decimal(LIQUIDITY_THRESHOLD):
            log.error(f"Not including pool {p['attributes']['name']}. Not enough liquidity.")
            return
        base_token_id = p["relationships"]["base_token"]["data"]["id"]
        chain, address = parse_token_id(base_token_id)
        if address == "So11111111111111111111111111111111111111112":
            base_token_id = p["relationships"]["quote_token"]["data"]["id"]
            chain, address = parse_token_id(base_token_id)
        if chain not in supported_chains:
            log.warning(f"Not including pool {p['attributes']['name']}. Chain {chain} not supported.")
            return
        existing_ids, existing_assets = load_existing_tokens()
        if base_token_id in existing_ids:
            # Update volume and liquidity
            shitcoin = find_asset_info(base_token_id, existing_assets)
            log.warning(f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} found!")
            shitcoin["liquidity"] = p["attributes"]["reserve_in_usd"]
            shitcoin["volume24"] = p["attributes"]["volume_usd"]["h24"]
            # If the last 24h volume is below VOLUME_THRESHOLD then omit
            if Decimal(shitcoin["volume24"]) < Decimal(VOLUME_THRESHOLD):
                log.warning(f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} removed because of low volume.")
                return
            return shitcoin
        # New trending token
        asset_details = (await get_request(BASE_URL + TOKEN_URL.format(network=chain, address=address), debug=True))["data"]
        log.warning(f"Adding new asset {chain}.{asset_details['attributes']['symbol']}-{address}.")
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

async def fetch_pools(start=1, finish=None):
    i = start
    pools = []
    res = (await get_request(BASE_URL + TRENDING_POOLS_URL.format(page=i), debug=True))["data"]
    pools += res
    while len(res) > 0 and (i < finish if finish else True):
        i += 1
        try:
            res = (await get_request(BASE_URL + TRENDING_POOLS_URL.format(page=i), debug=True))["data"]
            pools += res
        except Exception as e:
            log.warning(f"Error in getting pools for page={i}, {e}")
            res = []
    print(f"len(pools)={len(pools)}")
    assets = await process_pools(pools)
    assets = list(filter(lambda x: x is not None, assets))
    log.warning(f"Assets length: {len(assets)}")
    if len(assets) > 0:
        write_json(ASSETS_PATH, assets)
