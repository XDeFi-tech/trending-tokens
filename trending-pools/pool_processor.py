from decimal import Decimal
import asyncio
from asset import AssetInfo
from typing import Any, Dict, Optional, List
from constants import (
    supported_chains,
    BASE_URL,
    TOKEN_URL,
    TRENDING_POOLS_URL,
    ASSETS_PATH,
    LIQUIDITY_THRESHOLD,
    VOLUME_THRESHOLD,
    EXCLUSION_LIST,
    FROM_TIME,
    TO_TIME
)
from helpers import get_request, load_existing_tokens, write_json, parse_token_id, log


def find_asset_info(token_id, global_assets):
    for token in global_assets:
        if token["id"] == token_id:
            return token


async def parse_pool(p: Dict) -> Optional[Dict]:
    # Token request params
    params: Dict[str, Any] = {
        "sort": "creationTime",
        "order": "desc",
        "from": FROM_TIME,
        "to": TO_TIME,
        "page": 1,
        "pageSize": 50,
        "totalPages": 5,
    }
    base_token_id = None
    try:
        if Decimal(p["attributes"]["reserve_in_usd"]) < Decimal(LIQUIDITY_THRESHOLD):
            log.error(
                f"Not including pool {p['attributes']['name']}. Not enough liquidity."
            )
            return
        base_token_id = p["relationships"]["base_token"]["data"]["id"]
        chain, address = parse_token_id(base_token_id)
        if address in EXCLUSION_LIST:
            base_token_id = p["relationships"]["quote_token"]["data"]["id"]
            chain, address = parse_token_id(base_token_id)
            if address in EXCLUSION_LIST:
                return
        if chain not in supported_chains:
            log.warning(
                f"Not including pool {p['attributes']['name']}. Chain {chain} not supported."
            )
            return
        existing_ids, existing_assets = load_existing_tokens()
        if base_token_id in existing_ids:
            # Update volume and liquidity
            shitcoin = find_asset_info(base_token_id, existing_assets)
            log.warning(
                f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} found!"
            )
            shitcoin["liquidity"] = p["attributes"]["reserve_in_usd"]
            shitcoin["volume24"] = p["attributes"]["volume_usd"]["h24"]
            # If the last 24h volume is below VOLUME_THRESHOLD then omit
            if Decimal(shitcoin["volume24"]) < Decimal(VOLUME_THRESHOLD):
                log.warning(
                    f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} removed because of low volume."
                )
                return
            return shitcoin
        # New trending token
        asset_details = (
            await get_request(
                BASE_URL + TOKEN_URL.format(network=chain, address=address), params=params
            )
        )["data"]
        log.warning(
            f"Adding new asset {chain}.{asset_details['attributes']['symbol']}-{address}."
        )
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
    assets = await asyncio.gather(*[parse_pool(p) for p in pools])
    assets = list(filter(lambda x: x is not None, assets))
    log.warning(f"Number of assets loaded: {len(assets)}")
    current_ids, _ = load_existing_tokens()
    new_assets_ids = set(map(lambda x: x["id"], assets))
    ids_to_check = list(set(current_ids) - new_assets_ids)
    log.warning(f"Number of old assets to verify: {len(ids_to_check)}")
    if len(ids_to_check) > 0:
        assets += await process_assets_left(ids_to_check)
    if len(assets) > 0:
        write_json(ASSETS_PATH, assets)


async def process_assets_left(assets_ids: List[str]) -> List[Dict]:
    _, existing_assets = load_existing_tokens()
    updated_assets = []
    updated_ids = []
    for id in assets_ids:
        try:
            chain, address = parse_token_id(id)
            if address in EXCLUSION_LIST:
                continue
            asset_details = (
                await get_request(
                    BASE_URL + TOKEN_URL.format(network=chain, address=address)
                )
            )["data"]
            shitcoin = find_asset_info(id, existing_assets)
            shitcoin["liquidity"] = asset_details["attributes"]["total_reserve_in_usd"]
            shitcoin["volume24"] = asset_details["attributes"]["volume_usd"]["h24"]
            # If the last 24h volume is below VOLUME_THRESHOLD then omit
            if Decimal(shitcoin["volume24"]) < Decimal(VOLUME_THRESHOLD):
                log.warning(
                    f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} removed because of low volume."
                )
                continue
            if shitcoin["id"] not in updated_ids:
                updated_assets.append(shitcoin)
                updated_ids.append(shitcoin["id"])
        except Exception as e:
            log.warning(f"error in process_assets_left: {e}, id: {id}")
    log.warning(
        f"Number of assets left that were updated and need to be added: {len(updated_assets)}"
    )
    return updated_assets


async def fetch_pools(start=1, finish=None):
    i = start
    pools = []

    while (
        (
            resp := (
                await get_request(
                    BASE_URL + TRENDING_POOLS_URL.format(page=i), debug=True
                )
            )
        )
        and (res := resp.get("data", []))
        and len(res) > 0
        and (i < finish if finish else True)
    ):
        i += 1
        pools += res
    return pools


async def get_processed_pools():
    pools = await fetch_pools()
    await process_pools(pools)
