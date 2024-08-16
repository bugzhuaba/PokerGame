<template>
    <div class="game d-flex justify-content-center align-items-center vh-100">
        <div class="poke-table position-relative d-flex justify-content-center align-items-center">
            <div v-if="!roomId" class="player-selection d-flex align-items-center">
                <b-form-select v-model="selectedPlayers" :options="playerOptions" class="me-2"></b-form-select>
                <b-button @click="createRoom" variant="primary">Start</b-button>
            </div>
            <div
                v-for="(player, index) in players"
                :key="index"
                class="player-position"
            >
                <div class="cards" v-if="player.connected">
                    <div v-if="player.cards && player.cards[0]" class="poke-card card-1 card-front" :style="{ backgroundPosition: getCardPosition(player.cards[0]) }"></div>
                    <div v-else class="poke-card card-1"></div>
                    <div v-if="player.cards && player.cards[1]" class="poke-card card-2 card-front" :style="{ backgroundPosition: getCardPosition(player.cards[1]) }"></div>
                    <div v-else class="poke-card card-2"></div>
                </div>
                <div v-else class="qr-code">
                    <div style="color: white">Scan to join</div>
                    <img style="border-radius: 10px" :src="player.qrCode" alt="Scan to join" />
                </div>
                <div class="player-info" v-if="player.connected" :class="{ 'highlight': gameState.expected_action && gameState.expected_action.player === player.index }">
                    <div>Player {{ player.index }}</div>
                    <div>Chips: {{ player.chips }}</div>
                </div>
            </div>
            <div class="community-cards" v-if="roomId && gameState.status === 'playing'">
                <div class="poke-card card-front" v-for="(card, index) in communityCards" :key="'community-' + index" :style="{ backgroundPosition: getCardPosition(card) }"></div>
                <div class="poke-card" v-for="index in (5 - (communityCards ? communityCards.length : 0))" :key="'community-' + (index + 3)" :style="{ backgroundPosition: getCardPosition('default') }"></div>
            </div>
            <div class="action-buttons">
                <div v-if="gameState.status === 'round_finished'" style="font-size: 18px; color: white; margin-bottom: 10px">
                    Player {{gameState.reward.winner}} win the round, pot {{gameState.reward.reward}}
                </div>
                <div style="height: 60px">
                    <b-button
                        v-if="(gameState.status === 'waiting' || gameState.status === 'round_finished') && !allPlayersReady"
                        :disabled="true"
                        class="position-absolute start-btn"
                    >Continue...</b-button>
                    <b-button
                        v-if="(gameState.status === 'waiting' || gameState.status === 'round_finished') && allPlayersReady"
                        @click="startGame"
                        class="position-absolute start-btn"
                    >Continue...</b-button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import getDeviceId from "../device.js";
import { useToast, BFormSelect, BButton } from 'bootstrap-vue-next';
import axios from 'axios';
import QRCode from 'qrcode';

