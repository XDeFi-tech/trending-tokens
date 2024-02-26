import aiohttp
import asyncio
import logging
import json
from typing import Dict, Optional, Tuple
from functools import lru_cache

from constants import ASSETS_PATH

log = logging.getLogger(__name__)

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

def read_json(filename: str) -> Optional[Dict]:
    with open(filename) as json_file:
        try:
            return json.load(json_file)
        except Exception as e:
            log.error(f"Error while opening JSON file: {e}")

def write_json(filename: str, data: Dict) -> None:
    with open(filename, "w") as json_file:
        try:
            json.dump(data, json_file)
        except Exception as e:
            log.error(f"Error while writing into JSON file: {e}")

@lru_cache(maxsize=1)
def load_existing_tokens():
    assets = read_json(ASSETS_PATH)
    if assets:
        return list(map(lambda x: x["id"], assets)), assets
    else:
        return [], []

def parse_token_id(base_token_id: str) -> Tuple[str, str]:
    parsed_id = base_token_id.split("_")
    address = parsed_id[-1]
    chain = "_".join(parsed_id[:-1])
    return chain, address
