#!/usr/bin/python
import logging
import pickle
from pathlib import Path
from typing import List

import joblib
import numpy
import numpy as np
import pandas
from sklearn import svm as sklearn_svm
from tqdm import tqdm


class Compound:
    def __init__(self, svm: sklearn_svm, mean_sd: pandas.DataFrame, scores: List):
        self.svm = svm
        self.mean_sd = mean_sd
        self.scores = scores

    @classmethod
    def from_file(cls, unique_str: str, path: Path = Path.cwd() / "data/svm"):
        path = path / unique_str
        svm = joblib.load(path / "svm.joblib")
        mean_sd = pandas.read_csv(path / "mean_sd.csv")

        with open(path / "scores.pickle", 'rb') as filehandle:
            scores = pickle.load(filehandle)

        return cls(svm, mean_sd, scores)

    @classmethod
    def new(cls):
        svm = sklearn_svm.SVR()
        return cls(svm, pandas.DataFrame(), [])

    def save(self, unique_str: str, path: Path = Path.cwd() / "data/svm"):
        logging.info("[INFO] Saving model ...")
        path = path / unique_str
        path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.svm, path / "svm.joblib")
        self.mean_sd.to_csv(path / "mean_sd.csv", index=False)

        with open(path / "scores.pickle", 'wb') as filehandle:
            pickle.dump(self.scores, filehandle)

    def train(self, data: pandas.DataFrame):

        df = data.filter(like='Score_').copy()
        self.scores = df.columns.values.tolist()
        frames = []

        for score in self.scores:
            mean = df[score].mean()
            sd = df[score].std(ddof=0)

            frames.append([score, mean, sd])
            df[score] = (df[score].to_numpy() - mean) / sd

            df[score].fillna(mean)

        self.mean_sd = pandas.DataFrame(frames, columns=['score', 'mean', 'sd'])

        input = []
        expected = []

        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc="Process data for the SVM"):
            input.append(df.loc[index, self.scores].tolist())
            expected.append(row['qrel'])

        self.svm.fit(input, expected)

    def predict(self, df: pandas.DataFrame()):
        df["final"] = numpy.nan

        for score in self.scores:
            row = self.mean_sd.loc[self.mean_sd['score'] == score]
            mean = row["mean"].values[0]
            sd = row["sd"].values[0]

            df[score] = (df[score].to_numpy() - mean) / sd

            df[score].fillna(mean, inplace=True)

        for index, row in tqdm(df.iterrows(),
                               total=df.shape[0],
                               desc="Compute final score via SVM:"):
            feature = numpy.array(row[self.scores]).reshape(1, -1)

            df.loc[index, "final"] = self.svm.predict(feature)

        return df


def train(df: pandas.DataFrame, unique_str: str, path: Path = None):
    svm = Compound.new()
    svm.train(df)

    if path is None:
        svm.save(unique_str=unique_str)
    else:
        svm.save(unique_str=unique_str,path = path)


def df_add_score(df: pandas.DataFrame, unique_str: str, path: Path = None):

    if path is None:
        svm = Compound.from_file(unique_str=unique_str)
    else:
        svm = Compound.from_file(unique_str=unique_str,path = path)
    output = svm.predict(df)

    return output
