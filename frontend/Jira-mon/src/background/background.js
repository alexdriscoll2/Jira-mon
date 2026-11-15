function isJiraPage(url = '') {
	return /^https:\/\/([^.]+\.)?atlassian\.net\/jira(?:\/|$)/.test(url)
}

function updateAction(tabId, url) {
	if (typeof tabId !== 'number') return

	if (isJiraPage(url)) {
		chrome.action.setPopup({ tabId, popup: 'index.html' })
		chrome.action.enable(tabId)
	} else {
		chrome.action.setPopup({ tabId, popup: '' })
		chrome.action.disable(tabId)
	}
}

function updateOpenTabs() {
	chrome.action.disable()
	chrome.tabs.query({}, (tabs) => {
		tabs.forEach((tab) => updateAction(tab.id, tab.url))
	})
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
	if (changeInfo.url || changeInfo.status === 'loading') {
		updateAction(tabId, changeInfo.url || tab.url)
	}
})

chrome.tabs.onActivated.addListener(({ tabId }) => {
	chrome.tabs.get(tabId, (tab) => updateAction(tabId, tab.url))
})

chrome.runtime.onInstalled.addListener(updateOpenTabs)
chrome.runtime.onStartup.addListener(updateOpenTabs)
