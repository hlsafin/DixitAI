import json
from PyDictionary import PyDictionary
import gensim
import nltk
from nltk.corpus import words
import math
import random
from gensim.test.utils import common_texts
from gensim.models import Word2Vec
import gensim.downloader as api
import pickle
import os
import sys
import requests
import random
import spacy


with open('../clarifai/clippedData.json') as f_c:
    data_c = json.load(f_c)
English_words = set(words.words())

#Dictonary with clarifai annotated values
dictClarifai = {}
for image in data_c :
    values = data_c[image]
    img = image.split('.')
    imageNum = int(img[0])

    dictClarifai[imageNum] = []
    annotations = []
    for v in values:
        annotations.append(v[0])

    dictClarifai[imageNum] = annotations

    stop_words = ["person", "no person", "people", "man", "woman", "art",
        "lithograph", "drawing", "painting", "image", "sketch", "color", "design",
        "print", "lithograph", "portrait", "illustration", "girl", "boy"]

def generate_clue(image_num):
    if image_num in dictClarifai:
        annotation_list = dictClarifai[image_num]

        tags = [word for word in annotation_list if word not in stop_words]

        if len(annotation_list) <= 4:
            tags = tags
        else:
            tags = tags[:5]

        #ConceptNet
        #https://github.com/commonsense/conceptnet5/wiki/API
        #https://pyenchant.github.io/pyenchant/tutorial.html
        link = 'http://api.conceptnet.io/c/en/'
        conceptNetList = []
        # print('tags:', tags)
        for t in tags:
            if ' ' not in t:
                # print('t:',t)
                tagLink = link + t
                obj = requests.get(tagLink).json()
                for edge in obj['edges']:
                    # print('edge: ', i)
                    concept = ''
                    if edge['end']['label'] != t:
                        if edge['end']['label'] in words.words():
                            concept = edge['end']['label']
                            # print('label: ', edge['end']['label'], 'concept1:', concept)
                        if concept != '':
                            conceptNetList.append(concept)
                            # print('concept1-1:', concept)
                    else:
                        if edge['start']['label'] in words.words():
                            concept = edge['start']['label']
                            # print('label: ', edge['start']['label'], 'concept2:', concept)
                        if concept != '':
                            conceptNetList.append(concept)
                            # print('concept2-1:', concept)
        # print(tags)
        # print(conceptNetList)
        dictionary = PyDictionary()
        synonyms = []
        for x in tags:
            if ' ' not in x:
                s = dictionary.synonym(x)
                if s != None:
                    synonyms += s
        synonynms = synonyms + conceptNetList
        if synonyms == []:
            return tags[math.floor(len(tags) / 2)]
        return mostSim(tags, synonyms)
    else:
        return 'No annotations available'

def mostSim(tags, synonym_list):
    #Load medium sized spaCy English model
    nlp = spacy.load("en_core_web_md")

    synonym_list = set(synonym_list)
    synonym_list = list(synonym_list)

    #Remove non vocab words from tags list
    new_tags = []
    new_synonyms = []

    for t in tags:
        t_vector = nlp.vocab[t]
        if t in English_words and t_vector.has_vector:
            new_tags.append(t)

    for s in synonym_list:
        s_vector = nlp.vocab[s]
        if s in English_words and s_vector.has_vector:
            new_synonyms.append(s)


    dictS = {}
    for s in new_synonyms:
        sumSimilarityscores = 0
        for t in new_tags:
            s_vector = nlp.vocab[s]
            if s in English_words and s_vector.has_vector:
                t_nlp = nlp(t)
                s_nlp = nlp(s)
                score = s_nlp.similarity(t_nlp)
                sumSimilarityscores += score
        dictS[s] =  sumSimilarityscores/len(new_tags)
    simWord = max(dictS, key=dictS.get)
    dictS_list = dictS.items()
    sorted_list = sorted(dictS_list, key=lambda x: x[1], reverse=True)
    sorted_synonyms = [syn for syn, score in sorted_list]

    random_index = random.randint(0,2)

    return sorted_synonyms[random_index]

def storyteller_select_card(playerCards):
    #Generate a clue for each card in the storyteller's hand
    #Cards are represented by their image number
    dictCards = {}
    nlp = spacy.load("en_core_web_md")
    for card in playerCards:
        clue = generate_clue(card)
        annotation_list = dictClarifai[card]
        tags = filter(annotation_list, stop_words)
        print("Card: ", card)

        if len(annotation_list) <= 4:
            tags = tags
        else:
            tags = tags[:5]
        print("Annotations: ", tags)
        print("Clue:", clue)
        #Remove non vocab words from tags list
        new_tags = []
        new_synonyms = []

        for t in tags:
            t_vector = nlp.vocab[t]
            if t in English_words and t_vector.has_vector:
                new_tags.append(t)

        sumSimilarityscores = 0
        for t in new_tags:
            clue_vector = nlp.vocab[clue]
            if clue in English_words and clue_vector.has_vector:
                clue_nlp = nlp(clue)
                t_nlp = nlp(t)
                score = clue_nlp.similarity(t_nlp)
                sumSimilarityscores += score
        dictCards[clue] =  sumSimilarityscores/len(new_tags)
    simWord = min(dictCards, key=dictCards.get)
    print(dictCards)
    #Estimate how good the clue is using metric

    #Choose the card that produces metric that will result in at least one player guessing the generate_clue

    #Return card

    return simWord

def filter(unfiltered_list, filter_words):
    filtered = [word for word in unfiltered_list if word not in filter_words]
    return filtered

print(storyteller_select_card([63, 214, 200, 177, 188, 159]))
