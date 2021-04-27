#!/usr/bin/python
import pandas
import spacy
import re

# from spacy.lang.en.stop_words import STOP_WORDS
# from typing import List, Union
# import logging


class PreProcessing:
    def __init__(self, query: pandas.DataFrame):
        self.querys = query
        self.nlp = spacy.load("en_core_web_md")

    # ToDo add logging
    def lemma(self) -> None:
        result = []
        regex = re.compile("[@_!#$%^&*()<>?/\|}{~:,]")
        for index, row in self.querys.iterrows():

            buffer = self.nlp(row["query"])
            tmp = ""
            for token in buffer:
                if (regex.search(token.lemma_) is None) is False:
                    tmp = tmp + token.lemma_
                else:
                    tmp = tmp + " " + token.lemma_
            result.append([row["TopicID"], row["topic"], tmp, "preprocessing"])

        self.querys = pandas.concat(
            [
                self.querys,
                pandas.DataFrame(result, columns=["TopicID", "topic", "query", "tag"]),
            ]
        )

    # def stopword(self) -> None:
    #    result = []
    #    for index, row in self.querys.iterrows():
    #        title = [w for w in row['query'].split(" ") if w not in STOP_WORDS]
    #        result.append([row['topic']," ".join(title)])
    #     self.querys = pandas.concat([ pandas.DataFrame(result, columns=['topic', 'query']),self.querys ])

    def getQuery(self):
        return self.querys


if __name__ == "__main__":
    query = [
        "What is the difference between sex and love?",
        "What is the difference between sex and love?",
        "Which is better, a laptop or a desktop?",
    ]

    print("Org. query:")

    for i in query:
        print(i)

    preproc = PreProcessing(query)

    print("Lemma:")
    for i in preproc.lemma():
        print(i)

    print("StopWord:")
    for i in preproc.stopword():
        print(i)
