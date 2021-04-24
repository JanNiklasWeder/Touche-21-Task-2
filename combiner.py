#!/usr/bin/python
import logging
import os
import zipfile
from pathlib import Path
import wget as wget

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
from src.utility import df2trec


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
            self.noargs = [e.strip() for e in
                           noarg_topics.split(",")]  # for task 2020 only topic 6 and 13 do not need argument score
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

    def query_expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool = False,
                        embedded: bool = False):
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
            test: bool = True,
            query_size: int = 100,
            transform_model_name: str = 'gpt',
            out_file: Path = None):
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

        # Merging responses if multiple trec_ids
        original_topics = list(self.topics['topic'].unique())
        df = Merge(original_topics, df, weights, method).merging()

        if score_argumentative:
            # add "needArgument", needArgument must be added manually.
            df['needArgument'] = [tp not in self.noargs for tp in
                                  list(df['topic'])]  # return true if topic not in noargs, otherwise false
            targer_model_name = "classifyWD"
            df = ArgumentScore(df, targer_model_name, underscore).get_argument_score()

        if score_similarity:
            df = SimilarityScore(list(self.topics['topic'].unique()), df,
                                 transform_model_name).get_similarity_scores()  # topics here is the list of orginal titles

        if score_trustworthiness:
            page_rank = OpenPageRank(auth.get_key("OpenPageRank"))
            df['target_hostname'] = df['target_hostname'].str.replace('www\.', '', regex=True)
            df = page_rank.df_add_score(df)

        if score_bert:
            df = df_add_text(df,self.wD)

            path = self.wD / "data/bert/"

            if not path.is_dir():
                logging.info("Download of the Bert model this may take a moment.")
                path.mkdir(parents=True, exist_ok=True)
                path = path.parent / "bert.zip"
                wget.download(
                    "https://cloud.uzi.uni-halle.de/owncloud/index.php/s/Zcz1VnGkJwGSeGo/download?path=%2F&files=",
                    str(path))

                with zipfile.ZipFile(path, "r") as zip_ref:
                    zip_ref.extractall(path.parent)
                path.unlink(missing_ok=True)
                path = path.parent / "bert"

            bert = Bert(path)
            df = bert.df_add_score(df)

        path = self.wD / "data/svm"
        if dry_run:
            svm.train(df, unique_str, path)
            logging.info("Finished dry run")
        else:
            df = svm.df_add_score(df, unique_str, path)
            if out_file is None:
                df2trec.write(df, tag=unique_str, path=self.wD / "out.trec")
            else:
                df2trec.write(df, tag=unique_str, path=out_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str,
                        help="File path to 'topics-task-2.xml'")
    parser.add_argument("-p", "--Preprocessing", action='store_true', default=False,
                        help="Activate the Preprocessing (default: %(default)s)")
    parser.add_argument("-e", "--QueryExpansion", action='store_true', default=False,
                        help="Activate the QueryExpansion (default: %(default)s)")
    '''
    NEED WEIGHTS FOR MERGING
    '''

    parser.add_argument("-w", "--WeightsMerging", 
                        type=str, 
                        default="2; 1.5; 1; 1; 1; 1",
                        metavar='',
                        help="Adding six weights for merging responses: original; annotation; sensevec; embedded; preprocessing; syns")
  
    parser.add_argument("-m", "--MergeMethod", type=str, default='max', metavar='',
                        help="Method for merging responses (default: %(default)s)")

    parser.add_argument("-a", "--Argumentative", action='store_true', default=False,
                        help="Activate the argumentative score (default: %(default)s)")

    parser.add_argument("-s", "--Similarity", action='store_true', default=False,
                        help="Activate the similarity score (default: %(default)s)")

    parser.add_argument("-b", "--Bert", action='store_true', default=False,
                        help="Activate the computation of a score via Bert (default: %(default)s)")

    parser.add_argument("-u", "--Underscore", type=float, default=0.55, metavar='',
                        help="Underscore for argument score (default: %(default)s)")

    parser.add_argument("-t", "--Trustworthiness", action='store_true', default=False,
                        help="Activate the Trustworthiness score (default: %(default)s)")

    parser.add_argument("-v", "--loglevel", type=str, default="WARNING", metavar='',
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the detail of the log events (default: %(default)s)")

    parser.add_argument("-d", "--DryRun", action='store_true', default=False,
                        help="Start dry run to train the svm (default: %(default)s)")

    parser.add_argument("-o", "--output", type=str, default=str(Path.cwd()) + "out.trec", metavar='',
                        help="File path where the output should be stored (default: ./out.trec)")

    parser.add_argument("--size", type=int, default=100, metavar='',
                        help="Size of the requested reply from ChatNoir (default: %(default)s)")

    args = parser.parse_args()
    logging.basicConfig(filename="run.log", level=args.loglevel, filemode='w')

    wd = os.getcwd()

    combiner = Combine(args.Topics, wd)

    weights = [float(e.strip()) for e in args.WeightsMerging.split(";")]
    tags = ['original', 'annotation', 'sensevec', 'embedded', 'preprocessing', 'syns']
    try:
        weightsDictionary = {tags[i]:weights[i] for i in range(0,len(tags))}
    except Exception as inst: #when user input doesn't match the required length of weights
        print("ERROR:" + str(inst))
        print("incorrected input's format, using default weights")
        weightsDictionary = {'original': 2, 'annotation': 1.5, 'sensevec': 1, 'embedded': 1, 'preprocessing': 1,
                             'syns': 1}
    
    combiner.run(preprocessing=args.Preprocessing,
                 query_expansion=args.QueryExpansion,
                 weights=weightsDictionary,
                 method=args.MergeMethod,
                 score_argumentative=args.Argumentative,
                 underscore=args.Underscore,
                 score_similarity=args.Similarity,
                 score_trustworthiness=args.Trustworthiness,
                 score_bert=args.Bert,
                 dry_run=args.DryRun,
                 query_size=args.size)
