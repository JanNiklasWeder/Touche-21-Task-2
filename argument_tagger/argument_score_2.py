import requests
import json
import bs4
import regex as re
import time

#get argument labels from targer
def response_targer_api(doc):
    
    import regex as re
    
    payload=doc #doc already removed all special characters
    url = "https://demo.webis.de/targer-api/classifyWD"
    headers = {
        'Content-Type': 'text/plain'
    }
    '''
    def targer(retries=0, m_url, m_headers, m_payload):
        try:
            response = requests.request("POST", m_url, headers=m_headers, data=m_payload.encode('utf-8'), timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return targer(retries+1, m_url, m_headers,m_payload)
        return response.json()
    '''
    # Move on with your life! Yay!
    #response = requests.request("POST", url, headers=headers, data=payload)
    #response=targer(0,url, headers, payload)
    def targer():
        try:
            response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            time.sleep(1)
            return targer()
    response = targer()
    print(response)
    return response

def avg_argScore(resp_as_list):
    #
    count_arg_labels=0
    sum_probs=0.0
    arg_labels_probas=[]
    for ents_list in resp_as_list:
        for ent in ents_list:
            if ent['label'].endswith("-B") or ent['label'].endswith("-I"):
                count_arg_labels += 1
                sum_probs = sum_probs + float(ent['prob'])
                arg_labels_probas.append((ent['label'],ent['prob']))
    #average the probas from arg_labels
    if count_arg_labels==0:
        return 0
    else:
        avg_argScore = sum_probs/count_arg_labels
        if avg_argScore<=0.6:
            return 0
        else:
            return avg_argScore #arg_labels_probas

def remove_htmlTags(snippet):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', snippet)
