# -*- coding: utf-8 -*-
import logging
import tarfile

import nltk
import wget as wget


from nltk.corpus import  wordnet
from typing import List
import spacy
#en_core_web_md
import string
from tqdm import tqdm

from nltk.corpus import wordnet
from spacy.lang.en.stop_words import STOP_WORDS
import random
random.seed(10)
import numpy as np
from itertools import chain

#packages to find similar words by wordembedding and sense2vec
from sense2vec import Sense2VecComponent 
from sense2vec import Sense2Vec #for standalone
import pandas as pd
from pathlib import Path


#!/usr/bin/python

class QueryExpansion:

    def __init__(self, queries: pd.DataFrame, top_syns: int = 5, top_similar: int=2):
        nltk.download('wordnet')
        self.df_queries = queries
        
        self.nlp = spacy.load("en_core_web_md")
        self.top_syns = top_syns

        path = Path.cwd() / "data/s2v_reddit_2015_md"

        if not path.is_dir():
            logging.info("Will download s2v_reddit_2015_md this may take a while.")
            path = Path.cwd() / "data/s2v_reddit_2015_md.tar.gz"

            wget.download("https://github.com/explosion/sense2vec/releases/download/v1.0.0/s2v_reddit_2015_md.tar.gz",
                          str(path))

            with tarfile.open(path) as tar:
                path = path.parent / "s2v_reddit_2015_md"
                tar.extractall(path)
            (path.parent / "s2v_reddit_2015_md.tar.gz").unlink(missing_ok=True)

        path = path / "s2v_old"
        self.sense = self.nlp.add_pipe("sense2vec").from_disk(path)
        self.standalone_s2v = Sense2Vec().from_disk(path) #it is not dubplicated
        
        self.tags = ['CD','JJ','RB', 'NN', 'NNS','NNP','NNPS', 'VB']
        self.pos_tags = ['PROPN','VERB','NOUN','NUM']

        self.top_similar = top_similar

    # Query Expansion
    def expansion(self, relation: bool = False, synonyms: bool = False, sensevec: bool=False, embedded: bool=False):
        
        if relation:
          result = []
          result = [*result, *self.get_comparation_superlation_nouns_from_original_data()]
          self.df_queries = pd.concat([self.df_queries, pd.DataFrame(result, columns=['TopicID','topic', 'query', 'tag'])])

        if synonyms:
          result = []
          result = [*result, *self.synonyms()]
          self.df_queries = pd.concat([self.df_queries, pd.DataFrame(result, columns=['TopicID','topic', 'query', 'tag'])])
        
        if sensevec:
          result = []
          result = [*result, *self.similarwords_sensevec()]
          self.df_queries = pd.concat([self.df_queries, pd.DataFrame(result, columns=['TopicID','topic', 'query', 'tag'])])
        if embedded:
          result = []
          result = [*result, *self.similarwords_wordembedding()]
          self.df_queries = pd.concat([self.df_queries, pd.DataFrame(result, columns=['TopicID','topic', 'query', 'tag'])])

        return self.df_queries

    def similarwords_replace(self, query, similar_words):
        import copy
        expanded_queries=[]
        for word, similar_words in similar_words.items():
            for similar_word in similar_words:
                new_query=copy.deepcopy(query).replace(word, similar_word)
                expanded_queries.append(new_query)
        return expanded_queries
    def similarwords_sensevec(self):
        result=[]
        
        for original_query in tqdm(list(self.df_queries['topic'].unique()), desc="Sensevec progress"):

            original_topicid = self.df_queries[self.df_queries['topic']==original_query].iloc[0]['TopicID']

            doc = self.nlp(original_query)
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
            expanded_queries=self.similarwords_replace(original_query, similar_words)
            i = 1
            for new_query in expanded_queries:
              result.append([original_topicid, original_query,new_query, 'sensevec_'+str(i)])
              i = i +1
        return result

    def remove_punc(self, query: str):
        table = str.maketrans(dict.fromkeys(string.punctuation))
        title = query.translate(table)
        return str(title)

    def synonyms(self):
        result = []

        for query in tqdm(list(self.df_queries['topic'].unique()), desc="Synonyms progress"):
            original_topicid = self.df_queries[self.df_queries['topic']==query].iloc[0]['TopicID']

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
            result.append([original_topicid, query, temp + " " + " ".join(list(set(syn_pro_title))), 'syns'])
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

        for query in tqdm(list(self.df_queries['topic'].unique()), desc="Relation progress"):
            original_topicid = self.df_queries[self.df_queries['topic']==query].iloc[0]['TopicID']

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
            result.append([original_topicid, query, ' '.join(nouns_as_string), 'annotation'])
        return result
    def similarwords_wordembedding(self):
        result = []
        for query in tqdm(list(self.df_queries['topic'].unique()), desc="Embeddings progress"):
            original_topicid = self.df_queries[self.df_queries['topic']==query].iloc[0]['TopicID']

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
                            
                            try:
                              key = self.nlp.vocab.strings[word]
                              vector = self.nlp.vocab.vectors[key]
                              vector_asarray = np.asarray([vector])
                              ms = self.nlp.vocab.vectors.most_similar(vector_asarray, n=self.top_similar)
                              #print(ms)
                              similar_embedding = [self.nlp.vocab.strings[w] for w in ms[0][0]] #get only text from most_similar
                              #checking again if similar words are the same word
                              for word in similar_embedding:
                                  if (word != token.text) and (self.nlp(word)[0].lemma_ != token.lemma_):
                                      top_similar_words.append(self.nlp(word)[0].lemma_.lower())
                            except KeyError as err:
                              print(err)
                        except ValueError as err:
                            print(err)
                        
                        similar_words[token.text]=list(set(top_similar_words)) #only unique words
            
            #replace with similar words for new queries.
            expanded_queries = self.similarwords_replace(query, similar_words)
            
            i = 1
            for new_query in expanded_queries:
              result.append([original_topicid, query,new_query, 'embedded_'+str(i)])
              i = i +1
        return result

