#!/usr/bin/python
import requests


def OpenPageRank(website):
    url = 'https://openpagerank.com/api/v1.0/getPageRank'

    request_data = {
        "domains[]": {website},
    }
    headers = {
        'API-OPR': '--'
    }

    return requests.get(url, params=request_data, headers=headers)


if __name__ == "__main__":
    print(OpenPageRank("google.de").text)

