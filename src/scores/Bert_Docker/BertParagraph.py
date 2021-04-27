#!/usr/bin/python
import collections
import gc
import multiprocessing

import wandb
from simpletransformers.classification import ClassificationModel, ClassificationArgs
from pathlib import Path
from datetime import datetime
from typing import List
import argparse
import torch

import logging
import os
import xml.etree.ElementTree as ET
import requests
import re
import pandas
import time

from auth.auth import Auth

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


def reset_wandb_env():
    exclude = {"WANDB_PROJECT", "WANDB_ENTITY", "WANDB_API_KEY"}
    for k, v in os.environ.items():
        if k.startswith("WANDB_") and k not in exclude:
            del os.environ[k]


def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter("title"):
        buffer.append(title.text.strip())
    return buffer


def simpleSearch(data, size):
    url = "https://www.chatnoir.eu/api/v1/_search"

    request_data = {"apikey": "--", "query": data, "size": size, "index": ["cw12"]}

    return requests.post(url, data=request_data).json()


def retrievingFullDocuments(uuid, index):
    url = "https://www.chatnoir.eu/cache"

    request_data = {"uuid": uuid, "index": index, "raw": "raw", "plain": "plain"}

    data = requests.get(url, request_data).text
    data = re.sub("<[^>]+>", "", data)
    data = re.sub("\n", "", data)
    data = re.sub("&[^;]+;", "", data)

    # print(data)
    return data


def kFoldSweep(num_folds):
    sweep_q = multiprocessing.Queue()
    workers = []

    for num in range(num_folds):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=Bert,
            kwargs=dict(
                sweep_q=sweep_q,
                worker_q=q,
                DataSet=topic_df,
                testTopicIDs=i,
                workingDirectory=wd,
                qrels=qrels,
                ID_UUID=ID_UUID,
            ),
        )
        p.start()
        workers.append(Worker(queue=q, process=p))

    sweep_run = wandb.init(project="CrossValidation")
    sweep_id = sweep_run.sweep_id or "unknown"
    sweep_url = sweep_run.get_sweep_url()
    project_url = sweep_run.get_project_url()
    sweep_group_url = "{}/groups/{}".format(project_url, sweep_id)
    sweep_run.notes = sweep_group_url
    sweep_run.save()
    sweep_run_name = sweep_run.name or sweep_run.id or "unknown"

    metrics = []
    for num in range(num_folds):
        worker = workers[num]
        # start worker
        worker.queue.put(
            WorkerInitData(
                sweep_id=sweep_id,
                num=num,
                sweep_run_name=sweep_run_name,
                config=dict(sweep_run.config),
            )
        )
        # get metric from worker
        result = sweep_q.get()
        # wait for worker to finish
        worker.process.join()
        # log metric to sweep_run
        metrics.append(result.val_accuracy)
    sweep_run.log(dict(val_accuracy=sum(metrics) / len(metrics)))
    wandb.join()

    def accuracy_score(true_in, pred_in):
        accuracy = 0
        size = len(true_in)

        if size == 1:
            true_in = [true_in]
            pred_in = [pred_in]

        for true, pred in zip(true_in, pred_in):

            if true == 0:
                if pred == 0:
                    accuracy = +1

            elif true == 1:
                if pred == 1:
                    accuracy = +1
                elif pred == 2:
                    accuracy = +0.8

            else:  # true == 2
                if pred == 1:
                    accuracy = +0.8
                elif pred == 2:
                    accuracy = +1

        if accuracy == 0:
            return accuracy

        return accuracy / size


