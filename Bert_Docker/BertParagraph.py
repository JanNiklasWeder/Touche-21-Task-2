#!/usr/bin/python

from simpletransformers.classification import (ClassificationModel, ClassificationArgs)
from pathlib import Path
from datetime import datetime
import logging
import os
import sys
import xml.etree.ElementTree as ET
import requests
import re
import pandas as pd
import time
import random

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

if len(sys.argv) != 5:
    print("usage: 'python BertParagraph.py <topicFiles.xml> <qrels> <SelectTrainByTopic> <ModelName>'")
    sys.exit(1)


def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []

    for title in root.iter('title'):
        buffer.append(title.text.strip())
    return buffer


def simpleSearch(data, size):
    url = 'https://www.chatnoir.eu/api/v1/_search'

    request_data = {
        "apikey": "--",
        "query": data,
        "size": size,
        "index": ["cw12"],
    }

    return requests.post(url, data=request_data).json()


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

    # print(data)
    return data


SelectByTopic = sys.argv[3]
projectName = sys.argv[4]
topics = get_titles(sys.argv[1])
print(topics)
qrels = pd.read_csv(sys.argv[2], sep=" ", names=["TopicID", "Spacer", "trec_id", "Score"])

answers = []
texts = []
TopicID = 1
results = []

# check if ID-UUID exists
if Path('res/touche20-task2-docs-ID-UUID').is_file():
    print("[INFO] Reading touche20-task2-docs-ID-UUID")
    IDS = pd.read_csv('res/touche20-task2-docs-ID-UUID', names=["uuid", "trec_id"])
else:
    print("[ERROR] Please provide touche20-task2-docs-ID-UUID in the location './res/touche20-task2-docs-ID-UUID'")
    exit(1)

print(qrels)
print(IDS)

data = pd.merge(IDS, qrels, how="inner", on=["trec_id"])
size = IDS.shape[0]

# check if UUID-Text exists else create
if Path('res/UUID-Text.csv').is_file():
    print("[INFO] UUID-Text.csv found. Loading...")
    Documents = pd.read_csv('res/UUID-Text.csv', names=['uuid', 'trec_id', 'FullText'])
else:
    print("[INFO] UUID-Text.csv not found at './res/touche20-task2-docs-ID-UUID'. Creating ...")
    fullText = []

    print("[INFO] Retrieving Documents")
    for index, row in IDS.iterrows():
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

    Documents = pd.DataFrame(fullText, columns=['uuid', 'trec_id', 'FullText'])
    print("[INFO] Saving UUID-Text.csv")
    Documents.to_csv(path_or_buf="./res/UUID-Text.csv", index=False)

data = pd.merge(Documents, qrels, how="inner", on=["trec_id"])

id = 1
topic_df = []
for topic in topics:
    buffer = id, topic
    topic_df.append(buffer)
    id = id + 1

topic_df = pd.DataFrame(topic_df, columns=['TopicID', 'Topic'])
data = pd.merge(data, topic_df, how="inner", on=["TopicID"])

train_data = []
validate_data = []
test_data = []

print(data)

# Separate trainings test and evaluation data
if SelectByTopic:
    numbers = []
    frames = []
    for i in range(4):
        while True:
            number = round(random.uniform(0, 50))
            if not (number in numbers):
                numbers.append(number)
                break

        buffer = data.loc[data['TopicID'] == number]
        print(number)
        print(buffer)
        frames.append(buffer)
    test_df = pd.concat(frames)
    data = pd.concat([data, test_df]).drop_duplicates(keep=False)

    frames = []
    numbers = []
    for i in range(2):
        while True:
            number = round(random.uniform(0, 50))
            if not (number in numbers):
                numbers.append(number)
                break

        buffer = data.loc[data['TopicID'] == number]
        print(number)
        print(buffer)
        frames.append(buffer)

    validate_df = pd.concat(frames)
    data = pd.concat([data, validate_df]).drop_duplicates(keep=False)

    train_df = data

else:
    test_df = data.sample(frac=0.10)
    data = pd.concat([data, test_df]).drop_duplicates(keep=False)

    validate_df = data.sample(frac=0.05)
    data = pd.concat([data, validate_df]).drop_duplicates(keep=False)

    train_df = data

train_df = train_df[['Topic', 'FullText', 'Score']]
train_df.rename(columns={'Topic': "text_a", 'FullText': "text_b", 'Score': "labels"}, inplace=True)

validate_df = validate_df[['Topic', 'FullText', 'Score']]
validate_df.rename(columns={'Topic': "text_a", 'FullText': "text_b", 'Score': "labels"}, inplace=True)

test_df = test_df[['Topic', 'FullText', 'Score']]
test_df.rename(columns={'Topic': "text_a", 'FullText': "text_b", 'Score': "labels"}, inplace=True)

print(train_df)
print(test_df)
print(validate_df)

# Optional model configuration
os.environ['WANDB_API_KEY'] = '--'
model_args = ClassificationArgs()
model_args.num_train_epochs = 20
model_args.reprocess_input_data = True
model_args.overwrite_output_dir = True
model_args.wandb_project = projectName

#Freeze encoder Layers
model_args.train_custom_parameters_only = True
model_args.custom_parameter_groups = [
    {
        "params": ["classifier.weight"],
        #"lr": 1e-3,
    },
    {
        "params": ["classifier.bias"],
        #"lr": 1e-3,
        #"weight_decay": 0.0,
    },
]

# Create a ClassificationModel
model = ClassificationModel('bert', 'bert-base-cased', use_cuda=False, num_labels=3, args=model_args)
#model = ClassificationModel("bert", "./saves/")


# Train the model
print("[INFO] Starting training")
time.sleep(5)
model.train_model(train_df)

# Evaluate the model
print("[INFO] Evaluating the model")
time.sleep(5)

result, model_outputs, wrong_predictions = model.eval_model(
    test_df
)

timeStamp = datetime.now()
savePath = "./saves/" + projectName + timeStamp.strftime("%d-%m-%Y_%H:%M")
model.save_model(savePath)
savePath=savePath+"/data"
train_df.to_csv(path_or_buf=savePath+"/train.csv", index=True)
test_df.to_csv(path_or_buf=savePath+"/test.csv", index=True)
validate_df.to_csv(path_or_buf=savePath+"/validate.csv", index=True)

# Make predictions with the model
print("[INFO] Starting predictions")
time.sleep(5)
output =[]
for index, row in validate_df.iterrows():
    predictions, raw_outputs = model.predict(
        [
            [
                row['text_a'],
                row['text_b'],
            ]
        ]
    )
    buffer = predictions, "Bert: ", raw_outputs, "Expected: ", row['labels']
    output.append(buffer)
    print(buffer)

# Save evaluations
output = pd.concat(output)
output.to_csv(path_or_buf=savePath+"/evaluation.csv", index=True)