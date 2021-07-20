import json

with open("data.json") as f:
    data = json.load(f)


new_json={}
for key in data.keys():
    listt = []

    counter = 10
    for str in data[key][:11]:


        if str[0]=='no person':
            pass
        else:

            listt.append(str)
    new_json[key]=listt

for key in new_json.keys():
    new_json[key]=new_json[key][:10]




with open('clippedData.json', 'w') as json_file:
  json.dump(new_json, json_file)