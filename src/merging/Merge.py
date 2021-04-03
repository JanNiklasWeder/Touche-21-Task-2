from collections import Counter
from itertools import chain
import pandas as pd

import re
clean = re.compile('<.*?>')

'''
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
    
    def __init__(self, topics: [str], resp_df: pd.DataFrame, weights: dict, method: str):

        self.resp_df = resp_df
        self.weights = weights
        self.method = method
        self.original_topics = topics
       

    def merging(self):
        merged_topics = {}
        for topic in self.original_topics:
          splitdf = self.resp_df[self.resp_df['topic']==topic].reset_index(drop=True)
          res_tags_topic = {}
          for i in range(0, len(splitdf.index)):
            tag = splitdf.iloc[i]['tag']
            res = splitdf.iloc[i]['response']
            res_tags_topic[tag] = res

          merged_resp = self.merging_resp_topic(res_tags_topic)
          merged_topics[topic] = merged_resp

        
        df = self.to_df(merged_topics)
        return df

    def to_df(self, merged_topics):

        topics_col = []
        trecids_col = []
        uuids_col = []
        titles_col = []
        snippets_col = []
        hostnames_col=[]
        scores_col=[]
        updatedscores_col = []


        for topic, res in merged_topics.items():
          n = len(res['results'])
          topics_col.append(n*[topic])
          for doc in res['results']:
            trecids_col.append(doc['trec_id'])
            uuids_col.append(doc['uuid'])
            titles_col.append(re.sub(clean,'',doc['title']))
            snippets_col.append(re.sub(clean, '', doc['snippet']))
            hostnames_col.append(doc['target_hostname'])
            scores_col.append(doc['score'])
            updatedscores_col.append(doc['updated_score'])


        topics_col = list(chain.from_iterable(topics_col))
        
        final_merged_df = pd.DataFrame()
        final_merged_df['topic'] = topics_col
        final_merged_df['trec_id'] = trecids_col
        final_merged_df['uuid'] = uuids_col
        final_merged_df['title'] = titles_col
        final_merged_df['snippet'] = snippets_col
        final_merged_df['target_hostname'] = hostnames_col
        final_merged_df['score'] = scores_col
        final_merged_df['updated_score'] = updatedscores_col

        return final_merged_df

    def merging_resp_topic(self, res_tags):
        #resp['results'] = [doc1, doc2, ...]
        updated_resp_tags=[]
        for tag, resp in res_tags.items():
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
