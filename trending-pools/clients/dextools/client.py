import logging
import os
from typing import Dict
from datetime import datetime, timedelta, timezone

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

    async def get_solana_pools(
        self,
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
            + f"/v2/pool/solana?sort=creationTime&order=desc&from={startTime}&to={toTime}&page={page}&pageSize={page_size}"
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
