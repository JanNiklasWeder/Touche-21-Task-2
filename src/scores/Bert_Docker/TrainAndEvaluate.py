#!/usr/bin/python
import gc
import logging
import multiprocessing
import os
import subprocess
import time
from pathlib import Path

import requests
import re

import torch
from typing import List

import wandb
from simpletransformers.classification import (ClassificationModel, ClassificationArgs)
import pandas
import xml.etree.ElementTree as ET

from auth.auth import Auth

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


def accuracy_score(true_in, pred_in):
    accuracy = 0
    size = len(true_in)

    if size == 1:
        true_in = [true_in]
        pred_in = [pred_in]

    for true, pred in zip(true_in, pred_in):

        if true == 0:
            if pred == 0:
                accuracy = + 1
            elif pred == 1:
                accuracy = + .1

        elif true == 1:
            if pred == 1:
                accuracy = + 1
            elif pred == 2:
                accuracy = + .8
            else:
                accuracy = + .1

        else:  # true == 2
            if pred == 1:
                accuracy = + .8
            elif pred == 2:
                accuracy = + 1

    if accuracy == 0:
        return accuracy

    return accuracy / size


def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer


def retrievingFullDocuments(uuid, index):
    url = 'https://www.chatnoir.eu/cache'

    request_data = {
        "uuid": uuid,
        "index": index,
        "raw": "raw",
        "plain": "plain",
    }

    data = requests.get(url, request_data).text
    data = re.sub('<[^>]+>', '', data)
    data = re.sub('\n', '', data)
    data = re.sub('&[^;]+;', '', data)

    return data


def uuidToText(data: pandas.DataFrame):
    if Path('res/UUID-Text.csv').is_file():
        print("[INFO] UUID-Text.csv found. Loading...")
        Documents = pandas.read_csv('res/UUID-Text.csv', names=['uuid', 'trec_id', 'FullText'])
    else:
        print("[INFO] UUID-Text.csv not found at './res/touche20-task2-docs-ID-UUID'. Creating ...")
        fullText = []

        print("[INFO] Retrieving Documents")
        size = data.shape[0]

        for index, row in data.iterrows():
            uuid = row['uuid']
            trec_id = row['trec_id']

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

        Documents = pandas.DataFrame(fullText, columns=['uuid', 'trec_id', 'FullText'])
        print("[INFO] Saving UUID-Text.csv")
        Documents.to_csv(path_or_buf="./res/UUID-Text.csv", index=False)

    return pandas.merge(Documents, data, how="inner", on=["trec_id", "uuid"])


def split_data(data: pandas.DataFrame, testTopicID) -> (pandas.DataFrame,pandas.DataFrame, List[float]):

    frames = []
    if isinstance(testTopicID, int):
        test_df = pandas.DataFrame(data.loc[data['TopicID'] == testTopicID])
    else:
        for i in testTopicID:
            buffer = data.loc[data['TopicID'] == i]
            frames.append(buffer)

        test_df = pandas.concat(frames)

    train_df = pandas.concat([data, test_df]).drop_duplicates(keep=False)

    train_df = train_df[['Topic', 'FullText', 'Score']]
    train_df.rename(columns={'Topic': "text_a", 'FullText': "text_b", 'Score': "labels"}, inplace=True)
    test_df = test_df[['Topic', 'FullText', 'Score']]
    test_df.rename(columns={'Topic': "text_a", 'FullText': "text_b", 'Score': "labels"}, inplace=True)

    # calculating pos_weights based on trainings data
    pos_weights = train_df['labels'].value_counts(normalize=True).sort_index()
    logging.info('Frequencies are:\n {}'.format(pos_weights.to_string()))
    pos_weights = pos_weights.tolist()
    pos_weights = [1 - element for element in pos_weights]
    logging.info("Pos_weights are:\n{}".format(' '.join(map(str, pos_weights))))

    return train_df, test_df, pos_weights