class Bert:
    def __init__(
        self,
        sweep_q,
        worker_q,
        DataSet,
        testTopicIDs: List[int],
        name: str,
        workingDirectory: Path,
        qrels: Path,
        ID_UUID: Path,
        WandBKey: str,
    ):

        os.environ["WANDB_API_KEY"] = WandBKey
        reset_wandb_env()

        self.cuda_available = torch.cuda.is_available()
        self.wD = workingDirectory
        self.name = name
        qrels = pandas.read_csv(
            qrels, sep=" ", names=["TopicID", "Spacer", "trec_id", "Score"]
        )
        IDS = pandas.read_csv(ID_UUID, names=["uuid", "trec_id"])

        buffer = pandas.merge(IDS, qrels, how="inner", on=["trec_id"])
        buffer = pandas.merge(buffer, DataSet, how="inner", on=["TopicID"])

        self.data = self.uuidToText(buffer)

        frames = []

        logging.info("Prepearing test data")

        if isinstance(testTopicIDs, int):
            self.test_df = pandas.DataFrame(
                self.data.loc[self.data["TopicID"] == testTopicIDs]
            )
        else:
            for i in testTopicIDs:
                buffer = self.data.loc[self.data["TopicID"] == i]
                frames.append(buffer)

            self.test_df = pandas.concat(frames)
        self.train_df = pandas.concat([self.data, self.test_df]).drop_duplicates(
            keep=False
        )
        self.model = self.train(WandBKey)

    def __init__(
        self,
        DataSet,
        testTopicIDs: List[int],
        name: str,
        workingDirectory: Path,
        qrels: Path,
        ID_UUID: Path,
        WandBKey: str,
    ):
        os.environ["WANDB_API_KEY"] = WandBKey
        reset_wandb_env()

        self.cuda_available = torch.cuda.is_available()
        self.wD = workingDirectory
        self.name = name
        qrels = pandas.read_csv(
            qrels, sep=" ", names=["TopicID", "Spacer", "trec_id", "Score"]
        )
        IDS = pandas.read_csv(ID_UUID, names=["uuid", "trec_id"])

        buffer = pandas.merge(IDS, qrels, how="inner", on=["trec_id"])
        buffer = pandas.merge(buffer, DataSet, how="inner", on=["TopicID"])

        self.data = self.uuidToText(buffer)

        frames = []

        logging.info("Prepearing test data")

        if isinstance(testTopicIDs, int):
            self.test_df = pandas.DataFrame(
                self.data.loc[self.data["TopicID"] == testTopicIDs]
            )
        else:
            for i in testTopicIDs:
                buffer = self.data.loc[self.data["TopicID"] == i]
                frames.append(buffer)

            self.test_df = pandas.concat(frames)
        self.train_df = pandas.concat([self.data, self.test_df]).drop_duplicates(
            keep=False
        )
        self.model = self.train(WandBKey)

        # ToDo init for loading model without training

        # check if UUID-Text exists else create

    def uuidToText(self, data: pandas.DataFrame):
        if Path("res/UUID-Text.csv").is_file():
            print("[INFO] UUID-Text.csv found. Loading...")
            Documents = pandas.read_csv(
                "res/UUID-Text.csv", names=["uuid", "trec_id", "FullText"]
            )
        else:
            print(
                "[INFO] UUID-Text.csv not found at './res/touche20-task2-docs-ID-UUID'. Creating ..."
            )
            fullText = []

            print("[INFO] Retrieving Documents")
            size = data.shape[0]

            for index, row in data.iterrows():
                uuid = row["uuid"]
                trec_id = row["trec_id"]

                for x in range(10):  #
                    try:
                        buffer = uuid, trec_id, retrievingFullDocuments(uuid, "cw12")
                        fullText.append(buffer)
                        str_error = None
                    except Exception as str_error:
                        pass

                    if str_error:
                        time.sleep(10)
                        if x == 9:
                            print("[ERROR] Cannot retrieve Documents. Exiting ...")
                            exit(1)
                    else:
                        break

                if index % 100 == 0:
                    print("[PROGRESS] ", index, " of ", size)

            Documents = pandas.DataFrame(
                fullText, columns=["uuid", "trec_id", "FullText"]
            )
            print("[INFO] Saving UUID-Text.csv")
            Documents.to_csv(path_or_buf="./res/UUID-Text.csv", index=False)

        return pandas.merge(Documents, data, how="inner", on=["trec_id", "uuid"])

    def train(
        self,
        WandBKey: str,
        freezeEncoder: bool = True,
        modelName: str = "bert",
        modelType: str = "bert-base-cased",
    ):
        # wandb.init(
        #    project="CrossValidation",
        #    notes="Test-Topic :" + self.name)

        train_df = self.train_df[["Topic", "FullText", "Score"]]
        train_df.rename(
            columns={"Topic": "text_a", "FullText": "text_b", "Score": "labels"},
            inplace=True,
        )

        # calculating pos_weights based on trainings data
        pos_weights = train_df["labels"].value_counts(normalize=True).sort_index()
        logging.info("Frequencies are:\n" + pos_weights)
        pos_weights = pos_weights.tolist()
        pos_weights = [1 - element for element in pos_weights]
        logging.info("Pos_weights are:\n" + pos_weights)

        test_df = self.test_df[["Topic", "FullText", "Score"]]
        test_df.rename(
            columns={"Topic": "text_a", "FullText": "text_b", "Score": "labels"},
            inplace=True,
        )

        print(train_df)
        print(test_df)

        timeStamp = datetime.now()
        savePath = (
            "/app/Bert_Docker/saves/CrossValidationTopic" + self.name
        )  # + timeStamp.strftime("%d-%m-%Y_%H:%M")

        # create Folder if not exists
        output_dir = Path(savePath)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Optional model configuration
        model_args = ClassificationArgs()
        model_args.num_train_epochs = 30
        model_args.reprocess_input_data = True
        model_args.overwrite_output_dir = True
        model_args.wandb_project = "CrossValidation"
        model_args.save_eval_checkpoints = True
        model_args.save_model_every_epoch = False
        model_args.save_steps = -1
        model_args.output_dir = savePath

        # Freeze encoder Layers
        if freezeEncoder:
            model_args.train_custom_parameters_only = True
            model_args.custom_parameter_groups = [
                {"params": ["classifier.weight", "classifier.bias"], "lr": 1e-4}
            ]

        # Create a ClassificationModel

        model = ClassificationModel(
            modelName,
            modelType,
            use_cuda=self.cuda_available,
            num_labels=3,
            pos_weight=pos_weights,
            args=model_args,
        )
        # model = ClassificationModel("bert", "./saves/")

        exit(1)
        # Train the model
        print("[INFO] Starting training")
        time.sleep(5)
        model.train_model(train_df)
        model.train_model()

        # Evaluate the model
        print("[INFO] Evaluating the model")
        time.sleep(5)

        result, model_outputs, wrong_predictions = model.eval_model(test_df)

        output = []
        for index, row in test_df.iterrows():
            predictions, raw_outputs = model.predict([[row["text_a"], row["text_b"]]])
            output.append(predictions)

        test_df["predictions"] = output
        print(type(output))
        # model.save_model(savePath)
        savePath = savePath + "/data"
        output_dir = Path(savePath)
        output_dir.mkdir(parents=True, exist_ok=True)

        train_df.to_csv(path_or_buf=savePath + "/train.csv", index=True)
        test_df.to_csv(path_or_buf=savePath + "/test.csv", index=True)

        return model

    def predictions(self, data: pandas.DataFrame):
        # Make predictions with the model
        print("[INFO] Starting predictions")
        time.sleep(5)
        data["BertScore"] = ""

        # predictData = data[['Topic', 'FullText','uuid','trec_id']]
        # predictData.rename(columns={'Topic': "text_a", 'FullText': "text_b"}, inplace=True)

        output = []
        for index, row in data.iterrows():
            predictions, raw_outputs = self.model.predict(
                [[row["Topic"], row["FullText"]]]
            )

            row["BertScore"] = predictions

        return data


