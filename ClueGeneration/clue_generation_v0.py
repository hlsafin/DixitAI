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
from gensim.test.utils import common_texts
import pickle
import os
import sys
import requests
import random


with open('./Annotations/clippedData.json') as f_c:
    data_c = json.load(f_c)

with open('./Annotations/all_annotations.json') as f_a:
    data_a = json.load(f_a)

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

#Dictionary with hand annotated values
dictAllAnnotations = {}
for image in data_a :
    values = data_a[image]
    imageNum = int(image)
    dictAllAnnotations[imageNum] = {'literal': values['literal_annotations'], 'thematic': values['thematic_annotations']}

#Models

#GenSim with Glove
# model_g = api.load("glove-wiki-gigaword-300")
# #Gensim with Word2Vec
# model_w2v = api.load('word2vec-google-news-300')

#Save Models
# if not os.path.exists('Model'):
#     os.makedirs('Model')
# pickle.dump(model_g, open( 'Model/model_glove.pckl', 'wb' ))
# pickle.dump(model_w2v, open( 'Model/model_w2v.pckl', 'wb' ))

glove_model = pickle.load(open('Model/model_glove.pckl', 'rb' ))
# glove_model = model_g
# w2v_model = model_w2v

def generate_clue(image_num):
    if image_num in dictAllAnnotations:
        literal_list = dictAllAnnotations[image_num]['literal']
        thematic_list = dictAllAnnotations[image_num]['thematic']
        tags = []

        #Take the mid-tier most relevant annotations
        floor_literal = math.floor(len(literal_list) / 3)
        ceil_literal = math.floor(len(literal_list) / 3) * 2

        floor_thematic = math.floor(len(thematic_list) / 3)
        ceiling_thematic = math.floor(len(thematic_list) / 3) * 2

        #Choose one of those mid-tier annotations randomly
        index_literal = random.randint(floor_literal, ceil_literal)
        index_thematic = random.randint(floor_thematic, ceiling_thematic)
        tags.append(literal_list[index_literal])
        tags.append(thematic_list[index_thematic])


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
        return mostSim(glove_model, tags, synonyms)
    elif image_num in dictClarifai:
        annotation_list = dictClarifai[image_num]
        tags = []

        #Take the mid-tier most relevant annotations
        floor_annotations = math.floor(len(annotation_list) / 3)
        ceil_annotations = math.floor(len(annotation_list) / 3) * 2

        #Choose one of those mid-tier annotations randomly
        index = random.randint(floor_annotations, ceil_annotations)
        tags.append(annotation_list[index])

        # if len(annotation_list) <= 3:
        #     tags = annotation_list
        # else:
        #     #Take the mid-tier most relevant annotations
        #     index = math.floor(len(annotation_list) / 2)
        #     tags.append(annotation_list[index - 1])
        #     tags.append(annotation_list[index])
        #     tags.append(annotation_list[index + 1])

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
        return mostSim(glove_model, tags, synonyms)
    else:
        return 'No annotations available'

def mostSim(model, tags, synonym_list):
    synonym_list = set(synonym_list)
    synonym_list = list(synonym_list)

    #Remove non vocab words from tags list
    new_tags = []
    for t in tags:
        if t in model.vocab:
            new_tags.append(t)

    sumSimilarityscores = 0
    scoreCount = 0
    dictS = {}
    for s in synonym_list:
        for t in new_tags:
            if s in model.vocab:
                score = model.similarity(t, s)
                sumSimilarityscores += score
                dictS[s] =  sumSimilarityscores/len(tags)
        sumSimilarityscores = 0
    simWord = max(dictS, key=dictS.get)
    return simWord

#To Run: place the number of an image in image_number
# print(generate_clue(63))
