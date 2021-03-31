#!/usr/bin/python
import os
from pathlib import Path

import re
import pandas
import requests
from simpletransformers.classification import (ClassificationModel)
import xml.etree.ElementTree as ET

def retrievingFullDocuments(uuid):
    url = 'https://www.chatnoir.eu/cache'

    request_data = {
        "uuid": uuid,
        "index": "cw12",
        "raw": "raw",
        "plain": "plain",
    }

    data = requests.get(url, request_data).text
    data = re.sub('<[^>]+>', '', data)
    data = re.sub('\n', '', data)
    data = re.sub('&[^;]+;', '', data)

    # print(data)
    return data

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer

def pandas_to_qrel(data: pandas.DataFrame, save_dir: Path, name: str = 'Undefined') -> None:
    out = open(save_dir / name, "w")
    topic_ids = data['TopicID'].unique()

    for topic_id in topic_ids:
        rank = 1
        data_for_topic = data.loc[data['TopicID'] == topic_id].sort_values(by=['predictions'],ascending=False)
        data_for_topic = data_for_topic.drop_duplicates(subset=["TrecID"])

        for index, row in data_for_topic.iterrows():
            buffer = row['TopicID'], "Q0", row['TrecID'], rank, row['predictions'], name
            out.write(" ".join(map(str, buffer)) + "\n")
            rank += 1


if __name__ == "__main__":

    topics = Path("/home/jan/Uni/AdvancedInformationRetrival/touche/Bert_Docker/res/topics-task-2.xml")
    chatnoir_res = Path("/home/jan/Uni/AdvancedInformationRetrival/touche/ChatNoir/res/100.csv")
    fulltext = Path("/home/jan/Uni/AdvancedInformationRetrival/touche/Bert_Docker/res/UUID-Text.csv")
    name = "Bert"
    model_dir = Path("/home/jan/Uni/AdvancedInformationRetrival/touche/Bert_Docker/saves/CrossValidation")
    save_dir = Path("/home/jan/Uni/AdvancedInformationRetrival/touche/ndcg")

    topics = get_titles(topics)
    id = 1
    topic_df = []
    for topic in topics:
        buffer = id, topic
        topic_df.append(buffer)
        id = id + 1

    topic_df = pandas.DataFrame(topic_df, columns=['TopicID', 'Topic'])
    chatnoir_df = pandas.read_csv(chatnoir_res)
    fulltext_df = pandas.read_csv(fulltext)
    data = pandas.merge(topic_df, chatnoir_df, how="inner", on=["Topic"])
    data = pandas.merge(data, fulltext_df, how="inner", left_on=['TrecID', 'UUID'], right_on=['trec_id', 'uuid'])
    print(data)


    predictions = []
    for i in range(1, 51):
        path = model_dir / ("Topic" + str(i))
        data_for_topic = data.loc[data['TopicID'] == i]
        model = model = ClassificationModel(
                            "bert", path
                        )

        output = []
        for index, row in data_for_topic.iterrows():
            predictions, raw_outputs = model.predict(
                [
                    [
                        row['Topic'],
                        retrievingFullDocuments(row['UUID']),
                    ]
                ]
            )

            output.append(predictions[0])

        data_for_topic['predictions'] = output
        print("[INFO] predicting Topic "+ str(i))

    predictions_df = pandas.concat(predictions)
    print(predictions_df)
    data = pandas.merge(data, predictions_df, how="inner", left_on=['Topic', 'FullText'], right_on=['text_a', 'text_b'])
    print(data)


    pandas_to_qrel(data, save_dir, name)
