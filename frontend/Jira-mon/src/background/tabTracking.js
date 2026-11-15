export function isJiraPage(url = '') {
	return /^https:\/\/([^.]+\.)?atlassian\.net\/jira(?:\/|$)/.test(url)
}

const ignore = () => {}

export function updateAction(tabId, url) {
	if (typeof tabId !== 'number') return

	if (isJiraPage(url)) {
		chrome.action.setPopup({ tabId, popup: 'index.html' }).catch(ignore)
		chrome.action.enable(tabId).catch(ignore)
	} else {
		chrome.action.setPopup({ tabId, popup: '' }).catch(ignore)
		chrome.action.disable(tabId).catch(ignore)
	}
}

export function updateOpenTabs() {
	chrome.action.disable()
	chrome.tabs.query({}, (tabs) => {
		tabs.forEach((tab) => updateAction(tab.id, tab.url))
	})
}