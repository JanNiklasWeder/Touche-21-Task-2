#!/usr/bin/python
import time
from pathlib import Path

import requests

from auth.auth import Auth


def OpenPageRank(website):
    url = 'https://openpagerank.com/api/v1.0/getPageRank'
    auth = Auth(Path("../"))
    key = auth.get_key("OpenPageRank")

    request_data = {
        "domains[]": {website},
    }
    headers = {
        'API-OPR': key
    }

    output = []
    seconds = 10

    for x in range(10):

        success = False
        try:
            output = requests.get(url, params=request_data, headers=headers).json()['response']
            success = True
        except Exception as str_error:
            print("[ERROR] Cannot reach OpenPageRank. Retrying in %s seconds" % seconds)
            print("[ERROR] Code: %s" % str_error)
            time.sleep(seconds)
            seconds += seconds
            if x == 9:
                print("[ERROR] Failed 10 times. Exiting ...")
                exit(1)

        if success:
            break

    output = output[0]['page_rank_decimal']
    return output


if __name__ == "__main__":
    print(OpenPageRank("google.de").text)

