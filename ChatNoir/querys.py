#!/usr/bin/python
import logging
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas
from typing import List
import os
import argparse

from tqdm import tqdm

from auth.auth import Auth


def get_titles(file: Path) -> List[str]:
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer


class ChatNoir:
    def __init__(self, key: str, corpus: List[str], working_directory: Path):
        self.key = key
        self.corpus = corpus
        self.workingDir = working_directory / "ChatNoir"

    def __init__(self, key: str, corpus: str, working_directory: Path):
        self.key = key
        self.corpus = list()
        self.corpus.append(corpus)
        self.workingDir = working_directory / "ChatNoir"

    def __init__(self, key: str, working_directory: Path):
        self.key = key
        self.corpus = ["cw12"]
        self.workingDir = working_directory / "ChatNoir"

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

    def get_response(self, querys: List[str], querysize: str) -> pandas.DataFrame:
        querysize = str(querysize)

        # Loading Data for querysize if available
        save_path = self.workingDir / 'res' / (querysize + ".csv")
        if Path(save_path).is_file():
            logging.info("Loading ChatNoir query size: %s" % querysize)
            Data = pandas.read_csv(save_path)

            missing = [x for x in querys if x not in Data['Topic'].tolist()]
            if len(missing) > 0:
                logging.info("Requesting missing inquiries...")

        else:
            missing = querys
            logging.info("Query Size not cached requesting ...")
            Data = pandas.DataFrame()

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

            answer = pandas.DataFrame(answers, columns=['Topic', 'TrecID', 'UUID', 'target_hostname', 'Score'])
            Data = Data.append(answer)

            Path.mkdir(save_path.parent, parents=True, exist_ok=True)
            Data.to_csv(path_or_buf=save_path, index=False)

        # removing unrequested queries
        print(Data)
        Data = Data[Data['Topic'].isin(querys)]
        print(Data)

        return Data


if __name__ == "__main__":
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

    # assumption about topic id and correct rank | both not validated

    '''
    topicId = 1
    for topic in answers:
        print(topic)
        rank = 1
        for response in topic:
            buffer = topicId, "Q0", response['trec_id'], rank, response['score'], "JackSparrowVanilla"
            print(buffer)
            out.write(" ".join(map(str, buffer)) + "\n")
            rank += 1
        topicId += 1
    '''
