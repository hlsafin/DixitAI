from django.shortcuts import render, redirect
from django.http import HttpResponse
#from .forms import AnnotationForm, LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
import csv
import math
import os
import random
import base64
import json
import time
from . import clue_generation
from .models import *
from .forms import *
from . import playerClasses

ANNOTATION_URL = 'display/static/annotations/'
IMAGE_URL = 'display/static/images/'
MAX_PLAYERS = 4
CARDS_IN_HAND = 5
N_CARDS_IN_DECK = 228
GAME_STATES = ['Storyteller', 'GetDecoys', 'GuessStorytellerCard']
img_skip_list = [133, 98, 110]

prev_call = time.time()


def index(request):

    #if(imgStr in annoJSON):
        #annotations = ", ".join(annoJSON[imgStr]['literal_annotations']) + ", " + ", ".join(annoJSON[imgStr]['thematic_annotations'])
    #else:
         #annotations = "No annotations found"
    image_num = random.choice(range(N_CARDS_IN_DECK))+1

    hand = [0]*CARDS_IN_HAND

    for i in range(CARDS_IN_HAND):
        handNum = random.choice(range(N_CARDS_IN_DECK))+1
        while(handNum in hand or image_num == handNum):
            handNum = random.choice(range(N_CARDS_IN_DECK))+1
        hand[i] = handNum

    img1 =  IMAGE_URL+str(hand[0])+'.jpg'

    with open(img1, 'rb') as i1:
        image_data1 = base64.b64encode(i1.read()).decode('utf-8')

    img2 = IMAGE_URL+str(hand[1])+'.jpg'

    with open(img2, 'rb') as i2:
        image_data2 = base64.b64encode(i2.read()).decode('utf-8')

    img3 =  IMAGE_URL+str(hand[2])+'.jpg'

    with open(img3, 'rb') as i3:
        image_data3 = base64.b64encode(i3.read()).decode('utf-8')

    img4 = IMAGE_URL+str(hand[3])+'.jpg'

    with open(img4, 'rb') as i4:
        image_data4 = base64.b64encode(i4.read()).decode('utf-8')

    img5 = IMAGE_URL+str(hand[4])+'.jpg'

    with open(img5, 'rb') as i5:
        image_data5 = base64.b64encode(i5.read()).decode('utf-8')

    #form = AnnotationForm({'image_num': image_num, 'literal_annotation':'', 'thematic_annotation':''})
    image_path = IMAGE_URL+str(image_num)+'.jpg'

    annotations = return_ann(image_path)

    #Remove any words releted to "art", "illustration", "people", etc.
    stop_words = ["person", "no person", "people", "man", "woman", "art",
    "lithograph", "drawing", "painting", "image", "sketch", "color", "design",
    "print", "lithograph", "portrait", "illustration", "girl", "boy", 'one']

    annoList = annotations.split(",")

    filtered_annotations = [word.strip() for word in annoList if word.strip() not in stop_words]
    print(filtered_annotations)

    lastAnnos, tags, synonym_list = clue_generation.generate_clue_from_annos(annoList)
    print(lastAnnos)

    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    return render(request, 'displayTemplate.html', {'image':image_data, 
                                                    'annotations': lastAnnos, 
                                                    'hand1': image_data1, 
                                                    'hand2': image_data2, 
                                                    'hand3': image_data3, 
                                                    'hand4': image_data4, 
                                                    'hand5': image_data5, 
                                                    'clarifai': filtered_annotations, 
                                                    'tags': tags, 
                                                    'synonyms':synonym_list})


from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

import os
import json

