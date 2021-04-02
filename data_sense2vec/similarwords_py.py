import spacy
from spacy.lang.en.stop_words import STOP_WORDS

import numpy as np
import en_core_web_md
nlp = en_core_web_md.load()

from sense2vec import Sense2VecComponent
s2v = nlp.add_pipe("sense2vec")
s2v.from_disk("s2v_reddit_2015_md/s2v_old")

from sense2vec import Sense2Vec
standalone_s2v = Sense2Vec().from_disk("./s2v_reddit_2015_md/s2v_old")

import xml.etree.ElementTree as ET
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
file="topics-task-2.xml"
topics=get_titles(file)


#===========================================================================================================
def similarwords_replace(query, similar_words):
        import copy
        
        expanded_queries=[]
        new=[]
        
        
        
        for word, similars in similar_words.items():
            for similar_word in similars:
                print(similar_word)
                new_query=copy.deepcopy(query).replace(word, similar_word)
                expanded_queries.append(new_query)
        
        keys = similar_words.keys()
        for key in keys:
            for other_key in keys:
                if other_key!=key:
                    for sw in similar_words[key]:
                        pos_key = [ i for i in range(len(query.split(" "))) if query.split(" ")[i]==key]
                        #print(pos_key)
                        n = copy.deepcopy(query).replace(key, sw)
                        pos = [i+len(sw.split(" "))-1 for i in pos_key]
                        #print(pos)
                        #laptop 1 - desktop PC 1,2
                        for p in pos_key:
                            pos.append(p)
                        pos = list(set(pos))
                        print(pos)
                        new.append(n)
                        for swo in similar_words[other_key]:
                            pos_other = [ i for i in range(len(n.split(" "))) if n.split(" ")[i]==other_key and i not in pos]
                            print(pos_other)
                            print("========")
                            import numpy
                            text_as_arr = numpy.array(n.split(" "))
                            for idx in pos_other:
                                text_as_arr[idx]=swo
                            #nn = copy.deepcopy(n).replace(other_key, swo)
                            nn = " ".join(text_as_arr)
                            new.append(nn)
                        print("=======================================================")
        return new, expanded_queries

def get_similar_words(word, topn):
    ms = nlp.vocab.vectors.most_similar(np.asarray([nlp.vocab.vectors[nlp.vocab.strings[word]]]), n=topn)
    words = [nlp.vocab.strings[w] for w in ms[0][0]]
    return words

def similar_words_with_wordembeddings(topic, topn):
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
            if token.lemma_ not in STOP_WORDS or token.text not in STOP_WORDS:
                print(token.text)
                try:
                    similar_words_by_wordembeddings = get_similar_words(token.text, topn)
                    
                    for word in similar_words_by_wordembeddings:
                        if (word != token.text) and (nlp(word)[0].lemma_ != token.lemma_):
                            top_similar_words.append(nlp(word)[0].lemma_.lower())
                except ValueError as err:
                    print(err)
                print(set(top_similar_words))
                similar_words[token.text]=list(set(top_similar_words))
                print("="*80)
    return similar_words
    
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
            if token.lemma_ not in STOP_WORDS or token.text not in STOP_WORDS:
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

if __name__ == "__main__":
    r = get_similars_sense2vec(topics[0], topn=2)
    print(r)

    a,b= similarwords_replace(topics[0], r)
    print(a)
    print(b)

    rr = similar_words_with_wordembeddings(topics[0], 2)
    print(rr)
    a, b = similarwords_replace(topics[0], rr)

    print(a)
    print(b)
