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
parser.add_argument('comparative_relation') #annotation = True
parser.add_argument('weights') #weights
parser.add_argument('trec_id_cal') #max
parser.add_argument('sense') #using similar words from sense2vec
#parser.add_argument('weighted_score') 
#weighted_score: true means that weights are used to make new score for ranking
#weighted_score: false means that weights are used get one of documents with same id, original score for ranking
'''
xml: topic datei
n_topics: 50
size: 
lemma = True
Stopwords= False
Synonym = True
Annotation = True
Weights
trec_id_cal: duplikate trec_id -> max/average

run main_retrieval.py topics-task-2.xml 50 15 True False True True 2.25;1.75;1 max
'''
args = parser.parse_args()

assert os.path.exists(args.xml)
file = args.xml
n_topics = args.n_topics
#n_topics = 15
size = args.size
lemma = args.lemma
sw = args.sw
syn = args.syn
relation = args.comparative_relation
weights = args.weights
trec_id_cal = args.trec_id_cal
sense = args.sense
sort_by_updated_weighted_score = False #args.weighted_score

def main():
    topics = main_query_api.get_titles(file)
    weights_as_string = weights
    for e in [';','.']:
        weights_as_string = weights_as_string.replace(e,"")
    out = open("data/output_ntopics_"+str(n_topics)+"_"+str(lemma)+"_"+str(sw)+"_"+str(syn)+"_"+str(relation)+"_"+str(weights_as_string)+"_"+str(trec_id_cal)+"_"+str(sense)+".run", "w")
    answers = []
    index = 1
    for topic in topics:
        print("Getting response for", topic)
        answers.append(main_query_api.expanded_api(topic, size))
        index = index + 1
        #break
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
