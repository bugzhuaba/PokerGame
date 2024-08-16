<template>
    <div class="game">
        <div class="user-info">
            <div>
                <div class="wallet" style="margin-bottom: 10px">
                    <img src="/token.png" alt="" style="width: 40px; height: 40px; margin-right: 20px">
                    <span style="font-size: 18px; font-weight: bold">{{ myChips }}</span>
                </div>
                <div class="current-bets">
                    <div v-for="(chip, index) in gameInfo.chips" :key="index" v-if="gameInfo.bet">
                        <b-badge type="success">
                            Player {{ chip.index }}
                        </b-badge> {{ chip.chips }} chips (Bet: {{ gameInfo.bet[index] }})
                    </div>
                </div>
            </div>
        </div>
        <div class="action-buttons">
            <template v-if="isCurrentPlayerTurn && gameInfo.status === 'playing'">
                <button v-if="showAction('bet')" class="btn btn-primary" @click="openBetModal">Bet</button>
                <button v-if="showAction('call')" class="btn btn-success" @click="sendCall">Call</button>
                <button v-if="showAction('check')" class="btn btn-warning" @click="sendCheck">Check</button>
                <button v-if="showAction('raise')" class="btn btn-danger" @click="openRaiseModal">Raise</button>
            </template>
            <div v-else style="display: flex; justify-content: center">
                <div style="width: 90%">
                    <span style="color: #dbd4d4; font-size: 20px" v-if="gameInfo.status === 'waiting'">Waiting for Players join the table</span>
                    <span style="color: #dbd4d4; font-size: 20px" v-if="gameInfo.status === 'playing'">Waiting for Player {{ gameInfo.expected_action.player }} to act...</span>
                    <span style="color: #dbd4d4; font-size: 20px" v-if="gameInfo.status === 'round_finished'">Press the <span style="font-weight: bold">continue</span> button on the table</span>
                </div>
            </div>
        </div>
        <div class="bet-info">
            <div class="phase-info">Phase: {{ gameInfo.phase }}</div>
            <div class="pot-info">Pot: {{ gameInfo.pot }}</div>
            <div class="recent-actions">
                <div v-for="(turn, index) in gameInfo.turns" :key="index">
                    Player {{ turn.player }}: {{ turn.action }} {{ turn.value > 0 ? 'with ' + turn.value : '' }}
                </div>
            </div>
        </div>
        <div class="hand-cards">
            <div class="poke-card card-front"
                 v-for="(card, index) in playerCards"
                 :key="'hand-' + index"
                 :style="{ backgroundPosition: getCardPosition(card) }"></div>
        </div>

        <!-- Bet Modal -->
        <b-modal ref="betModal" id="bet-modal" title="Place Your Bet" @ok="placeBet">
            <b-form-group label="Bet Amount">
                <b-form-input v-model="betAmount" type="number" min="1"></b-form-input>
            </b-form-group>
        </b-modal>

        <!-- Raise Modal -->
        <b-modal ref="raiseModal" id="raise-modal" title="Raise Your Bet" @ok="placeRaise">
            <b-form-group label="Raise Amount">
                <b-form-input v-model="raiseAmount" type="number" min="1"></b-form-input>
            </b-form-group>
        </b-modal>
    </div>
</template>

<script>
import { useToast, BToast, BModal, BFormGroup, BFormInput, BBadge } from 'bootstrap-vue-next';
import getDeviceId from "@/device.js";

