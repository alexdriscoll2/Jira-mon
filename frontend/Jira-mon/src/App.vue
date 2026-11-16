<script setup lang="ts">
import Toolbar from 'primevue/toolbar'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Message from 'primevue/message'
import Dialog from 'primevue/dialog'

import jiraLogo from '@/assets/Jira_icon.svg'
import pokeball from '@/assets/pokeball_white.png'

import { ref, computed, onMounted } from 'vue'

interface Pokemon { id: number; name: string | null; sprite_url: string }
interface Box { id: string; issue_key: string; summary: string }
interface CollectionItem { reward_id: string; issue_key: string; summary: string; pokemon: Pokemon }

const user = ref<{ email: string } | null>(null)
const boxes = ref<Box[]>([])
const collection = ref<CollectionItem[]>([])
const revealed = ref<Pokemon | null>(null)
const status = ref('')
const busy = ref(false)
const connecting = ref(false)
const activeTab = ref('home')

// "alex@example.com" -> "alex"
const displayName = computed(() => user.value?.email.split('@')[0] ?? '')

// The reveal dialog is open whenever there is a Pokémon to show.
const showReveal = computed({
  get: () => revealed.value !== null,
  set: (open: boolean) => {
    if (!open) revealed.value = null
  },
})

// Sends a message to the background script and unwraps the { ok, data } reply.
async function call<T>(message: object): Promise<T> {
  const res = await chrome.runtime.sendMessage(message)
  if (!res?.ok) {
    const err: string = res?.error ?? 'No response from the background script'
    if (err.includes('Session expired')) user.value = null
    throw new Error(err)
  }
  return res.data as T
}

async function refresh() {
  try {
    const sync = await call<{ unopened: Box[] }>({ type: 'SYNC_REWARDS' })
    boxes.value = sync.unopened
    collection.value = await call<CollectionItem[]>({ type: 'GET_COLLECTION' })
    status.value = ''
  } catch (e) {
    status.value = (e as Error).message
  }
}

async function connect() {
  connecting.value = true
  status.value = ''
  try {
    const res = await chrome.runtime.sendMessage({ type: 'CONNECT_JIRA' })
    if (!res?.ok) {
      status.value = `Login failed: ${res?.error ?? 'no response'}`
      return
    }
    user.value = res.user
    await refresh()
  } catch (e) {
    status.value = (e as Error).message
  } finally {
    connecting.value = false
  }
}

async function openNext() {
  const box = boxes.value[0]
  if (!box || busy.value) return
  busy.value = true
  try {
    const result = await call<{ pokemon: Pokemon }>({ type: 'OPEN_BOX', rewardId: box.id })
    revealed.value = result.pokemon
    await refresh()
  } catch (e) {
    status.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

function goToCollection() {
  revealed.value = null
  activeTab.value = 'collection'
}

async function logout() {
  await chrome.runtime.sendMessage({ type: 'LOGOUT' })
  user.value = null
  boxes.value = []
  collection.value = []
  revealed.value = null
  activeTab.value = 'home'
  status.value = ''
}

onMounted(async () => {
  const res = await chrome.runtime.sendMessage({ type: 'GET_SESSION' })
  user.value = res?.user ?? null
  if (user.value) await refresh()
})
</script>

<template>
  <Toolbar class="app-toolbar">
    <template #start>
      <span class="logo-slot logo-slot--before-title">
        <img :src="jiraLogo" alt="" class="logo-jira" />
      </span>
      <h1 class="app-toolbar__title">Jira-mon</h1>
      <span class="logo-slot logo-slot--after-title">
        <img :src="pokeball" alt="" class="logo-pokeball" />
      </span>
    </template>
  </Toolbar>

  <Tabs v-model:value="activeTab" class="app-tabs">
    <TabList class="app-tablist">
      <Tab value="home">
        Home
        <Badge
          v-if="boxes.length"
          :value="boxes.length"
          severity="danger"
          size="small"
          class="tab-badge"
        />
      </Tab>
      <Tab value="collection">Collection</Tab>
    </TabList>

    <TabPanels>
      <TabPanel value="home">
        <p class="text-surface-500 mt-1">
          Hello <b>{{ displayName || 'trainer' }}</b>
        </p>

        <div class="grid-container">
          <div>
            <template v-if="user === null">
              <p class="text-surface-500 mt-1">Connect Jira to earn a pokemon for every finished ticket.</p>
              <Button label="Connect to Jira" :loading="connecting" @click="connect" />
            </template>

            <template v-else>
              <p class="text-surface-500 mt-1">Boxes ready: <b>{{ boxes.length }}</b></p>
              <p class="text-surface-500 mt-1">Collected: <b>{{ collection.length }}</b></p>

              <Button v-if="boxes.length" label="Open box" :loading="busy" @click="openNext" />
              <p v-else class="text-surface-500 mt-1">Finish a ticket to earn your next pokemon.</p>

              <div class="logout-row">
                <Button label="Log out" severity="secondary" text size="small" @click="logout" />
              </div>
            </template>
          </div>

          <div class="pokeball-cell">
            <img :src="pokeball" alt="" class="pokeball-grey" />
          </div>
        </div>
      </TabPanel>

      <TabPanel value="collection">
        <h2 class="text-lg font-bold">Collection ({{ collection.length }})</h2>

        <p v-if="!collection.length" class="text-surface-500 mt-1">
          Nothing here yet. Open a box to add your first Pokémon.
        </p>

        <div v-else class="collection-grid">
          <img
            v-for="item in collection"
            :key="item.reward_id"
            :src="item.pokemon.sprite_url"
            :alt="item.pokemon.name ?? `#${item.pokemon.id}`"
            :title="`${item.pokemon.name ?? '#' + item.pokemon.id} (from ${item.issue_key})`"
          />
        </div>
      </TabPanel>
    </TabPanels>
  </Tabs>

  <Message v-if="status" severity="error" size="small" class="status-message">
    {{ status }}
  </Message>

  <Dialog
    v-model:visible="showReveal"
    modal
    header="Box opened"
    :draggable="false"
    :style="{ width: '18rem' }"
  >
    <div v-if="revealed" class="reveal">
      <img :src="revealed.sprite_url" :alt="revealed.name ?? 'Pokémon'" />
      <p class="reveal-name">{{ revealed.name ?? `#${revealed.id}` }}</p>
    </div>

    <template #footer>
      <Button label="View collection" severity="secondary" text @click="goToCollection" />
      <Button
        v-if="boxes.length"
        :label="`Open next box (${boxes.length})`"
        :loading="busy"
        @click="openNext"
      />
      <Button v-else label="Done" @click="showReveal = false" />
    </template>
  </Dialog>
</template>

<style scoped>
.tab-badge {
  margin-left: 0.4rem;
}

.logout-row {
  margin-top: 0.75rem;
}

.collection-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.collection-grid img {
  width: 100%;
}

.status-message {
  margin: 0.5rem;
}

.reveal {
  text-align: center;
}

.reveal img {
  width: 140px;
  height: 140px;
}

.reveal-name {
  margin: 0.25rem 0 0;
  font-size: 1.1rem;
  font-weight: 600;
  text-transform: capitalize;
}
</style>