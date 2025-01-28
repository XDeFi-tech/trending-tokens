import json
import logging
from collections.abc import Awaitable, Callable
from json import JSONDecodeError
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from helpers import remove_none
from constants import FILE_LOGS

HTTP_REQUEST_TIMEOUT = 10

log = logging.getLogger(__name__)
if FILE_LOGS:
    log.addHandler(logging.FileHandler("output.log", mode="w"))


class BaseFetcherException(Exception):
    """Base exception class."""

    message = "BaseFetcherException"

    def __init__(self, *, message: str = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class HTTPClientException(BaseFetcherException):
    message = "HTTP request failed"


class MultipleRequestFailed(HTTPClientException):
    message = "get_request Max retry in request exceeded"


class GetRequestException(HTTPClientException):
    message = "get_request failed"


class PostRequestException(HTTPClientException):
    message = "post_request failed"


class MultiplePostRequestFailed(HTTPClientException):
    message = "post_request Max retry in request exceeded"


async def get_request(
    url: str,
    headers: Optional[Dict] = None,
    query: Dict = None,
    timeout: int = HTTP_REQUEST_TIMEOUT,
    num_retries: int = 1,
    backoff_on_rate_limit: bool = True,
    debug: bool = False,
    response_type: str = "json",
    override_metric_attrs: Optional[Dict] = None,
    error_handler: Optional[Callable[[ClientResponse], None]] = None,
):
    """

    @param url: URL to make the request to
    @param headers: Headers to be included in the http request
    @param params: Http query parameters to be included in the http request
    @param num_retries:
    @param debug:
    @param timeout: Number of seconds before the request times out, default value is 20 seconds
    @return: response from the request based on the response_type. Default is json
    """
    """
    Handle get request with retry. Function is not cached.

    Example:

        await get_request(url="https://api.0x.org/swap/v1/quote", params={"sellToken": "ETH", "buyToken": "DAI"}, num_of_retries=3, debug=True)

    Args:
        url (StrOrURL): URL to make the request to
        headers (Optional[Dict], optional): Headers to be included in the http request. Defaults to None.
        query (Dict, optional): Http query parameters to be included in the http request. Defaults to None.
        timeout (int, optional): Number of seconds before the request times out. Defaults to HTTP_REQUEST_TIMEOUT.
        num_retries (int, optional): Number of seconds before the request times out. Defaults to 1.
        debug (bool, optional): will log an info log. Defaults to False.
        response_type (str, optional): if not set to json it will return text response. Defaults to "json".

    Raises:
        GetRequestException: _description_
        MultipleRequestFailed: _description_

    Returns:
        Any: response from the request based on the response_type. Default to json
    """
    headers = headers or {}
    query_str = urlencode(
        remove_none(dictionary=query or {}),
        True,
    )
    full_url = f"{url}?{query_str}" if query_str else url
    while num_retries > 0:
        try:
            return await _get_request(
                url=full_url,
                headers=headers,
                timeout=timeout,
                debug=debug,
                response_type=response_type,
                override_metric_attrs=override_metric_attrs,
                error_handler=error_handler,
            )
        except TimeoutError as e:
            raise GetRequestException(
                url=url,
                retry=num_retries,
                message=f"Request timed out after {timeout} seconds",
                error=e,
            ) from e

        except ClientError as e:
            num_retries -= 1
            if num_retries == 0:
                raise MultipleRequestFailed(url=url, retry=num_retries, error=e) from e

        # re-raise the exception to be able to propagate the custom exceptions
        except Exception as e:
            raise e


async def post_request(
    url: str,
    data: Any,
    headers: Optional[Dict] = None,
    query: Dict = None,
    timeout: int = HTTP_REQUEST_TIMEOUT,
    num_retries: int = 1,
    debug: bool = False,
    response_type: str = "json",
    override_metric_attrs: Optional[Dict] = None,
    error_handler: Optional[Callable[[ClientResponse], None]] = None,
):
    """
    Handle post request with retry.
    Function is not cached yet.
    third party providers.

    Example:

        gql_query = '''
            query TxClassifierGetTokenData($input: [CryptoAssetArgs!]!) {
            assets {
                cryptoAssets(input: $input) {
                id
                symbol
                image
                }
            }
            }
        '''

        json_data = {
            "query": gql_query,
            "variables": {"input": [{"chain": "Ethereum", "contract": "0x98f3c9e6E3fAce36bAAd05FE09d375Ef1464288B"}]},
        }

        await post_request(url="https://gql-router.dev.xdefi.services/graphql", data=json_data, num_of_retries=3, debug=True)


    Args:
        url (StrOrURL): to make the request to
        data (Any): any json encoded data that post request accepts.
        headers (Optional[Dict], optional): Headers to be included in the http request. Defaults to None.
        query (Dict, optional):  Http query parameters to be included in the http request. Defaults to None.
        timeout (int, optional):  Number of seconds before the request times out. Defaults to HTTP_REQUEST_TIMEOUT.
        num_retries (int, optional): the number of retries if fails. Defaults to 1.
        debug (bool, optional): if set to True will print info log level. Defaults to False.
        response_type (str, optional): if not set to json it will return text response. Defaults to "json".

    Raises:
        PostRequestException: _description_
        MultiplePostRequestFailed: _description_

    Returns:
        Any: response from the request based on the response_type. Default to json
    """
    headers = headers or {}
    query_str = urlencode(
        remove_none(dictionary=query or {}),
        True,
    )
    full_url = f"{url}?{query_str}" if query_str else url
    while num_retries > 0:
        try:
            return await _post_request(
                url=full_url,
                data=data,
                headers=headers,
                timeout=timeout,
                debug=debug,
                response_type=response_type,
                override_metric_attrs=override_metric_attrs,
                error_handler=error_handler,
            )
        except TimeoutError as e:
            raise PostRequestException(
                url=url,
                retry=num_retries,
                message=f"Request timed out after {timeout} seconds",
                error=e,
            ) from e

        except ClientError as e:
            num_retries -= 1
            if num_retries == 0:
                raise MultiplePostRequestFailed(
                    url=url, retry=num_retries, error=e
                ) from e

        # re-raise the exception to be able to propagate the custom exceptions
        except Exception as e:
            raise e


async def _get_request(
    *,
    url: str,
    headers: Optional[Dict] = None,
    timeout: int,
    debug: bool,
    response_type: str,
    override_metric_attrs: Optional[Dict] = None,
    error_handler: Optional[Callable[[ClientResponse], None]] = None,
):
    headers = headers or {}
    async with ClientSession(
        headers=headers, timeout=ClientTimeout(total=timeout)
    ) as session:
        async with session.get(url) as resp:
            if debug:
                log.info(f"Response status for {url} : {resp.status}")
            
            if resp.status > 299:
                log.warning(
                    f"GET request failed for {url} with status code: {resp.status}. Response text: {await resp.text(encoding='utf-8')}"
                )
            return await _parse_response(
                resp, response_type, error_handler=error_handler
            )


async def _post_request(
    *,
    url: str,
    headers: Dict,
    data: Any,
    timeout: int,
    debug: bool,
    response_type: str,
    override_metric_attrs: Optional[Dict] = None,
    error_handler: Optional[Callable[[ClientResponse], None]] = None,
):
    headers = headers or {}
    async with ClientSession(
        headers=headers, timeout=ClientTimeout(total=timeout)
    ) as session:
        async with session.post(url=url, data=data) as resp:
            if debug:
                log.info(f"Response status for {url} : {resp.status}")
            if resp.status > 299:
                log.warning(
                    f"POST request failed for {url} with status code: {resp.status}. Response text: {await resp.text(encoding='utf-8')}"
                )
            return await _parse_response(
                resp, response_type, error_handler=error_handler
            )


async def _parse_response(
    response: ClientResponse,
    response_type,
    error_handler: Optional[Callable[[ClientResponse], Awaitable[None]]] = None,
):
    if error_handler:
        # this function should raise custome exception based on ClientResponse.status and return None if no issue.
        await error_handler(response)
    if response_type == "json":
        try:
            resp = await response.json()
            if isinstance(resp, str):
                return json.loads(resp)
            else:
                return resp
        except JSONDecodeError as e:
            raise GetRequestException(
                url=response.url,
                response_text=response.text,
                response_type=response_type,
                response_status=response.status,
                message="Failed to parse response",
                error=e,
            ) from e
    elif response_type == "response_object":
        return response
    return await response.text()
