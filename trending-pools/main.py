import asyncio
import time

from helpers import log
from pool_processor import get_processed_pools


async def run_async():
    tic = time.time()
    await get_processed_pools()
    toc = time.time()
    log.warning(f"Fetching trending assets took: {round(toc-tic, 3)}s")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_async())
