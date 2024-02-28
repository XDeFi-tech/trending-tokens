import pytest
import sys
import os
from mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)) + "/trending-pools")

from pool_processor import parse_pool

minu_pool = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {
            "h1": "21475.753838700075959",
            "h24": "234671.45"
        },
        "reserve_in_usd": "394219.3869"
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token"
            }
        }
    }
}

minu_pool_low_volume = {
    "id": "bsc_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {
            "h1": "2475.753838700075959",
            "h24": "2671.45"
        },
        "reserve_in_usd": "394219.3869"
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token"
            }
        }
    }
}
base_asset_pool = {
    "id": "base_0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
    "attributes": {
        "address": "0x91d8d7dfcadc8e04195e75069e1316e01ba7f01c",
        "name": "MINU / WBNB",
        "volume_usd": {
            "h1": "21475.753838700075959",
            "h24": "234671.45"
        },
        "reserve_in_usd": "394219.3869"
    },
    "relationships": {
        "base_token": {
            "data": {
                "id": "base_0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
                "type": "token"
            }
        }
    }
}


@patch("helpers.get_request", return_value={
    "data": {
        "attributes": {
            "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4",
            "symbol": "MINU",
            "decimals": 18,
        }
    }
}
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
        "volume24": "234671.45"}


@pytest.mark.asyncio
async def test_parse_pool_non_supported_chain():
    assert (await parse_pool(base_asset_pool)) is None


@patch("helpers.load_existing_tokens", return_value=(["bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4"], [
    {
        "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "chain": "bsc", 
        "symbol": "MINU",
        "decimals": 18, 
        "liquidity": "3000000", 
        "volume24": "200000"}
]))
@pytest.mark.asyncio
async def test_parse_existing_pool(token_lists):
    assert (await parse_pool(minu_pool)) == {
        "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "chain": "bsc", 
        "symbol": "MINU",
        "decimals": 18, 
        "liquidity": "394219.3869", 
        "volume24": "234671.45"}
    
@patch("helpers.load_existing_tokens", return_value=(["bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4"], [
    {
        "id": "bsc_0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "address": "0xf48f91df403976060cc05dbbf8a0901b09fdefd4", 
        "chain": "bsc", 
        "symbol": "MINU",
        "decimals": 18, 
        "liquidity": "3000000", 
        "volume24": "200000"}
]))
@pytest.mark.asyncio
async def test_parse_existing_pool_with_low_volume(token_lists):
    assert (await parse_pool(minu_pool_low_volume)) is None