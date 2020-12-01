import requests
import m_preprocessing
import xml.etree.ElementTree as ET

from retrieval_main import n_topics, lemma, sw, syn
preprocessed_topics = open('preprocessed_topics_20'+'_ntopics_'+ n_topics +'_'+ lemma +'_'+ sw +'_'+ syn + '.txt', 'w')

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            title = m_preprocessing.prepro(title.text.strip(), lemma, sw, syn)
            preprocessed_topics.writelines(title + '\n')
            buffer.append(title)
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
    print(resp)
    return resp.json()