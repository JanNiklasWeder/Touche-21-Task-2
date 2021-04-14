#!/usr/bin/python

from typing import List
import en_core_web_sm
import string
#from nltk.corpus import wordnet
from spacy.lang.en.stop_words import STOP_WORDS
import random
import numpy as np

#packages to find similar words by wordembedding and sense2vec
from sense2vec import Sense2VecComponent 
from sense2vec import Sense2Vec #for standalone

#global tags

class QueryExpansion:

    def __init__(self, query: List[str], top_syns: int = 5, top_similar: int=2):
        self.original_query = query
        self.nlp = en_core_web_sm.load()
        self.top_syns = top_syns

        self.sense = self.nlp.add_pipe("sense2vec").from_disk("s2v_reddit_2015_md/s2v_old")
        self.standalone_sense = Sense2Vec().from_disk("./s2v_reddit_2015_md/s2v_old") #it is not dubplicated
        
        self.tags = ['CD','JJ','RB', 'NN', 'NNS','NNP','NNPS', 'VB']
        self.pos_tags = ['PROPN','VERB','NOUN','NUM']

        self.top_similar = top_similar

    # Query Expansion
    def expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        result = []
        '''
        if relation:
            result = [*result, *self.get_comparation_superlation_nouns_from_original_data()]

        if synonyms:
            result = [*result, *self.synonyms()]
        '''
        if sensevec:
            result = [*result, *self.similarwords_sensevec()] #each topic there are multi expanded queries by similar words because of replacing methods

        if embedded:
            result = [*result, *self.similarwords_wordembedding()]

        # ToDo combine original or return only new ones
        return result

    def similarwords_replace(self, query, similar_words):
        import copy
        expanded_queries=[]
        for word, similar_words in similar_words.items():
            
                for similar_word in similar_words:
                    new_query=copy.deepcopy(query).replace(word, similar_word)
                    expanded_queries.append(new_query)
        return expanded_queries

    def similarwords_wordembedding(self):
        result = []
        for query in self.original_query:
            doc = self.nlp(query)
            #expanded queries
            expanded_queries=[]
            similar_words={}
            for token in doc:
                top_similar_words=[]
                if token.tag_ in self.tags or token.pos_ in self.pos_tags:
                    if token.lemma_ not in STOP_WORDS or token.text not in STOP_WORDS:
                        try:
                            word=token.lemma_
                            print(word)
                            ms = self.nlp.vocab.vectors.most_similar(np.asarray([self.nlp.vocab.vectors[self.nlp.vocab.strings[word]]]), self.top_similar)
                            print(ms)
                            similar_embedding = [self.nlp.vocab.strings[w] for w in ms[0][0]] #get only text from most_similar
                            
                            #checking again if similar words are the same word
                            for word in similar_embedding:
                                if (word != token.text) and (self.nlp(word)[0].lemma_ != token.lemma_):
                                    top_similar_words.append(self.nlp(word)[0].lemma_.lower())
                        except ValueError as err:
                            print(err)
                        
                        similar_words[token.text]=list(set(top_similar_words)) #only unique words
            
            #replace with similar words for new queries.
            expanded_queries = self.similarwords_replace(query, similar_words)
            result.append(expanded_queries)
        return result
        
    def similarwords_sensevec(self):
        result=[]
        for query in self.original_query:
            doc = self.nlp(query)
            expanded_queries=[]
            similar_words={}
            for token in doc:
                top_similar_words=[]
                if token.tag_ in self.tags or token.pos_ in self.pos_tags:
                    if token.lemma_ not in STOP_WORDS or token.text not in STOP_WORDS:
                        try:
                            for e in token._.s2v_most_similar(self.top_similar):
                                word = e[0][0].strip() #get only word from ((word, tag), proba)
                                if (word != token.text) and (self.nlp(word)[0].lemma_ != token.lemma_):
                                    top_similar_words.append(word)
                        except ValueError as err:
                            for ent in doc.ents:
                                if ent.text == token.text:
                                    try:
                                        for e in ent._.s2v_most_similar(self.top_similar):
                                            word = e[0][0].strip() #get only word from ((word, tag), proba)
                                            if (word != token.text) and (self.nlp(word)[0].lemma_ != token.lemma_):
                                                top_similar_words.append(word)

                                    except ValueError as err:
                                        
                                        query = token._.s2v_other_senses[0] #get first similar words by entity_tag
                                        for e in self.standalone_s2v.most_similar(query, n=self.top_similar):
                                            word = e[0].split("|")[0].strip() #get only word from (word|tag, proba)
                                            if (word != token.text) and (self.nlp(word)[0].lemma_ != token.lemma_):
                                                top_similar_words.append(word)
                        
                        similar_words[token.text]=list(set(top_similar_words))
            expanded_queries=self.similarwords_replace(query, similar_words)
            result.append(expanded_queries)
        return result

    def remove_punc(self, query: str):
        table = str.maketrans(dict.fromkeys(string.punctuation))
        title = query.translate(table)
        return str(title)


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

    print("sensevec")
    for i in expansion.expansion(sensevec=True):
        print(i)

    print("embedded:")
    for i in expansion.expansion(embedded=True):
        print(i)

    print("Both:")
    for i in expansion.expansion(sensevec=True, embedded=True):
        print(i)
