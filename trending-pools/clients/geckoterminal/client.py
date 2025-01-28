import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional

from constants import (
    ASSETS_PATH,
    EXCLUSION_LIST,
    LIQUIDITY_THRESHOLD,
    VOLUME_THRESHOLD,
    supported_chains,
)
from helpers import load_existing_tokens, log, parse_token_id, write_json
from models import AssetInfo

from ..base import BaseAsyncHttpClient


class GeckoterminalClient(BaseAsyncHttpClient):
    """
    Integrated gecko terminal token fetcher client
    """

    logger: logging.Logger
    _request_kwargs = None
    _api_key: str
    _base_url: str

    def __init__(self):
        self._base_url = "https://api.geckoterminal.com/api/v2"
        self.logger = logging.getLogger("GeckoterminalClient")
        self._client_name = "GeckoterminalClient"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_trending_pools(
        self, page: int, debug: bool = False, num_retries: int = 1
    ):
        url = self._base_url + f"/networks/trending_pools?page={page}"
        try:
            resp = await self._get(
                url=url, response_type="json", debug=debug, num_retries=num_retries
            )
            return resp
        except Exception as e:
            self.logger.warning(
                f"failed to fetch trending pools from {url} because of the error {e}"
            )
            raise e

    async def get_token(
        self, network, address, debug: bool = False, num_retries: int = 1
    ):
        url = self._base_url + f"/networks/{network}/tokens/{address}"
        try:
            resp = await self._get(
                url=url, response_type="json", debug=debug, num_retries=num_retries
            )
            return resp
        except Exception as e:
            self.logger.warning(
                f"failed to fetch trending pools from {url} because of the error {e}"
            )
            raise e

    def find_asset_info(self, token_id, global_assets):
        for token in global_assets:
            if token["id"] == token_id:
                return token

    async def parse_pool(self, p: Dict) -> Optional[Dict]:
        base_token_id = None
        try:
            if Decimal(p["attributes"]["reserve_in_usd"]) < Decimal(
                LIQUIDITY_THRESHOLD
            ):
                self.logger.error(
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
                shitcoin = self.find_asset_info(base_token_id, existing_assets)
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
                await self.get_token(network=chain, address=address, num_retries=3)
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

    async def process_pools(self, pools):
        assets = await asyncio.gather(*[self.parse_pool(p) for p in pools])
        assets = list(filter(lambda x: x is not None, assets))
        log.warning(f"Number of assets loaded: {len(assets)}")
        current_ids, _ = load_existing_tokens()
        new_assets_ids = set(map(lambda x: x["id"], assets))
        ids_to_check = list(set(current_ids) - new_assets_ids)
        log.warning(f"Number of old assets to verify: {len(ids_to_check)}")
        if len(ids_to_check) > 0:
            assets += await self.process_assets_left(ids_to_check)
        if len(assets) > 0:
            write_json(ASSETS_PATH, assets)

    async def process_assets_left(self, assets_ids: List[str]) -> List[Dict]:
        _, existing_assets = load_existing_tokens()
        updated_assets = []
        updated_ids = []
        for id in assets_ids:
            try:
                chain, address = parse_token_id(id)
                if address in EXCLUSION_LIST:
                    continue
                asset_details = (
                    await self.get_token(network=chain, address=address, num_retries=3)
                )["data"]
                shitcoin = self.find_asset_info(id, existing_assets)
                shitcoin["liquidity"] = asset_details["attributes"][
                    "total_reserve_in_usd"
                ]
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

    async def fetch_pools(self, start=1, finish=None):
        i = start
        pools = []

        while (
            (resp := (await self.get_trending_pools(page=i, debug=True, num_retries=3)))
            and (res := resp.get("data", []))
            and len(res) > 0
            and (i < finish if finish else True)
        ):
            i += 1
            pools += res
        return pools
