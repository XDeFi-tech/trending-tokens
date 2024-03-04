from typing import NamedTuple


class AssetInfo(NamedTuple):
    id: str
    chain: str
    address: str
    decimals: int
    symbol: str
    liquidity: str
    volume24: str
