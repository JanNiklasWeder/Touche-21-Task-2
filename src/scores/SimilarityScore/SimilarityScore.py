# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
import time
from collections import Counter
from itertools import chain
import pandas as pd

'''
topics is a list of all topics
transformModel is User-Input for which transform model should be used
'''

#install packages
from simpletransformers.language_representation import RepresentationModel
from scipy.spatial import distance

class SimilarityScore:
    def __init__(self, all_topics: [str], data: pd.DataFrame, transform_model_name: str =='gpt'):
      
        self.data = data
        self.n_samples = 5
        self.topics = all_topics
        #self.transform_model
        if transform_model_name=='gpt':
          gpt2_model = RepresentationModel(
                    model_type="gpt2",
                    model_name="gpt2-medium",
                    use_cuda=False
                )
          self.transform_model = gpt2_model
        if transform_model_name == "bert":
          bert_model = RepresentationModel(
                model_type="bert",
                model_name="bert-base-uncased",
                use_cuda=False
            )
          self.transform_model = bert_model

    def set_topic_ids(self):
        i = 1
        topic_ids = []
        for topic in self.topics:
          splitdf = self.data[self.data['topic']==topic].reset_index(drop=True)
          topic_ids.append(len(splitdf.index)*[i])
          i = i + 1
        topic_ids = list(chain(*topic_ids))
        print(topic_ids)
        return topic_ids

    def get_similarity_scores(self):
        topic_ids = self.set_topic_ids()
        similarity_scores = []
        for i in range(0, len(self.data.index)):
          topic_id = topic_ids[i]
          doc = self.data.iloc[i]['title'] + self.data.iloc[i]['snippet']
          similarity_score = self.calculate_similarity_for_doc(topic_id, doc)
          similarity_scores.append(similarity_score)
        self.data['similarity_score'] = similarity_scores
        return self.data

    def calculate_similarity_for_doc(self, topic_id, doc):
        
        generated_texts = self.load_generated_text_for_topic(topic_id)

        #add query and generted_texts in a list
        tmp = []
        tmp.append(doc)
        for text in generated_texts:
            tmp.append(text)
        
        #transformation to vectors
        vectors = self.transform_model.encode_sentences(tmp, combine_strategy='mean')
        #similarity 
        scores = []
        doc_vector=vectors[0]
        generated_texts_vectors = vectors[1:]
        
        for vector in generated_texts_vectors:
            scores.append(1- distance.cosine(doc_vector,vector))

        similarity_score = sum(scores)/len(scores)
        return similarity_score
    def load_generated_text_for_topic(self, required_topic_id):
        '''
        1. this filename is depend von python script generated_text
        2. transform "topic[i]. generated_text[i][j]" to vector
        3. j= [0,n_samples].
        '''
        filename="text_task20/generated_texts.txt"

        with open(filename) as f:
            lines = f.read()
        generated_texts=[]
        for line in lines.split("="*40 + "\n"):
            if len(line.replace("\n",""))!=0:
                generated_texts.append([e.replace("\n", "") for e in line.split("\n\n\n")])
        generated_texts={(i+1): generated_texts[i] for i in range(0,len(generated_texts))}
        '''
        1. combine topic and generated text
        2. topic_id: List[query+generated_text[j] for j in [0, n_saples]]
        3. topics = get_titles(file)
        '''
        dict_combined_data={}
        topic_id=0
        for i in range(0,len(self.topics)):
            topic_id=i+1
            liste = [topics[i]+". "+ e for e in generated_texts[i+1]]
            dict_combined_data[topic_id] = liste
        
        generated_texts = dict_combined_data[required_topic_id]
        return generated_texts

if __name__ == "__main__":
    
    #READ RESULTS FROM CHATNOIR UND MERGED DF
    merged_resp = pd.read_csv('merged_results.csv', sep=";")
    print(merged_resp)

    print("\n"+"=====================GET ALL TOPICS=================")
    n_topics=50
    def get_titles(filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        buffer = []
        i=1
        for title in root.iter('title'):
            if i<=int(n_topics):
                buffer.append(title.text.strip())
            i=i+1
        return buffer
    filename="topics-task-2.xml"
    topics=get_titles(filename)


    print("\n"+"===================DF WITH SIMILARITY SCORE==============")
    df_with_similarity_score = SimilarityScore(topics, merged_resp, 'gpt').get_similarity_scores()
    print(df_with_similarity_score)