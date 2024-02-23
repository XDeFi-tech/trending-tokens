import time
import logging
import asyncio
from pool_processor import fetch_pools

log = logging.getLogger(__name__)


async def run_async():
    tic = time.time()
    await fetch_pools(1, 6)
    toc = time.time()
    log.warning(f"Fetching trending assets took: {round(toc-tic, 3)}s")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_async())