def return_ann(image_path):
    stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

    file1 = open(os.path.join(os.path.realpath('.'),"api_key.txt"),"r+")
    key = file1.readline().rstrip("\n")
    file1.close()

    # This is how you authenticate.
    metadata = (('authorization', 'Key '+ key),)

    data = []
    test_image = "https://pocket-image-cache.com/direct?url=https%3A%2F%2Fpocket-syndicated-images.s3.amazonaws.com%2F5d1625e19354f.jpg"

    with open(image_path, "rb") as f:
        file_bytes = f.read()

    request = service_pb2.PostModelOutputsRequest(
        # This is the model ID of a publicly available General model. You may use any other public or custom model ID.
        model_id='aaa03c23b3724a16a56b629203edc62c',
        inputs=[
        resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))
        ])
    response = stub.PostModelOutputs(request, metadata=metadata)

    if response.status.code != status_code_pb2.SUCCESS:
        raise Exception("Request failed, status code: " + str(response.status.code))

    for concept in response.outputs[0].data.concepts:
        print('%12s: %.2f' % (concept.name, concept.value))
        data.append(concept.name)

    return ", ".join(data)

def newGame(request, game_num = None):
    if(request.method == 'GET'):
        if(game_num == None):
            form = JoinGameForm()
            return render(request, "new_game.html", {'form':form})
        else:
            form = JoinGameForm()
            game = Game.objects.filter(pk=game_num)
            if(len(game) == 0):
                return redirect('/new_game/')
            else:
                game = game[0]
            player_ids = eval(game.player_ids)
            if('player_name' in request.session):
                player_name = request.session['player_name']
                if(player_name not in player_ids):
                    player_name = None
            else:
                player_name = None

            print(player_name)

            if(game.n_players >= MAX_PLAYERS and player_name == None):
                return render(request, "new_game.html", {'form':form, 'errors':'Game full'})
            elif(player_name != None and game.n_players < MAX_PLAYERS):
                return render(request, "waiting_room.html", {'form':form, 
                                                             'info': str(game.n_players) + ' have joined.', 
                                                             'players':player_ids, 
                                                             'game_url':'/new_game/'+str(game_num)}
                )
            elif(player_name != None and game.n_players >= MAX_PLAYERS):
                return redirect('/play_game/'+str(game_num))
            elif(player_name == None and game.n_players < MAX_PLAYERS):
                return render(request, "new_game.html", {'form':form})

    elif(request.method == 'POST'):
        form = JoinGameForm(request.POST)
        print(game_num)
        if(form.is_valid()):
            # player = Player.objects.create(**form.cleaned_data)
            # player = Player.objects.get(pk = form.cleaned_data['player_name'])
            player = Player.objects.filter(pk = form.cleaned_data['player_name'])
            if(len(player) == 0):
                player = Player.objects.create(**form.cleaned_data)
            else:
                player = player[0]
                player.role = 'Guesser'
                player.save()
            request.session['player_name'] = player.player_name

            if(game_num == None):
                agent_player = Player.objects.filter(pk = 'DixitAI')
                if(len(agent_player) == 0):
                    agent_player = Player.objects.create(player_name = 'DixitAI', role = 'Storyteller')
                else:
                    agent_player = agent_player[0]
                    agent_player.role = 'Storyteller'
                    agent_player.save()
                
                game = Game.objects.create(player_ids = str([agent_player.player_name, player.player_name]))
                agent_player.game_foreign_key.add(game)
                player.game_foreign_key.add(game)
                player.role = 'Guesser'
                game_num = game.id
                game.n_players += 1
                game_full = False
                request.session['game_num'] = game_num
                
                agent_player.save()
                player.save()
                game.save()

                return redirect('/new_game/'+str(game_num))
            
            else:
                game = Game.objects.get(pk=game_num)
                player.game_foreign_key.add(game)
                player_ids = eval(game.player_ids)
                player_ids.append(form.cleaned_data['player_name'])
                game.n_players += 1
                if(game.n_players >= MAX_PLAYERS):
                    game_full = True
                else:
                    game_full = False
                game.player_ids = str(player_ids)
                game.save()
            
            player.save()

            if(game_full):
                return redirect('/play_game/'+str(game_num))
            else:
                return redirect('/new_game/'+str(game_num))

        else:
            return render(request, "new_game.html", {'form':form, 'errors':form.errors})

