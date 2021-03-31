#!/usr/bin/python

import logging
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from typing import List, Union


class PreProcessing:

    def __init__(self, query: str):
        self.querys = [query]
        self.nlp = spacy.load("en_core_web_sm")

    def __init__(self, query: List[Union[str, str]]):
        self.querys = query
        self.nlp = spacy.load("en_core_web_sm")

    # ToDo add logging
    def lemma(self) -> None:
        result = []

        for query in self.querys:
            buffer = self.nlp(query)
            buffer = " ".join([str(token.lemma_) for token in buffer])
            result.append(buffer)

        self.querys = result

    def stopword(self) -> None:
        result = []

        for query in self.querys:
            title = [w for w in query.split(" ") if w not in STOP_WORDS]
            result.append(" ".join(title))

        self.querys = result

    def getQuery(self):
        return self.querys




if __name__ == "__main__":
    query = ["What is the difference between sex and love?",
             "What is the difference between sex and love?",
             "Which is better, a laptop or a desktop?"]

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
