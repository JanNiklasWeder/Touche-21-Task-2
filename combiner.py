#!/usr/bin/python
import logging
import os
from pathlib import Path

import pandas

from src.preprocessing.QueryExpansion import QueryExpansion
from src.postprocessing.SVM import svm
from src.scores.Bert_Docker.load_bert import Bert

from src.preprocessing.PreProcessing import PreProcessing
from src.merging.Merge import Merge

from src.scores.PageRank.OpenPageRank import OpenPageRank
from src.scores.ArgumentScore.ArgumentScore import ArgumentScore
from src.scores.SimilarityScore.SimilarityScore import SimilarityScore


from src.utility.ChatNoir.querys import ChatNoir, get_titles, df_add_text
from src.utility.auth.auth import Auth


class Combine:

    def __init__(self, topics_xml: str, workingDirectory: Path):

        topics = get_titles(topics_xml)
        topics["query"] = topics["topic"]
        topics["tag"] = "original"

        self.topics = topics
        self.wD = Path(workingDirectory)

        try:
            with open(self.wD / "data/noarg_topics.txt") as f:
                noarg_topics = f.read()
            self.noargs = [e.strip() for e in noarg_topics.split(",")] #for task 2020 only topic 6 and 13 do not need argument score
        except FileNotFoundError:
            logging.warning("No noarg_topics.txt found assuming it is empty")
            self.noargs = []

    def preprocess(self, lemma: bool = True):

        # ToDo order is not directly changeable
        # ToDo split lemma and stopword into single functions

        # PREPROCESSING to EXPANSION
        preproc = PreProcessing(self.topics)

        if lemma:
            preproc.lemma()

        buffer = preproc.getQuery()
        self.topics = buffer
        self.topics = self.topics.sort_index()
        self.topics = self.topics.reset_index(drop=True)
        
    def query_expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        expansion = QueryExpansion(self.topics)
        self.topics = expansion.expansion(relation=relation, synonyms=synonyms, sensevec=sensevec, embedded=embedded) 
        
    def run(self,
            preprocessing: bool = True,
            query_expansion: bool = True,
            weights: dict = {'original': 2, 'annotation': 1.5, 'sensevec': 1, 'embedded': 1, 'preprocessing': 1,
                             'syns': 1}, method: str = 'max',
            score_argumentative: bool = True,
            underscore: float = 0.55,
            score_trustworthiness: bool = True,
            lemma: bool = True,
            relation: bool = True, synonyms: bool = True, sensevec: bool = True, embedded: bool = True,
            score_similarity: bool = True,
            score_bert: bool = True,
            dry_run: bool = False,
            test:bool = True,
            query_size: int = 100,
           transform_model_name: str = 'gpt'):
        pandas.set_option('display.max_columns', None)

        if test:
            query_size = 3
        elif dry_run:
            query_size = 1000

        # create identification str for the svm
        saved_args = locals()
        unique_str = ""
        for key, value in saved_args.copy().items():
            if type(value) is bool and key.startswith("score") and value is True:
                unique_str = unique_str + key.lstrip("score")

        # REMOVE ATTRIBUTE stopwords
        if preprocessing and not dry_run:
            self.preprocess(lemma)

        if query_expansion and not dry_run:
            self.query_expansion(relation=relation, synonyms=synonyms, sensevec=sensevec, embedded=embedded)

        # request to chatnoir
        auth = Auth(self.wD)
        chatnoir = ChatNoir(auth.get_key("ChatNoir"), self.wD)

        if dry_run:
            df = chatnoir.get_response(self.topics, query_size)

            qrels = pandas.read_csv(self.wD / "data/touche2020-task2-relevance-withbaseline.qrels",
                                    sep=" ",
                                    names=["TopicID", "Spacer", "TrecID", "qrel"])

            qrels = qrels[["TopicID", "TrecID", "qrel"]]

            df = pandas.merge(qrels, df, how="inner", on=["TrecID", "TopicID"])
            
        else:
            df = chatnoir.get_response(self.topics, query_size)
            df = df.sort_values(by='Score_ChatNoir', ascending=False).reset_index(drop=True)

        #Merging responses if multiple trec_ids
        original_topics = list(self.topics['topic'].unique())
        df = Merge(original_topics, df, weights, method).merging()

        if score_argumentative:
            #add "needArgument", needArgument must be added manually.
            df['needArgument'] = [tp not in self.noargs for tp in list(df['topic'])] #return true if topic not in noargs, otherwise false
            targer_model_name = "classifyWD"
            df = ArgumentScore(df, targer_model_name, underscore).get_argument_score()

        if score_similarity:
            df = SimilarityScore(list(self.topics['topic'].unique()), df, transform_model_name) #topics here is the list of orginal titles

        if score_trustworthiness:
            page_rank = OpenPageRank(auth.get_key("OpenPageRank"))
            df['target_hostname'] = df['target_hostname'].str.replace('www\.', '', regex=True)
            df = page_rank.df_add_score(df)


        if score_bert:
            df = df_add_text(df)
            bert = Bert(self.wD / "data/bert/")
            df = bert.df_add_score(df)

        if dry_run:
            svm.train(df, unique_str,self.wD)
            print("Finished dry run")
            return
        else:
            df = svm.df_add_score(df, unique_str,self.wD)

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
        'original': 5,
        'annotation': 4,
        'sensevec': 3,
        'embedded': 3,
        'preprocessing': 2,
        'syns': 1},
                        help="Adding weights for merging responses")

    parser.add_argument("-M", "--MergeMethod", type=str, default='max',
                        help="Method for merging responses (default: %(default)s)")

    parser.add_argument("-A", "--Argumentative", type=bool, default=True,
                        help="Activate the argumentative score (default: %(default)s)")
    parser.add_argument("-B", "--Bert", action='store_true', default=False,
                        help="Activate the computation of a score via Bert (default: %(default)s)")

    parser.add_argument("-U", "--Underscore", type=float, default=0.55,
                        help="Underscore for argument score (default: %(default)s)")

    parser.add_argument("-T", "--Trustworthiness", type=bool, default=True,
                        help="Activate the Trustworthiness score (default: %(default)s)")
    parser.add_argument("-v", "--loglevel", type=str, default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the detail of the log events (default: %(default)s)")
    parser.add_argument("--DryRun", action='store_true', default=False,
                        help="Start dry run to train the svm (default: %(default)s)")
    args = parser.parse_args()

    logging.basicConfig(filename="run.log", level=args.loglevel, filemode='w')

    wd = os.getcwd()

    combiner = Combine(args.Topics, wd)


    combiner.run(preprocessing=args.Preprocessing,
                 query_expansion=args.QueryExpansion,
                 weights=args.WeightsMerging,
                 method=args.MergeMethod,
                 score_argumentative=args.Argumentative,
                 underscore=args.Underscore,
                 score_trustworthiness=args.Trustworthiness,
                 score_bert=args.Bert,
                 dry_run=args.DryRun)
