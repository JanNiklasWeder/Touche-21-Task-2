#!/usr/bin/python
import sys
from pathlib import Path
import pandas
import PageRank.OpenPageRank
import ChatNoir.querys

if (len(sys.argv) != 3):
    print("usage: \"python query.py <RunName> <ChatNoirQuerySize>\"")
    sys.exit(1)

topics = ChatNoir.querys.get_titles("./res/topics-task-2.xml")
querySize = sys.argv[2]

if Path('./ChatNoir/res/' + querySize).is_file():
    print("[INFO] Loading ChatNoir query size: ", querySize)
    Data = pandas.read_csv('./ChatNoir/res/'+ querySize, names=['TopicID', 'TrecID', 'UUID', 'target_hostname', 'Score'])
else:
    print("[INFO] Query Size not cached requesting ...")
    answers = []
    topicID = 1
    for topic in topics:
        print("[INFO] Getting response for", topic)
        response = ChatNoir.querys.api(topic, querySize)['results']
        print(response)
        for answer in response:
            buffer = topicID, answer['trec_id'], answer['uuid'], answer['target_hostname'], answer['score']
            answers.append(buffer)

    Data = (pandas.DataFrame(answers, columns=['TopicID', 'TrecID', 'UUID', 'target_hostname', 'Score']))
    Data.to_csv(path_or_buf="./ChatNoir/res/" + querySize, index=False)

for index, row in Data.iterrows():
    print(row['target_hostname'])
    print(PageRank.OpenPageRank.OpenPageRank( row['target_hostname'] )['response'])