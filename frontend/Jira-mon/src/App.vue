<script setup lang="ts">
import Toolbar from 'primevue/toolbar'
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';

import jiraLogo from '@/assets/Jira_icon.svg'
import pokeball from '@/assets/pokeball_white.png'

import { ref, onMounted } from 'vue'

const user = ref<{ email: string } | null>(null)

const status = ref('not connected')

async function connect() {
  status.value = 'waiting for Atlassian...'
  try {
    const res = await chrome.runtime.sendMessage({ type: 'CONNECT_JIRA' })
    if (!res) {
      status.value = 'no response from background script'
    } else {
      status.value = res.ok ? `connected as ${res.user.email}` : `failed: ${res.error}`
      user.value = res.user
    }
  } catch (err) {
    status.value = 'error: ' + err
  }
}

onMounted(async () => {
  const res = await chrome.runtime.sendMessage({ type: 'GET_SESSION' })
  user.value = res?.user ?? null
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

  <Tabs value="tab1" class="app-tabs">
    <TabList class="app-tablist">
      <Tab value="tab1">Home</Tab>
      <Tab value="tab2">Collection</Tab>
    </TabList>
    <TabPanels>
        <TabPanel value="tab1">
          <p class="text-surface-500 mt-1">Hello <b>Name</b></p>
          <div class="grid-container">
            <div>
              <p class="text-surface-500 mt-1">stats</p>

              <div v-if="user === null">
                <button @click="connect">Connect to Jira</button>
              </div>
              <div v-else>connected as {{ user.email }}!</div>
              
            </div>
            <div class="pokeball-cell">
              <img :src="pokeball" alt="" class="pokeball-grey" />
            </div>
          </div>
        </TabPanel>
        <TabPanel value="tab2">
          <h2 class="text-lg font-bold">Collection</h2>
          <p class="text-surface-500 mt-1">This is your collection.</p>
        </TabPanel>
    </TabPanels>
  </Tabs>

</template>

<style scoped></style>
