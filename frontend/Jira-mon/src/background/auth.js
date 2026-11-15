
const JIRA_CLIENT_ID = 'F3AWMlsX5dkTLLRCfpLQhSbIn8dxKDOa'

const SCOPES = ['read:jira-work', 'read:jira-user', 'offline_access'].join(' ')

export async function connectJira() {
  const redirectUri = chrome.identity.getRedirectURL()
  const state = crypto.randomUUID()

  const params = new URLSearchParams({
    audience: 'api.atlassian.com',
    client_id: JIRA_CLIENT_ID,
    scope: SCOPES,
    redirect_uri: redirectUri,
    state,
    response_type: 'code',
    prompt: 'consent',
  })

  const responseUrl = await chrome.identity.launchWebAuthFlow({
    url: `https://auth.atlassian.com/authorize?${params}`,
    interactive: true,
  })

  const result = new URL(responseUrl)
  if (result.searchParams.get('state') !== state) {
    throw new Error('State mismatch, so the response was rejected')
  }
  const error = result.searchParams.get('error')
  if (error) throw new Error(error)

  return result.searchParams.get('code')
}

const API_URL = 'http://localhost:8000'

export async function sendCodeToBackend(code) {
  const res = await fetch(`${API_URL}/auth/jira/callback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Backend error ${res.status}`)
  }
  return res.json()
}
