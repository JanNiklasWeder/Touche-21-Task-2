#!/usr/bin/python
import argparse
import requests
import os
import xml.etree.ElementTree as ET
import sys
#import m_preprocessing
import main_expansion_query_api
import main_argument_score_2
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
parser.add_argument('targer_model')
parser.add_argument('underscore')
args = parser.parse_args()

assert os.path.exists(args.xml)
file = args.xml
n_topics = args.n_topics
size = args.size
lemma = args.lemma
sw = args.sw
syn = args.syn
targer_model = args.targer_model
underscore = args.underscore

def main():
    topics = main_expansion_query_api.get_titles(file) #topics = [(topic, true/false) for n_topics]
    '''
    true: comparative topics
    false: superlative oder other topics
    '''
    str_score=str(underscore).replace('.','')
    out = open("files_local/expanded_output_ntopics_"+str(n_topics)+"_"+str(size)+"_"+str(lemma)+"_"+str(sw)+"_"+str(syn)+"_"+str(targer_model)+"_underscore_"+str_score+".run", "w")
    answers = []
    for topic, arg_value in topics:
        #answers.append(main_expansion_query_api.chatnoir_api(topic, size, arg_value)) 
        answers.append(main_expansion_query_api.api(topic, size, arg_value)) 
        print("Getting response for", topic)


    # assumption about topic id and correct rank | both not validated
    topicId = 1

    for topic in answers:
        #print(topic)
        rank = 1
        for response in topic['results']:
            buffer = topicId, "Q0", response['trec_id'], rank, response['score'], "JackSparrowVanilla"#, response['title'], response['snippet']
            #print(buffer)
            out.write("\t".join(map(str, buffer)) + "\n")
            rank += 1
        topicId += 1

if __name__ == "__main__":
    sys.exit(main())
# print(subprocess.check_output(args=["/home/roberto/Programms/trec_eval-master/trec_eval", "-m", "ndcg",
#                                    "/home/roberto/Programms/trec_eval-master/test/qrels.test",
#                                    "/home/roberto/Programms/trec_eval-master/test/results.test"]))
