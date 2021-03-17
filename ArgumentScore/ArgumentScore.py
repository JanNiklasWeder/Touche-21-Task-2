import requests
import json
import bs4
import regex as re
import time

#ex: targer = classifyWD, classifyNewWD, classifyWD_dep

#global targer_model

#targer_model = "classifyWD"
#global underscore
#underscore = "0.7"

class ArgumentScore:
    #doc must be preprocessed bevor argument score. See SimilarityScore

    def __init__(self, needArgument: bool, doc: str, targer_model_name: str, underscore: float):
        #needArgument describes argumentative topic
        seft.doc = doc
        self.needArgument = needArgument
        self.targer_model = targer_model_name

        self.underscore = underscore

    def response_targer_api(self):
        
        import regex as re
        
        payload=self.doc #doc already removed all special characters

        url = "https://demo.webis.de/targer-api/"+self.targer_model
        headers = {
            'Content-Type': 'text/plain'
        }
        
        def targer(self):
            try:
                response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                time.sleep(1)
                return self.targer()
        #================================
        response = self.targer()
        return response

    def get_argument_score(self):
        
        if self.needArgument:
            resp = self.response_targer_api()

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
                    return 0
                else:
                    avg_argScore = sum_probs/count_arg_labels
                    if avg_argScore<=float(underscore):
                        return 0
                    else:
                        return avg_argScore #arg_labels_probas
            else:
                count_arg_labels=0
                for ents_list in resp:
                    for ent in ents_list:
                        if ent['label'].endswith("-B") or ent['label'].endswith("-I"):
                            count_arg_labels += 1
                avg_argScore = count_arg_labels/len(resp)
                if avg_argScore<=float(underscore):
                    return 0
                else:
                    return avg_argScore #arg_labels_probas
