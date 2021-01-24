#!/usr/bin/python
import sys
import pandas
import PageRank.OpenPageRank
import ChatNoir.querys

if (len(sys.argv) != 3):
    print("usage: \"python query.py <RunName> <ChatNoirQuerySize>\"")
    sys.exit(1)

querySize = sys.argv[2]

Data = ChatNoir.querys.get_response(querySize)

for index, row in Data.iterrows():
    print(row['target_hostname'])
    print(PageRank.OpenPageRank.OpenPageRank( row['target_hostname'] )['response'])