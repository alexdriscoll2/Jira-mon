export const API_URL = 'http://localhost:8000'

export async function saveSession({ user, session_token }) {
  await chrome.storage.local.set({ user, session_token })
}

export async function getSession() {
  return chrome.storage.local.get(['user', 'session_token'])
}

export async function clearSession() {
  await chrome.storage.local.remove(['user', 'session_token'])
}

// Use this for every call to your own API from now on.
export async function apiFetch(path, options = {}) {
  const { session_token } = await chrome.storage.local.get('session_token')
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${session_token}` },
  })
  if (res.status === 401) {
    await clearSession()
    throw new Error('Session expired, please reconnect Jira')
  }
  return res
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Backend error ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}
