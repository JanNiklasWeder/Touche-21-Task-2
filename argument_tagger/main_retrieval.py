#!/usr/bin/python
import argparse
import requests
import os
import xml.etree.ElementTree as ET
import sys
#import m_preprocessing
import expansion_query_api
import argument_score_2
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

args = parser.parse_args()

assert os.path.exists(args.xml)
file = args.xml
n_topics = args.n_topics
size = args.size
lemma = args.lemma
sw = args.sw
syn = args.syn

def main():
    topics = expansion_query_api.get_titles(file) #topics = [(topic, true/false) for n_topics]
    '''
    true: comparative topics
    false: superlative oder other topics
    '''
    out = open("expanded_output_ntopics_"+str(n_topics)+"_"+str(lemma)+"_"+str(sw)+"_"+str(syn), "w")
    answers = []
    for topic, arg_value in topics:
        answers.append(expansion_query_api.api(topic, size, arg_value)) 
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

if __name__ == "__main__":
    sys.exit(main())
# print(subprocess.check_output(args=["/home/roberto/Programms/trec_eval-master/trec_eval", "-m", "ndcg",
#                                    "/home/roberto/Programms/trec_eval-master/test/qrels.test",
#                                    "/home/roberto/Programms/trec_eval-master/test/results.test"]))
