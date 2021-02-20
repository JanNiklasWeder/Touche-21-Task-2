import argparse
import logging
import os
import random
from pathlib import Path
from typing import List

import numpy
import pandas
from sklearn import svm
from joblib import dump, load
from tqdm import tqdm

import PageRank.OpenPageRank
from ChatNoir.querys import ChatNoir, get_titles
from auth.auth import Auth


class SVR:
    def __init__(self, DataSet, numberOfTestTopics: int, name: str, workingDirectory: Path):
        frames = []
        numbers = []

        logging.info("Prepearing test data")
        # ToDo check the variable
        for i in range(numberOfTestTopics):
            while True:
                number = round(random.uniform(0, 50))
                if not (number in numbers):
                    numbers.append(number)
                    break

            buffer = data.loc[data['TopicID'] == number]
            frames.append(buffer)

        self.test_df = pandas.concat(frames)
        self.train_df = pandas.concat([DataSet, self.test_df]).drop_duplicates(keep=False)
        self.X = []
        self.Y = []
        self.regr = svm.SVR()
        self.name = name
        self.wD = workingDirectory
        self.savePath = self.wD / "SVM" / "res" / self.name

    def __init__(self, DataSet, testTopicIDs: int, name: str, workingDirectory: Path):

        self.test_df = pandas.DataFrame(DataSet.loc[DataSet['TopicID'] == testTopicIDs])
        self.train_df = pandas.concat([DataSet, self.test_df]).drop_duplicates(keep=False)
        self.X = []
        self.Y = []
        self.regr = svm.SVR()
        self.name = name
        self.wD = workingDirectory
        self.savePath = self.wD / "SVM" / "res" / self.name

    def __init__(self, DataSet, testTopicIDs: List[int], name: str, workingDirectory: Path):
        frames = []

        logging.info("Prepearing test data")
        for i in range(testTopicIDs):
            buffer = DataSet.loc[DataSet['TopicID'] == i]
            frames.append(buffer)

        self.test_df = pandas.concat(frames)
        self.train_df = pandas.concat([DataSet, self.test_df]).drop_duplicates(keep=False)
        self.X = []
        self.Y = []
        self.regr = svm.SVR()
        self.name = name
        self.wD = workingDirectory
        self.savePath = self.wD / "SVM" / "res" / self.name

    def prepData(self):
        DataSet = self.train_df
        logging.info("Prepearing training data")

        with tqdm(total=DataSet.shape[0], desc='Progress') as pbar:
            for index, row in DataSet.iterrows():

                # ToDo read Pagerank from DataSet
                pagerank = PageRank.OpenPageRank.OpenPageRank(row['target_hostname'])
                buffer = (row['Score'], pagerank)
                self.X.append(buffer)

                buffer = row['QrelScore']
                self.Y.append(buffer)
                pbar.update(1)

    def train(self):
        logging.info("[INFO] Training model ...")
        self.regr.fit(self.X, self.Y)

    def save(self):
        logging.info("[INFO] Saving model ...")
        dump(self.regr, self.savePath / "save.joblib")

    def test(self,save: bool = True ):
        test_data = []

        logging.info("[INFO] Testing ...")
        for index, row in self.test_df.iterrows():
            # ToDo read Pagerank from DataSet
            pagerank = PageRank.OpenPageRank.OpenPageRank(row['target_hostname'])
            feature = numpy.array([row['Score'], pagerank]).reshape(1, -1)

            expected_value = row['QrelScore']
            prediction = self.regr.predict(feature)
            buffer = row['Score'], pagerank, expected_value, prediction
            test_data.append(buffer)
            logging.debug("Prediction:", prediction, "Expected value:", expected_value)

        if save:
            training_data = pandas.DataFrame(test_data,
                                             columns=['ChatNoirScore', 'OpenPageRank', 'QrelScore', 'Prediction'])
            training_data.to_csv(path_or_buf=self.savePath / "training.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str,
                        help="File path to 'topics-task-2.xml'")
    parser.add_argument("Qrels", type=str,
                        help="File path to 'touche2020-task2-relevance-withbaseline.qrels'")
    parser.add_argument("-v", "--loglevel", type=str, default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the shown log events (default: %(default)s)")

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    qrels = pandas.read_csv(args.Qrels, sep=" ",
                            names=["TopicID", "Spacer", "TrecID", "QrelScore"])

    qrels = qrels[["TopicID", "TrecID", "QrelScore"]]

    querysize = 1000

    wd = Path(os.getcwd())
    wd = wd.parent

    auth = Auth(wd)
    keyChatNoir = auth.get_key("ChatNoir")

    requests = get_titles(args.Topics)

    chatnoir = ChatNoir(keyChatNoir, wd)

    data = chatnoir.get_response(requests, querysize)[['TrecID', 'UUID', 'target_hostname', 'Score']]
    data = pandas.merge(qrels, data, how="inner", on=["TrecID"])

    logging.info("Starting CrossValidation")

    for i in range(1, len(requests) + 1):
        svr = SVR(data, testTopicIDs=i, name="CrossValidationTopic_" + str(i), workingDirectory=wd)
        svr.prepData()
        svr.train()
        svr.test(True)

# Potential Loading
# regr = load('../SVM/res/save.joblib')
