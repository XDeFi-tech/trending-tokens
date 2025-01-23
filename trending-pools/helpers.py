import json
import logging
from copy import deepcopy
from functools import lru_cache
from typing import Dict, Optional, Tuple

from constants import ASSETS_PATH, FILE_LOGS

log = logging.getLogger("globalLogger")
if FILE_LOGS:
    log.addHandler(logging.FileHandler("output.log", mode="w"))


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


def remove_none(*, dictionary: Dict) -> Dict:
    dictionary = deepcopy(dictionary)
    for key, value in list(dictionary.items()):
        if value is None:
            del dictionary[key]
        elif isinstance(value, dict):
            remove_none(dictionary=value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_none(dictionary=item)
    return dictionary
