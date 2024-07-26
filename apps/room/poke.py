import random
from enum import Enum
from typing import Optional, List, Dict, Any

from treys import Card, Evaluator, Deck
from pydantic import BaseModel


class GamePhase(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class PlayerStatus(str, Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALLIN = "allin"


class ActionType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    BET = "bet"
    CALL = "call"
    RAISE = "raise"
    FOLD = "fold"
    CHECK = "check"
    ALLIN = "allin"
    SHOWDOWN = "showdown"


class PlayerAction(BaseModel):
    type: ActionType
    value: Optional[int] = None


class Player(BaseModel):
    index: int
    chips: int
    status: PlayerStatus


class TurnAction(BaseModel):
    player: int
    action: ActionType
    value: Optional[int] = None


class PlayerRoundState(BaseModel):
    index: int
    bet: int
    status: PlayerStatus
    hand: List[int]


class RoundState(BaseModel):
    phase: GamePhase
    community_cards: List[int]
    pot: int
    turns: List[TurnAction] = []
    remaining_deck: List[int] = []
    reward: Optional[Dict[int, int]] = None
    players: Dict[int, PlayerRoundState] = {}
    expected_action: Dict[str, Any] = {}

    @property
    def deck(self):
        deck = Deck()
        if not self.remaining_deck:
            self.remaining_deck = Deck.GetFullDeck()
            random.shuffle(self.remaining_deck)
            deck.cards = self.remaining_deck
            return deck

        def deal(self, index):
            cards = self.deck.draw(2)
            if index in self.players:
                raise ValueError("Error: duplicate deal")
            self.players[index] = PlayerRoundState(index=index, bet=0, status=PlayerStatus.ACTIVE, hand=cards)
            return cards

        def deal_community_cards(self, num: int):
            self.community_cards += self.deck.draw(num)


class GameState(BaseModel):
    players: Dict[int, Player]
    dealer: int = 0
    rounds: List[RoundState] = []

    def next_dealer(self):
        self.dealer = (self.dealer + 1) % 2 + 1

    @property
    def small_blind_index(self):
        return (self.dealer + 1) % 2 + 1

    @property
    def big_blind_index(self):
        return (self.dealer + 2) % 2 + 1

    @property
    def current_round(self):
        return self.rounds[-1]


class PokerGame:
    def __init__(self):
        self.state: Optional[GameState] = None
        self.evaluator = Evaluator()
        self.round: Optional[RoundState] = None
        self.current_player: int = 1

    def new_round(self):
        # init round
        new_round = RoundState(
            phase=GamePhase.PREFLOP,
            community_cards=[],
            pot=0
        )

        self.round = new_round
        self.state.rounds.append(new_round)

        # deal community cards
        self.advance_phase()

        # deal cards
        for player in self.state.players.values():
            new_round.deal(player.index)

        # set small blind and big blind 1 - max players
        self.state.dealer = (self.state.dealer % len(self.state.players)) + 1

        # deal blinds
        self.deal_blinds()

    def add_player(self, index: int, chips: int):
        player = Player(index=index, chips=chips, status=PlayerStatus.ACTIVE)
        self.state.players[index] = player

    def deal_blinds(self):
        sb_player = self.state.players[self.state.small_blind_index]
        sb_round_player = self.round.players[self.state.small_blind_index]
        small_blind_amount = 10
        sb_player.chips -= small_blind_amount
        sb_round_player.bet = small_blind_amount
        self.round.pot += small_blind_amount
        self.round.pot += small_blind_amount
        self.round.turns.append(
            TurnAction(player=self.state.small_blind_index, action=ActionType.BET, value=small_blind_amount))
        bb_player = self.state.players[self.state.big_blind_index]
        bb_round_player = self.round.players[self.state.big_blind_index]
        big_blind_amount = 20
        bb_player.chips -= big_blind_amount
        bb_round_player.bet = big_blind_amount
        self.round.pot += big_blind_amount
        self.round.turns.append(
            TurnAction(player=self.state.big_blind_index, action=ActionType.BET, value=big_blind_amount))
        self.set_next_action()

    def set_next_action(self):
        active_players = [p for p in self.state.players.values() if p.status == PlayerStatus.ACTIVE]
        if not active_players:
            return
        self.current_player = (self.current_player % len(self.state.players)) + 1
        # while self.state.players[self.current_player].status != PlayerStatus.ACTIVE:
        #     self.current_player = (self.current_player % len(self.state.players)) + 1
        self.round.expected_action = {"player": self.current_player,
                                      "actions": self.get_available_actions(self.current_player)}

    def get_available_actions(self, player_index: int) -> List[ActionType]:
        actions = [ActionType.FOLD]
        current_bet = self.round.players[player_index].bet
        max_bet = max(p.bet for p in self.round.players.values())
        if current_bet == max_bet:
            actions.append(ActionType.CHECK)
        else:
            actions.append(ActionType.CALL)
        if max_bet == 0:
            actions.append(ActionType.BET)
        else:
            actions.append(ActionType.RAISE)
        return actions

    def check_and_advance_phase(self):
        # last action acted by dealer & all player acted
        if len(self.round.players) == 2:
            last_player = self.state.dealer % 2 + 1
        else:
            last_player = self.state.dealer

        if self.current_player == last_player and self.all_players_acted():
            print("next")
            self.advance_phase()

    def handle_action(self, player_index: int, action: PlayerAction):
        if self.round.expected_action["player"] != player_index:
            raise ValueError(f"Player {player_index} is not expected to act now")
        player = self.state.players[player_index]
        player_round = self.round.players[player_index]
        if player.status in [PlayerStatus.FOLDED, PlayerStatus.ALLIN]:
            raise ValueError(f"Player {player_index} cannot perform actions in {player.status} status")
        if action.type not in self.round.expected_action["actions"]:
            raise ValueError(f"Action {action.type} is not allowed for player {player_index}")

        if action.type == ActionType.BET:
            player_round.bet += action.value
            player.chips -= action.value
            self.round.pot += action.value
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.BET, value=action.value))
        elif action.type == ActionType.CALL:
            max_bet = max(a.value for a in self.round.turns if a.action == ActionType.BET)
            call_amount = max_bet - player_round.bet
            player_round.bet = max_bet
            player.chips -= call_amount
            self.round.pot += call_amount
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.CALL, value=max_bet))
        elif action.type == ActionType.RAISE:
            max_bet = max(a.value for a in self.round.turns if a.action == ActionType.BET)
            raise_amount = action.value
            player_round.bet = max_bet + raise_amount
            player.chips -= raise_amount
            self.round.pot += raise_amount
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.RAISE, value=raise_amount))
        elif action.type == ActionType.FOLD:
            player_round.status = PlayerStatus.FOLDED
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.FOLD))
        elif action.type == ActionType.CHECK:
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.CHECK))
        elif action.type == ActionType.ALLIN:
            allin_amount = player.chips
            player_round.bet += allin_amount
            self.round.pot += allin_amount
            player.chips = 0
            player_round.status = PlayerStatus.ALLIN
            self.round.turns.append(TurnAction(player=player_index, action=ActionType.ALLIN, value=allin_amount))
        elif action.type == ActionType.SHOWDOWN:
            self.handle_showdown()

        self.round.players[player_index] = PlayerRoundState(
            index=player_index,
            bet=player_round.bet,
            status=player_round.status,
            hand=player_round.hand
        )

        self.check_and_advance_phase()
        self.set_next_action()

    def handle_showdown(self):
        hands = {
            player.index: [Card.new(Card.int_to_str(card)) for card in player.hand] for player in self.round.players.values() if player.status == PlayerStatus.ACTIVE
        }
        board = [Card.new(Card.int_to_str(card)) for card in self.round.community_cards]
        best_hand = None
        best_score = None
        winner = None

        for index, hand in hands.items():
            score = self.evaluator.evaluate(board, hand)
            if best_score is None or score < best_score:
                best_score = score
                best_hand = hand
                winner = index

        self.round.reward = {winner: self.round.pot}
        self.state.players[winner].chips += self.round.pot
        self.round.pot = 0
        self.round.phase = GamePhase.SHOWDOWN
        self.state.rounds.append(self.round)
        self.new_round()

    def advance_phase(self):
        if self.round.phase == GamePhase.PREFLOP:
            self.round.deal_community_cards(3)
            self.round.phase = GamePhase.FLOP
        elif self.round.phase == GamePhase.FLOP:
            self.round.deal_community_cards(1)
            self.round.phase = GamePhase.TURN
        elif self.round.phase == GamePhase.TURN:
            self.round.deal_community_cards(1)
            self.round.phase = GamePhase.RIVER
        elif self.round.phase == GamePhase.RIVER:
            self.round.phase = GamePhase.SHOWDOWN
            self.handle_showdown()
        else:
            self.round.phase = GamePhase.SHOWDOWN
            self.handle_showdown()

    def to_json(self) -> str:
        return self.state.model_dump_json(indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "PokerGame":
        game_state = GameState.parse_raw(json_str)
        game = cls()
        game.state = game_state
        if game.state.rounds:
            game.round = game.state.rounds[-1]
        return game










