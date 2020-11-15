#!/usr/bin/python

import requests
#import subprocess
import xml.etree.ElementTree as ET
import sys

if(len(sys.argv) !=2):
    print("usage: \"python query.py topicFiles.xml\"")
    sys.exit(1)

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
        "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
        "query": data,
        "size": size,
        "index": ["cw12"],
    }

    return requests.post(url, data=request_data).json()


topics = get_titles(sys.argv[1])
out = open("output", "w")

answers = []
for topic in topics:
    answers.append(api(topic, 5))
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
