import pytest
import sys
import os 

sys.path.append(os.path.dirname(os.path.dirname(__file__)) + "/trending-pools")

from helpers import parse_token_id

@pytest.mark.parametrize(
        "id, chain_and_address",
        [
            ("polygon_pos_0xCrazyShitcoin0", ("polygon_pos", "0xCrazyShitcoin0")),
            ("eth_0xCrazyShitcoin1", ("eth", "0xCrazyShitcoin1")),
            ("eth-goerli_0xCrazyShitcoin2", ("eth-goerli", "0xCrazyShitcoin2")),
        ]
)
def test_parse_token_id(id, chain_and_address):
    assert parse_token_id(id) == chain_and_address
