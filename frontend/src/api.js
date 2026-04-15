import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function transcribeAudio(blob, language = 'hi-IN') {
  const form = new FormData()
  form.append('audio', blob, 'audio.webm')
  form.append('language', language)
  const { data } = await api.post('/api/voice/transcribe', form)
  return data.transcript
}

export async function chatWithAgent(message, language = 'hi-IN') {
  const { data } = await api.post('/api/agent/chat', {
    farmer_id: 'demo_farmer',
    session_id: 'demo_session',
    message,
    language,
  })
  return data.response
}

export async function speakText(text, language = 'hi-IN') {
  const response = await api.post(
    '/api/voice/speak',
    { text, language },
    { responseType: 'blob' }
  )
  return URL.createObjectURL(response.data)
}
