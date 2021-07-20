import random
import os
from . import clue_generation
from .nonstorytellerrole import nonStoryTellerSelectCard
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

import json

ANNOTATION_URL = 'display/static/annotations/'
IMAGE_URL = 'display/static/images/'

class PlayerClass():

    def __init__(self, cards = '', player_name = ''):
        self.cardsInHand = cards
        self.player_name = player_name
        self.role = 'Guesser'
    
    def addCard(self, card):
        if(len(self.cardsInHand) == 6):
            print('Err: Hand full in PlayerClass. Can\'t add more cards. ')
            return 0
        self.cardsInHand.append(int(card))
        return 1

    def setRole(self, role):
        if(role not in ['Storyteller', 'Guesser']):
            print('Err: Invalid role')
            return 0
        self.role = role
        return 1

    def removeCard(self, card):
        if(len(self.cardsInHand) == 0):
            print('Err: Hand full in PlayerClass. Can\'t remove more cards. ')
            return 0
        self.cardsInHand.remove(int(card))
        return 1

    def getHand(self):
        return self.cardsInHand



class AgentClass(PlayerClass):

    def __init__(self, cards, player_name = ''):
        super().__init__(cards, player_name)
        # add dictionaries, models etc. 


    def return_ann(self,image_path):
        stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

        file1 = open(os.path.join(os.path.realpath('.'),"api_key.txt"),"r+")
        key = file1.readline().rstrip("\n")
        file1.close()

        # This is how you authenticate.
        metadata = (('authorization', 'Key '+ key),)

        data = []

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


    def storyteller_clue(self):
        flag = True
        image_path = ''
        while(flag):
            image_num = random.choice(self.cardsInHand)
            # if(image_num == 110 or image_num == 0):
            #     continue
            if(str(image_num)+'.jpg' in os.listdir(IMAGE_URL)):
                flag = False
                image_path = IMAGE_URL + str(image_num)+'.jpg'

        annotations = self.return_ann(image_path)
        annoList = annotations.split(",")
        clue, _, _ = clue_generation.generate_clue_from_annos(annoList)

        return (image_num, clue)

    
    def get_decoy(self, clue):
        ''' Selects a card from hand that matches the clue as closely as possible. '''

        clue = clue
        playersCards = self.cardsInHand
        dictAnnotations = {}
        for cards in playersCards:
            image_path = IMAGE_URL+str(cards)+'.jpg'
            annotations = self.return_ann(image_path)
            annoList = annotations.split(",")
            dictAnnotations[cards] = annoList

        maxcard, maxvalue = nonStoryTellerSelectCard(dictAnnotations, playersCards, clue, True)
        selectedCard = maxcard
        return selectedCard

    def guess_storyteller_card(self, arrayCards, clue): 
        ''' Selects the card that would be the storytellers'''

        #cards chosen (decoy + storyteller card)

        clue = clue
        playersCards = arrayCards
        dictAnnotations = {}
        for cards in playersCards:
            image_path = IMAGE_URL+str(cards)+'.jpg'
            annotations = self.return_ann(image_path)
            annoList = annotations.split(",")
            dictAnnotations[cards] = annoList

        card, value = nonStoryTellerSelectCard(dictAnnotations, playersCards, clue, False)
        selectedCard = card
        return selectedCard

    def setRole(self, role):
        return super().setRole(role)

    def getHand(self):
        return super().getHand()

    
class DeckOfCards():
    def __init__(self, used_cards = []):
        self.cardsInDeck = []

        for i in range (1, 229):
            if(i in used_cards):
                continue
            self.cardsInDeck.append(i)
        random.shuffle(self.cardsInDeck)

    def getCard(self):
        if len(self.cardsInDeck) == 0:
            # for i in range (0, 228):
            #     self.cardsInDeck.append(i)
            # random.shuffle(self.cardsInDeck)
            return -1
        
        return self.cardsInDeck.pop()


