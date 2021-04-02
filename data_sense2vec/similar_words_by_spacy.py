import spacy
import numpy as np
import en_core_web_md
import xml.etree.ElementTree as ET
import spacy
from sense2vec import Sense2VecComponent
from sense2vec import Sense2Vec
import itertools
import copy
import pandas as pd

nlp = en_core_web_md.load()
n_topics=50

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    buffer = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            buffer.append(title.text.strip())
        i=i+1
    return buffer
#============= ORGINAL TOPICS =================
file="topics_task_2_touche20/topics-task-2.xml"
topics=get_titles(file)
#=============SENSE2VEC MODELL=================
s2v = nlp.add_pipe("sense2vec")
s2v.from_disk("s2v_reddit_2015_md/s2v_old")

standalone_s2v = Sense2Vec().from_disk("s2v_reddit_2015_md/s2v_old")

def get_similars_sense2vec(topic, topn):
    tags = ['CD',
            'JJ',
            'RB', 
            'NN', 'NNS','NNP','NNPS', 
            'VB']
    pos_tags = ['PROPN','VERB','NOUN','NUM']

    doc = nlp(topic)
    similar_words={}
    for token in doc:
        top_similar_words=[]
        if token.tag_ in tags or token.pos_ in pos_tags:
            print(token.text)
            try:
                for e in token._.s2v_most_similar(topn):
                    word = e[0][0].strip() #get only word from ((word, tag), proba)
                    if (word != token.text) and (nlp(word)[0].lemma_ != token.lemma_):
                        top_similar_words.append(word)
            except ValueError as err:
                for ent in doc.ents:
                    if ent.text == token.text:
                        try:
                            for e in ent._.s2v_most_similar(topn):
                                word = e[0][0].strip() #get only word from ((word, tag), proba)
                                if (word != token.text) and (nlp(word)[0].lemma_ != token.lemma_):
                                    top_similar_words.append(word)
                            
                        except ValueError as err:
                            print(token._.s2v_other_senses == ent._.s2v_other_senses)
                            query = token._.s2v_other_senses[0] #get first similar words by entity_tag
                            print(token._.s2v_other_senses[0])
                            print(ent._.s2v_other_senses[0])
                            for e in standalone_s2v.most_similar(query, n=topn):
                                word = e[0].split("|")[0].strip() #get only word from (word|tag, proba)
                                if (word != token.text) and (nlp(word)[0].lemma_ != token.lemma_):
                                    top_similar_words.append(word)
            print(set(top_similar_words))
            similar_words[token.text]=list(set(top_similar_words))
            print("="*80)
    return similar_words
#==========GET SIMILAR WORDS==========================================
similar_words_by_topics=[]
for topic in topics:
    similar_words_by_topics.append(get_similars_sense2vec(topic, topn=5)) #index = 0 = topic 1

#==========ADD SIMILAR WORDS to topics================================
shorted_topics =[]
expanded_topics=[]
similar_words_by_topics_copy = copy.deepcopy(similar_words_by_topics)
index = 0
for similar_words in similar_words_by_topics_copy:
    #print(similar_words)
    topic = topics[index]
    tmp = []
    for key,value_ in similar_words.items():
        value = copy.deepcopy(value_)
        value.insert(0,key)
        tmp.append(list(set(value)))
    #print(tmp)
    #only observed similar words
    shorted_merged = list(set(list(itertools.chain.from_iterable(tmp))))
    shorted_topic = " ".join(list(set(" ".join(shorted_merged).split(" ")))) #after merging remove the same words in a query
    shorted_topics.append(shorted_topic) #only similar words
    
    #expansion
    expanded_merged = shorted_topic
    print(expanded_merged)
    #add words to the original topics
    expanded_topic = topic + " " + " ".join(list(set(expanded_merged.split(" "))))
    print(expanded_topic)
    expanded_topics.append(expanded_topic)
    index = index +1

df = pd.DataFrame({"title": topics, "5_similar":similar_words_by_topics, "shorted_topic": shorted_topics, "expanded_topic": expanded_topics})
df.index +=1
print(df)
def write_text(file_name, m_list):
    myfile = open(file_name+'.txt', 'w')
    for text in m_list:
        myfile.write(text + "\n\n")
write_text("shorted_topics", shorted_topics)
write_text("expanded_topics", expanded_topics)