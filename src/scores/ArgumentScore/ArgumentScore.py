# -*- coding: utf-8 -*-
import requests
import json
import regex as re
import time
import pandas as pd

from tqdm import tqdm

#Model Name: targer = classifyWD, classifyNewWD, classifyWD_dep


#targer_model = "classifyWD"
#global underscore
#underscore = "0.55"


'''
DataFrame doc_df: columns= [neddArgument, topic, query, tag, trec_id, uuid, ...]
'''

class ArgumentScore:
    #doc must be preprocessed bevor argument score. See SimilarityScore
    #needArgument describes argumentative topic
        

    def __init__(self, doc_df: pd.DataFrame, targer_model_name: str, underscore: float):
        
        self.doc_df = doc_df.reset_index(drop=True)
        self.targer_model = targer_model_name
        self.underscore = underscore
        
    def get_argument_score(self):
        argScores = []

        for i in tqdm(range(0, len(self.doc_df.index)), desc="Argument score progress:"):
          doc = self.doc_df.iloc[i]['title'] + '. ' + self.doc_df.iloc[i]['snippet']
          needArgument = self.doc_df.iloc[i]['needArgument']

          if needArgument:
              resp = self.response_targer_api(doc)

              if self.targer_model!="classifyNewWD":
                  count_arg_labels=0
                  sum_probs=0.0
                  arg_labels_probas=[]
                  for ents_list in resp:
                      for ent in ents_list:
                          if ent['label'].endswith("-B") or ent['label'].endswith("-I"):
                              count_arg_labels += 1
                              sum_probs = sum_probs + float(ent['prob'])
                              arg_labels_probas.append((ent['label'],ent['prob']))
                  if count_arg_labels==0:
                      argScores.append(0)
                  else:
                      avg_argScore = sum_probs/count_arg_labels
                      if avg_argScore<=float(self.underscore):
                          argScores.append(0)
                      else:
                          argScores.append(avg_argScore) #arg_labels_probas
              else: #other models hat other response format
                  count_arg_labels=0
                  for ents_list in resp:
                      for ent in ents_list:
                          if ent['label'].endswith("-B") or ent['label'].endswith("-I"):
                              count_arg_labels += 1
                  avg_argScore = count_arg_labels/len(resp)
                  if avg_argScore<=float(underscore):
                      argScores.append(0)
                  else:
                      argScores.append(avg_argScore) #arg_labels_probas
          else:
              argScores.append(None)
        self.doc_df['Score_Argument'] = argScores
        return self.doc_df

    def response_targer_api(self, doc):
        
        clean = re.compile('<.*?>')
        doc = re.sub(clean, '', doc)
        
        payload=doc #doc already removed all special characters
        url = "https://demo.webis.de/targer-api/"+self.targer_model
        headers = {
            'Content-Type': 'text/plain'
        }
        
        def targer():
            try:
                response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                time.sleep(1)
                return targer()
        
        response = targer()
        return response

if __name__ == "__main__":
    
    #use defined attributes
    underscore=0.1
    targer_model_name = "classifyWD"

    #example for dataframe
    df = pd.DataFrame()
    df['needArgument'] = [True, True, False]
    df['topic'] = ['what is better, laptop or desktop', 'what is better, laptop or desktop', 'what is the highest mountain in the world?']
    df['title'] = ['laptop is more usefull then desktop', 'laptop or desktop for study', 'Everest - excited experience']
    df['snippet'] = ['firstly man can bringt it easy everywhere. Laptop is almost powerfull enough for almose use-cases', 'it is depend von what u study. I think laptop is comfortable to travel, computer science students need PC', 'I was there 3 months ago']
    
    #argument scores for all rows of dataframe results
    df = ArgumentScore(df, targer_model_name, underscore).get_argument_score()
    pd.set_option('display.max_columns', 10)
    print(df)