import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()
import random
from spacy.lang.en.stop_words import STOP_WORDS
import string
import nltk
from nltk.corpus import wordnet

'''
Problems:
- how can sleep better -> does not need premises/claims??
- what are difference ... -> ?
'''

synonyms_by_titles = open('synonyms_by_titles.txt', 'w')
top_syns = 5
def get_comparation_superlation_nouns_from_original_data(data):
    nouns_as_string=[]
    doc = nlp(data)
    annotations = ['CC','CD',
                    'JJ','JJR','JJS',
                    'RB','RBR','RBS', 
                    'NN', 'NNS','NNP','NNPS', 
                    'VB']
    for token in doc:
        if token.tag_ in annotations:
            nouns_as_string.append(token.text)
    return ' '.join(nouns_as_string)

def synFastText(data):
    return data
def prepro(title, lemma, stopword, syn):
    if lemma=="True":
        doc = nlp(title)
        title = " ".join([str(token.lemma_) for token in doc])
    if stopword=="True":
        title = remove_stopword(title)
    if syn =="True":
        title = wordnet_syns(title)
    #print("after preprocessing: " + title)
    return title
def wordnet_syns(title):
    new_title = remove_punc(title)
    syn_pro_title = list()
    temp = new_title
    new_title = nlp(new_title)
    for token in new_title:
        syn_token=find_syns_word(token)
        syn_pro_title.extend([syn for syn in list(set(syn_token)) if syn != str(token.text)]) #distinct and remove the same words
    #print(syn_pro_title)
    synonyms_by_titles.writelines(" ".join(list(set(syn_pro_title))) + "\n")
    title = temp + " " + " ".join(list(set(syn_pro_title)))
    return title
def find_syns_word(token):
    syn_token=[]
    if (token.pos_=="NOUN"):
        for synset in wordnet.synsets(token.lemma_):
            for lemma in synset.lemmas()[:top_syns]: #top 5 synonyms
                if "_" not in lemma.name(): #not include the words with _ ex: basketball_game
                    syn_token.append(lemma.name())
                else:
                    for w in lemma.name().split("_"):
                        if w not in STOP_WORDS:
                            syn_token.append(w) #add words with _ to two words ex. laptop_computer -> laptop and computer
    syn_token = [w for w in syn_token if w!=" " and len(w)!=0]
    if len(syn_token)>5:
        return random.sample(syn_token, k=5) #after top 5 synonyms + splited words -> long titles -> reducing the syns random with 5
    else:
        return syn_token

def remove_punc(title):
    table = str.maketrans(dict.fromkeys(string.punctuation))
    title = title.translate(table)
    return str(title)
def remove_stopword(title):
    title = [ w for w in title.split(" ") if w not in STOP_WORDS]
    return " ".join(title)