def playGame(request, game_num=None):
    global prev_call
    if(game_num == None):
        return HttpResponse('Game number missing. Bad request.')
    else:
        if('player_name' in request.session):
            player_name = request.session.get('player_name')
        else:
            return redirect('/new_game/'+str(game_num))

    game = Game.objects.filter(pk = game_num)
    if(len(game) == 0):
        return redirect('/new_game/')
    else:
        game = game[0]
    player = Player.objects.get(pk = player_name)
    game_state = eval(game.state)
    print("Player: ", player.player_name)
    print("Role: ", player.role)
    print("Game State: ", game_state)
    print("Game Log: ", game.game_log)

    if(player_name not in eval(game.player_ids)):
        return redirect('/new_game/'+str(game_num))

    if(game.game_log == ''):
        game_log = []
    else:
        game_log = eval(game.game_log)

    if(game_state['round'] == 0):
        game_state = {'round':1, 'turn': 'Storyteller'}
        scores = [[]]
        for i, p_name in enumerate(eval(game.player_ids)):
            scores[0].append({'player_name': p_name, 'score': 0})
            p = Player.objects.get(pk = p_name)
            p.cards = ''
            p.save()
        game.scores = str(scores)
        game.state = str(game_state)
        game.save()

    print(eval(game.first_load))
    if(eval(game.first_load) == None):
        game.first_load = str([])
        print(game.first_load)
        game.save()

    first_load = eval(game.first_load)
    if(first_load == None):
        first_load = []

    print("Getting agent stuff")
    agent_player = Player.objects.get(pk='DixitAI')
    used_cards = []
        
    if(game.used_cards != ''):
        used_cards = eval(game.used_cards)

    if(agent_player.cards == ''):
        hand = [0]*CARDS_IN_HAND

        for i in range(CARDS_IN_HAND):
            handNum = random.choice(range(N_CARDS_IN_DECK))+1
            if(game.used_cards != ''):
                used_cards = eval(game.used_cards)
            while(handNum in hand or handNum in used_cards or handNum in img_skip_list):
                if(game.used_cards != ''):
                    used_cards = eval(game.used_cards)
                handNum = random.choice(range(N_CARDS_IN_DECK))+1
            hand[i] = handNum
            used_cards.append(handNum)
            game.used_cards = str(used_cards)
            game.save()
            print(used_cards)
        
    else:
        hand = eval(agent_player.cards)
        print("Player hand: ", hand)
        
        if(len(hand)<CARDS_IN_HAND):
            for i in range(len(hand), CARDS_IN_HAND):
                handNum = random.choice(range(N_CARDS_IN_DECK))+1
                while(handNum in hand or handNum in used_cards or handNum in img_skip_list):
                    used_cards = eval(game.used_cards)
                    handNum = random.choice(range(N_CARDS_IN_DECK))+1
                hand.append(handNum)
                used_cards.append(handNum)
                game.used_cards = str(used_cards)
                game.save()
                print(used_cards)
    
    agent_player.cards = str(hand)
    agent_player.save()
    game.used_cards = str(used_cards)
    game.save()

    AgentClassObject = playerClasses.AgentClass(eval(agent_player.cards), 'DixitAI')
    AgentClassObject.setRole(agent_player.role)
    game.first_load = str(set([]))
    print(game_state)
    print(game.loading_agent)

    if(game.loading_agent == 'False' or time.time() - prev_call > 40):
        prev_call = time.time()
        print(agent_player.role)
        if(agent_player.role == 'Storyteller' and game_state['turn'] == 'Storyteller' and len(game_log)<game_state['round']):
            game.loading_agent = 'True'
            game.save()
            game_log.append({'Round': game_state['round'], 'Storyteller': agent_player.player_name})
            game.game_log = str(game_log)
            game.save()
            try:
                image_num, clue = AgentClassObject.storyteller_clue()
            except:
                image_num, clue = AgentClassObject.storyteller_clue()
                game.loading_agent = 'False'
                game.save()

            print(image_num, clue)
            game_state['turn'] = 'GetDecoys'
            game_log = eval(game.game_log)
            game_log[-1]['Clue'] = clue
            game_log[-1]['decoys'] = {agent_player.player_name:image_num}
            game.state = str(game_state)
            game.game_log = str(game_log)

            newHand = eval(agent_player.cards)
            for card in eval(agent_player.cards):
                if(card == image_num):
                    newHand.remove(card)
            agent_player.cards = str(newHand)
                
            agent_player.save()
            game.loading_agent = 'False'
            game.save()

        else: 
            if(agent_player.role == 'Guesser' and game_state['turn'] == 'GetDecoys' and ('decoys' not in game_log[-1] or agent_player.player_name not in game_log[-1]['decoys'])):
                game.loading_agent = 'True'
                game.save()
                game_log = eval(game.game_log)
                if('decoys' not in game_log[-1]):
                    game_log[-1]['decoys'] = {}
                game_log[-1]['decoys'][agent_player.player_name] = -1

                try:
                    decoy = AgentClassObject.get_decoy(game_log[-1]['Clue'])
                except:
                    decoy = AgentClassObject.get_decoy(game_log[-1]['Clue'])
                    game.loading_agent = 'False'
                    game.save()
                
                game = Game.objects.get(pk = game_num)
                game_log = eval(game.game_log)
                if('decoys' not in game_log[-1]):
                    game_log[-1]['decoys'] = {}
                game_log[-1]['decoys'][agent_player.player_name] = int(decoy)
                game.game_log = str(game_log)
                newHand = eval(agent_player.cards)
                for card in eval(agent_player.cards):
                    if(card == int(decoy)):
                        newHand.remove(card)
                
                agent_player.cards = str(newHand)
                
                agent_player.save()
                game.loading_agent = 'False'
                game.save()

                if(len(game_log[-1]['decoys'].keys()) >= MAX_PLAYERS):
                    game_state['turn'] = 'GuessStorytellerCard'
                    game.state = str(game_state)
                    game.save()

            elif(agent_player.role == 'Guesser' and game_state['turn'] == 'GuessStorytellerCard' and ('guesses' not in game_log[-1] or agent_player.player_name not in game_log[-1]['guesses'])):
                game.loading_agent = 'True'
                game.save()
                decoyCards = []
                for i, p_name in enumerate(game_log[-1]['decoys']):
                    if(p_name == agent_player.player_name):
                        continue
                    decoyCards.append(game_log[-1]['decoys'][p_name])
                try:
                    guess = AgentClassObject.guess_storyteller_card(decoyCards, game_log[-1]['Clue'])
                except:
                    guess = AgentClassObject.guess_storyteller_card(decoyCards, game_log[-1]['Clue'])
                    game.loading_agent = 'False'
                    game.save()

                game = Game.objects.get(pk = game_num)
                game_log = eval(game.game_log)
                if('guesses' not in game_log[-1]):
                    game_log[-1]['guesses'] = {}
                    
                game_log[-1]['guesses'][agent_player.player_name] = int(guess)
                game.game_log = str(game_log)
                game.loading_agent = 'False'
                game.save()

                if(len(game_log[-1]['guesses'].keys()) == MAX_PLAYERS-1):
                    game_state['turn'] = 'Storyteller'
                    game_state['round'] += 1
                    print(game_state['round'])
                    
                    game.state = str(game_state)
                    game.save()

                    iteration = math.ceil(game_state['round']/MAX_PLAYERS)
                    storyteller_turns = eval(game.player_ids)*iteration
                    print(storyteller_turns)
                    new_storyteller = storyteller_turns[game_state['round']-1]
                    
                    player_names = eval(game.player_ids)
                    for p_name in player_names:
                        p = Player.objects.get(pk = p_name)
                        if(p_name == new_storyteller):
                            p.role = 'Storyteller'
                        else:
                            p.role = 'Guesser'
                    
                        p.save()
    
    if(request.method == 'GET'):
        used_cards = []
            
        if(game.used_cards != ''):
            used_cards = eval(game.used_cards)

        if(player.cards == ''):
            hand = [0]*CARDS_IN_HAND

            for i in range(CARDS_IN_HAND):
                handNum = random.choice(range(N_CARDS_IN_DECK))+1
                if(game.used_cards != ''):
                    used_cards = eval(game.used_cards)
                while(handNum in hand or handNum in used_cards or handNum in img_skip_list):
                    if(game.used_cards != ''):
                        used_cards = eval(game.used_cards)
                    handNum = random.choice(range(N_CARDS_IN_DECK))+1
                hand[i] = handNum
                used_cards.append(handNum)
                game.used_cards = str(used_cards)
                game.save()
                print(used_cards)
            
        else:
            hand = eval(player.cards)
            print("Player hand: ", hand)
            
            if(len(hand)<CARDS_IN_HAND):
                for i in range(len(hand), CARDS_IN_HAND):
                    handNum = random.choice(range(N_CARDS_IN_DECK))+1
                    while(handNum in hand or handNum in used_cards or handNum in img_skip_list):
                        used_cards = eval(game.used_cards)
                        handNum = random.choice(range(N_CARDS_IN_DECK))+1
                    hand.append(handNum)
                    used_cards.append(handNum)
                    game.used_cards = str(used_cards)
                    game.save()
                    print(used_cards)
        
        player.cards = str(hand)
        player.save()
        game.used_cards = str(used_cards)
        game.save()
        hand = eval(player.cards)

        imgs = []
        for i, card in enumerate(hand):
            img = IMAGE_URL+str(card)+'.jpg'
            imgs.append({})
            imgs[-1]['img_num'] = card
            with open(img, 'rb') as im:
                imgs[-1]['img_data'] = base64.b64encode(im.read()).decode('utf-8') 

        form = GameForm()
        if(player.role == 'Guesser'):
            form.clue = 'N/A'
        

        if(game_state['turn'] == 'Storyteller'):
            if(player.role == 'Guesser'):
                refresh = True
                first_load = eval(game.first_load)
                first_load = list(first_load)
                if(first_load == None):
                    first_load = []

                first_load.append(player_name)
                game.first_load = str(first_load)
                print(game.first_load)
                game.save()
            else:
                refresh = False

            return render(request, 'play_game.html', {'form': form, 'player_name': player_name, 'player_role': player.role, 'imgs': imgs, 'refresh': refresh, 
                                                      'game_num': game_num, 'scores': eval(game.scores)[-1], 'scores': eval(game.scores)[-1],
                                                      'game_state' : eval(game.state), 'storyteller': eval(game.game_log)[-1]['Storyteller']})

        else:
            # if('guesses' in game_log[-1] and len(game_log[-1]['guesses'].keys()) == MAX_PLAYERS-1):
            #     print("Got all guesses")
            #     print(game_state['round'])
                        
            #     game.state = str(game_state)
            #     dictPlayers = []
            #     for i, p_name in enumerate(eval(game.player_ids)):
            #         p = Player.objects.get(pk = p_name)
            #         if(player_name == game_log[-1]['Storyteller']):
            #             guess = None
            #         else:
            #             guess = game_log[-1]['guesses'][player_name] 
            #         dictPlayers.append({'player_info': p, 'card_guessed':guess})

            #     GameObject = playerClasses.GameClass(game_log = game_log, n_players = game.n_players, 
            #                                         player_ids = eval(game.player_ids), scores = eval(game.scores),
            #                                         used_cards=eval(game.used_cards), game_state=game_state)
            #     updatedScores = GameObject.calculateScore(dictPlayers)
            #     scores = eval(game.scores)
            #     scores.append([])
            #     for player_name in updatedScores:
            #         score = updatedScores[player_name]
            #         scores[-1].append({'player_name': player_name, 'score': score})
            #     game.scores = str(scores)                 
            #     game.save()

            #     iteration = math.ceil(game_state['round']/MAX_PLAYERS)
            #     storyteller_turns = eval(game.player_ids)*iteration
            #     print(storyteller_turns)
            #     new_storyteller = storyteller_turns[game_state['round']-1]
                
            #     player_names = eval(game.player_ids)
            #     for p_name in player_names:
            #         p = Player.objects.get(pk = p_name)
            #         if(p_name == new_storyteller):
            #             p.role = 'Storyteller'
            #         else:
            #             p.role = 'Guesser'
                
            #         p.save()
            #     return render(request, 'play_game.html', {'form': form, 'player_name': player_name, 'player_role': player.role, 'imgs': imgs, 'refresh': False,
            #                                               'game_num': game_num, 'clue': game_log[-1]['Clue'], 'scores': eval(game.scores)[-1]})

            game_log = eval(game.game_log)
            if(len(game_log[-1]['decoys']) == MAX_PLAYERS):
                decoy_imgs = []
                refresh = False
                guessed = False

                if(player.role == 'Storyteller'):
                    refresh = True
                    guessed = True

                for i, p_name in enumerate(game_log[-1]['decoys']):
                    card = game_log[-1]['decoys'][p_name]
                    if(p_name == player_name and player.role != 'Storyteller'):
                        continue
                    decoy_img = IMAGE_URL+str(card)+'.jpg'
                    decoy_imgs.append({})
                    decoy_imgs[-1]['img_num'] = card
                    decoy_imgs[-1]['grey'] = False
                    
                    print(game_log)
                    if(('guesses' in game_log[-1]) and (player.player_name in game_log[-1]['guesses'])):
                        refresh = True
                        guessed = True
                        if(decoy_imgs[-1]['img_num'] != game_log[-1]['guesses'][player.player_name]):
                            decoy_imgs[-1]['grey'] = True

                    with open(decoy_img, 'rb') as im:
                        decoy_imgs[-1]['img_data'] = base64.b64encode(im.read()).decode('utf-8')

                return render(request, 'play_game.html', {'form': form, 'player_name': player_name, 'player_role': player.role, 'imgs': imgs, 
                                                          'storyteller': eval(game.game_log)[-1]['Storyteller'],
                                                          'refresh': refresh, 'waiting':False, 'game_state': eval(game.state), 'decoy_imgs': decoy_imgs, 
                                                          'game_num': game_num, 'clue': game_log[-1]['Clue'], 'scores': eval(game.scores)[-1], 'guessed':guessed})
            
            elif(player.player_name in game_log[-1]['decoys']):
                waiting_for = eval(game.player_ids)
                for p_name in game_log[-1]['decoys']:
                    waiting_for.remove(p_name)
                return render(request, 'play_game.html', {'form': form, 'player_name': player_name, 'player_role': player.role, 'imgs': imgs, 
                                                          'storyteller': eval(game.game_log)[-1]['Storyteller'],
                                                          'refresh': True, 'waiting':True, 'game_state' : eval(game.state), 'decoy_imgs': waiting_for, 
                                                          'game_num': game_num, 'clue': game_log[-1]['Clue'], 'scores': eval(game.scores)[-1]})

            else:
                return render(request, 'play_game.html', {'form': form, 'player_name': player_name, 'player_role': player.role, 'imgs': imgs, 'refresh': False,
                                                          'storyteller': eval(game.game_log)[-1]['Storyteller'],
                                                          'game_num': game_num, 'clue': game_log[-1]['Clue'], 'scores': eval(game.scores)[-1], 
                                                          'game_state' : eval(game.state)})

    else:
        form = GameForm(request.POST)
        if(form.is_valid()):
            if(player.role == 'Storyteller' and game_state['turn'] == 'Storyteller'):
                if(form.cleaned_data['clue'] == ''):
                    return HttpResponse('No Clue give. Bad Request.')

                game_state['turn'] = 'GetDecoys'
                game.state = str(game_state)
                if(len(game_log) == game_state['round']):
                    game_log[-1] = {'Round': game_state['round'], 'Clue': form.cleaned_data['clue'], 'Storyteller': player_name}
                else:
                    game_log.append({'Round': game_state['round'], 'Clue': form.cleaned_data['clue'], 'Storyteller': player_name})
                game_log[-1]['decoys'] = {player_name:int(form.cleaned_data['img_num'])}
                
                game.game_log = str(game_log)
                game.save()

                newHand = eval(player.cards)
                for card in eval(player.cards):
                    if(card == int(form.cleaned_data['img_num'])):
                        newHand.remove(card)
                player.cards = str(newHand)
                    
                player.save()
                

            else: 
                if(game_state['turn'] == 'GetDecoys'):
                    game_log = eval(game.game_log)
                    if('decoys' not in game_log[-1]):
                        game_log[-1]['decoys'] = {}
                    game_log[-1]['decoys'][player_name] = int(form.cleaned_data['img_num'])
                    game.game_log = str(game_log)
                    game.save()
                    newHand = eval(player.cards)
                    for card in eval(player.cards):
                        if(card == int(form.cleaned_data['img_num'])):
                            newHand.remove(card)
                    
                    player.cards = str(newHand)
                    
                    player.save()
                    game.save()

                    if(len(game_log[-1]['decoys'].keys()) >= MAX_PLAYERS):
                        game_state['turn'] = 'GuessStorytellerCard'
                        game.state = str(game_state)
                        game.save()

                elif(game_state['turn'] == 'GuessStorytellerCard'):
                    if('guesses' not in game_log[-1]):
                        game_log[-1]['guesses'] = {}
                    game_log[-1]['guesses'][player_name] = int(form.cleaned_data['img_num'])
                    game.game_log = str(game_log)
                    game.save()

                    if(len(game_log[-1]['guesses'].keys()) == MAX_PLAYERS-1):
                        game_state['turn'] = 'Storyteller'
                        game_state['round'] += 1
                        print("Got all guesses")
                        print(game_state['round'])
                                
                        game.state = str(game_state)
                        dictPlayers = []
                        for i, p_name in enumerate(eval(game.player_ids)):
                            p = Player.objects.get(pk = p_name)
                            if(player_name == game_log[-1]['Storyteller']):
                                guess = None
                            else:
                                guess = game_log[-1]['guesses'][player_name] 
                            dictPlayers.append({'player_info': p, 'card_guessed':guess})

                        GameObject = playerClasses.GameClass(game_log = game_log, n_players = game.n_players, 
                                                            player_ids = eval(game.player_ids), scores = eval(game.scores),
                                                            used_cards=eval(game.used_cards), game_state=game_state)
                        updatedScores = GameObject.calculateScore(dictPlayers)
                        scores = eval(game.scores)
                        scores.append([])
                        for player_name in updatedScores:
                            score = updatedScores[player_name]
                            scores[-1].append({'player_name': player_name, 'score': score})
                        game.scores = str(scores)                 
                        game.save()

                        iteration = math.ceil(game_state['round']/MAX_PLAYERS)
                        storyteller_turns = eval(game.player_ids)*iteration
                        print(storyteller_turns)
                        new_storyteller = storyteller_turns[game_state['round']-1]
                        
                        player_names = eval(game.player_ids)
                        for p_name in player_names:
                            p = Player.objects.get(pk = p_name)
                            if(p_name == new_storyteller):
                                p.role = 'Storyteller'
                                if(p_name != 'DixitAI'):
                                    game_log.append({'Storyteller': p_name})
                                    game.game_log = str(game_log)
                                    game.save()
                            else:
                                p.role = 'Guesser'
                        
                            p.save()

        return redirect('/play_game/' + str(game_num))