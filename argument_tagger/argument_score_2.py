import requests
import json
import bs4
import regex as re

def remove_htmlTags(snippet):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', snippet)

#get argument labels from target
def response_targer_api(doc):
    
    import regex as re
    
    payload=doc #doc already removed all special characters
    url = "https://demo.webis.de/targer-api/classifyWD"
    headers = {
        'Content-Type': 'text/plain'
    }
    response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
    return response.json()

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