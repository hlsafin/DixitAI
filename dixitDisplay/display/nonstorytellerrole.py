# -*- coding: utf-8 -*-
"""NonStoryTellerRole.ipynb

"""

import random
import spacy
# !pip install -U spacy
# !python -m spacy download en_core_web_md
#Load medium sized spaCy English model

def nonStoryTellerSelectCard(dictAnnotations, playersCards, clue, decoy):
  sim = []
  dictS = {}
  nlp = spacy.load("en_core_web_md")
  for c in playersCards:
    #clarifai_annotations
    annotation_list = dictAnnotations[c]
    #Remove any words releted to "art", "illustration", "drawing", etc.
    stop_words = ["person", "no person", "people", "man", "woman", "art",
    "lithograph", "drawing", "painting", "image", "sketch", "color", "design",
    "print", "lithograph", "portrait", "illustration", "girl", "boy", 'one']
    tags = [word.strip() for word in annotation_list if word.strip() not in stop_words]
    #print(tags)

    new_tags = ' '.join(tags)
    new_tags_spacy = nlp(new_tags)
    clue_ = nlp(clue)
    sumSimilarityscores = 0
    count = 0
    for t in new_tags_spacy:
      if (t.is_oov):
        continue
      score = t.similarity(clue_)
      #print(score)
      sumSimilarityscores += score
      count += 1

    dictS[c] = sumSimilarityscores/count

  #sort dictionary
  dictS_list = dictS.items()
  sorted_list = sorted(dictS_list, key=lambda x: x[1], reverse=True)
  print(sorted_list)
  sorted_cards = [card for card, score in sorted_list]
  print(sorted_cards)
  #if selecting decoy card from own hand, decoy = true
  if decoy:
    max_card = sorted_list[0][0]
    max_value = sorted_list[0][1]
  else: #selecting the storyteller's card from all the other players cards
    random_index = random.randint(0,len(sorted_list)-1)
    print(random_index)
    max_card = sorted_list[random_index][0]
    max_value = sorted_list[random_index][1]
    
  #print(max_card, max_value)
  return max_card,max_value

#Testing
# from IPython.display import Image
# import spacy
# #Image('example.png')
# path = 'DixitCards/images/'
# image = 34
# cards = [1 , 2, 3 ,4, 5, 6]
# clue = "escape"
# print("card: " + clue )
# display(Image(path + str(image)+'.jpg', width=100, height=100))
# print("Cards in Hand")

# cardC = nonStoryTellerSelectCard(annotations, cards,clue, False)

# print("Card chosen")
# print("clue:", clue)
# display(Image(path + str(cardC[0])+'.jpg', width=100, height=100))