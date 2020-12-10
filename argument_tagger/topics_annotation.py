import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()

'''
hier will be annoted, which topics compartive are.
I think, comparative topics need arguments/premises/claims
- comparative topics - True
- other topics - False

Problems:
- how can sleep better -> does not need premises/claims??
- what are difference ... -> ?
'''

def comparative_topic(text):
    doc = nlp(text)
    for token in doc:
        if token.tag_=="JJR" or token.tag_=="RBR": 
            '''
            check comparative sentences (not include superalive sentences)
            comparative sentences: comparative adjects, comparative adverbs
            '''
            return 1
        if token.text == "or" or token.lemma_ == "prefer": #when verbs, ex: prefer, using "or" for recognation?!
            return 1
    return 0
