import json
import traceback
from typing import Any
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from .models import Room, Player
from .models import Player

from channels.generic.websocket import AsyncWebsocketConsumer

from apps.room.poke import PokerGame, GameState, PlayerAction

game = PokerGame()
game.state = GameState(players={})


class GameConsumer(AsyncWebsocketConsumer):
    room_id: int | None = None
    room_group_name: str | None = None
    device_id: str | None = None
    game: PokerGame | None = None
    player: Any

    async def connect(self):
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        device_id = query_params.get("device_id")
        if device_id is None or len(device_id) < 1:
            await self.close(code=400, reason="device_id is required")
            return
        self.device_id = device_id[0]
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        try:
            room = await Room.objects.aget(id=self.room_id)
        except Room.DoesNotExist:
            await self.close(code=404, reason="no such room")
            return
        players = await sync_to_async(room.player_set.filter)(device__pk=self.device_id)
        self.player = await players.afirst()
        if self.player is None:
            await self.close(code=403, reason="device not in room")
            return
        self.room_group_name = f'room_{self.room_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.player.status = Player.Status.ONLINE
        self.player.channel_id = self.channel_name
        await self.player.asave()
        await self.accept()

        online_players = await sync_to_async(room.player_set.filter)(status=Player.Status.ONLINE)
        if await online_players.acount() == room.player_count:
            room = await Room.objects.aget(id=self.room_id)
            online_players = await sync_to_async(room.player_set.filter)(status=Player.Status.ONLINE)
            async for player in online_players:
                game.add_player(player.index, 100)

            game.new_round()

            async for player in online_players:
                await self.channel_layer.send(
                    player.channel_id,
                    {
                        'type': 'deal',
                        'data': {
                            'index': player.index,
                            'cards': game.round.players[player.index].hand
                        }
                    }
                )

            room.status = Room.Status.PLAYING
            await room.asave()

            game.set_next_action()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'global_msg',
                    'data': game.round.expected_action
                }
            )

    async def disconnect(self, close_code):
        self.player.status = Player.Status.OFFLINE
        self.player.channel_id = None
        await self.player.asave()
        if self.room_group_name is None:
            return
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            message = json.loads(text_data)
        try:
            action = PlayerAction(**message)
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': str(e)
            }))
            return
        try:
            game.handle_action(self.player.index, action)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': str(e)
            }))
            print(traceback.format_exc())
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'global_msg',
                'data': game.round.expected_action
            }
        )

        print(game.to_json())

    async def deal(self, event: dict):
        await self.send(text_data=json.dumps({
            'type': 'deal',
            'data': event["data"]
        }))

    async def global_msg(self, event):
        await self.send(text_data=json.dumps(event))
