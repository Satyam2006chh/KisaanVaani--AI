import { useEffect, useRef, useState } from 'react'
import { ArrowDown, Globe, Loader, MapPin, Mic, MicOff, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, speakText, transcribeAudio } from '../../api'
import './Hero.css'

const S = { IDLE: 'idle', RECORDING: 'recording', PROCESSING: 'processing', SPEAKING: 'speaking' }

const HINTS = {
  [S.IDLE]:       'Mic dabao aur bolna shuru karo',
  [S.RECORDING]:  'Sun raha hoon… bolte raho',
  [S.PROCESSING]: 'Soch raha hoon…',
  [S.SPEAKING]:   'Jawab sun lo… dobara poochne ke liye mic dabao',
}

export default function Hero() {
  const { user, languages } = useAuth()
  const [status,     setStatus]     = useState(S.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply,      setReply]      = useState('')
  const [error,      setError]      = useState('')
  
  const recognitionRef = useRef(null)
  const audioRef = useRef(null)

  const userLang = languages.find(l => l.code === user?.language)?.name || 'Hindi'
  const langCode = user?.language || 'hi-IN'

  useEffect(() => () => {
    // cleanup: stop MediaRecorder stream or SpeechRecognition
    try { recognitionRef.current?.stream?.getTracks?.().forEach(t => t.stop()) } catch {}
    try { recognitionRef.current?.abort?.() } catch {}
    audioRef.current?.pause()
  }, [])

  async function startRecording() {
    audioRef.current?.pause()
    audioRef.current = null
    setError(''); setTranscript(''); setReply('')

    // Prefer MediaRecorder + backend STT. Fallback to Web SpeechRecognition.
    if (navigator.mediaDevices && window.MediaRecorder) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
        const recorder = new MediaRecorder(stream, { mimeType: mime })
        const chunks = []

        recorder.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data) }
        recorder.onstart = () => { setStatus(S.RECORDING) }
        recorder.onerror = (e) => {
          setError('Recording error: ' + (e?.error?.name || e?.error || 'unknown'))
          setStatus(S.IDLE)
        }
        recorder.onstop = async () => {
          setStatus(S.PROCESSING)
          const blob = new Blob(chunks, { type: mime })
          try {
            const text = await transcribeAudio(blob)
            setTranscript(text)
            if (text && text.trim()) {
              await handleChat(text)
            } else {
              setError('Koi awaaz nahi aayi. Mic ke paas bolein.')
              setStatus(S.IDLE)
            }
          } catch (err) {
            setError('Transcription failed. ' + (err?.response?.data?.detail || err.message))
            setStatus(S.IDLE)
          } finally {
            // stop tracks
            try { stream.getTracks().forEach(t => t.stop()) } catch {}
          }
        }

        recognitionRef.current = { recorder, stream }
        recorder.start()
      } catch (err) {
        setError('Mic access error. Browser permissions likely denied.')
        setStatus(S.IDLE)
      }
      return
    }

    // Fallback: Web Speech API (client-side STT)
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      setError('Aapka browser voice input support nahi karta. Chrome use karein.')
      return
    }
  }

  async function handleChat(text) {
    try {
      const response = await chatWithAgent(text)
      setReply(response)
      try {
        const url   = await speakText(response)
        const audio = new Audio(url)
        audioRef.current = audio
        setStatus(S.SPEAKING)
        audio.onended = audio.onerror = () => { setStatus(S.IDLE); audioRef.current = null }
        await audio.play()
      } catch {
        setStatus(S.IDLE)
      }
    } catch (e) {
      setError('Error: ' + (e?.response?.data?.detail || e.message))
      setStatus(S.IDLE)
    }
  }

  function handleMicClick() {
    if (status === S.IDLE) {
      startRecording()
    } else if (status === S.RECORDING) {
      // stop MediaRecorder or SpeechRecognition
      const cur = recognitionRef.current
      if (cur?.recorder) {
        try { cur.recorder.stop() } catch {}
      } else {
        try { cur?.stop?.() || cur?.abort?.() } catch {}
      }
    } else if (status === S.SPEAKING) {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      setStatus(S.IDLE)
      startRecording()
    }
  }

  const isRecording = status === S.RECORDING
  const isBusy      = status === S.PROCESSING

  return (
    <section className="hero animate-reveal" id="hero">
      <div className="hero__blob hero__blob--1" />
      <div className="hero__blob hero__blob--2" />

      <div className="container hero__inner centered-content">
        <div className="hero__top-bar">
          <div className="hero__badge glass-panel">
            <span className="hero__badge-dot" />
            LIVE AI ASSISTANT
          </div>
          
          {user && (
            <div className="hero__user-pills">
              <div className="user-pill glass-panel">
                <User size={14} /> <span>{user.name}</span>
              </div>
              <div className="user-pill glass-panel">
                <MapPin size={14} /> <span>{user.city || 'Kheti'}</span>
              </div>
            </div>
          )}
        </div>

        <div className="hero__content">
          <h1 className="hero__title">
            Bolo, Samjho,<br />
            <span className="highlight">Badlo Apni Zindagi</span>
          </h1>
          
          <p className="hero__sub">
            Namaste <span className="highlight">{user?.name || 'Kisaan'}</span> ji! Main aapki help ke liye taiyaar hoon. 
            Mausam, Mandi rates aur latest kheti samachar ke liye mic dabaiye.
          </p>
        </div>

        <div className="hero__assistant glass-panel animate-reveal" style={{ animationDelay: '0.2s' }}>
          <div className="assistant__chat-area">
            {transcript && (
              <div className="chat-bubble user-bubble animate-reveal">
                <div className="bubble-label">Aapne Bola</div>
                <p>{transcript}</p>
              </div>
            )}
            
            {reply && (
              <div className="chat-bubble ai-bubble animate-reveal">
                <div className="bubble-label">KisaanVaani AI</div>
                <p>{reply}</p>
              </div>
            )}

            {!transcript && !reply && !error && (
              <div className="chat-placeholder">
                <div className="pulse-circle">
                  <Mic size={40} className="highlight" />
                </div>
                <p className="mic-status">{HINTS[status]}</p>
              </div>
            )}

            {error && <div className="chat-error animate-reveal">⚠️ {error}</div>}
          </div>

          <div className="assistant__controls">
            <div className="mic-container">
              <button
                className={`mic-trigger ${isRecording ? 'active' : ''}`}
                onClick={handleMicClick}
                disabled={isBusy}
              >
                {isBusy ? <Loader size={48} className="spin" /> : 
                 isRecording ? <MicOff size={48} /> : <Mic size={48} />}
              </button>
              <div className="mic-status">{isRecording ? 'Listening...' : 'Tap to Speak'}</div>
            </div>
          </div>
        </div>

        <div className="hero__footer animate-reveal" style={{ animationDelay: '0.4s' }}>
          <div className="stat-group">
            <span className="stat-val">22</span>
            <span className="stat-lbl">Languages</span>
          </div>
          <div className="stat-sep" />
          <div className="stat-group">
            <span className="stat-val">LIVE</span>
            <span className="stat-lbl">Mandi Rates</span>
          </div>
          <div className="stat-sep" />
          <div className="stat-group">
            <span className="stat-val">AI</span>
            <span className="stat-lbl">News Crawl</span>
          </div>
        </div>
      </div>
    </section>
  )
}