class GameClass():
    def __init__(self, game_log = '', n_players = 1, player_ids = '', scores = '', used_cards = '', game_state = ''):
        self.game_log = game_log
        self.game_state = game_state
        self.round = self.game_state['round']
        self.n_players = n_players
        self.player_ids = player_ids
        self.scores = scores
        self.used_cards = used_cards
        self.clue = None
        self.deck = DeckOfCards(used_cards)

    def clue_from_storyteller(self, clue):
        if(clue == None or clue == ''):
            return 'Error: Clue None or empty string.'
        else:
            self.clue = clue

    def start_game(self):
        self.storyteller = self.player_ids[0]
        self.game_log.append({'storyteller': self.storyteller, 'round': 1})
    
    def calculateScore(self, dictA):
        #dictionary: [{player info (player_name, role, cardsinHand), cardGuessed}]
        playerGuesses = {}
        storyTellerCard = None
        storyTeller = {}
        numPlayer = self.n_players - 1
        playerCards = {}
        storyTellerName = ""
        current_scores = {}
        print(self.scores[-1])
        for score_dict in self.scores[-1]:
            current_scores[score_dict['player_name']] = score_dict['score']
        print(current_scores)
        #store player guesses and storyteller card
        for playA in dictA:
            print(playA)
            player_info = playA['player_info']
            cardGuessed = playA['card_guessed']
            role = player_info.role
            cards = eval(player_info.cards)
            player_name = player_info.player_name
            if role == 'Guesser':
                playerGuesses[player_name] = cardGuessed
                playerCards[player_name] = cards
            else:
                storyTellerCard = cardGuessed
                storyTellerName = player_name

        #count the number of correct guesses of cards
        countGuesses = 0
        correctPlayers = []
        for key in playerGuesses:
            player_name = key
            guess = playerGuesses[player_name]
            #print(guess)
            if guess == storyTellerCard:
                countGuesses+=1
                correctPlayers.append(player_name)

        scores = {}
        storytellerPt = 0
        playerPt = 0
        addPoints = False 
        #score calculation
        if countGuesses == numPlayer:
            #if all players have found storytellers card 
            storytellerPt = 0
            playerPt = 2
            addPoints =  True
        elif countGuesses == 0: 
            #none of the player found storytellers card
            storytellerPt = 0
            playerPt = 2
            addPoints = True
        else:
            #otherwisecardsInHand
            storytellerPt = 3
            playerPt = 3


        current_scores[storyTellerName] = current_scores[storyTellerName] + storytellerPt
        #updates scores for nonstoryteller players
        for key in playerCards:
            playerName = key
            cards = playerCards[key]
            if addPoints: #if all players get points
                current_scores[playerName] += playerPt
            else:  #if only some players get points
                if playerName in correctPlayers:
                    current_scores[playerName] += playerPt
            #check if other players guessed their decoy card and if so add an additional point
            for x in playerGuesses:
                cardX = playerGuesses[x]
                if cardX in cards: 
                    current_scores[playerName] += 1

        return current_scores
        
                    


            


###################TEST############################          



# ply1 = PlayerClass(1, 2, 3, 4, 5, 6, player_name = 'TestPlayer1')
# ply2 = PlayerClass(11, 12, 13, 14, 15, 16, player_name = 'TestPlayer2')
# ag1 = AgentClass(21, 22, 23, 24, 25, 26, player_name = 'TestAgent')



# game = GameClass()
# ply2.role = 'StoryTeller'
# game.clue = 'light'
# game.player_ids = ['TestPlayer1', 'TestPlayer2', 'TestAgent']
# game.scores = scores = {'TestPlayer1': 0, 'TestPlayer2' : 0 , 'TestAgent': 0}
# game.n_players = 3

# #print("Choose decoy card: ",ag1.get_decoy(game.clue))
# dictCards = [30, 31, 32, 33, 34]
# #print("Guess Storteller Card: ", ag1.guess_storyteller_card(dictCards, game.clue))
# dictP = [{'player_info': ply1, 'card_guessed': 11}, {'player_info': ply2, 'card_guessed': 11}, {'player_info': ag1, 'card_guessed': 1} ]
# #one player guesses correct
# game.calculateScore(dictP)
# print ("round1: " ,game.scores)
# #no one guesses correct
# ply2.role = 'Guesser'
# ply1.role = 'StoryTeller'
# dictP = [{'player_info': ply1, 'card_guessed': 2}, {'player_info': ply2, 'card_guessed': 22}, {'player_info': ag1, 'card_guessed': 12} ]
# game.calculateScore(dictP)
# print("round2: ", game.scores)
# #all player guesses correct
# ply1.role = 'Guesser'
# ag1.role = 'StoryTeller'
# dictP = [{'player_info': ply1, 'card_guessed': 25}, {'player_info': ply2, 'card_guessed': 25}, {'player_info': ag1, 'card_guessed': 25} ]
# game.calculateScore(dictP)
# print("round3: " , game.scores)
