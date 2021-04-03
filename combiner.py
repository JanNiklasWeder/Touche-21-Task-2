#!/usr/bin/python
import logging
import os
from pathlib import Path

import pandas

from src.preprocessing.query_expansion.QueryExpansion import QueryExpansion
from src.preprocessing.PreProcessing import PreProcessing
from src.merging.Merge import Merge

from src.ChatNoir.ChatNoir import ChatNoir


from src.scores.PageRank.OpenPageRank import OpenPageRank

from src.utility.ChatNoir.querys import ChatNoir, get_titles
from src.utility.auth.auth import Auth


class Combine:

    def __init__(self, topics_xml: str, workingDirectory: Path):

        topics = get_titles(topics_xml)
        df = pandas.DataFrame(list(zip(topics, topics)), columns=['topic', 'query', 'tag'])

        self.topics = df
        self.wD = Path(workingDirectory)

    def preprocess(self, lemma: bool = True, stopword: bool = True):

        # ToDo order is not directly changeable
        # ToDo split lemma and stopword into single functions
        
        # PREPROCESSING to EXPANSION
        preproc = PreProcessing(self.topics)

        if lemma:
            preproc.lemma()

        if stopword:
            preproc.stopword()

        buffer = preproc.getQuery()
        self.topics = buffer

    def query_expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        expansion = QueryExpansion(self.topics)

        self.topics = [*self.topics, *expansion.expansion(relation=relation, synonyms=synonyms, sensevec=sensevec, embedded=embedded)]

    def argumentative(self):
        #must define which topic need argumentative score
        print("Hey")

    def trusworthiness(self):
        print("Hey")
    def merging_responses(self,df_resp):
        return 0

    def run(self, 
    preprocessing: bool = True, 
    query_expansion: bool = True, 
    weights: dict = {'original':5,  'annotation':4,'sensevec': 3, 'embedded':3,'preprocessing':2,'syns':1}, 
    method: str = 'max', argumentative: bool = True,
    trustworthiness: bool = True, lemma: bool = True, stopword: bool = True,
    relation: bool = True, synonyms: bool = True, sensevec: bool=True, embedded: bool=True):

        #if preprocessing:
        #    self.preprocess(lemma, stopword)

        if query_expansion:
            self.query_expansion(relation=relation, synonyms=synonyms, sensevec=sensevec, embedded=embedded)

        # request to chatnoir
        #auth = Auth(self.wD)
        #chatnoir = ChatNoir(auth.get_key("ChatNoir"), self.wD)

<<<<<<< HEAD
        chatnoir = ChatNoir(self.topics, size=100) #topics as dataframe
        chatnoir_df = chatnoir.get_response()
=======
        df = chatnoir.get_response(self.topics, 100)

        '''
        if argumentative:
            # create argumentative score for every request
            print("Hey")
        '''
        print(df)
        if trustworthiness:
            page_rank = OpenPageRank(auth.get_key("OpenPageRank"))
            df['target_hostname']=df['target_hostname'].str.replace('www\.', '', regex=True)
            df = page_rank.df_add_score(df)
>>>>>>> af0bfa2582223991590bfb76e99c378db8e26bad

        #MERGING AFTER RESPONSES FOR EACH TOPIC
        merged_df = Merge(topics, chatnoir_df, weights, method=method).merging() #topics is not self.topics
        
        pandas.set_option('display.max_columns', None)
<<<<<<< HEAD
        print(merged_df)
=======

        if trustworthiness:
            while True:
                break
        print(df)
>>>>>>> af0bfa2582223991590bfb76e99c378db8e26bad


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str,
                        help="File path to 'topics-task-2.xml'")
    parser.add_argument("-P", "--Preprocessing", type=bool, default=True,
                        help="Activate the Preprocessing (default: %(default)s)")
    parser.add_argument("-E", "--QueryExpansion", type=bool, default=True,
                        help="Activate the QueryExpansion (default: %(default)s)")
    '''
    NEED WEIGHTS FOR MERGING
    '''
    parser.add_argument("-W", "--WeightsMerging", type=dict, default={
        'original':5,  
        'annotation':4,
        'sensevec': 3, 
        'embedded':3,
        'preprocessing':2,
        'syns':1},
                        help="Adding weights for merging responses")

    parser.add_argument("-M", "--MergeMethod", type=str, default='max',
                        help="Method for merging responses (default: %(default)s)")

    parser.add_argument("-A", "--Argumentative", type=bool, default=True,
                        help="Activate the argumentative score (default: %(default)s)")
    parser.add_argument("-T", "--Trustworthiness", type=bool, default=True,
                        help="Activate the Trustworthiness score (default: %(default)s)")
    parser.add_argument("-v", "--loglevel", type=str, default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the detail of the log events (default: %(default)s)")
    args = parser.parse_args()

    logging.basicConfig(filename="run.log", level=args.loglevel, filemode='w')

    wd = os.getcwd()

    combiner = Combine(args.Topics, wd)
    combiner.run(args.Preprocessing, args.QueryExpansion, args.WeightsMerging, args.MergeMethod, args.Argumentative, args.Trustworthiness)
