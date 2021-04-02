from collections import Counter
from itertools import chain

'''
input for each topic:

+ topic_id
+ res:
    resp[tag] = chatnoir_resp
    resp[sensevec_1] = chatnoir_resp
    resp[sensevec_2] = chatnoir_resp
    ...
+ weights:
    weights['original'] = 
    weights['preprocessing']=
    weights['annotation'] = 
    weights['syns'] = 
    weights['sensevec'] = (all queries of 'sensevec' haben same weights)
    weights['embedded'] = (all queries of 'embedded' haben same weights)

+method: max or mean
output:
'''

class Merge:

    def __init__(self, topic_id: int, resp: dict, weights: dict, method: str):
        self.topic_id = topic_id
        self.res_tags = resp
        self.weights = weights
        self.method = method

    def merging_res(self):
        #resp['results'] = [doc1, doc2, ...]
        updated_resp_tags=[]
        for tag, resp in self.res_tags.items():
            updated_resp = self.update_scores_by_tags(tag, resp['results']) #(tag, updated_resp)
            updated_resp_tags.append(updated_resp)
        
        sorted_updated_resp_tags = list(chain.from_iterable([updated_resp[1] for updated_resp in updated_resp_tags]))
        #sort list by update_score: list of docs 
        sorted_updated_resp_tags = sorted(sorted_updated_resp_tags, key=lambda doc: doc['updated_score'], reverse=True)
        #find docs with same trec-id = trec-id appear multiple times
        trec_ids = [doc['trec_id'] for doc in sorted_updated_resp_tags]
        multiple_ids = [trec_id for trec_id, count in dict(Counter(trec_ids)).items() if count!=1]
        
        merged_resp=[]
        if multiple_ids!=[]:
            merged_resp = self.mergen_for_multiple_ids(sorted_updated_resp_tags, multiple_ids)
        else:
            merged_resp = sorted_updated_resp_tags
        return {'results':merged_resp}

    def update_scores_by_tags(self, tag, resp):
        updated_resp = []
        
        if "sensevec" in tag:
            weight = self.weights['sensevec']
        elif "embedded" in tag: #because embedded_1, embedded_2, ...
            weight = self.weights['embedded']
        else:
            weight = self.weights[tag]

        for doc in resp:
                doc['updated_score'] =  doc['score']*weight #update score with weight
                updated_resp.append(doc)

        return (tag, updated_resp)

    def mergen_for_multiple_ids(self, sorted_updated_resp_tags, multiple_ids):
        merged = []
        if self.method=="max":
            
            max_docs = []
            for trec_id in multiple_ids:
                
                docs_id = [doc for doc in sorted_updated_resp_tags if doc['trec_id']==trec_id] #get docs with same id
                #find doc with max-update-score
                
                max_score = max([doc['updated_score'] for doc in sorted_updated_resp_tags if doc['trec_id']==trec_id])
                
                max_doc = [doc for doc in docs_id if doc['updated_score']==max_score][0]
                
                max_docs.append(max_doc)
                
            
            #add results with unique trec_id
            for doc in sorted_updated_resp_tags:
                if doc['trec_id'] not in multiple_ids:
                    merged.append(doc)
            #add result with largest score from max_docs
            for max_doc in max_docs:
                merged.append(max_doc)
            #here sorting by score, not update-score, because update-score is only used for merging
            
            merged = sorted(merged, key=lambda doc: doc['score'], reverse=True)

        else: #self.method=="mean"
            avg_docs = []
            for trec_id in multiple_ids:
                from statistics import mean
                #get information, first doc index 0 and then update score:
                avg_doc = [doc for doc in sorted_updated_resp_tags if doc['trec_id']==trec_id][0] #already sorted, index[0] means the largest score
                avg_doc['updated_score'] = mean([doc['updated_score'] for doc in sorted_updated_resp_tags if doc['trec_id']==trec_id])
                avg_docs.append(avg_doc)
            
            for doc in sorted_updated_resp_tags:
                if doc['trec_id'] not in multiple_ids:
                    merged.append(doc)
            #add result with avg score from same_trec_ids_max_value
            for max_doc in avg_docs:
                merged.append(max_doc)
            merged = sorted(merged, key=lambda doc: doc['score'], reverse=True)

        return merged
if __name__ == "__main__":
  #INPUT
  topic_id = 1
  fake_resp = {
      'original': {'results':[
                              {'trec_id':1, 'score':5},
                              {'trec_id':2,'score':4},
                              {'trec_id':3, 'score':4}
                              ]},
      'preprocessing': {'results':[
                              {'trec_id':1, 'score':1},
                              {'trec_id':2, 'score':1},
                              {'trec_id':5, 'score':1}
                              ]},
      'annotation': {'results':[
                              {'trec_id':4, 'score':3},
                              {'trec_id':2, 'score':2},
                              {'trec_id':3, 'score':1}
                              ]},
      'syns': {'results':[
                              {'trec_id':5, 'score':2},
                              {'trec_id':2, 'score':2},
                              {'trec_id':4, 'score':1}
                              ]},
      'sensevec_1': {'results':[
                              {'trec_id':1, 'score':3},
                              {'trec_id':2, 'score':5},
                              {'trec_id':3, 'score':5}
                              ]},
      'sensevec_2': {'results':[
                              {'trec_id':1, 'score':2},
                              {'trec_id':6, 'score':1},
                              {'trec_id':3, 'score':1}
                              ]},
      'embedded_1': {'results':[
                              {'trec_id':7, 'score':2},
                              {'trec_id':8, 'score':1},
                              {'trec_id':9, 'score':1}
                              ]},
      'embedded_2': {'results':[
                              {'trec_id':1, 'score':2},
                              {'trec_id':6, 'score':3.5},
                              {'trec_id':7, 'score':2}
                              ]},
      'embedded_3': {'results':[
                              {'trec_id':4, 'score':1},
                              {'trec_id':5, 'score':2},
                              {'trec_id':6, 'score':3}
                              ]}
  }
  weights = {
      'original':2,
      'annotation': 1.75,
      'sensevec': 1.5,
      'embedded': 1.5,
      'syns': 1,
      'preprocessing': 1
  }
  print("Ergebnisse mit Max-Method")
  print(Merge(topic_id,fake_resp, weights, method='max').merging_res())
  print("Ergebnisse mit Mean-Method")
  print(Merge(topic_id,fake_resp, weights, method='mean').merging_res())