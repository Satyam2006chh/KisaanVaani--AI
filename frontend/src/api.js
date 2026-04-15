import axios from 'axios'

const getToken = () => localStorage.getItem('token')
const getUser  = () => { try { return JSON.parse(localStorage.getItem('user')) } catch { return null } }

const getSessionId = () => {
  let sid = sessionStorage.getItem('session_id')
  if (!sid) {
    sid = `s_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    sessionStorage.setItem('session_id', sid)
  }
  return sid
}

const api = () => axios.create({
  headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
})


export async function chatWithAgent(message) {
  const user = getUser()
  const { data } = await api().post('/api/agent/chat', {
    farmer_id:  user?.farmer_id || 'guest',
    session_id: getSessionId(),
    message,
    language:   user?.language || 'hi-IN',
  })
  return data.response
}


export async function speakText(text) {
  const user = getUser()
  const response = await api().post(
    '/api/voice/speak',
    { text, language: user?.language || 'hi-IN' },
    { responseType: 'blob' },
  )
  return URL.createObjectURL(response.data)
}


export async function transcribeAudio(blob) {
  const user = getUser()
  const mime = blob.type || 'audio/webm'
  const ext  = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm'
  const form = new FormData()
  form.append('audio', blob, `audio.${ext}`)
  form.append('language', user?.language || 'hi-IN')
  const { data } = await api().post('/api/voice/transcribe', form)
  return data.transcript
}
