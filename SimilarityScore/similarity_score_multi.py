#other packages for testing script, they are already from main
import requests
import xml.etree.ElementTree as ET
import time
from collections import Counter
from itertools import chain
#==================================IMPORT VARIABLE FROM MAIN ========================================
#import global variables
#from main import topics, n_samples, transform_model_name
#==========================================================================
'''
topics is a list of all topics
n_samples is User-Input for number of generated texts for each topic
transformModel is User-Input for which transform model should be used
'''

#install packages
from simpletransformers.language_representation import RepresentationModel
from scipy.spatial import distance

class SimilarityScore:
    
    def __init__(self, topic_id: int, doc: str, n_samples: int, transform_model_name: str):
        
        self.topic_id = topic_id
        self.doc = doc
        
        self.n_samples=n_samples
        self.model_name = transform_model_name

        #load transform model
        if self.model_name == "gpt":
            gpt2_model = RepresentationModel(
                    model_type="gpt2",
                    model_name="gpt2-medium",
                    use_cuda=False
                )
            score.transform_model = gpt2_model
            
        if self.model_name == "bert":
            bert_model = RepresentationModel(
                model_type="bert",
                model_name="bert-base-uncased",
                use_cuda=False
            )
            self.transform_model = bert_model

        
    def load_generated_text_for_topic(self):
        '''
        1. this filename is depend von python script generated_text
        2. transform "topic[i]. generated_text[i][j]" to vector
        3. j= [0,n_samples].
        '''
        filename="text_task20/generated_text.txt"

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
        for i in range(0,50):
            topic_id=i+1
            liste = [topics[i]+". "+ e for e in generated_texts[i+1]]
            dict_combined_data[topic_id] = liste
        
        generated_texts = dict_combined_data[self.topic_id]
        return generated_texts
    
    def calculate_similarity(self):
        
        generated_texts = self.load_generated_text_for_topic()

        #add query and generted_texts in a list
        tmp = []
        

        tmp.append(self.doc)
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

def chatnoir_api(topic, size):
    import time
    import requests

    url = 'https://www.chatnoir.eu/api/v1/_search'
    request_data = {
        "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
        "query": topic,
        "size": size,
        "index": ["cw12"],
    }
    def chatnoir_req():
        try:
            response_=requests.post(url, data=request_data)
            response_.raise_for_status()
            return response_.json()
        except requests.exceptions.HTTPError:
            time.sleep(1)
            return chatnoir_req()

    results = chatnoir_req()['results']
    return results

def preprocessing(results):
    import re
    clean = re.compile('<.*?>')

    preprocessed_docs ={} #{ trec_id: title + snippet}
    for result in results:
        trec_id = result['trec_id']
        doc = result['title']+'. ' + result['snippet']
        doc = re.sub(clean, '', doc) #remove html tags
        preprocessed_docs[trec_id] = doc
    
    return preprocessed_docs

if __name__ == "__main__":

    #list all topics must be imported as global variable
    n_topics=50
    def get_titles(file):
        tree = ET.parse(file)
        root = tree.getroot()
        buffer = []
        i=1
        for title in root.iter('title'):
            if i<=int(n_topics):
                buffer.append(title.text.strip())
            i=i+1
        return buffer
    file="topics-task-2.xml"
    topics=get_titles(file)

    #from user input
    n_samples=5
    transform_model_name="bert"

    #===========EXAMPLE: test similarity score for a topic=======================
    query={}
    topic_id = 2
    query[topic_id]="Which is better, a laptop or a desktop?"

    #response from chatnoir for a topic
    results = chatnoir_api(query[topic_id],size=15)

    
    #===========SIMILAR SCORE FOR EACH DOC OF RESPONSE===========================
    #using only trec_id, title and snippet to determine the similarity score
    docs = preprocessing(results)

    #similar score
    similar_scores={}
    for trec_id, doc in docs.items():
        '''
        SimilarityScore() for a response-doc from a topic-id
        '''
        similar_score = SimilarityScore(topic_id, doc, n_samples, transform_model_name).calculate_similarity()
        similar_scores[trec_id] = similar_score

    
    print("list of similarity scores for a topic")
    print(similar_scores)

    #expend result with new key: result['similarity]
    for result in results:
        trec_id = result['trec_id']
        result['similarity'] = similar_scores[trec_id]
    print(result)
    