if __name__ == "__main__":
    
    topics = ["What is the difference between sex and love?",
             "Which is the highest mountain in the world?",
             "Which is better, a laptop or a desktop?"]
             
    topics = ['What is the difference between sex and love?', 
             'Which is better, a laptop or a desktop?', 
             'Which is better, Canon or Nikon?', 
             'What are the best dish detergents?', 
             'What are the best cities to live in?', 
             'What is the longest river in the U.S.?', 
             'Which is healthiest: coffee, green tea or black tea and why?', 
             'What are the advantages and disadvantages of PHP over Python and vice versa?', 
             'Why is Linux better than Windows?', 'How to sleep better?', 
             'Should I buy an LCD TV or a plasma TV?', 
             'Train or plane? Which is the better choice?',
             'What is the highest mountain on Earth?',
             'Should one prefer Chinese medicine or Western medicine?',
              'What are the best washing machine brands?', 
             'Should I buy or rent?', 'Do you prefer cats or dogs, and why?', 
             'What is the better way to grill outdoors: gas or charcoal?', 
             'Which is better, MAC or PC?', 'What is better: to use a brush or a sponge?',
             'Which is better, Linux or Microsoft?', 'Which is better, Pepsi or Coke?', 'What is better, Google search or Yahoo search?', 
             'Which one is better, Netflix or Blockbuster?', 'Which browser is better, Internet Explorer or Firefox?', 
             'Which is a better vehicle: BMW or Audi?', 'Which one is better, an electric stove or a gas stove?', 
             'What planes are best, Boeing or Airbus?', 'Which is better, Disneyland or Disney World?', 
             'Should I buy an Xbox or a PlayStation?', 'Which has more caffeine, coffee or tea?', 
             'Which is better, LED or LCD Reception Displays?', 'What is better: ASP or PHP?', 
             'What is better for the environment, a real or a fake Christmas tree?', 'Do you prefer tampons or pads?', 
             'What IDE is better for Java: NetBeans or Eclipse?', 'Is OpenGL better than Direct3D in terms of portability to different platforms?', 
             'What are the differences between MySQL and PostgreSQL in performance?', 'Is Java code more readable than code written in Scala?', 
             'Which operating system has better performance: Windows 7 or Windows 8?', 'Which smartphone has a better battery life: Xperia or iPhone?', 
             'Which four wheel truck is better: Ford or Toyota?', 'Should I prefer a Leica camera over Nikon for portrait photographs?',
             'Which company has a larger capitalization: Apple or Microsoft?', 'Which laptop has a better durability: HP or Dell?',
             'Which beverage has more calories per glass: beer or cider?', 'Is admission rate in Stanford higher than that of MIT?',
             'Is pasta healthier than pizza?', 'Which city is more expensive to live in: San Francisco or New York?', 
             'Whose salary is higher: basketball or soccer players?']
    
    df = pd.DataFrame(list(zip(topics, topics, len(topics)*['original'])), columns=['topic', 'query', 'tag'])
    print(df)

    pd.set_option('display.max_columns', 4)
    expansion = QueryExpansion(df)
    df_relation = expansion.expansion(relation=True, synonyms=True, sensevec=True, embedded=True)

    for q in topics:
        print(q)
        print(df_relation[df_relation['topic']==q])
        print(100*"=")