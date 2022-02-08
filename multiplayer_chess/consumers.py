
import json
import numpy as np
import chess
from channels.generic.websocket import AsyncWebsocketConsumer

from project_chess.settings import SECRET_KEY
from .models import *
from channels.db import database_sync_to_async


class HomeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        # create a group containing only one user

        await self.channel_layer.group_add(
            f'{self.user.username}_channel',  # group name
            self.channel_name
        )
        await self.markOnline()
        print(f'{self.user} is connected and online')
        await self.accept()

    async def disconnect(self, close_code):

        await self.markOffline()
        # Leave room group
        await self.channel_layer.group_discard(
            f'{self.user.username}_channel',
            self.channel_name
        )

    async def send_notification(self, event):
        friend_name = event["friend_name"]
        await self.send(text_data=json.dumps({
            'friend_name': friend_name
        }))

    @database_sync_to_async
    def markOnline(self):
        player = Player.objects.get(user=self.user)
        player.is_online = True
        player.save()

    @database_sync_to_async
    def markOffline(self):
        player = Player.objects.get(user=self.user)
        player.is_online = False
        player.save()


class RandomMatchConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.game_completed = False

    async def connect(self):

        self.user = self.scope["user"]
        self.room_name = self.createRoomName()

        # check if there are Gamerooms waiting
        self.gameroom = await self.getGameroom()

        if self.gameroom:
            print("gameroom found")
            # set this player's opponent to the player in the group
            self.opponent = await self.getPlayerInRoom()

            # add player to gameroom
            await self.addPlayerToGameroom()
            self.room_name = self.gameroom.room_name

            # before adding player to the group set the player who is in the group's opponet to this player
            # since this player is not yet added to the group, set_opponent function will be called only for the player in the group
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'set_opponent',
                    'opponent': str(self.user.username)
                }
            )

            # add user to the group with group_name = room_name
            await self.channel_layer.group_add(
                self.room_name,  # group name
                self.channel_name
            )

            self.color = 1  # 1 -> black

            await self.accept()

            # call start_game function in both instances
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'start_game',
                }
            )
        else:
            # Create new Gameroom
            print("gameroom creating...")
            print(self.room_name)
            self.gameroom = await self.createGameroom(self.room_name)

            # add user to the group with group_name = room_name
            await self.channel_layer.group_add(
                self.room_name,  # group name
                self.channel_name
            )

            self.color = 0  # 0 -> white

            await self.accept()

        print(f'{self.user} joined {self.room_name}')

    async def disconnect(self, close_code):

        # make gameroom inactive (or delete it if the game is not completed)
        await self.deactivateGameroom()

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        move = text_data_json["move"]

        # update board in both instances and send that move and next legal moves to both players

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'update_board_and_send_move_to_player',
                'move': move
            }
        )

    async def set_opponent(self, event):
        self.opponent = event['opponent']

    async def update_board_and_send_move_to_player(self, event):
        move = event['move']
        # check if this move will capture a piece
        captured = self.getCapturedPiece(move)

        # update the board
        self.board.push_san(move)

        # if game is completed update winner in gameroom
        print(self.board.result())
        if self.board.result() != "*":
            await self.updateResult(self.board.result())

        legal_moves = []
        for i in list(self.board.legal_moves):
            legal_moves.append(str(i))
        # print(legal_moves)
        await self.send(text_data=json.dumps({
            'type': 1,  # 1 indicates theplayer that a move is being sent
            'move': move,
            'legal_moves': legal_moves,
            'result': self.board.result(),
            'turn': 0 if self.board.turn else 1,
            'board': self.getBoardAsArray(),
            'captured': captured
        }))

    async def start_game(self, event):
        print(f'{self.user} is ready to start')

        self.board = chess.Board()
        legal_moves = []
        for i in list(self.board.legal_moves):
            legal_moves.append(str(i))
        # print(legal_moves)
        await self.send(text_data=json.dumps({
            'type': 0,  # 0 indicates the client to set up the board and start the match
            'opponent': self.opponent,
            'color': self.color,
            'legal_moves': legal_moves,
            'board': self.getBoardAsArray(),
            'turn': 0 if self.board.turn else 1   # 0 is white's turn
        }))

    def createRoomName(self):
        # Create unique Gameroom name
        return str(self.user.username) + "_gameroom"

    def getBoardAsArray(self):
        arr = str(self.board.fen()).split(' ')[0].split('/')
        arr_board = []
        for r in arr:
            t = []
            for c in r:
                if c.isdigit():
                    t += ['.' for _ in range(int(c))]
                else:
                    t.append(c)
            arr_board.append(t)
        print(arr_board)
        if self.color == 0:
            return arr_board
        return np.rot90(arr_board, 2).tolist()

    @database_sync_to_async
    def updateResult(self, result):
        print(result)
        self.game_completed = True
        if result == '1-0':
            # white won
            if self.color == 0:
                self.gameroom.winner = Player.objects.get(user=self.user)
                self.gameroom.save()
        elif result == '0-1':
            # black won
            if self.color == 1:
                self.gameroom.winner = Player.objects.get(user=self.user)
                self.gameroom.save()

    @database_sync_to_async
    def getGameroom(self):
        # matchmaking can be implemented here
        return Gameroom.objects.filter(active=True, private=False).first()

    @database_sync_to_async
    def getPlayerInRoom(self):
        return str(self.gameroom.players.all()[0].user.username)

    @database_sync_to_async
    def createGameroom(self, room_name):
        gameroom = Gameroom.objects.create(room_name=room_name)
        gameroom.players.add(Player.objects.get(user=self.user))
        print("gameroom created")
        return gameroom

    @database_sync_to_async
    def deactivateGameroom(self):
        gameroom = Gameroom.objects.filter(
            room_name=self.room_name, active=True)[0]
        if self.game_completed:
            gameroom.active = False
            gameroom.save()
        else:
            gameroom.delete()

    @database_sync_to_async
    def addPlayerToGameroom(self):
        self.gameroom.players.add(Player.objects.get(user=self.user))
        self.gameroom.save()

    def getCapturedPiece(self, move_str):
        move = chess.Move(chess.parse_square(
            move_str[:2]), chess.parse_square(move_str[2:]))
        if self.board.is_capture(move):
            if self.board.is_en_passant(move):
                return chess.PAWN
            else:
                return self.board.piece_at(move.to_square).symbol()
        return "."


