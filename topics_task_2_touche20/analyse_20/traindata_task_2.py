from pandas import DataFrame
import numpy as np

def read_train(file):
    f = open(file, "r")
    train_data=[]
    for x in f:
        x = x.split(" ")
        train_data.append([int(x[0]),x[2],x[3][0]])
    train_data = DataFrame(train_data, columns=["topic_id", "doc_id", "rel_rank"]) 
    return train_data

def train_by_topic(train_data,topic_id):
    df_topic = train_data[train_data["topic_id"]==topic_id].reset_index(drop=True)
    return df_topic
file="touche2020-task2-relevance-withbaseline.qrels"
train_data = read_train(file)
nResults_by_topic=[]

for topic_id in train_data.topic_id.unique():
    nResults_by_topic.append(train_by_topic(train_data, topic_id).shape[0])
    #get results
    '''
    array([34, 33, 32, 36, 36, 39, 37, 35, 35, 39, 32, 37, 36, 41, 33, 35, 32,
       41, 33, 37, 31, 32, 32, 32, 34, 33, 36, 32, 37, 33, 34, 49, 36, 27,
       34, 44, 21, 36, 41, 41, 38, 36, 27, 35, 39, 37, 35, 40, 45, 43])
    '''