def train(train_df: pandas.DataFrame, test_df: pandas.DataFrame, save_dir: str, project_name: str, pos_weights: List[float] = None, testTopicID: int = None, use_custom_accuracy: bool = False,
          use_early_stopping: bool = False, freeze_encoder: bool = True):

    if testTopicID is None:
        save_path = Path(save_dir) / Path(project_name) / Path("Topic" + "undefined")
    else:
        save_path = Path(save_dir) / Path(project_name) / Path("Topic" + str(testTopicID))



    model_args = ClassificationArgs()
    model_args.num_train_epochs = 30
    model_args.reprocess_input_data = True
    model_args.overwrite_output_dir = True
    model_args.wandb_project = project_name
    model_args.save_eval_checkpoints = True
    model_args.save_model_every_epoch = False
    model_args.save_steps = -1
    model_args.output_dir = save_path
    model_args.sliding_window = True
    model_args.learning_rate = 1e-9
    model_args.train_batch_size = 4
    model_args.eval_batch_size = 4

    if use_early_stopping:
        model_args.use_early_stopping = True
        model_args.early_stopping_delta = 0.01
        model_args.early_stopping_metric = "mcc"
        model_args.early_stopping_metric_minimize = False
        model_args.early_stopping_patience = 3
        model_args.evaluate_during_training_steps = 1000

    # Freeze encoder Layers
    if freeze_encoder:
        model_args.train_custom_parameters_only = True
        model_args.custom_parameter_groups = [
            {
                "params": ['classifier.weight', 'classifier.bias'],
                "lr": 1e-5,
            },
        ]

    # Create a ClassificationModel

    if pos_weights is None:
        model = ClassificationModel(
            "bert",
            "bert-base-cased",
            use_cuda=torch.cuda.is_available(),
            num_labels=3,
            args=model_args)
    else:
        model = ClassificationModel(
            "bert",
            "bert-base-cased",
            use_cuda=torch.cuda.is_available(),
            num_labels=3,
            weight=pos_weights,
            args=model_args)

    # Train the model
    logging.info("Starting training")
    print(model.get_named_parameters())
    gpu_lock.acquire()

    if use_custom_accuracy:
        model.train_model(train_df, eval_df=test_df, acc=accuracy_score)
    else:
        print(1)
        # model.train_model(train_df, eval_df=test_df)

    # Evaluate the model
    logging.info("Evaluating the model")
    save = save_path / "hanging-1"
    save.mkdir(parents=True, exist_ok=True)

    if use_custom_accuracy:
        result, model_outputs, wrong_predictions = model.eval_model(
            test_df, acc=accuracy_score
        )
    else:
        print(1)
        # result, model_outputs, wrong_predictions = model.eval_model(test_df)

    save_path = save_path / "data"
    save_path.mkdir(parents=True, exist_ok=True)
    output = []
    save = save_path / "hanging0"
    save.mkdir(parents=True, exist_ok=True)

    for index, row in test_df.iterrows():
        predictions, raw_outputs = model.predict(
            [
                [
                    row['text_a'],
                    row['text_b'],
                ]
            ]
        )

        output.append(predictions[0])

    save = save_path / "hanging1"
    save.mkdir(parents=True, exist_ok=True)
    logging.info("Saving train and test data")
    test_df['predictions'] = output
    train_df.to_csv(path_or_buf=save_path / "train.csv", index=True)
    test_df.to_csv(path_or_buf=save_path / "test.csv", index=True)
    logging.info("Finisched")
    save = save_path / "hanging2"
    save.mkdir(parents=True, exist_ok=True)


def use_bert(**kwargs):
    run = wandb.init(
        project=kwargs.get("project_name"),
        notes="Test-Topic : " + str(kwargs.get("testTopicID")),
        reinit=True
    )

    train(**kwargs)
    run.finish()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()




if __name__ == "__main__":

    topics = Path("./res/topics-task-2.xml")
    qrels = Path("./res/touche2020-task2-relevance-withbaseline.qrels")
    ID_UUID = Path("./res/touche20-task2-docs-ID-UUID")
    save_dir = Path("./saves/")
    name = "other"

    current_dir = Path.cwd()
    subprocess.call(['chmod', '-R', '777', current_dir])
    topics = current_dir / topics
    qrels = current_dir / qrels
    ID_UUID = current_dir / ID_UUID
    save_dir = current_dir / save_dir
    auth = Auth(current_dir.parent)
    keyChatNoir = auth.get_key("WandB")
    logging.basicConfig(filename=current_dir / 'run.log', encoding='utf-8', level=logging.DEBUG)

    topics = get_titles(topics)
    id = 1
    topic_df = []
    for topic in topics:
        buffer = id, topic
        topic_df.append(buffer)
        id = id + 1

    topic_df = pandas.DataFrame(topic_df, columns=['TopicID', 'Topic'])
    qrels = pandas.read_csv(qrels, sep=" ", names=["TopicID", "Spacer", "trec_id", "Score"])
    IDS = pandas.read_csv(ID_UUID, names=["uuid", "trec_id"])
    buffer = pandas.merge(IDS, qrels, how="inner", on=["trec_id"])
    buffer = pandas.merge(buffer, topic_df, how="inner", on=["TopicID"])
    data = uuidToText(buffer)

    WandBKey = auth.get_key("WandB")
    os.environ['WANDB_API_KEY'] = WandBKey
    multiprocessing.set_start_method('spawn')

    #prepare first datasets
    gpu_lock = multiprocessing.Lock()
    train_df, test_df, pos_weights = split_data(data,1)
    p_old = multiprocessing.Process(target=use_bert,
                                    kwargs={"train_df": train_df,
                                            "test_df": test_df,
                                            "pos_weights": pos_weights,
                                            "testTopicID": i,
                                            "save_dir": save_dir,
                                            "project_name": name})

    for i in range(30, 51):
        p_new = multiprocessing.Process(target=use_bert,
                                    kwargs={"train_df": train_df,
                                            "test_df": test_df,
                                            "pos_weights": pos_weights,
                                            "testTopicID": i,
                                            "save_dir": save_dir,
                                            "project_name": name})
        p_new.start()
        train_df, test_df, pos_weights= split_data(data, i+1)
        p_old.join()
        gpu_lock.release()

        gc.collect()
        use_bert(kwargs={"data": data,
                         "testTopicID": i,
                         "save_dir": save_dir,
                         "project_name": name})
        print(i)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
    os.chmod(current_dir, 0o777)