export default {
    components: {
        BToast,
        BModal,
        BFormGroup,
        BFormInput,
        BBadge
    },
    data() {
        return {
            gameInfo: {
                chips: [],
                pot: 0,
                bet: [],
                expected_action: {
                    player: null,
                    actions: []
                },
                phase: '',
                turns: []
            },
            socket: null,
            deviceId: getDeviceId(),
            roomId: this.getQueryParam('room'),
            playerCards: [],
            playerId: Number(this.getQueryParam('index')), // Ensure playerId is a number
            showToast: useToast(),
            betAmount: 1,
            raiseAmount: 1
        };
    },
    methods: {
        showAction(action) {
            return this.gameInfo.expected_action.actions.includes(action);
        },
        sendBet(amount) {
            this.sendAction('bet', amount);
        },
        sendRaise(amount) {
            this.sendAction('raise', amount);
        },
        sendCall() {
            this.sendAction('call');
        },
        sendCheck() {
            this.sendAction('check');
        },
        sendAction(actionType, value = null) {
            let action = {type: actionType};
            if (value !== null) {
                action.value = value;
            }
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(action));
            }
        },
        connectWebSocket() {
            if (!this.deviceId) {
                console.error('Device ID is required');
                return;
            }
            this.socket = new WebSocket(`ws://localhost:8000/ws/game/${this.roomId}/?room=${this.roomId}&device_id=${this.deviceId}&index=${this.playerId}`);

            this.socket.onopen = (event) => {
                console.log('WebSocket is connected.');
                this.toast('Connected to WebSocket');
            };

            this.socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleServerMessage(message);
            };

            this.socket.onclose = (event) => {
                console.log(event)
                console.log('WebSocket is closed.');
                this.toast('WebSocket connection closed', 'danger');
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.toast('WebSocket error', 'danger');
            };
        },
        handleServerMessage(message) {
            if (message.type === 'deal') {
                this.displayCards(message.data);
            } else if (message.type === "global_msg") {
                this.updateGameState(message.data);
            } else if (message.type === 'error') {
                this.toast(message.data, 'danger');
            }
        },
        displayCards(data) {
            console.log(`Player ${data.index} cards: ${data.cards.join(', ')}`);
            this.playerCards = data.cards;
        },
        updateGameState(data) {
            this.gameInfo = data;
        },
        getCardPosition(card) {
            const rankOrder = {
                '2': 0,
                '3': 1,
                '4': 2,
                '5': 3,
                '6': 4,
                '7': 5,
                '8': 6,
                '9': 7,
                'T': 8,
                'J': 9,
                'Q': 10,
                'K': 11,
                'A': 12
            };

            const suitOrder = {
                's': 0,
                'h': 1,
                'd': 2,
                'c': 3
            };

            const rank = card[0];
            const suit = card[1];

            const xPercent = -100 * rankOrder[rank];
            const yPercent = -100 * suitOrder[suit];

            return `${xPercent}% ${yPercent}%`;
        },
        getQueryParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        },
        toast(message, type = 'success') {
            // Show the toast and capture the instance
            const toastInstance = this.showToast.show({
                props: {
                    title: "Notification",
                    variant: type,
                    pos: 'top-center',
                    value: 3000,
                    body: message,
                    noFade: true,
                    rel: "ref"
                },
            });
        },
        openBetModal() {
            this.$refs.betModal.show();
        },
        openRaiseModal() {
            this.$refs.raiseModal.show();
        },
        placeBet() {
            this.sendBet(this.betAmount);
        },
        placeRaise() {
            this.sendRaise(this.raiseAmount);
        }
    },
    computed: {
        myChips() {
            for (const chip of this.gameInfo.chips) {
                if (chip.index === this.playerId) {
                    return chip.chips;
                }
            }
            return "";
        },
        isCurrentPlayerTurn() {
            return this.gameInfo.expected_action?.player === this.playerId;
        }
    },
    created() {
        this.connectWebSocket();
    },
    beforeUnmount() {
        if (this.socket) {
            this.socket.close();
        }
    },
};
</script>

<style scoped>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
}

.game {
    width: 100vw;
    height: 100vh;
    background-image: url("/background.jpg");
    background-position: center;
    background-repeat: no-repeat;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
    padding-bottom: 20px;
    box-sizing: border-box;
}

.user-info {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(255, 255, 255, 0.8);
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.action-buttons {
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
}

.action-buttons button {
    margin: 0 10px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
}

.bet-info {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 255, 255, 0.8);
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.pot-info {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 15px;
    text-align: end;
}

.current-bets div {
    font-size: 16px;
    margin-bottom: 3px;
}

.phase-info {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 5px;
}

.hand-cards {
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    width: 380px;
    height: 340px;
}

.poke-card {
    width: 205.34px;
    height: 314.5px;
    background-image: url("/cardback.png");
    background-size: cover;
    border-radius: 14px;
    box-shadow: 6px 2px 2px 2px rgba(0, 0, 0, 0.4), 4px 0 0 5px rgba(0, 0, 0, 0.38);
    position: absolute;
}

.poke-card:first-child {
    transform: rotate(-15deg);
    left: 40px;
}

.poke-card:last-child {
    transform: rotate(15deg);
    left: 120px;
}

.card-front {
    background-image: url("/cards-hand.png");
    background-size: 1300% 400%;
}

.wallet {
    display: flex;
    align-items: center;
}

.recent-actions {
    max-height: 100px;
    overflow-y: auto;
    text-align: start;
}

.recent-actions div {
    font-size: 14px;
    margin-bottom: 5px;
}
</style>
