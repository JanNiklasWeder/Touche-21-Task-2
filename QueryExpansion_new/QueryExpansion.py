# -*- coding: utf-8 -*-
'''
!pip install spacy

from google.colab import drive
drive.mount('/content/drive')

!unzip -u "/content/drive/MyDrive/Colab_Notebooks/s2v_reddit_2015_md.zip" -d "/content"

!pip install sense2vec

!python -m spacy download en_core_web_md

!pip install nltk

!pip install pandas
'''

import nltk
nltk.download('wordnet')
from nltk.corpus import  wordnet
from typing import List
import spacy
#en_core_web_md
import string
from nltk.corpus import wordnet
from spacy.lang.en.stop_words import STOP_WORDS
import random
import numpy as np
from itertools import chain

#packages to find similar words by wordembedding and sense2vec
from sense2vec import Sense2VecComponent 
from sense2vec import Sense2Vec #for standalone
import pandas as pd

#!/usr/bin/python


#global tags

class QueryExpansion:

    def __init__(self, query: List[str], top_syns: int = 5, top_similar: int=2):
        self.original_query = query
        self.nlp = spacy.load("en_core_web_md")
        self.top_syns = top_syns

        self.sense = self.nlp.add_pipe("sense2vec").from_disk("s2v_reddit_2015_md/s2v_old")
        self.standalone_sense = Sense2Vec().from_disk("./s2v_reddit_2015_md/s2v_old") #it is not dubplicated
        
        self.tags = ['CD','JJ','RB', 'NN', 'NNS','NNP','NNPS', 'VB']
        self.pos_tags = ['PROPN','VERB','NOUN','NUM']

        self.top_similar = top_similar

    # Query Expansion
    def expansion(self, original: bool = True, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        result = []
        turnOn = 0
        if original:
            original_queries = [('original', query) for query in self.original_query]
            result = [*result, *original_queries]
            turnOn = turnOn + 1
        #print(turnOn)
        if relation:
            
            new_queries = self.get_comparation_superlation_nouns_from_original_data()
            i = turnOn
            for new_query in new_queries:
              result.insert(i, ('annotation', new_query))
              i = i + 1 + turnOn
            turnOn = turnOn + 1

        if synonyms:
            new_queries = self.synonyms()
            i = turnOn
            for new_query in new_queries:
              result.insert(i, ('syns',new_query))
              i = i + 1 + turnOn
            turnOn = turnOn + 1
            
            #result = [*result, *self.synonyms()]
        
        if sensevec:
            #result = [*result, *self.similarwords_sensevec()] #each topic there are multi expanded queries by similar words because of replacing methods
            new_queries = self.similarwords_sensevec()
            i = turnOn
            
            for queries in new_queries:
              #print(queries)
              length = len(queries)
              #print(length)
              index = 1 #for tag sensevec
              for query in queries:
                #print(query)
                result.insert(i, ('sensevec_'+str(index),query))
                i = i + 1
                index = index + 1
              i = i + turnOn
              #print(i)
            turnOn = turnOn + 1

        if embedded:
            #result = [*result, *self.similarwords_wordembedding()]
            new_queries = self.similarwords_wordembedding()
            i = turnOn
            
            for queries in new_queries:
              #print(queries)
              length = len(queries)
              #print(length)
              index = 1 #for tag sensevec
              for query in queries:
                #print(query)
                result.insert(i, ('embedded_'+str(index),query))
                i = i + 1
                index = index + 1
              i = i + turnOn
              #print(i)
            turnOn = turnOn + 1

        #cover to dataframe
        df = self.dfCover(result)
        return df
    def dfCover(self, expansion_result):
        df = pd.DataFrame()
        indices=[]
        #make original col
        for e in expansion_result:
          if e[0]=='original':
            indices.append((expansion_result.index(e), e[1]))
        topics = []
        for i in range(0,len(indices)-1):
          n = indices[i+1][0] - indices[i][0]
          #print(n)
          topic = indices[i][1]
          #print(topic)
          topics.append(n * [topic])
        #
        last_index = indices[-1][0]
        last_topic = indices[-1][1]
        last_n = len(expansion_result[last_index:])
        topics.append(last_n * [last_topic])

        #merging
        topics = list(chain.from_iterable(topics))
        #print("check length")
        #print(len(topics))
        #print(len(expansion_result))
        #expansion in dataframe
        df['topic'] = topics
        df['expansions'] = expansion_result
        df['query'] = [e[1] for e in expansion_result]
        df['tag'] = [e[0] for e in expansion_result]
        return df

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
                            #print(word)
                            ms = self.nlp.vocab.vectors.most_similar(np.asarray([self.nlp.vocab.vectors[self.nlp.vocab.strings[word]]]), n=self.top_similar)
                            #print(ms)
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

    def synonyms(self):
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

    def find_syns_word(self, token: str):
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
            return random.sample(syn_token,k=5)  # after top 5 synonyms + splited words -> long titles -> reducing the syns random with 5
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

if __name__ == "__main__":
    query = ["What is the difference between sex and love?",
             "Which is the highest mountain in the world?",
             "Which is better, a laptop or a desktop?"]

    print("Org. query:")

    for i in query:
        print(i)

    expansion = QueryExpansion(query)
    print("=====================================================================")
    print(expansion.expansion(original=True,relation=True, synonyms=False, sensevec=True))
    print("=====================================================================")
    print(expansion.expansion(original=True,relation=True, synonyms=True, embedded=True))