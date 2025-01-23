import os
import sys

import pytest
from mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)) + "/trending-pools")

from pool_processor import parse_pool

minu_pool = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {"h1": "21475.753838700075959", "h24": "234671.45"},
        "reserve_in_usd": "394219.3869",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token",
            }
        }
    },
}

minu_pool_missing_volume = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {"h1": "21475.753838700075959"},
        "reserve_in_usd": "394219.3869",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token",
            }
        }
    },
}

minu_pool_low_volume = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {"h1": "2475.753838700075959", "h24": "2671.45"},
        "reserve_in_usd": "394219.3869",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token",
            }
        }
    },
}

minu_pool_low_liquidity = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {"h1": "2475.753838700075959", "h24": "2671.45"},
        "reserve_in_usd": "19499.3869",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token",
            }
        }
    },
}

base_asset_pool = {
    "id": "base_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {"h1": "21475.753838700075959", "h24": "234671.45"},
        "reserve_in_usd": "394219.3869",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "base_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token",
            }
        }
    },
}

sol_pool = {
    "id": "solana_BJKVBffxiaYgiqu7FeLbdVuhLrnXFFEr3KtH9SuboEdr",
    "attributes": {
        "address": "BJKVBffxiaYgiqu7FeLbdVuhLrnXFFEr3KtH9SuboEdr",
        "name": "SOL / MAI",
        "volume_usd": {
            "h1": "4486.75019495503720866724797605362203203000202612395689050435316312537258021",
            "h24": "589711.91",
        },
        "reserve_in_usd": "139550.7145",
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "solana_So11111111111111111111111111111111111111112",
                "type": "token",
            }
        },
        "quote_token": {
            "data": {
                "id": "solana_CdvCJJQHeU7qzpDWsRjR2E1Vp7GoQfBtg4joR9yprR5Z",
                "type": "token",
            }
        },
    },
}


@patch(
    "helpers.get_request",
    return_value={
        "data": {
            "attributes": {
                "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "symbol": "MINU",
                "decimals": 18,
            }
        }
    },
)
@patch("helpers.load_existing_tokens", return_value=([], []))
@pytest.mark.asyncio
async def test_parse_pool(get_response, token_lists):
    assert (await parse_pool(minu_pool)) == {
        "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
        "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
        "chain": "bsc",
        "symbol": "MINU",
        "decimals": 18,
        "liquidity": "394219.3869",
        "volume24": "234671.45",
    }


@pytest.mark.asyncio
async def test_parse_pool_non_supported_chain():
    assert (await parse_pool(base_asset_pool)) is None


@patch(
    "helpers.load_existing_tokens",
    return_value=(
        ["bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4"],
        [
            {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "chain": "bsc",
                "symbol": "MINU",
                "decimals": 18,
                "liquidity": "3000000",
                "volume24": "200000",
            }
        ],
    ),
)
@pytest.mark.asyncio
async def test_parse_existing_pool(token_lists):
    assert (await parse_pool(minu_pool)) == {
        "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
        "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
        "chain": "bsc",
        "symbol": "MINU",
        "decimals": 18,
        "liquidity": "394219.3869",
        "volume24": "234671.45",
    }


@patch(
    "pool_processor.load_existing_tokens",
    return_value=(
        ["bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4"],
        [
            {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "chain": "bsc",
                "symbol": "MINU",
                "decimals": 18,
                "liquidity": "3000000",
                "volume24": "200000",
            }
        ],
    ),
)
@pytest.mark.asyncio
async def test_parse_existing_pool_with_low_volume(token_lists):
    assert (await parse_pool(minu_pool_low_volume)) is None


@pytest.mark.asyncio
async def test_parse_low_liquidity_pool():
    assert (await parse_pool(minu_pool_low_liquidity)) is None


@patch(
    "http.get_request",
    return_value={
        "data": {
            "id": "solana_CdvCJJQHeU7qzpDWsRjR2E1Vp7GoQfBtg4joR9yprR5Z",
            "type": "token",
            "attributes": {
                "address": "CdvCJJQHeU7qzpDWsRjR2E1Vp7GoQfBtg4joR9yprR5Z",
                "name": "Multi AI",
                "symbol": "MAI",
                "decimals": 9,
            },
        }
    },
)
@patch("helpers.load_existing_tokens", return_value=([], []))
@pytest.mark.asyncio
async def test_parse_pool_sol_as_base_token(get_response, token_lists):
    assert (await parse_pool(sol_pool)) == {
        "id": "solana_CdvCJJQHeU7qzpDWsRjR2E1Vp7GoQfBtg4joR9yprR5Z",
        "address": "CdvCJJQHeU7qzpDWsRjR2E1Vp7GoQfBtg4joR9yprR5Z",
        "chain": "solana",
        "symbol": "MAI",
        "decimals": 9,
        "liquidity": "139550.7145",
        "volume24": "589711.91",
    }


@patch(
    "helpers.load_existing_tokens",
    return_value=(
        ["bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4"],
        [
            {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "chain": "bsc",
                "symbol": "MINU",
                "decimals": 18,
                "liquidity": "3000000",
                "volume24": "200000",
            }
        ],
    ),
)
@pytest.mark.asyncio
async def test_parse_existing_pool_with_error(token_lists):
    assert (await parse_pool(minu_pool_missing_volume)) is None
