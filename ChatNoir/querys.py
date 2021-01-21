#!/usr/bin/python

import requests
# import subprocess
import xml.etree.ElementTree as ET
import sys


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
        "apikey": "--",
        "query": data,
        "size": size,
        "index": ["cw12"],
    }

    return requests.post(url, data=request_data).json()


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
        for response in topic['results']:
            buffer = topicId, "Q0", response['trec_id'], rank, response['score'], "JackSparrowVanilla"
            print(buffer)
            out.write(" ".join(map(str, buffer)) + "\n")
            rank += 1
        topicId += 1

    # print(subprocess.check_output(args=["/home/roberto/Programms/trec_eval-master/trec_eval", "-m", "ndcg",
    #                                    "/home/roberto/Programms/trec_eval-master/test/qrels.test",
    #                                    "/home/roberto/Programms/trec_eval-master/test/results.test"]))