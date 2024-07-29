import json
import traceback
from typing import Any
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from .models import Room, Player
from .models import Player

from channels.generic.websocket import AsyncWebsocketConsumer
from .poke import PokerGame, PlayerAction, ActionType, GameStatus
from apps.room.poke import PokerGame, GameState, PlayerAction
from .models import Room, Player, Device

game = PokerGame()
game.state = GameState(players={})


class GameConsumer(AsyncWebsocketConsumer):
    room_id: int | None = None
    room_group_name: str | None = None
    device_id: str | None = None
    game: PokerGame | None = None
    player: Any | None = None
    is_tablet = False

    async def connect(self):
        await self.accept()
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        device_id = query_params.get("device_id")
        if device_id is None or len(device_id) < 1:
            await self.close(code=400, reason="device_id is required")
            return
        self.device_id = device_id[0]
        room_id = query_params.get("room")
        if room_id is not None and len(room_id) == 1:
            self.room_id = room_id[0]

        is_tablet = self.device_id.startswith("tablet")
        if is_tablet:
            device_type = Device.Type.TABLET
        else:
            device_type = Device.Type.MOBILE
        device, _ = await Device.objects.aget_or_create(device_id=self.device_id, type=device_type)
        if self.room_id is not None:
            try:
                room = await Room.objects.aget(id=self.room_id)
            except Room.DoesNotExist:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'data': 'no such room'
                }))
                await self.close(code=4001, reason="no such room")
                return
        else:
            await self.send(
                text_data=json.dumps({
                    'type': 'error',
                    'data': 'room_id is required'
                })
            )
            return
        self.game = room.game_state

        if device.type == Device.Type.TABLET:
            self.is_tablet = True
            room_table = await sync_to_async(lambda: room.table)()
            if room_table == device:
                device.channel_id = self.channel_name
                await device.asave()
                self.room_group_name = f'room_{self.room_id}'
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.send_state()
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'data': 'tablet not in this room'
                }))
                await self.close(code=4003, reason="tablet not in this room")
            return

        index = query_params.get("index")
        if index is not None and len(index) == 1:
            index = index[0]
        try:
            player_in_chair = await Player.objects.aget(room=room, index=index)
            if await sync_to_async(lambda: player_in_chair.device)() != device:
                await self.send(
                    text_data=json.dumps({
                        'type': 'error',
                        'data': 'chair not available'
                    })
                )
                await self.close()
                return
        except Player.DoesNotExist:
            player_in_chair = await Player.objects.acreate(device=device, room=room, index=index)

        self.player = player_in_chair

        self.room_group_name = f'room_{self.room_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        self.player.status = Player.Status.ONLINE
        self.player.channel_id = self.channel_name
        await self.player.asave()

        if self.game.state.players.get(self.player.index) is None:
            self.game.add_player(int(self.player.index), 100)

        if self.game.state.status != self.game.state.status.WAITING:
            # reconnected
            await self.channel_layer.send(
                self.channel_name,
                {
                    'type': 'deal',
                    'data': {
                        'index': self.player.index,
                        'cards': self.game.round.players[self.player.index].hand
                    }
                }
            )

        await self.send_state()

    async def disconnect(self, close_code):
        if not self.is_tablet and self.player is not None:
            self.player.status = Player.Status.OFFLINE
            self.player.channel_id = None
            await self.player.asave()

        if self.room_group_name is not None:
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
        room = await Room.objects.aget(id=self.room_id)
        if action.type == ActionType.NEW_ROUND and self.is_tablet and self.game.state.status != GameStatus.ROUND_PLAYING:
            online_players = await sync_to_async(room.player_set.filter)(status=Player.Status.ONLINE)
            self.game.new_round()
            async for player in online_players:
                await self.channel_layer.send(
                    player.channel_id,
                    {
                        'type': 'deal',
                        'data': {
                            'index': player.index,
                            'cards': self.game.round.players[player.index].hand
                        }
                    }
                )
            self.game.state.status = GameStatus.ROUND_PLAYING
            await room.asave()
            self.game.set_next_action()
            await self.send_state()
            return

        try:
            self.game.handle_action(int(self.player.index), action)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': str(e)
            }))
            print(traceback.format_exc())
            return

        await self.send_state()

    async def send_state(self):
        room = await Room.objects.aget(id=self.room_id)
        state = {
                'type': 'global_msg',
                'data': {
                    "chips": [player.model_dump() for player in self.game.state.players.values()],
                    "status": self.game.state.status,
                    "player_count": room.player_count
                }
            }
        if self.game.state.rounds:
            state_started = {
                "pot": self.game.state.current_round.pot,
                "community_cards": self.game.state.current_round.community_cards,
                "expected_action": self.game.round.expected_action,
                "phase": self.game.state.current_round.phase,
                "turns": [turn.model_dump() for turn in self.game.state.current_round.turns],
                "bet": [player.bet for player in self.game.state.current_round.players.values()],
                "reward": self.game.state.current_round.reward
            }
            state["data"].update(state_started)
        await self.channel_layer.group_send(
            self.room_group_name,
            state
        )



    async def deal(self, event: dict):
        await self.send(text_data=json.dumps({
            'type': 'deal',
            'data': event["data"]
        }))

    async def global_msg(self, event):
        await self.send(text_data=json.dumps(event))
