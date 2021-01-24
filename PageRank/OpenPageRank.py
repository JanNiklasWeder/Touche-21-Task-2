#!/usr/bin/python
import time

import requests
import auth.auth

def OpenPageRank(website):
    url = 'https://openpagerank.com/api/v1.0/getPageRank'

    request_data = {
        "domains[]": {website},
    }
    headers = {
        'API-OPR': auth.auth.get_key('OpenPageRank')
    }

    output = []
    seconds = 10

    for x in range(10):  #
        try:
            output = requests.get(url, params=request_data, headers=headers).json()['response']
            str_error = None
        except Exception as str_error:
            pass

        if str_error:
            print("[ERROR] Cannot reach OpenPageRank. Retrying in %s seconds" % seconds)
            time.sleep(seconds)
            seconds += seconds
            if x == 9:
                print("[ERROR] Cannot reach OpenPageRank. Exiting ...")
                exit(1)
        else:
            break

    output = output[0]['page_rank_decimal']
    #print(output)
    return output


if __name__ == "__main__":
    print(OpenPageRank("google.de").text)

