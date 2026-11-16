
import { connectJira, sendCodeToBackend } from './auth.js'
import { saveSession, getSession, clearSession, apiFetch, apiJson } from './session.js'
import { updateAction, updateOpenTabs } from './tabTracking.js'


// Tab tracking listeners

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
	if (changeInfo.url || changeInfo.status === 'loading') {
		updateAction(tabId, changeInfo.url || tab.url)
	}
})

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => {
    if (chrome.runtime.lastError || !tab) return
    updateAction(tabId, tab.url)
  })
})

chrome.runtime.onInstalled.addListener(updateOpenTabs)
chrome.runtime.onStartup.addListener(updateOpenTabs)



const apiHandlers = {
  SYNC_REWARDS: () => apiJson('/rewards/sync', { method: 'POST' }),
  OPEN_BOX: (m) => apiJson(`/rewards/${m.rewardId}/open`, { method: 'POST' }),
  GET_COLLECTION: () => apiJson('/rewards/collection'),
}

// Auth listeners

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'CONNECT_JIRA') {
    connectJira()
      .then(sendCodeToBackend)
      .then(async (login) => {
        await saveSession(login)
        sendResponse({ ok: true, user: login.user })
      })
      .catch((err) => {
        console.error('Jira connect failed:', err)
        sendResponse({ ok: false, error: String(err) })
      })
    return true
  }

  if (message.type === 'GET_SESSION') {
    getSession().then(({ user }) => sendResponse({ user: user ?? null }))
    return true
  }

  if (message.type === 'LOGOUT') {
    clearSession().then(() => sendResponse({ ok: true }))
    return true
  }

  const handler = apiHandlers[message.type]
  if (handler) {
    handler(message)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: err.message }))
    return true
  }
})
