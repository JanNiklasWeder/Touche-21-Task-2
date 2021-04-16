#!/usr/bin/python
import io
import logging
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import torch
from simpletransformers.config.model_args import ClassificationArgs
from tqdm import tqdm

logging.basicConfig(level=logging.WARNING)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

import pandas
from simpletransformers.classification import ClassificationModel


class Bert:
    def __init__(self, path_to_model: Path):
        model_args = ClassificationArgs()

        cache_dir = path_to_model / "cache/"
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_args.cache_dir = cache_dir

        self.model = ClassificationModel(
            "bert", path_to_model, use_cuda=torch.cuda.is_available(), args=model_args
        )

    def predict(self, topic: str, text: str):
        prediction, raw_output = self.model.predict(
            [
                [
                    topic,
                    text,
                ]
            ]
        )

        logging.info("Raw prediction was : " + str(raw_output))
        return prediction

    def df_add_score(self, df: pandas.DataFrame):
        combinations = df[['topic', 'FullText']].drop_duplicates()
        print(combinations)

        for index, row in tqdm(combinations.iterrows(),
                               total=combinations.shape[0],
                               desc="Bert score progress:"):
            f = io.StringIO()
            with redirect_stderr(f):
                combinations.loc[index, 'Score_Bert'] = self.predict(row["topic"], row["FullText"])

        result = df.merge(combinations, how="left", on=["topic", "FullText"])
        return result