export default {
    components: {
        BFormSelect,
        BButton
    },
    data() {
        return {
            gameState: {},
            pot: 30,
            phase: 'preflop',
            socket: null,
            players: [],
            communityCards: [],
            selectedPlayers: 2,
            playerOptions: [
                {value: 2, text: '2 Players'},
                {value: 3, text: '3 Players'},
                {value: 4, text: '4 Players'},
                {value: 5, text: '5 Players'},
                {value: 6, text: '6 Players'},
                {value: 7, text: '7 Players'},
                {value: 8, text: '8 Players'}
            ],
            useToast: useToast(),
            deviceId: getDeviceId(),
            roomId: this.getQueryParam("room")
        };
    },
    computed: {
        allPlayersReady() {
            return this.players.length > 0 && this.players.every(player => player.connected);
        }
    },
    methods: {
        async createRoom() {
            try {
                const response = await axios.post('http://localhost:8000/room/create/', {
                    player_count: this.selectedPlayers,
                    table: "tablet-" + this.deviceId
                });
                if (response.data.code === 0) {
                    const roomId = response.data.data.id;
                    window.location.href = `/?isTable=1&room=${roomId}`;
                } else {
                    this.toast(response.data.msg, 'danger');
                }
            } catch (error) {
                this.toast('Failed to create room', 'danger');
            }
        },
        connectWebSocket(roomId, deviceId) {
            if (!roomId || !deviceId) {
                console.error('Room ID and Device ID are required');
                return;
            }
            this.socket = new WebSocket(`ws://localhost:8000/ws/game/${roomId}/?room=${roomId}&device_id=tablet-${deviceId}`);

            this.socket.onopen = () => {
                console.log('WebSocket is connected.');
                this.toast('Connected to WebSocket');
            };

            this.socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleServerMessage(message);
            };

            this.socket.onclose = () => {
                console.log('WebSocket is closed.');
                this.toast('WebSocket connection closed', 'danger');
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.toast('WebSocket error', 'danger');
            };
        },
        handleServerMessage(message) {
            if (message.type === 'global_msg') {
                this.updateGameState(message.data);
            } else if (message.type === 'error') {
                this.toast(message.data, 'danger');
            }
        },
        updateGameState(data) {
            this.gameState = data;
            this.players = [];
            for (let i = 1; i <= data.player_count; i++) {
                const player = data.chips.find(player => player.index === i) || undefined;
                if (player === undefined) {
                    this.players.push({
                        index: i,
                        connected: false,
                        qrCode: ''
                    });
                    this.generateQRCode(i).then(qrCode => {
                        this.players[i - 1].qrCode = qrCode;
                    });
                } else {
                    player["connected"] = true;
                    this.players.push(player);
                }
            }
            this.pot = data.pot;
            this.phase = data.phase;
            this.communityCards = data.community_cards;
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

            if (!card) return '';

            const rank = card[0];
            const suit = card[1];

            const xPercent = -100 * rankOrder[rank];
            const yPercent = -100 * suitOrder[suit];

            return `${xPercent}% ${yPercent}%`;
        },
        startGame() {
            console.log(`Starting game with ${this.selectedPlayers} players`);
            this.socket.send(JSON.stringify({type: 'new_round'}));
        },
        initializeGame(config) {
            this.selectedPlayers = config.players || 2;
            const roomId = config.roomId || 1;
            const deviceId = config.deviceId || this.deviceId;
            this.connectWebSocket(roomId, deviceId);
        },
        getQueryParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        },
        toast(message, type = 'success') {
            const toastInstance = this.useToast.show({
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
        async generateQRCode(playerIndex) {
            const protocol = window.location.protocol;
            const host = window.location.host;
            const baseURL = protocol + "//" + host;
            const qrText = `${baseURL}/?room=${this.roomId}&index=${playerIndex}`;
            try {
                return await QRCode.toDataURL(qrText, {width: 150});
            } catch (err) {
                console.error('Failed to generate QR code:', err);
                return '';
            }
        },
    },
    mounted() {
        if (this.roomId) {
            const config = {
                players: 2,
                roomId: this.roomId,
                deviceId: this.deviceId
            };
            this.initializeGame(config);
        } else {
            console.log('Room ID not provided, skipping WebSocket connection.');
        }
    }
};
</script>

<style scoped>
.game {
    width: 100vw;
    height: 100vh;
    background-image: url("/public/background.jpg");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.poke-table {
    width: 80%;
    height: 60%;
    background-image: url("/public/table_bga_blue.png");
    background-size: 100% 100%;
    background-position: center;
    background-repeat: no-repeat;
}

.player-position {
    position: absolute;
    width: 400px;
    height: 20%;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    transition: border 0.3s ease;
}

.cards {
    display: flex;
    position: relative;
    height: 170px;
    margin-right: 10px;
    width: 180px;
}

.poke-card {
    width: 102.67px;
    height: 157.25px;
    background-image: url("public/cardback.png");
    position: absolute;
    border-radius: 7px;
    box-shadow: 3px 1px 1px 1px rgba(0, 0, 0, .4), 2px 0 0 2.5px rgba(0, 0, 0, .38);
}

.card-front {
    background-image: url("public/cards.png");
}

.card-1 {
    transform: rotate(-15deg);
    left: 20px;
}

.card-2 {
    transform: rotate(15deg);
    left: 60px;
}

.player-info {
    margin-bottom: 10px;
    text-align: center;
    font-weight: bold;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.8);
    padding: 10px;
}

.player-position:nth-child(1) {
    top: 1%;
    left: 50%;
    transform: translateX(-50%);
}

.player-position:nth-child(2) {
    top: 7%;
    left: 85%;
    transform: translateX(-50%);
}

.player-position:nth-child(3) {
    top: 55%;
    left: 95%;
    transform: translate(-50%, -50%);
}

.player-position:nth-child(4) {
    top: 85%;
    left: 85%;
    transform: translateX(-50%);
}

.player-position:nth-child(5) {
    top: 112%;
    left: 50%;
    transform: translate(-50%, -100%);
}

.player-position:nth-child(6) {
    top: 85%;
    left: 15%;
    transform: translateX(-50%);
}

.player-position:nth-child(7) {
    top: 55%;
    left: 5%;
    transform: translate(-50%, -50%);
}

.player-position:nth-child(8) {
    top: 7%;
    left: 15%;
    transform: translateX(-50%);
}

.community-cards {
    display: flex;
    justify-content: center;
    align-items: center;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.community-cards .poke-card {
    position: static;
    margin: 0 5px;
}

.pot-info {
    position: absolute;
    top: 10%;
    left: 50%;
    transform: translateX(-50%);
    text-align: center;
    font-weight: bold;
    color: #fff;
}

.highlight {
    border: 5px solid yellow;
}

.start-btn {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
.action-buttons {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
</style>
