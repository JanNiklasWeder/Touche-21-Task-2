#!/usr/bin/python
import logging
import os
from pathlib import Path

import pandas

from scores.Bert_Docker.load_bert import Bert
from src.preprocessing.query_expansion.QueryExpansion import QueryExpansion
from src.preprocessing.PreProcessing import PreProcessing

from src.scores.PageRank.OpenPageRank import OpenPageRank

from src.utility.ChatNoir.querys import ChatNoir, get_titles, df_add_text
from src.utility.auth.auth import Auth


class Combine:

    def __init__(self, topics_xml: str, workingDirectory: Path):

        topics = get_titles(topics_xml)
        df = pandas.DataFrame(list(zip(topics, topics)), columns=['topic', 'query'])

        self.topics = df
        self.wD = Path(workingDirectory)

    def preprocess(self, lemma: bool = True, stopword: bool = True):

        # ToDo order is not directly changeable
        # ToDo split lemma and stopword into single functions
        preproc = PreProcessing(self.topics)

        if lemma:
            preproc.lemma()

        if stopword:
            preproc.stopword()

        buffer = preproc.getQuery()
        self.topics = buffer

    def query_expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        expansion = QueryExpansion(self.topics)

        self.topics = [*self.topics, *expansion.expansion(relation=relation, synonyms=synonyms)]

    def argumentative(self):
        print("Hey")

    def run(self, preprocessing: bool = True, query_expansion: bool = True, argumentative: bool = True,
            trustworthiness: bool = True, lemma: bool = True, stopword: bool = True,
            relation: bool = True, synonyms: bool = True, bert:bool = True):

        if preprocessing:
            self.preprocess(lemma, stopword)

        #if query_expansion:
        #    self.query_expansion(relation=relation, synonyms=synonyms)

        # request to chatnoir
        auth = Auth(self.wD)
        chatnoir = ChatNoir(auth.get_key("ChatNoir"), self.wD)

        df = chatnoir.get_response(self.topics, 100)

        '''
        if argumentative:
            # create argumentative score for every request
            print("Hey")
        '''
        if trustworthiness:
            page_rank = OpenPageRank(auth.get_key("OpenPageRank"))
            df['target_hostname']=df['target_hostname'].str.replace('www\.', '', regex=True)
            df = page_rank.df_add_score(df)

        pandas.set_option('display.max_columns', None)

        if bert:
            df = df_add_text(df)
            print(df)
            bert = Bert(self.wD / "data/bert/")
            df = bert.df_add_score(df)



        print(df)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str,
                        help="File path to 'topics-task-2.xml'")
    parser.add_argument("-P", "--Preprocessing", type=bool, default=True,
                        help="Activate the Preprocessing (default: %(default)s)")
    parser.add_argument("-E", "--QueryExpansion", type=bool, default=True,
                        help="Activate the QueryExpansion (default: %(default)s)")
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
    combiner.run(args.Preprocessing, args.QueryExpansion, args.Argumentative, args.Trustworthiness)
