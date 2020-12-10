import requests
import json
import bs4

def cal_argScores(results, arg_value):

    if arg_value==False:
        return { results[i]['uuid']:0 for i in range(0,len(results))} # return 0 argScore for all found documents uuids for a topic
    else:
        uuids = [ results[i]['uuid'] for i in range(0,len(results))]
        docs=get_texts_from_origin_webpages(uuids) #docs={uuid:founded_text}
        uuid_argScore={}
        for uuid, doc in docs.items():
            uuid_argScore[uuid]=get_argument_score(doc)
            
        return uuid_argScore
def get_texts_from_origin_webpages(uuids):
    docs = {}
    for uuid in uuids:
        p_values,response=get_p_values_plain_html(uuid) #get p_values from plain html of uuid original webpage
        docs[uuid] = ".".join([p.get_text() for p in p_values])
    #docs[uuid] = original_text from response uuid-original webpage
    return docs #{uuid: text}

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

def get_argument_score(doc):
    payload=doc
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'text/plain'
    }
    url = "https://demo.webis.de/targer-api/classifyWD"
    response = requests.request("POST", url, headers=headers, data=payload)

    print(json.loads(response.text)[0])
    score=0
    return score
