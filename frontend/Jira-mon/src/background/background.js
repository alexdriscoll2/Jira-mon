
import { connectJira, sendCodeToBackend } from './auth.js'
import { saveSession, getSession, clearSession } from './session.js'
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
})
