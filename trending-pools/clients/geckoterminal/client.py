import logging
from typing import Dict

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
