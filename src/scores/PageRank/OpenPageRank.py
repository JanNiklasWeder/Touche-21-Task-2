#!/usr/bin/python
import logging
import os
import pickle
import time
from pathlib import Path
from typing import List, Tuple

import numpy
import pandas
import requests


class OpenPageRank():

    def __init__(self, key: [str], wd: Path = Path.cwd()):
        self.wd = wd / "data/PageRank"
        Path.mkdir(self.wd, parents=True, exist_ok=True)
        self.key = key
        self.url = 'https://openpagerank.com/api/v1.0/getPageRank'

    def request_page_rank(self, website: List[str]) -> List[Tuple[str,int]]:

        request_data = {
            "domains[]": set(website),
        }

        headers = {
            'API-OPR': self.key
        }

        output = []
        seconds = 10

        for x in range(10):

            success = False
            try:
                output = requests.get(self.url, params=request_data, headers=headers)
                output = output.json()['response']
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

        result = []
        for i in output:
            result.append([i['domain'],i['page_rank_decimal']])

        return result

    def get_page_rank(self, websites: pandas.DataFrame) -> pandas.DataFrame:
        save_path = self.wd

        missing = websites['target_hostname'].tolist()
        save = None

        if Path(save_path / "websites.pickle").is_file():
            logging.info("Loading PageRank save")
            save = pandas.read_csv(save_path/"data.csv")

            with open(save_path / "websites.pickle", 'rb') as filehandle:
                saved = pickle.load(filehandle)

            missing = [x for x in missing if x not in saved]
            if len(missing) > 0:
                logging.info("Requesting missing PageRank scores...")

        frames = []

        for index in range(0, len(missing), 100):
            request = missing[index:index + 100]
            frames = [*frames, *self.request_page_rank(request)]

        result = pandas.DataFrame(frames, columns=['target_hostname', 'Score_PageRank'])

        if save is not None:
            result = pandas.concat([save, result]).reset_index(drop=True)

        if len(missing)> 0:
            result.to_csv(path_or_buf=save_path/"data.csv", index=False)

            with open(save_path / "websites.pickle", 'wb') as filehandle:
                pickle.dump(websites['target_hostname'].tolist(), filehandle)

        return result

    def df_add_score(self, df: pandas.DataFrame):
        """
        Returns a DataFrame extended by the 'Score_PageRank' column. This column contains the OpenPageRank. As input
        a DataFrame with the column 'target_hostname' is expected, which must contain the corresponding domain name.

        Parameters:
            df (DataFrame): DataFrame with the domains in the 'target_hostname' column.

        Returns:
            extended DataFrame (DataFrame): DataFrame that has been extended by the 'Score_PageRank' column.
        """
        websites = pandas.DataFrame(df['target_hostname'].unique(),columns=["target_hostname"])

        result = self.get_page_rank(websites)

        result = df.merge(result, how="left", on="target_hostname")
        return result


if __name__ == "__main__":
    print({"google.de"})
    buffer = OpenPageRank("ckc840wswkg8kckwswk8w8k8wwsgwkocsok0kcok")
    print(buffer.get_page_rank({"google.de","google.com"}))
