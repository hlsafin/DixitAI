import json
import numpy as np
import matplotlib.pyplot as plt
with open("data.json") as f:
    data = json.load(f)


new_json={}
for key in data.keys():
    listt = []

    counter = 10
    for str in data[key][:11]:


        if str[0] in ('no person','art','people','illustration'):
            pass
        else:

            listt.append(str)
    new_json[key]=listt

for key in new_json.keys():
    new_json[key]=new_json[key][:10]

#
# with open('clippedData2.json', 'w') as json_file:
#   json.dump(new_json, json_file)


list_of_words=[]
for keys in new_json.keys():
    list_of_words.append(np.asarray(new_json[keys])[:, 0])
concat_words =np.concatenate(np.asarray(list_of_words))
# hist = plt.hist(concat_words)
#
import collections
from heapq import nlargest
dictCount = {}

words,counts= np.unique(concat_words,return_counts=True)
for wrd,cnt in zip(words,counts):
    dictCount[wrd]=cnt


mostcommonwords=nlargest(20, dictCount, key = dictCount.get)
for x in mostcommonwords:
    print(x, round(dictCount[x]/228,ndigits=3))

# plt.xticks(rotation='vertical')
# plt.show()
print('')
new = sorted(dictCount.values())
# with open('clippedData.json', 'w') as json_file:
#   json.dump(new_json, json_file)