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

// In dev mode (Vite), VITE_API_URL is empty → requests go to relative /api/...
// which Vite proxies to localhost:8000.  In production, it's the full Render URL.
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = () => axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
})


export async function chatWithAgent(message, englishMessage = null, language = null, image = null) {
  const user = getUser()
  console.log('[API] chatWithAgent:', { message: message?.substring(0, 50), hasEnglish: !!englishMessage, language })
  try {
    const { data } = await api().post('/api/agent/chat', {
      farmer_id:  user?.farmer_id || 'guest',
      session_id: getSessionId(),
      message,
      english_message: englishMessage,
      language:   language || user?.language || 'hi-IN',
      image:      image,
    })
    console.log('[API] chatWithAgent response:', { hasResponse: !!data.response })
    return data // Return full data object
  } catch (err) {
    console.error('[API] chatWithAgent error:', err.response?.status, err.message)
    throw err
  }
}


export async function speakText(text, language = null, speaker = null) {
  const user = getUser()
  console.log('[API] speakText:', { textLength: text?.length, language })
  try {
    const response = await api().post(
      '/api/voice/speak',
      { text, language: language || user?.language || 'hi-IN', speaker },
      { responseType: 'blob' },
    )
    const audioUrl = URL.createObjectURL(response.data)
    console.log('[API] speakText audio generated:', audioUrl.substring(0, 50))
    return audioUrl
  } catch (err) {
    console.error('[API] speakText error:', err.response?.status, err.message)
    throw err
  }
}


export async function transcribeAudio(blob, language = null) {
  const user = getUser()
  const mime = blob.type || 'audio/webm'
  const ext  = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm'
  const form = new FormData()
  form.append('audio', blob, `audio.${ext}`)
  form.append('language', language || user?.language || 'hi-IN')
  
  console.log('[API] transcribeAudio:', { blobSize: blob.size, ext, language, baseUrl: API_BASE_URL || '(relative/proxy)' })
  
  try {
    // Use the shared api() instance so base URL + proxy + auth are consistent
    const { data } = await api().post(
      '/api/voice/transcribe',
      form,
      { 
        timeout: 60000,
        // Let axios + FormData set the correct Content-Type with boundary
        headers: { 'Content-Type': undefined }
      }
    )
    console.log('[API] transcribeAudio response:', { status: data.status, hasTranscript: !!data.transcript })
    return data
  } catch (err) {
    console.error('[API] transcribeAudio error:', { status: err.response?.status, message: err.message, data: err.response?.data })
    throw err
  }
}
