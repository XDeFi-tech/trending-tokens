import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
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

DEXTOOLS_API_KEY = os.getenv("DEXTOOLS_API_KEY", None)


class DexToolsClient(BaseAsyncHttpClient):
    """
    Integrated gecko terminal token fetcher client
    """

    logger: logging.Logger
    _request_kwargs = None
    _api_key: str
    _base_url: str

    def __init__(self):
        self._base_url = "https://public-api.dextools.io/standard/"
        self._api_key = DEXTOOLS_API_KEY
        self.logger = logging.getLogger("DexToolsClient")
        self._client_name = "DexToolsClient"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        if self._api_key:
            headers["X-API-Key"] = self._api_key

        return headers

    async def get_pools(
        self,
        chain: str,
        page: int = 0,
        page_size: int = 50,
        debug: bool = False,
        num_retries: int = 1,
    ):
        if page < 0:
            raise ValueError("page cannot be a negative number, it must start from 0.")

        if page_size < 0:
            raise ValueError("page_size cannot be a negative number.")

        now = datetime.now(tz=timezone.utc)
        yesterday = now - timedelta(days=1)
        startTime = yesterday.strftime("%Y-%m-%dT%H:%M:%S.0000z")
        toTime = now.strftime("%Y-%m-%dT%H:%M:%S.0000z")

        url = (
            self._base_url
            + f"/v2/pool/{chain}?sort=creationTime&order=desc&from={startTime}&to={toTime}&page={page}&pageSize={page_size}"
        )
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

    async def get_pools_liquidity(
        self,
        chain: str,
        address: str,
        debug: bool = False,
        num_retries: int = 1,
    ):
        url = self._base_url + f"/v2/pool/{chain}/{address}/liquidity"
        try:
            resp = await self._get(
                url=url, response_type="json", debug=debug, num_retries=num_retries
            )
            return resp
        except Exception as e:
            self.logger.warning(
                f"failed to fetch pool from {url} because of the error {e}"
            )
            raise e

    async def get_liquidity_pool_price_info(
        self,
        chain: str,
        address: str,
        debug: bool = False,
        num_retries: int = 1,
    ):
        url = self._base_url + f"/v2/pool/{chain}/{address}/price"
        try:
            resp = await self._get(
                url=url, response_type="json", debug=debug, num_retries=num_retries
            )
            return resp
        except Exception as e:
            self.logger.warning(
                f"failed to fetch prices for the pool from {url} because of the error {e}"
            )
            raise e

    async def get_all_pools(self, chain: str):
        pools = []
        first_page = await self.get_pools(
            chain=chain, page=0, debug=True, num_retries=3
        )
        page = None
        total_pages = None
        if data := first_page.get("data"):
            page = int(data.get("page"))
            total_pages = int(data.get("totalPages"))
            pools.extend(data.get("results"))
            self.logger.info(
                f"Dextools client fetched page:{page} totalPages: {total_pages}, number of pools{len(pools)}"
            )

        if page is not None and total_pages is not None:
            while page < total_pages:
                nth_page = await self.get_pools(
                    chain=chain, page=page + 1, debug=True, num_retries=3
                )
                if data := nth_page.get("data"):
                    page = int(data.get("page"))
                    pools.extend(data.get("results"))
                    self.logger.info(
                        f"Dextools client fetched page:{page} totalPages: {total_pages}, number of pools{len(pools)}"
                    )
        return pools

    def find_asset_info(self, token_id, global_assets):
        for token in global_assets:
            if token["id"] == token_id:
                return token

    async def parse_pool(self, pool: Dict, chain: str) -> Optional[Dict]:
        base_token_address = None
        base_token_chain = chain
        base_token_id = None
        pool_liquidity = None
        pool_liquidity_price = None
        liquidity = None
        if chain not in supported_chains:
            log.warning(
                f"Not including pool {pool['exchange']['name']}. Chain {chain} not supported."
            )
            return
        try:
            address = pool.get("address")
            if address:
                pool_liquidity = await self.get_pools_liquidity(
                    chain=chain, address=address
                )
                pool_liquidity_price = await self.get_liquidity_pool_price_info(
                    chain=chain, address=address
                )
                if not pool_liquidity:
                    self.logger.error(
                        f"No liquidity pool found for address {address} on the chain {chain}"
                    )
                    return
                if not pool_liquidity_price:
                    self.logger.error(
                        f"No pool_liquidity_price found for address {address} on the chain {chain}"
                    )
                    return
            else:
                self.logger.error(f"No address found for the pool {pool}")
                return

            liquidity = Decimal(pool_liquidity["data"]["liquidity"])
            if liquidity < Decimal(LIQUIDITY_THRESHOLD):
                self.logger.error(
                    f"Not including pool {pool['exchange']['name']} ad address {address}, not enough liquidity: {liquidity}."
                )
                return
            base_token_chain = chain
            base_token_address = pool["mainToken"]["address"]
            base_token_symbol = pool["mainToken"]["symbol"]
            base_token_id = f"{base_token_chain}_{base_token_address}"
            if base_token_address in EXCLUSION_LIST:
                if base_token_address in EXCLUSION_LIST:
                    return
            existing_ids, existing_assets = load_existing_tokens()
            if base_token_id in existing_ids:
                # Update volume and liquidity
                shitcoin = self.find_asset_info(base_token_id, existing_assets)
                log.warning(
                    f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} found!"
                )
                shitcoin["liquidity"] = liquidity
                shitcoin["volume24"] = pool_liquidity_price["data"]["volume24"]
                # If the last 24h volume is below VOLUME_THRESHOLD then omit
                if Decimal(shitcoin["volume24"]) < Decimal(VOLUME_THRESHOLD):
                    log.warning(
                        f"Asset {shitcoin['chain']}.{shitcoin['symbol']}-{shitcoin['address']} removed because of low volume."
                    )
                    return
                return shitcoin
            log.warning(f"Adding new asset {chain}.{base_token_symbol}-{address}.")
            return AssetInfo(
                id=base_token_id,
                chain=chain,
                address=address,
                decimals=0,  # TODO: find a way to fetch decimals
                symbol=base_token_symbol,
                liquidity=pool_liquidity["data"]["liquidity"],
                volume24=pool_liquidity_price["data"]["volume24"],
            )._asdict()
        except Exception as e:
            log.error(f"error: {e}, id: {base_token_id}")

    async def process_pools(self, pools: List[Dict], chain: str):
        assets = await asyncio.gather(*[self.parse_pool(pool=p, chain=chain) for p in pools])
        # assets = []
        # for pool in pools:
        #     assets.append(await self.parse_pool(pool=pool, chain=chain))
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
                pool_liquidity = await self.get_pools_liquidity(
                    chain=chain, address=address
                )
                pool_liquidity_price = await self.get_liquidity_pool_price_info(
                    chain=chain, address=address
                )
                shitcoin = self.find_asset_info(id, existing_assets)
                shitcoin["liquidity"] = pool_liquidity["data"]["liquidity"]
                shitcoin["volume24"] = pool_liquidity_price["data"]["volume24"]
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
