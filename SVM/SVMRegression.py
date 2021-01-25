import random

import numpy
import pandas
from sklearn import svm
from joblib import dump, load

import ChatNoir.querys
import PageRank.OpenPageRank

qrels = pandas.read_csv('../res/touche2020-task2-relevance-withbaseline.qrels', sep=" ",
                        names=["TopicID", "Spacer", "TrecID", "QrelScore"])

qrels = qrels[["TopicID", "TrecID", "QrelScore"]]

querysize = 1000
data = ChatNoir.querys.get_response(querysize)[['TrecID', 'UUID', 'target_hostname', 'Score']]
data = pandas.merge(qrels, data, how="inner", on=["TrecID"])

# Score PageRank
# QrelScore

X = []
Y = []
numbers = []
frames = []

print("[INFO] Prepearing test data")
for i in range(2):
    while True:
        number = round(random.uniform(0, 50))
        if not (number in numbers):
            numbers.append(number)
            break

    buffer = data.loc[data['TopicID'] == number]
    frames.append(buffer)
test_df = pandas.concat(frames)
data = pandas.concat([data, test_df]).drop_duplicates(keep=False)

size = data.shape[0]
print("[INFO] Prepearing training data")
for index, row in data.iterrows():
    pagerank = PageRank.OpenPageRank.OpenPageRank(row['target_hostname'])
    buffer = (row['Score'], pagerank)
    X.append(buffer)
    buffer = row['QrelScore']
    Y.append(buffer)
    if index % 100 == 0:
        print("[PROGRESS] ", index, " of ", size)

print(X)
print(Y)

print("[INFO] Training model ...")
regr = svm.SVR()
regr.fit(X, Y)

print("[INFO] Saving model ...")
dump(regr, '../SVM/res/save.joblib')

training_data = []

print("[INFO] Testing ...")
for index, row in test_df.iterrows():
    pagerank = PageRank.OpenPageRank.OpenPageRank(row['target_hostname'])
    feature = numpy.array([row['Score'], pagerank]).reshape(1,-1)

    expected_value = row['QrelScore']
    prediction = regr.predict(feature)
    buffer = row['Score'], pagerank, expected_value, prediction
    training_data.append(buffer)
    print("[INFO] Prediction:", prediction, "Expected value:", expected_value)

training_data = pandas.DataFrame(training_data, columns=['ChatNoirScore', 'OpenPageRank', 'QrelScore', 'Prediction'])
training_data.to_csv(path_or_buf="./res/training.csv")
# Potential Loading
# regr = load('../SVM/res/save.joblib')