class FriendMatchConsumer(RandomMatchConsumer):
    def __init__(self):
        super().__init__()
        self.game_completed = False

    async def connect(self):
        self.user = self.scope["user"]
        self.friend_name = self.scope['url_route']['kwargs']['friend_name']
        self.room_name = self.getRoomName(friend_name=self.friend_name)

        self.gameroom = await self.getGameroom()
        if self.gameroom:
            print("friend gameroom found")

            # set this player's opponent to the player in the group
            self.opponent = await self.getPlayerInRoom()

            # add player to gameroom
            await self.addPlayerToGameroom()
            self.room_name = self.gameroom.room_name

            # before adding player to the group set the player who is in the group's opponet to this player
            # since this player is not yet added to the group, set_opponent function will be called only for the player in the group
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'set_opponent',
                    'opponent': str(self.user.username)
                }
            )

            # add user to the group with group_name = room_name
            await self.channel_layer.group_add(
                self.room_name,  # group name
                self.channel_name
            )

            self.color = 1  # 1 -> black

            await self.accept()

            # call start_game function in both instances
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'start_game',
                }
            )
        else:
            # Create new Gameroom
            print("friend gameroom creating...")
            print(self.room_name)
            self.gameroom = await self.createGameroom(self.room_name)

            # add user to the group with group_name = room_name
            await self.channel_layer.group_add(
                self.room_name,  # group name
                self.channel_name
            )

            self.color = 0  # 0 -> white

            await self.accept()

            # send notification to friend who is in his own channel group named {usernmame}_channel
            await self.channel_layer.group_send(

                f"{self.friend_name}_channel",
                {
                    'type': 'send_notification',
                    'friend_name': self.user.username
                }

            )

    @database_sync_to_async
    def getGameroom(self):
        return Gameroom.objects.filter(room_name=self.room_name, active=True, private=True).first()

    @database_sync_to_async
    def createGameroom(self, room_name):
        gameroom = Gameroom.objects.create(room_name=room_name, private=True)
        gameroom.players.add(Player.objects.get(user=self.user))
        print("friend gameroom created")
        return gameroom

    def getRoomName(self, friend_name):
        # create unique room_name using two players' usernames
        a, b = min(self.user.username, friend_name), max(
            self.user.username, friend_name)
        return f'{a}_{b}_gameroom'
