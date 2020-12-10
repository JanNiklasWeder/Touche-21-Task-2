import topics_annotation
from main_retrieval import n_topics
import requests
import xml.etree.ElementTree as ET
import argument_score_2
import regex as re
#import pandas as pd
#file="topics-task-2.xml"

'''
expand get_titles for comparative topics, not superlative topics
buffer = [(topic_title, bool_args) for 50 topics]
'''
def remove_htmlTags(snippet):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', snippet)

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            title = title.text.strip()
            if topics_annotation.comparative_topic(title) == True: #checking if topic needs arguments/premise/claims
                buffer.append((title, True))
            else:
                buffer.append((title,False))
        i=i+1
    return buffer #list of tuples (topic, bool_argument) for n_topics

def api(topic, size, arg_value):
    '''
    if arg_value == True:
        - calcualate the premise/clams score from target_api
    else
        - premise/claim == 0
    '''
    url = 'https://www.chatnoir.eu/api/v1/_search'

    request_data = {
        "apikey": "67fac2d9-0f98-4c19-aab0-18c848bfa130",
        "query": topic,
        "size": size,
        "index": ["cw12"],
    }
    resp=requests.post(url, data=request_data).json()
    if arg_value==False:
        return resp
    else:
        results = resp['results']
        uuids_snippets = [ (results[i]['uuid'],remove_htmlTags(results[i]['snippet'])) for i in range(0,len(results))]
        docs= get_texts_from_origin_webpages(uuids_snippets) #get paragraphs from original websites with uuids
        '''
        check arg_value for target api premise and claims
        resp['results] = list of documents for a topic -> need "UUID" for argument_score
        '''
        arg_scores_all_uuids={}
        for uuid, doc in docs.items():
            res = argument_score_2.response_targer_api(doc)
            arg_scores_all_uuids[uuid]=argument_score_2.avg_argScore(res)
        
        resp=add_arg_score_to_response(arg_scores_all_uuids,resp)
        return resp
def add_arg_score_to_response(avg_scores,resp):
    new_resp=[]
    for doc in resp:
        actual_uuid = doc['uuid']
        print(actual_uuid)
        relScore=float(doc['score'])
        print(avg_scores)
        agrScore = avg_scores[actual_uuid]
        doc['score'] = relScore*(1+agrScore)
        new_resp.append(doc)
    return sorted(new_resp,key= lambda doc: doc['score'], reverse=True)

def get_p_values_plain_html(uuid):
    url = "https://www.chatnoir.eu/cache?uuid="+uuid+"&index=cw12&raw"#&plain"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).text
    #only get tags name <p> from html web pages
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response,'html.parser')
    p_values = soup.find_all('p')
    return p_values,response
def get_texts_from_origin_webpages(uuids_snippets):
    docs = {}
    for uuid,snippet in uuids_snippets:
        p_values,response=get_p_values_plain_html(uuid) #get p_values from plain html of uuid original webpage
        docs[uuid] = snippet+" .".join([remove_special_characters(p.get_text()) for p in p_values])
    return docs
def remove_special_characters(doc):
    return re.sub('[^A-Za-z0-9]+', ' ', doc)
