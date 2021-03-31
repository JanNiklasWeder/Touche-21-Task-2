#!/usr/bin/python
import pandas
import ChatNoir.querys
import PageRank.OpenPageRank
from pathlib import Path

qrels = pandas.read_csv('../res/touche2020-task2-relevance-withbaseline.qrels', sep=" ",
                        names=["TopicID", "Spacer", "TrecID", "QrelScore"])

querysize = 1000
data = ChatNoir.querys.get_response(querysize)

data = pandas.merge(qrels, data, how="inner", on=["TrecID"])
output = []
size = data.shape[0]

print("[INFO] Creating comparison.csv for PageRank and Qrels")
for index, row in data.iterrows():
    pagerank = PageRank.OpenPageRank.OpenPageRank(row['target_hostname'])
    buffer = (row['target_hostname'],row['QrelScore'],row['Score'], pagerank)
    output.append(buffer)

    if index % 100 == 0:
        print("[PROGRESS] ", index, " of ", size)

output = pandas.DataFrame(output, columns=['target_hostname', 'QrelScore', 'ChatNoirScore', 'pagerank'])


Path("./res").mkdir(parents=True, exist_ok=True)
output.to_csv("./res/ComparisonPageRank2Qrel-Size%s.csv" % querysize)