def use_bert(**kwargs):
    run = wandb.init(project="CrossValidation", notes="Test-Topic : " + i, reinit=True)

    model = Bert(**kwargs)
    del model
    return


if __name__ == "__main__":

    # Prepearing CrossValidation

    parser = argparse.ArgumentParser()
    parser.add_argument("Topics", type=str, help="File path to 'topics-task-2.xml'")
    parser.add_argument(
        "Qrels",
        type=str,
        help="File path to 'touche2020-task2-relevance-withbaseline.qrels'",
    )
    parser.add_argument(
        "ID_UUID", type=str, help="File path to 'touche2020-task2-docs-ID_UUID'"
    )
    parser.add_argument(
        "-v",
        "--loglevel",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the shown log events (default: %(default)s)",
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    wd = Path(os.getcwd())
    wd = wd.parent

    auth = Auth(wd)
    os.environ["WANDB_API_KEY"] = auth.get_key("WandB")

    Worker = collections.namedtuple("Worker", ("queue", "process"))
    WorkerInitData = collections.namedtuple(
        "WorkerInitData", ("num", "sweep_id", "sweep_run_name", "config")
    )
    WorkerDoneData = collections.namedtuple("WorkerDoneData", ("val_accuracy"))

    topics = get_titles(args.Topics)
    id = 1
    topic_df = []
    for topic in topics:
        buffer = id, topic
        topic_df.append(buffer)
        id = id + 1

    topic_df = pandas.DataFrame(topic_df, columns=["TopicID", "Topic"])
    name = "CrossValidationTopic"
    qrels = args.Qrels
    ID_UUID = args.ID_UUID
    WandBKey = auth.get_key("WandB")

    for i in range(1, 51):
        multiprocessing.set_start_method("spawn")
        q = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=Bert,
            kwargs={
                "DataSet": topic_df,
                "testTopicIDs": i,
                "name": name + str(i),
                "workingDirectory": wd,
                "qrels": qrels,
                "ID_UUID": ID_UUID,
                "WandBKey": WandBKey,
            },
        )
        p.start()
        logging.info("Started run with test topic : " + str(i))
        p.join()
        p.close()

        print(i)
        with Bert(
            DataSet=topic_df,
            testTopicIDs=i,
            name=name + str(i),
            workingDirectory=wd,
            qrels=qrels,
            ID_UUID=ID_UUID,
            WandBKey=WandBKey,
        ):
            time.sleep(1)

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
