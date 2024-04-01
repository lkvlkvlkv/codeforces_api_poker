""" 
    This script is used to crawl the Codeforces API and retrieve the user's status.
    The data is then parsed and stored in JSON files.
"""

import hashlib
import json
import random
import string
import time
import requests
from sortedcontainers import SortedDict
from sensitive_info import KEY, SECRET


BASE_URL = "https://codeforces.com/api/"



def unix_timestamp() -> int:
    """
    Returns the current Unix timestamp as an integer.

    Returns:
        int: The current Unix timestamp.
    """
    return int(time.time())


def sha512hex(hash_string: str) -> str:
    """
    Calculates the SHA-512 hash of the given string and returns it as a hexadecimal string.

    Parameters:
    ext (str): The string to calculate the hash for.

    Returns:
    str: The SHA-512 hash of the input string as a hexadecimal string.
    """
    return hashlib.sha512(hash_string.encode())


def api_signature(method: str, params: dict) -> str:
    """
    Generate an API signature for the given method and parameters.

    Args:
        method (str): The API method.
        params (dict): The parameters for the API method.

    Returns:
        str: The generated API signature.

    """
    rand = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )
    hash_string = rand + "/" + method + "?"
    sd = SortedDict(params)
    for key, value in sd.items():
        hash_string += f"{key}={value}&"
    hash_string = hash_string[:-1]
    hash_string += "#" + SECRET
    return rand + sha512hex(hash_string).hexdigest()


def get_user_status(_handle: str, _from: int, _count: int) -> list:
    """
    Retrieves the status of a user from the Codeforces API.

    Args:
        _handle (str): The handle (username) of the user.
        _from (int): The index of the first submission to return.
        _count (int): The number of submissions to return.

    Returns:
        list: A list of submission objects representing the user's status.

    Raises:
        None

    """
    timestamp = unix_timestamp()
    method = "user.status"
    api_sig = api_signature(
        method,
        {
            "apiKey": KEY,
            "handle": _handle,
            "from": _from,
            "count": _count,
            "time": timestamp,
        },
    )
    url = f"{BASE_URL}{method}?apiKey={KEY}&time={timestamp} \
            &apiSig={api_sig}&handle={_handle}&from={_from}&count={_count}"

    response = requests.get(url, timeout=10)
    data = response.json()
    status = data["status"]
    if status == "FAILED":
        print(data["comment"])
        return None
    return data["result"]


def parse_data(data):
    """
    Parses the given data and performs various operations on it.

    Args:
        data (list): A list of dictionaries representing the data to be parsed.

    Returns:
        None
    """
    data = list(
        filter(lambda x: x["verdict"] == "OK" and "rating" in x["problem"], data)
    )
    exist_name = []
    data = list(
        filter(
            lambda x: x["problem"]["name"] not in exist_name
            and not exist_name.append(x["problem"]["name"]),
            data,
        )
    )
    data = sorted(data, key=lambda x: x["problem"]["rating"])

    with open("data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=4))

    rating = {}
    for submission in data:
        if submission["problem"]["rating"] in rating:
            rating[submission["problem"]["rating"]] += 1
        else:
            rating[submission["problem"]["rating"]] = 1
    with open("rating.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(rating, indent=4))

    tags = {}
    for submission in data:
        for tag in submission["problem"]["tags"]:
            if tag in tags:
                tags[tag] += 1
            else:
                tags[tag] = 1
    with open("tags.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(tags, indent=4))


if __name__ == "__main__":
    submission_list = get_user_status("LKV0429", 1, 1000)
    parse_data(submission_list)
