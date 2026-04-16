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
    <section className="hero" id="hero">
      <div className="hero__grid"            aria-hidden="true" />
      <div className="hero__blob hero__blob--green" aria-hidden="true" />
      <div className="hero__blob hero__blob--gold"  aria-hidden="true" />

      <div className="container hero__inner">
        <div className="hero__badge">
          <span className="hero__badge-dot" />
          India's First Voice AI for Farmers &nbsp;🌾
        </div>

        {user && (
          <div className="hero__user-banner">
            <span className="hero__user-info"><User size={13} /> {user.name}</span>
            <span className="hero__user-info">
              <MapPin size={13} />
              {[user.city, user.district, user.state].filter(Boolean).join(', ')}
            </span>
            <span className="hero__user-info"><Globe size={13} /> {userLang}</span>
          </div>
        )}

        <h1 className="hero__title">
          Bolo, Samjho,<br />
          <span className="highlight">Badlo Apni Zindagi</span>
        </h1>

        <p className="hero__sub">
          Sirf bolne se paayein sarkari yojanaon ki jankari,<br className="hero__br" />
          mausam, mandi bhav aur fasal salah — {userLang} mein.
        </p>

        <div className="hero__mic-wrap">
          <div className="hero__mic-ring hero__mic-ring--3" />
          <div className="hero__mic-ring hero__mic-ring--2" />
          <div className="hero__mic-ring hero__mic-ring--1" />
          <button
            className={`hero__mic-btn${isRecording ? ' hero__mic-btn--active' : ''}`}
            onClick={handleMicClick}
            disabled={isBusy}
            aria-label="Mic"
          >
            {isBusy
              ? <Loader size={34} className="spin" />
              : isRecording
                ? <MicOff size={34} />
                : <Mic size={34} />}
          </button>
        </div>

        <p className="hero__mic-hint">{HINTS[status]}</p>

        {transcript && <p className="hero__transcript">🗣 {transcript}</p>}
        {reply      && <p className="hero__reply">🤖 {reply}</p>}
        {error      && <p className="hero__error">⚠️ {error}</p>}

        <div className="hero__cta-row">
          <a href="#features"    className="btn-primary">Explore Features</a>
          <a href="#how-it-works" className="btn-outline">How It Works</a>
        </div>

        <div className="hero__stats">
          {[
            { num: '11',   label: 'Indian Languages' },
            { num: '5+',   label: 'AI Tools' },
            { num: '600M', label: 'Potential Users' },
            { num: '100%', label: 'Voice Driven' },
          ].map(s => (
            <div key={s.label} className="hero__stat">
              <span className="hero__stat-num">{s.num}</span>
              <span className="hero__stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      <a href="#about" className="hero__scroll" aria-label="Scroll down">
        <ArrowDown size={17} />
      </a>
    </section>
  )
}
