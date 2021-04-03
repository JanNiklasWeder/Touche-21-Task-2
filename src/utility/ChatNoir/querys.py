#!/usr/bin/python
import logging
import pickle
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas
from typing import List
import os
import argparse

from tqdm import tqdm

def get_titles(file: Path) -> List[str]:
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer


class ChatNoir:

    def __init__(self, key: str, working_directory: Path, corpus: List[str] = ["cw12"]):
        self.key = key
        self.corpus = corpus
        self.workingDir = working_directory / "data/ChatNoirCache"

    def api(self, data: str, size: int) -> dict:
        url = 'https://www.chatnoir.eu/api/v1/_search'

        request_data = {
            "apikey": self.key,
            "query": data,
            "size": size,
            "index": self.corpus,
        }

        output = ""
        seconds = 10

        for attempt in range(10):  #
            success = False
            try:
                response = (requests.post(url, data=request_data))
                output = response.json()['results']
                success = True
            except Exception as str_error:
                logging.warning("Cannot retrieve Documents. Retrying in %s seconds" % seconds)
                logging.warning("Code: %s" % str_error)

                try:
                    logging.warning("Response was : %s" % response)
                except:
                    continue

                time.sleep(seconds)
                seconds += seconds
                if attempt == 9:
                    logging.critical("Failed 10 times. Exiting ...")
                    exit(1)

            if success:
                break

        return output

    def get_response(self, data: pandas.DataFrame, querysize: str) -> pandas.DataFrame:
        querys = data['query'].tolist()
        
        # RESPONSES MUST BE ASSIGNED WITH TAGS
        tags = data['tag'].tolist()

        querysize = str(querysize)

        # Loading Data for querysize if available
        save_path = self.workingDir / (querysize + ".csv")
        save_list = self.workingDir / (querysize + ".pickle")

        if Path(save_list).is_file():
            logging.info("Loading ChatNoir query size: %s" % querysize)
            result = pandas.read_csv(save_path)

            with open(save_list, 'rb') as filehandle:
                saved = pickle.load(filehandle)

            missing = [x for x in querys if x not in saved]
            if len(missing) > 0:
                logging.info("Requesting missing inquiries...")

        else:
            missing = querys
            logging.info("Query Size not cached requesting ...")
            result = pandas.DataFrame()

        # if a query is still missing request it and save the new DataFrame
        if len(missing) > 0:
            answers = []

            for query in tqdm(missing, desc="ChatNoir query progress"):
                logging.debug("Getting response for '%s'" % query)
                response = self.api(query, querysize)
                logging.debug(response)
                for answer in response:
                    buffer = query, answer['trec_id'], answer['uuid'], answer['target_hostname'], answer['score']
                    answers.append(buffer)

            answer = pandas.DataFrame(answers, columns=['query', 'TrecID', 'UUID', 'target_hostname', 'Score_ChatNoir'])
            result = result.append(answer)

            Path.mkdir(save_path.parent, parents=True, exist_ok=True)
            result.to_csv(path_or_buf=save_path, index=False)

            with open(save_list, 'wb') as filehandle:
                pickle.dump(querys, filehandle)

        # removing unrequested queries
        result = result[result['query'].isin(querys)]
        print(data)
        print(result)

        data = data.merge(result, how="inner", on="query")
        return data


if __name__ == "__main__":

    '''
    not working at the moment
    '''
    wd = Path(os.getcwd())
    wd = wd.parent

    auth = Auth(wd)
    keyChatNoir = auth.get_key("ChatNoir")

    chatnoir = ChatNoir(keyChatNoir, wd)

    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str,
                        help="File path to 'topics-task-2.xml'")
    parser.add_argument("-v", "--loglevel", type=str, default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the shown log events (default: %(default)s)")

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    topics = get_titles(args.Topics)

    # out = open("output", "w")

    size = 50
    test = chatnoir.get_response(topics, size)

    print(test)
