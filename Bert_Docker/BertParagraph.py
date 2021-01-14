#!/usr/bin/python
from simpletransformers.classification import (ClassificationModel, ClassificationArgs)
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

retrieveDocuments=False
SelectByTopic = True

if (len(sys.argv) != 3):
    print("usage: \"python query.py topicFiles.xml qrels\"")
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
        "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
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


topics = get_titles(sys.argv[1])
print(topics)
qrels = pd.read_csv(sys.argv[2], sep=" ", names=["TopicID", "Spacer", "trec_id", "Score"])

answers = []
texts = []
TopicID = 1
results = []
IDS = pd.read_csv('touche20-task2-docs-ID-UUID', names=["uuid", "trec_id"])

print(qrels)
print(IDS)

data = pd.merge(IDS, qrels, how="inner", on=["trec_id"])
size = IDS.shape[0]

if retrieveDocuments:
    fullText = []

    print("[INFO] Retrieving Documents")
    for index,row in IDS.iterrows():
        uuid = row['uuid']
        trec_id = row['trec_id']
        buffer = uuid,trec_id,retrievingFullDocuments(uuid,"cw12")
        fullText.append(buffer)
        if index%100==0: print("[PROGRESS] ",index," of ", size)

    Documents = pd.DataFrame(fullText, columns=['uuid','trec_id', 'FullText'])

    Documents.to_csv(path_or_buf="UUID-Text.csv",index=False)
else:
    Documents = pd.read_csv('UUID-Text.csv', names=['uuid','trec_id', 'FullText'])

data = pd.merge(Documents, qrels, how="inner", on=["trec_id"])

id=0
topic_df = []
for topic in topics:
    buffer = id,topic
    topic_df.append(buffer)
    id=+1

topic_df = pd.DataFrame(topic_df, columns=['TopicID','Topic'])
data = pd.merge(data, topic_df, how="inner", on=["TopicID"])

frames = []
if SelectByTopic :
    for i in range(6):
        buffer =(data.loc[data['TopicID'] == random.uniform(0, size)])
        data[~data.isin(buffer)].dropna()
        frames.append(buffer)
        test_df = pd.concat(frames)
else:
    test_df = data.sample(frac=0.10)
    data[~data.isin(test_df)].dropna()
    validate_df = data.sample(frac=0.05)
    data[~data.isin(validate_df)].dropna()
    train_df = data

train_data = []
validate_data = []
test_data = []

print(data)


train_df = train_df[['Topic', 'FullText','Score']]
train_df.rename(columns={'Topic':"text_a", 'FullText':"text_b",'Score':"labels"}, inplace=True)

validate_df = validate_df[['Topic', 'FullText','Score']]
validate_df.rename(columns={'Topic':"text_a", 'FullText':"text_b",'Score':"labels"}, inplace=True)

test_df = test_df[['Topic', 'FullText','Score']]
test_df.rename(columns={'Topic':"text_a", 'FullText':"text_b",'Score':"labels"}, inplace=True)


print(train_df)
print(test_df)
print(validate_df)

# Optional model configuration
os.environ['WANDB_API_KEY'] = '5d78ab478578484b83144e9a4c3d2919391da815'
model_args = ClassificationArgs()
model_args.num_train_epochs = 1
model_args.reprocess_input_data = True
model_args.overwrite_output_dir = True
model_args.wandb_project = "project"

# Create a ClassificationModel
model = ClassificationModel('bert', 'bert-base-cased', use_cuda=False,num_labels=3, args=model_args)

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

# Make predictions with the model
print("[INFO] Starting predictions")
time.sleep(5)
for index, row in validate_df.iterrows():
    predictions, raw_outputs = model.predict(
        [
            [
                row['text_a'],
                row['text_b'],
            ]
        ]
    )
    print(predictions, "Bert: ", raw_outputs, "Expected: ", row['labels'])
