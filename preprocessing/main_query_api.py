import requests
import main_preprocessing
import xml.etree.ElementTree as ET
import time
from main_retrieval import n_topics, lemma, sw, syn, relation, weights, trec_id_cal
from collections import Counter
from itertools import chain
preprocessed_topics = open('preprocessed_topics_20'+'_ntopics_'+ n_topics +'_'+ lemma +'_'+ sw +'_'+ syn + '.txt', 'w')

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            #title = main_preprocessing.prepro(title.text.strip(), lemma, sw, syn)
            #preprocessed_topics.writelines(title + '\n')
            buffer.append(title.text.strip())
        i=i+1
    return buffer
def base_chatnoir_api(data, size):
    url = 'https://www.chatnoir.eu/api/v1/_search'

    request_data = {
        "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
        "query": data,
        "size": size,
        "index": ["cw12"],
    }
    resp=requests.post(url, data=request_data)
    #print(resp)
    return resp.json()
def auto_query_expansion(data, lemma, sw, syn, relation):
    queries_dict={}
    queries_dict['original'] = data
    queries_dict['simple_prepro'] = main_preprocessing.prepro(data, lemma, sw, syn)
    if relation=="True":
        queries_dict['nouns'] = main_preprocessing.get_comparation_superlation_nouns_from_original_data(data)
    return queries_dict
def expanded_api(data, size):
    url = 'https://www.chatnoir.eu/api/v1/_search'
    all_responses = {}
    
    all_queries = auto_query_expansion(data, lemma, sw, syn, relation)

    for desc, data in all_queries.items():
        #print("TEXT: " + data)
        request_data = {
            "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
            "query": data,
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
        all_responses[desc] = resp
    #print(all_responses)
    return merge_results(all_responses, size)

def chatnoir_score_update(desc, results):
    main_weights = weights.split(";")
    
    m_weights = {'original': float(main_weights[0]), 'nouns': float(main_weights[1]), 'simple_prepro': float(main_weights[2])}
    #print(m_weights)
    updated_results=[]
    #print(desc)
    for result in results:
        #results is a list, result is a dictionary
        chatnoir_score = result['score']
        #print(chatnoir_score)
        result['score'] = chatnoir_score*m_weights[desc]
        #print(result['score'])
        updated_results.append(result)
    return (desc, updated_results)
def check_id(ids):
    #print("check if same ids occurs")
    #print(Counter(ids))
    return 0
def get_resp_after_merging(all_responses, size):
    #test program
    response={}
    all_results=[]
    for desc, resp in all_responses.items():
        results=resp['results']
        all_results.append(results)
    
    all_results = list(chain.from_iterable(all_results))
    #print(len(all_results))
    sorted_all_results_by_score= sorted(all_results,key= lambda doc: doc['score'], reverse=True)
    sorted_all_results = remove_same_trec_ids(sorted_all_results_by_score)
    response={'results':sorted_all_results[:int(size)]}
    return response
def merge_results(all_responses, size):
    #all_responses: dict[desc] = response
    desc_results_updated_score =[]
    for desc, resp in all_responses.items():
        updated_results = chatnoir_score_update(desc, resp['results'])
        desc_results_updated_score.append(updated_results)

    #sort desc_trecid_value by new score / result[2]
    all_results_after_updating = list(chain.from_iterable([des_results[1] for des_results in desc_results_updated_score]))

    sorted_all_results_by_score = sorted(all_results_after_updating, key=lambda doc: doc['score'], reverse=True)
    '''
    #trec_ids = [result['trec_id'] for result in all_results_after_updating]
    #check_id(trec_ids)
    #uuids = [result['uuid'] for result in all_results_after_updating]
    #check_id(uuids)

    #final response after update 
    #updated_resp = get_resp_after_merging(all_responses, size)
    '''
    trec_ids = [result['trec_id'] for result in sorted_all_results_by_score]
    same_trec_ids = [trec_id for trec_id, count in dict(Counter(trec_ids)).items() if count!=1]
    final_results_by_expansion=[]
    if same_trec_ids!=[]:
        final_results_by_expansion = remove_same_trec_ids(sorted_all_results_by_score, same_trec_ids)
    else:
        final_results_by_expansion = sorted_all_results_by_score
    updated_resp = {'results':final_results_by_expansion[:int(size)]}
    return updated_resp

def remove_same_trec_ids(sorted_all_results_by_score, same_trec_ids):
    
    #trec_id_cal from main_retrieval

    if trec_id_cal=="max":
        #only doc with largest score in case same trec_id appear
        final_all_results = []
        same_trec_ids_max_value = []
        for trec_id in same_trec_ids:
            #get information and then update score
            max_doc = [doc for doc in sorted_all_results_by_score if doc['trec_id']==trec_id][0]
            max_doc['score'] = max([doc['score'] for doc in sorted_all_results_by_score if doc['trec_id']==trec_id])
            same_trec_ids_max_value.append(max_doc)
        
        #add results with unique trec_id
        for doc in sorted_all_results_by_score:
            if doc['trec_id'] not in same_trec_ids:
                final_all_results.append(doc)
        #add result with largest score from same_trec_ids_max_value
        for max_doc in same_trec_ids_max_value:
            final_all_results.append(max_doc)
        
        final_all_results = sorted(final_all_results, key=lambda doc: doc['score'], reverse=True)
        return final_all_results
    else:  #condition=="average", #average values of case same_trec_ids docs
        final_all_results = []
        same_trec_ids_avg_value = []
        for trec_id in same_trec_ids:
            from statistics import mean
            #get information, first doc index 0 and then update score:
            avg_doc = [doc for doc in sorted_all_results_by_score if doc['trec_id']==trec_id][0]
            factor = len(avg_doc)
            avg_doc['score'] = mean([doc['score'] for doc in sorted_all_results_by_score if doc['trec_id']==trec_id])
            same_trec_ids_avg_value.append(avg_doc)
        
        for doc in sorted_all_results_by_score:
            if doc['trec_id'] not in same_trec_ids:
                final_all_results.append(doc)
        #add result with avg score from same_trec_ids_max_value
        for max_doc in same_trec_ids_avg_value:
            final_all_results.append(max_doc)
        final_all_results = sorted(final_all_results, key=lambda doc: doc['score'], reverse=True)
        return final_all_results
    #else: with weights