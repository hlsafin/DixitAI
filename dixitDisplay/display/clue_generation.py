import json
from PyDictionary import PyDictionary
import nltk
from nltk.corpus import words
import math
import random
import pickle
import os
import sys
import requests
import random
import spacy
import en_core_web_sm
import itertools
import time
import concurrent.futures
import threading

from PyDictionary import PyDictionary


#Dictonary with clarifai annotated values
#Models

# GenSim with Glove
# glove_model = api.load("glove-wiki-gigaword-300")
#Gensim with Word2Vec
# model_w2v = api.load('word2vec-google-news-300')

#Save Models
# if not os.path.exists('Model'):
#     os.makedirs('Model')
# print("Writing model to disk")
# pickle.dump(glove_model, open( 'Model/model_glove.pckl', 'wb' ))
# pickle.dump(model_w2v, open( 'Model/model_w2v.pckl', 'wb' ))

print("Loading model from disk")
# glove_model = pickle.load(open('Model/model_glove.pckl', 'rb' ))
nlp = spacy.load("en_core_web_md")

# glove_model = model_g
# w2v_model = model_w2v


# use threading for I/O operation of making API calls to synonyms.com

thread_local = threading.local()
def create_pydict():
    """
    Initialises a PyDictionary class object so we can use it to make calls to the synonyms.com API.
    :param :
    :return: An initialised PyDictionary class
    """
    if not hasattr(thread_local, "synonym"):
        thread_local.session = PyDictionary()
    return thread_local.session


def get_synonym(term):
    """
    Gets the synonyms for a single term passed in.
    :param term: A string to get the synonyms for
    :return: The synonyms of the term passed in
    """
    dictionary = create_pydict()
    try:
        return dictionary.synonym(term)
    except TypeError:
        print(f"{term} is not of string type. Please pass in a string!")


def get_synonym_all(terms, threads=15):
    """
    Gets all the synonyms for each term within a list of terms passed in.
    :param terms: A list of terms to get the synonyms for
    :param threads: Maximum number of threads to execute get_synonym function calls asynchronously
    :return: A dictionary where the keys are the terms and the values are the synonyms
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        synonyms = list(executor.map(get_synonym, terms))
        terms_synonyms = dict(zip(terms, synonyms))
        return terms_synonyms

def generate_clue_from_annos(annotations):
    annotation_list = annotations

    #Remove any words releted to "art", "illustration", "drawing", etc.
    stop_words = ["person", "no person", "people", "man", "woman", "art",
    "lithograph", "drawing", "painting", "image", "sketch", "color", "design",
    "print", "lithograph", "portrait", "illustration", "girl", "boy", 'one']

    tags = [word.strip() for word in annotation_list if word.strip() not in stop_words]
    print("Tags: ", tags)
    start = time.time()

    # if len(annotation_list) >= 7:
    #     tags = tags[2:7]

    if(len(annotation_list) >4):
        tags = tags[:5]

    link = 'http://api.conceptnet.io/c/en/'
    conceptNetList = []
    # conceptNetList_comp = []
    for t in tags:
        if ' ' not in t:
            # print('t:',t)
            tagLink = link + t
            obj = requests.get(tagLink).json()

            nltk_words = words.words()

            conceptNetList.extend(
                [edge['end']['label'] for edge in obj['edges'] if (edge['end']['label'] in nltk_words and edge['end']['label'] != t)]
            )
            conceptNetList.extend(
                [edge['start']['label'] for edge in obj['edges'] if (edge['start']['label'] in nltk_words and edge['end']['label'] == t)]
                                  )

            # for edge in obj['edges']:
            #     # print('edge: ', edge)
            #     if edge['end']['label'] != t:
            #         if edge['end']['label'] in words.words():
            #             concept = edge['end']['label']
            #             conceptNetList.append(concept)
            #             # print('concept1-1:', concept)
            #     else:
            #         if edge['start']['label'] in words.words():
            #             concept = edge['start']['label']
            #             conceptNetList.append(concept)
            #             # print('concept2-1:', concept)

    # print("conceptNetList_comp is the same as conceptNetList: ", set(conceptNetList) == set(conceptNetList_comp))
    # print(set(conceptNetList), set(conceptNetList_comp))
    print(time.time() - start)
    start = time.time()
    dictionary = PyDictionary()
    #synonyms = []
    synonyms2 = []
    # for x in tags:
    #     if ' ' not in x:
    #         s = dictionary.synonym(x)
    #         #s2 = get_synonym_all(tags)
    #         s2 = get_synonym(x)
    #         if s != None:
    #             #synonyms2.extend(s2)
    #             synonyms.extend(s)

    # synonyms2.extend(get_synonym_all(tags))
    # synonyms2.extend([get_synonym_all(x) for x in tags])
    #synonyms.extend(conceptNetList)
    #synonyms2
    get_syz=get_synonym_all(tags)
    get_syz['conceptNetList']=conceptNetList
    sublist=list(get_syz.values())
    flat_list = list(itertools.chain(*sublist))
    #print(synonyms)
    # for key in get_syz:

    synonym_list=[word for word in flat_list if word not in stop_words]
    #synonym_list = [word for word in synonyms if word not in stop_words]
    print("PyDictionary done")
    print(time.time() - start)

    if synonym_list == []:
        return tags[math.floor(len(tags) / 2)]

    return mostSim(tags, synonym_list), tags, synonym_list

def mostSim(tags, synonym_list):
    #Load medium sized spaCy English model
    global nlp
    start = time.time()
    synonym_list = list(set(synonym_list))

    new_tags_joined = ' '.join(tags)
    new_synonyms_joined = ' '.join(synonym_list)

    new_tags_joined = nlp(new_tags_joined)
    new_synonyms_joined = nlp(new_synonyms_joined)

    dictS = {}
    for s in new_synonyms_joined:
        sumSimilarityscores = 0
        n_tags = 0
        if(s.is_oov):
            continue
        for t in new_tags_joined or t.text in tags:
            if(t.is_oov):
                continue
            score = s.similarity(t)
            sumSimilarityscores += score
            n_tags += 1
        dictS[s.text] =  sumSimilarityscores/n_tags
    # simWord = max(dictS, key=dictS.get)
    dictS_list = dictS.items()
    sorted_list = sorted(dictS_list, key=lambda x: x[1], reverse=True)
    sorted_synonyms = [syn for syn, score in sorted_list]

    random_index = random.randint(0,2)

    print("SpaCy similarity done")
    print(time.time() - start)
    # return 0
    return sorted_synonyms[random_index]

#To Run: place the number of an image in image_number
## testing
# print(generate_clue_from_annos(['food','milk','risk']))
