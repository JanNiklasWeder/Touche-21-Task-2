#packages
import requests
import xml.etree.ElementTree as ET
import time
from collections import Counter
from itertools import chain
import re
from simpletransformers.language_representation import RepresentationModel
from scipy.spatial import distance

#main_retrival and main_query_api from preprocessing folder
#update main_retrieval for attribbute n_gpt_samples: 3,5,...

from main_retrieval import transform_model_name, n_gpt_samples
from main_query_api import get_titles


#default transform model. It can be overwritten by function: def get_transform_model()
model = RepresentationModel(
                model_type="gpt2",
                model_name="gpt2-medium",
                use_cuda=False
            )

'''
NOTE: Index of topics 2021 from 51 to 100

GENERATED TEXTS:
    read already generated texts from gpt from folder gpt-texts -> generated_texts.txt
    generated-texts.txt: each topic - n_samples answers as samples

TRANSFORM-MODELL: gpt or bert
'''

#functions from preprocessing file
def remove_htmlTags(doc):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', doc)
def get_texts_title_snippet(trecIds_titles_snippets):
    docs={}
    for trec_id, title, snippet in trecIds_titles_snippets:
        docs[trec_id] = title + ". " + snippet
    return docs

def get_gpt_generated_texts():
    with open('generated_texts.txt') as f:
        lines = f.read()
    generated_data=[]
    for line in lines.split("="*40 + "\n"): #=*40 separation samples for each topic - see file generated-texts to see more
        if len(line.replace("\n",""))!=0:
            generated_data.append([e.replace("\n", "") for e in line.split("\n\n\n")]) #sample1 \n\n\n sample2
    return generated_data

def get_combined_data(topics, generated_data):
    '''
    topic: list of (topic-query + answers from gpt)
    '''
    dict_combine_data={}
    for i in range(0,50):
        topicId=i+1 #index of topic: 1 bis 50
        liste = [topics[i]+". "+ e for e in generated_data[i+1]]
        dict_combine_data[topicId] = liste

def get_transform_model(transform_model_name):
    global model
    if transform_model_name == "gpt":
        gpt2_model = RepresentationModel(
                model_type="gpt2",
                model_name="gpt2-medium",
                use_cuda=False
            )
        model = gpt2_model
    else: #BERT
        bert_model = RepresentationModel(
            model_type="bert",
            model_name="bert-base-uncased",
            use_cuda=False
        )
        model = bert_model #overite the default model
    return model

def similarity(doc, topicId):

    global n_gpt_samples
    start = n_gpt_samples*(topicId-1) #5: 5 samples

    texts = []
    texts = dict_combined_data[topicId] #text from gpt2

    tmp = []
    tmp.append(doc)
    for t in texts:
        tmp.append(t)
    vectors = model.encode_sentences(tmp, combine_strategy='mean')
    
    simi_scores = []
    doc_vector=vectors[0] #vector of chatnoir text
    generated_texts_vectors = vectors[1:] #other vectors of gpt-texts
    
    for vector in generated_texts_vectors:
        simi_scores.append(1- distance.cosine(doc_vector,vector))

    #average similar score between answer of chatnoir and answers from transform model
    similarity_score = sum(simi_scores)/len(simi_scores)
    texts = []
    
    return similarity_score

def update_response(similarity_scores,resp, statusAdd):
    new_resp = []
    if statusAdd==False: #using directly similarity score for reranking
        for doc in resp['results']:
            trec_id = doc['trec_id']
            #relevance_score=float(doc['score'])
            similarity_score= similarity_scores[trec_id]
            
            #change end_score
            doc['score'] = similarity_score
            new_resp.append(doc)
    else:
        for doc in resp['results']:
            trec_id = doc['trec_id']
            relevance_score=float(doc['score'])
            similarity_score= similarity_scores[trec_id]
            
            #change end_score
            doc['score'] = relevance_score + relevance_score*similarity_score #relevance_score*(1+similarity_score)
            new_resp.append(doc)
            
    return {'results':sorted(new_resp,key= lambda doc: doc['score'], reverse=True)}
    
def chatnoir_api(topicID, topic, size, spamRank, statusAdd):
    
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
    resp = chatnoir_req()
    print("="*40 + "GET RESPONSES" + "="*40)
    results = resp['results']
    
    trecIds_titles_snippets = [(results[i]['trec_id'],remove_htmlTags(results[i]['title']), remove_htmlTags(results[i]['snippet'])) for i in range(0,len(results))]
    docs= get_texts_title_snippet(trecIds_titles_snippets) #only titles and snippets
    
    similarity_scores={}
    for trec_id, doc in docs.items():
        print(remove_htmlTags(doc))
        score = similarity(remove_htmlTags(doc), topicID)
        print(score)
        similarity_scores[trec_id]=score
    #print(similarity_scores)
    
    #similarity_scores = dict(sorted(x.items(), key=lambda item: item[1]))
    if spamRank==False:
        resp=update_response(similarity_scores,resp, statusAdd)
        
    return similarity_scores, resp

if __name__ == "__main__":
    topics = get_titles("topics-task-2.xml")
    generated_data = get_gpt_generated_texts() #loading file
    dict_combined_data = get_combined_data(topics, generated_data)