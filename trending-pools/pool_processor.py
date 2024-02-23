from decimal import Decimal
import asyncio
from asset import AssetInfo
import logging
from typing import Dict, Optional
from constants import supported_chains, BASE_URL, TOKEN_URL, TRENDING_POOLS_URL, ASSETS_PATH
from helpers import get_request, load_existing_tokens, write_json

log = logging.getLogger(__name__)

def find_asset_info(token_id, global_assets):
    for token in global_assets:
        if token["id"] == token_id:
            return token

async def parse_pool(p: Dict) -> Optional[Dict]:
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
        existing_ids, existing_assets = load_existing_tokens()
        if address == "So11111111111111111111111111111111111111112":
            base_token_id = p["relationships"]["quote_token"]["data"]["id"]
        if base_token_id in existing_ids:
            # Update volume and liquidity
            shitcoin = find_asset_info(base_token_id, existing_assets)
            log.warning(f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} found!")
            shitcoin["liquidity"] = p["attributes"]["reserve_in_usd"]
            shitcoin["volume24"] = p["attributes"]["volume_usd"]["h24"]
            if Decimal(shitcoin["volume24"]) < Decimal(1e4):
                log.warning(f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} removed because of low volume.")
                return
            return shitcoin
        chain, address = base_token_id.split("_")
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

async def fetch_pools(start=1, finish=2):
    i = start
    res = (await get_request(BASE_URL + TRENDING_POOLS_URL.format(page=i)))["data"]
    while len(res) > 0 and i < finish:
        i += 1
        res += (await get_request(BASE_URL + TRENDING_POOLS_URL.format(page=i)))["data"]

    assets = await process_pools(res)
    assets = list(filter(lambda x: x is not None, assets))
    log.warning(f"Assets length: {len(assets)}")
    if len(assets) > 0:
        write_json(ASSETS_PATH, assets)
