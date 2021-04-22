#!/usr/bin/python
import logging
import pickle
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

import pandas
import requests
from tqdm import tqdm

clean = re.compile("<.*?>")


def get_titles(file: Path) -> pandas.DataFrame:
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for topic in root.iter("topic"):
        title = topic.find("title").text
        id = topic.find("number").text

        buffer.append([int(id.strip()), title.strip()])

    return pandas.DataFrame(buffer, columns=["TopicID", "topic"])


def uuid2doc(uuid, index: str = "cw12"):
    url = "https://www.chatnoir.eu/cache"

    request_data = {
        "uuid": uuid,
        "index": index,
        "raw": "raw",
        "plain": "plain",
    }

    seconds = 10

    for attempt in range(10):
        success = False
        try:
            data = requests.get(url, request_data).text
            success = True
        except Exception as str_error:
            logging.warning(
                "Cannot retrieve Documents. Retrying in %s seconds" % seconds
            )
            logging.warning("Code: %s" % str_error)

            time.sleep(seconds)
            seconds += seconds
            if attempt == 9:
                logging.critical("Failed 10 times. Exiting ...")
                exit(1)

        if success:
            break

    data = re.sub("<[^>]+>", "", data)
    data = re.sub("\n", "", data)
    data = re.sub("&[^;]+;", "", data)

    return data


def uuids2df(uuid: pandas.DataFrame) -> pandas.DataFrame:
    save_path = Path.cwd() / "data/ChatNoirCache"

    missing = uuid["uuid"].tolist()
    save = None

    if Path(save_path / "uuid.pickle").is_file():
        logging.info("Loading text save")
        save = pandas.read_csv(save_path / "uuid.csv")

        with open(save_path / "uuid.pickle", "rb") as filehandle:
            saved = pickle.load(filehandle)
            # saved = save['uuid'].unique().tolist()

        missing = [x for x in missing if x not in saved]
        if len(missing) > 0:
            logging.info("Requesting missing docs ...")

    frames = []

    for uuid in tqdm(missing, desc="ChatNoir query docs progress"):
        frames.append([uuid, uuid2doc(uuid)])

    result = pandas.DataFrame(frames, columns=["uuid", "FullText"])

    if save is not None:
        result = pandas.concat([save, result]).reset_index(drop=True)

    if len(missing) > 0:
        result.to_csv(path_or_buf=save_path / "uuid.csv", index=False)

        with open(save_path / "uuid.pickle", "wb") as filehandle:
            pickle.dump(result["uuid"].tolist(), filehandle)

    return result


def df_add_text(df: pandas.DataFrame):
    uuids = pandas.DataFrame(df["uuid"].unique(), columns=["uuid"])

    result = uuids2df(uuids)

    result = df.merge(result, how="left", on="uuid")
    return result


class ChatNoir:
    def __init__(self, key: str, working_directory: Path, corpus: List[str] = ["cw12"]):
        self.key = key
        self.corpus = corpus
        self.workingDir = working_directory / "data/ChatNoirCache"

    def api(self, data: str, size: int) -> dict:
        url = "https://www.chatnoir.eu/api/v1/_search"

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
                response = requests.post(url, data=request_data)
                output = response.json()["results"]
                success = True
            except Exception as str_error:
                logging.warning(
                    "Cannot retrieve Documents. Retrying in %s seconds" % seconds
                )
                logging.warning("Code: %s" % str_error)

                try:
                    logging.warning("Response was : %s" % response)
                except NameError:
                    continue

                time.sleep(seconds)
                seconds += seconds
                if attempt == 9:
                    logging.critical("Failed 10 times. Exiting ...")
                    exit(1)

            if success:
                break

        return output

    def get_response(self, data: pandas.DataFrame, querysize: int) -> pandas.DataFrame:
        querys = data["query"].tolist()

        querysize = str(querysize)

        # Loading Data for querysize if available
        save_path = self.workingDir / (querysize + ".csv")
        save_list = self.workingDir / (querysize + ".pickle")

        if Path(save_list).is_file():
            logging.info("Loading ChatNoir query size: %s" % querysize)
            result = pandas.read_csv(save_path)

            with open(save_list, "rb") as filehandle:
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
                    # clean html tags
                    answer["title"] = re.sub(clean, "", answer["title"])
                    answer["snippet"] = re.sub(clean, "", answer["snippet"])

                    buffer = (
                        query,
                        answer["trec_id"],
                        answer["uuid"],
                        answer["title"],
                        answer["snippet"],
                        answer["target_hostname"],
                        answer["score"],
                    )
                    answers.append(buffer)

            answer = pandas.DataFrame(
                answers,
                columns=[
                    "query",
                    "TrecID",
                    "uuid",
                    "title",
                    "snippet",
                    "target_hostname",
                    "Score_ChatNoir",
                ],
            )
            result = result.append(answer)

            Path.mkdir(save_path.parent, parents=True, exist_ok=True)
            result.to_csv(path_or_buf=save_path, index=False)

            with open(save_list, "wb") as filehandle:
                pickle.dump(querys, filehandle)

        # removing unrequested queries
        result = result[result["query"].isin(querys)]

        data = data.merge(result, how="inner", on="query")
        return data
