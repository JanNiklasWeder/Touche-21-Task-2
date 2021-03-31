#!/usr/bin/python

from typing import List
import spacy
import string
from nltk.corpus import wordnet
from spacy.lang.en.stop_words import STOP_WORDS
import random


class QueryExpansion:

    def __init__(self, query: List[str], top_syns: int = 5):
        self.original_query = query
        self.nlp = spacy.load("en_core_web_sm")
        self.top_syns = top_syns

    # Query Expansion
    def expansion(self, relation: bool = False, synonyms: bool = False):
        result = []

        if relation:
            result = [*result, *self.get_comparation_superlation_nouns_from_original_data()]

        if synonyms:
            result = [*result, *self.synonyms()]

        # ToDo combine original or return only new ones
        return result

    def synonyms(self) -> List[str]:
        result = []

        for query in self.original_query:
            new_title = self.remove_punc(query)
            syn_pro_title = list()
            temp = new_title
            new_title = self.nlp(new_title)
            for token in new_title:
                syn_token = self.find_syns_word(token)
                syn_pro_title.extend(
                    [syn for syn in list(set(syn_token)) if
                     syn != str(token.text)])  # distinct and remove the same words
            # print(syn_pro_title)
            # synonyms_by_titles.writelines(" ".join(list(set(syn_pro_title))) + "\n")
            # ToDo temp(org) + syns or only syns?
            result.append(temp + " " + " ".join(list(set(syn_pro_title))))

        return result

    def remove_punc(self, query: str) -> str:
        table = str.maketrans(dict.fromkeys(string.punctuation))
        title = query.translate(table)
        return str(title)

    def find_syns_word(self, token: str) -> str:
        syn_token = []
        if (token.pos_ == "NOUN"):
            # ToDo automate wordnet install
            for synset in wordnet.synsets(token.lemma_):
                for lemma in synset.lemmas()[:self.top_syns]:  # top 5 synonyms
                    if "_" not in lemma.name():  # not include the words with _ ex: basketball_game
                        syn_token.append(lemma.name())
                    else:
                        for w in lemma.name().split("_"):
                            if w not in STOP_WORDS:
                                syn_token.append(
                                    w)  # add words with _ to two words ex. laptop_computer -> laptop and computer
        syn_token = [w for w in syn_token if w != " " and len(w) != 0]

        # ToDo remove random influence
        if len(syn_token) > 5:
            return random.sample(syn_token,
                                 k=5)  # after top 5 synonyms + splited words -> long titles -> reducing the syns random with 5
        else:
            return syn_token

    def get_comparation_superlation_nouns_from_original_data(self):
        result =[]

        for query in self.original_query:
            nouns_as_string = []
            doc = self.nlp(query)
            annotations = ['CC', 'CD',
                           'JJ', 'JJR', 'JJS',
                           'RB', 'RBR', 'RBS',
                           'NN', 'NNS', 'NNP', 'NNPS',
                           'VB']
            for token in doc:
                if token.tag_ in annotations:
                    nouns_as_string.append(token.text)
            result.append(' '.join(nouns_as_string))
        return result

    # ToDo Merge


if __name__ == "__main__":
    query = ["What is the difference between sex and love?",
             "What is the difference between sex and love?",
             "Which is better, a laptop or a desktop?"]

    print("Org. query:")

    for i in query:
        print(i)

    expansion = QueryExpansion(query)

    print("None:")
    for i in expansion.expansion():
        print(i)

    print("Relation:")
    for i in expansion.expansion(relation=True):
        print(i)

    print("Synonyms:")
    for i in expansion.expansion(synonyms=True):
        print(i)

    print("Both:")
    for i in expansion.expansion(True, True):
        print(i)
