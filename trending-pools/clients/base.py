from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any, Dict, Optional

from aiohttp import ClientResponse
from yarl import URL

from .http import HTTP_REQUEST_TIMEOUT, get_request, post_request


class BaseAsyncHttpClient(ABC):
    """
    The generic http client, providing the basic functionality for all clients which use the requests.
    """

    _client_name: str
    _error_handler: Optional[Callable[[ClientResponse], Awaitable[None]]] = None
    logger: Logger

    @abstractmethod
    def __init__(self):
        """
        Initialize what is needed to function
        """
        pass

    @abstractmethod
    def _get_headers(self):
        """
        Some providers required headers differ from one another
        make sure to implement this method properly to return a dictionary
        of the required http headers.
        """
        pass

    def _override_metric_attributes(self, url: str) -> Dict:
        """
            returns the extra set of metric attributes to be updated on the `utils.clients.http.get_metrics_attributes_and_instrument`
            as `attrs_override` param.

        Args:
            url (str): raw url str to be parsed and having sensetive data removed.

        Returns:
            Dict: a dict to override the metric attributes.
        """
        url: URL = URL(url)
        attrs = {
            "client_name": self._client_name,
            # raw_path doesn't contain query strings, this will prevent the unwanted label explosion on metrics.
            # make sure to override this function to remove any sensetive data that is not part of the query strings.
            "path": url.raw_path,
        }

        return attrs

    async def _get(
        self,
        url: str,
        query: Dict = None,
        timeout: int = HTTP_REQUEST_TIMEOUT,
        num_retries: int = 1,
        debug: bool = False,
        response_type: str = "json",
    ) -> Any:
        return await get_request(
            url=url,
            headers=self._get_headers(),
            query=query,
            timeout=timeout,
            num_retries=num_retries,
            debug=debug,
            response_type=response_type,
            override_metric_attrs=self._override_metric_attributes(url=url),
            error_handler=self._error_handler,
        )

    async def _post(
        self,
        url: str,
        data: Any,
        query: Dict = None,
        timeout: int = HTTP_REQUEST_TIMEOUT,
        num_retries: int = 1,
        debug: bool = False,
    ) -> Any:
        return await post_request(
            url=url,
            data=data,
            headers=self._get_headers(),
            query=query,
            timeout=timeout,
            num_retries=num_retries,
            debug=debug,
            response_type="json",
            override_metric_attrs=self._override_metric_attributes(url=url),
            error_handler=self._error_handler,
        )
