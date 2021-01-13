#!/usr/bin/python
import argparse
import requests
import os
import xml.etree.ElementTree as ET
import sys
#import main_preprocessing
import main_query_api
import main_preprocessing
'''
if(len(sys.argv) !=4):
    print("usage: \"python query.py topics-task-2.xml n_topics size lemma sw syn\"")
    sys.exit(1)
'''

parser = argparse.ArgumentParser()

parser.add_argument('xml')
parser.add_argument('n_topics')
parser.add_argument('size')
parser.add_argument('lemma')
parser.add_argument('sw')
parser.add_argument('syn')
parser.add_argument('comparative_relation')
parser.add_argument('weights')
parser.add_argument('trec_id_cal')

args = parser.parse_args()

assert os.path.exists(args.xml)
file = args.xml
n_topics = args.n_topics
size = args.size
lemma = args.lemma
sw = args.sw
syn = args.syn
relation = args.comparative_relation
weights = args.weights
trec_id_cal = args.trec_id_cal
def main():
    topics = main_query_api.get_titles(file)
    weights_as_string = weights
    for e in [';','.']:
        weights_as_string = weights_as_string.replace(e,"")
    out = open("files_2/output_ntopics_"+str(n_topics)+"_"+str(lemma)+"_"+str(sw)+"_"+str(syn)+"_"+str(relation)+"_"+str(weights_as_string)+"_"+str(trec_id_cal)+".run", "w")
    answers = []
    for topic in topics:
        #print("Getting response for", topic)
        answers.append(main_query_api.expanded_api(topic, size))
        
        #topic as annotations represent
        #answers.append(main_query_api.base_chatnoir_api(topic, size))

    # assumption about topic id and correct rank | both not validated
    topicId = 1

    for topic in answers:
        #print(topic)
        rank = 1
        for response in topic['results']:
            buffer = topicId, "Q0", response['trec_id'], rank, response['score'], "JackSparrowVanilla"
            #print(buffer)
            out.write(" ".join(map(str, buffer)) + "\n")
            rank += 1
        topicId += 1

if __name__ == "__main__":
    sys.exit(main())
# print(subprocess.check_output(args=["/home/roberto/Programms/trec_eval-master/trec_eval", "-m", "ndcg",
#                                    "/home/roberto/Programms/trec_eval-master/test/qrels.test",
#                                    "/home/roberto/Programms/trec_eval-master/test/results.test"]))