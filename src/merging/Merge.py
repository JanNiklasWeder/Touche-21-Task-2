from collections import Counter
from itertools import chain
import pandas

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
    def __init__(self, topics: [str], resp_df: pandas.DataFrame, weights: dict, method: str):

        self.resp_df = resp_df.reset_index(drop=True)
        self.weights = weights
        self.method = method
        self.original_topics = topics
        self.merged_df = pandas.DataFrame()

    def get_weight(self, tag):
        w = 1 #default
        if "sensevec" in tag:
            w = self.weights['sensevec']
        elif "embedded" in tag: #because embedded_1, embedded_2, ...
            w = self.weights['embedded']
        else:
            w = self.weights[tag]
        return w

    def update_all_scores_with_weights(self):
        weighted_scores = []
        for i in range(0,len(self.resp_df.index)):
            tag = self.resp_df.iloc[i].tag
            w = self.get_weight(tag)
            chatnor_score = self.resp_df.iloc[i].Score_ChatNoir
            weighted_scores.append(w*chatnor_score)
        self.resp_df['Weighted_Score_ChatNoir'] = weighted_scores

    def merging(self):
        #update all scores by weights > Weighted_Score_ChatNoir
        self.update_all_scores_with_weights()
        #columns updated after update_all_scores_with_weights
        column_names = list(self.resp_df.columns)

        final_merged_df = pandas.DataFrame(columns=column_names) #create empty dataframes

        for topic in self.original_topics:
            #response dataframe by topic
            splitdf = self.resp_df[self.resp_df['topic']==topic].reset_index(drop=True)

            #df of non duplicated documents
            non_dupl = splitdf.drop_duplicates(subset ="TrecID",keep = False, inplace=False).reset_index(drop=True)

            #duplicated documents
            dupl_df = splitdf[splitdf.duplicated(['TrecID'], keep=False)]

            if len(dupl_df.index)!=0:
                dupl_ids = list(splitdf[splitdf.duplicated(['TrecID'], keep=False)]['TrecID'].unique())
                #update query, tag and score
                merged_rows = []
                for trecid in dupl_ids:
                    #using Weighted_Score_ChatNoir to select one of duplication
                    dupl_by_id = dupl_df[dupl_df['TrecID']==trecid]
                    if self.method=="max":
                        max_score = max(list(dupl_by_id['Weighted_Score_ChatNoir']))
                        max_doc = list(dupl_by_id[dupl_by_id['Weighted_Score_ChatNoir']==max_score].iloc[0].values) #may more then 1 docs with max_score, get the first
                        merged_rows.append(max_doc)
                    else: #mean
                        from statistics import mean
                        mean_score = mean(list(dupl_by_id['Weighted_Score_ChatNoir']))
                        #mean_doc is dictionary
                        mean_doc = dupl_by_id[dupl_by_id['tag']=='original'].iloc[0].to_dict() #priority response of original query
                        mean_doc['Weighted_Score_ChatNoir'] = mean_score
                        merged_rows.append(list(mean_doc.values()))
                    
                    #create dataframe to save docs, which are selected from multiple trec_ids
                    merged_dupl = pandas.DataFrame(merged_rows, columns=column_names)
                    
                    #add non_dupl and merged_dupl to get non_dupl_pro_topic: result of each topic
                    merged_df_by_topic = pandas.concat([non_dupl, merged_dupl])
                    
                    final_merged_df = pandas.concat([final_merged_df,merged_df_by_topic])
            else:
                final_merged_df = pandas.concat([final_merged_df,non_dupl])
        return final_merged_df.sort_values(by='Score_ChatNoir', ascending=False).reset_index(drop=True)