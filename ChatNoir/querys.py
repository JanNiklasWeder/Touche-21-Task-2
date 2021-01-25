#!/usr/bin/python
import time

import requests
# import subprocess
import xml.etree.ElementTree as ET
import sys
from pathlib import Path
import pandas
import auth.auth


def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer


def api(data, size):
    url = 'https://www.chatnoir.eu/api/v1/_search'

    request_data = {
        "apikey": auth.auth.get_key('ChatNoir'),
        "query": data,
        "size": size,
        "index": ["cw12"],
    }

    output = ""
    seconds = 10

    for x in range(10):  #
        success = False
        try:
            output = requests.post(url, data=request_data).json()['results']
            success = True
        except Exception as str_error:
            print("[ERROR] Cannot retrieve Documents. Retrying in %s seconds" % seconds)
            print("[ERROR] Code: %s" % str_error)
            time.sleep(seconds)
            seconds += seconds
            if x == 9:
                print("[ERROR] Failed 10 times. Exiting ...")
                exit(1)

        if success:
            break

    return output


def get_response(querysize):
    querysize = str(querysize)
    # Using provided Topics from ./res/topics-task-2.xml
    topics = get_titles("../res/topics-task-2.xml")

    # Loading Data for querysize if available otherwise requesting

    if Path('../ChatNoir/res/' + querysize).is_file():
        print("[INFO] Loading ChatNoir query size: ", querysize)
        Data = pandas.read_csv('../ChatNoir/res/' + querysize,
                               names=['TopicID', 'TrecID', 'UUID', 'target_hostname', 'Score'])
    else:
        print("[INFO] Query Size not cached requesting ...")
        answers = []
        topicID = 1
        for topic in topics:
            print("[INFO] Getting response for '%s'" % topic)
            response = api(topic, querysize)
            # print(response)
            for answer in response:
                buffer = topicID, answer['trec_id'], answer['uuid'], answer['target_hostname'], answer['score']
                answers.append(buffer)

        topicID += 1
        Data = (pandas.DataFrame(answers, columns=['TopicID', 'TrecID', 'UUID', 'target_hostname', 'Score']))
        Data.to_csv(path_or_buf="../ChatNoir/res/" + querysize, index=False)
    return Data


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("usage: \"python query.py topics-task-2.xml\"")
        sys.exit(1)

    topics = get_titles(sys.argv[1])
    out = open("output", "w")
    size = 50
    answers = []
    for topic in topics:
        answers.append(api(topic, size))
        print("Getting response for", topic)

    # assumption about topic id and correct rank | both not validated
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

    # print(subprocess.check_output(args=["/home/roberto/Programms/trec_eval-master/trec_eval", "-m", "ndcg",
    #                                    "/home/roberto/Programms/trec_eval-master/test/qrels.test",
    #                                    "/home/roberto/Programms/trec_eval-master/test/results.test"]))
