#!/usr/bin/python
import logging
import os
from pathlib import Path

from ChatNoir.querys import ChatNoir, get_titles
from PreProcessing.PreProcessing import PreProcessing
from QueryExpansion.QueryExpansion import QueryExpansion
from auth.auth import Auth


class Combine:

    def __init__(self, topics_xml: str, workingDirectory: Path):
        self.topics = get_titles(topics_xml)
        self.wD = Path(workingDirectory)

    def preprocess(self, lemma: bool = True, stopword: bool = True):
        preproc = PreProcessing(self.topics)

        if lemma:
            preproc.lemma()

        if stopword:
            preproc.stopword()

        # ToDo ask if append replace or what else
        self.topics = [*self.topics, *preproc.getQuery()]

    def query_expansion(self, relation: bool = True, synonyms: bool = True):
        expansion = QueryExpansion(self.topics)

        self.topics = [*self.topics, *expansion.expansion(relation=relation, synonyms=synonyms)]

    def argumentative(self):
        print("Hey")

    def trusworthiness(self):
        print("Hey")

    def run(self, preprocessing: bool = True, query_expansion: bool = True, argumentative: bool = True,
            trustworthiness: bool = True, lemma: bool = True, stopword: bool = True,
            relation: bool = True, synonyms: bool = True):

        if preprocessing:
            self.preprocess(lemma, stopword)

        if query_expansion:
            self.query_expansion(relation=relation, synonyms=synonyms)

        # request to chatnoir
        auth = Auth(self.wD)
        chatnoir = ChatNoir(auth.get_key("ChatNoir"), self.wD)

        df = chatnoir.get_response(self.topics, 100)

        '''
        if argumentative:
            # create argumentative score for every request
            print("Hey")
        '''

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

    logging.basicConfig(filename="run.log", level=args.loglevel)

    wd = os.getcwd()

    combiner = Combine(args.Topics, wd)
    combiner.run(args.Preprocessing, args.QueryExpansion, args.Argumentative, args.Trustworthiness)

