import requests
import m_preprocessing
import xml.etree.ElementTree as ET
import time
from retrieval_main import n_topics, lemma, sw, syn
preprocessed_topics = open('preprocessed_topics_20'+'_ntopics_'+ n_topics +'_'+ lemma +'_'+ sw +'_'+ syn + '.txt', 'w')

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            #title = m_preprocessing.prepro(title.text.strip(), lemma, sw, syn)
            #preprocessed_topics.writelines(title + '\n')
            buffer.append(title.text.strip())
        i=i+1
    return buffer
def api(data, size):
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
def expanded_api(data, size):
    url = 'https://www.chatnoir.eu/api/v1/_search'
    all_responses = []
    
    expansion={}
    expansion['origin'] = data
    #print(data + "\n")
    #print(m_preprocessing.prepro(data, lemma, sw, syn))
    expansion['expand'] = m_preprocessing.prepro(data, lemma, sw, syn)
    #expansion.add(m_preprocessing.synFastText(data))
    
    for desc, data in expansion.items():
        print("TEXT: " + data)
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
        all_responses.append((desc,resp))
    return merge_results(all_responses, size)
def merge_results(all_responses, size):
    response={}
    all_results=[]
    for desc, resp in all_responses:
        results=resp['results']
        all_results.append(results)
    from itertools import chain
    all_results = list(chain.from_iterable(all_results))
    print(len(all_results))
    sorted_all_results_by_score= sorted(all_results,key= lambda doc: doc['score'], reverse=True)
    sorted_all_results = remove_identical_uuids(sorted_all_results_by_score)
    response={'results':sorted_all_results[:int(size)]}
    return response
def remove_identical_uuids(sorted_all_results_by_score):
    end_all_results = sorted_all_results_by_score
    #using only the doc with uuid first appeared in the list
    
    return end_all_results