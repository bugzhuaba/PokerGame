<script>
import {BToastOrchestrator} from "bootstrap-vue-next";

import Hand from "@/components/hand.vue";
import PokeTable from "@/components/table.vue";

export default {
    components: {
        BToastOrchestrator,
        Hand,
        PokeTable
    },
    data() {
        return {
            isTable: this.getQueryParam("isTable") === "1"
        }
    },
    methods: {
        getQueryParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        },
    }
}
</script>

<template>
    <BToastOrchestrator />
    <poke-table v-if="isTable"></poke-table>
    <hand v-else></hand>
</template>

<style scoped>

</style>
