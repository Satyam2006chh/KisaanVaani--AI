import { useState, useRef } from 'react'
import { Mic, MicOff, ArrowDown, Loader } from 'lucide-react'
import { transcribeAudio, chatWithAgent, speakText } from '../../api'
import './Hero.css'

const STATES = { IDLE: 'idle', RECORDING: 'recording', PROCESSING: 'processing', SPEAKING: 'speaking' }

export default function Hero() {
  const [status, setStatus] = useState(STATES.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  const mediaRef = useRef(null)
  const chunksRef = useRef([])

  const hints = {
    [STATES.IDLE]: 'Tap the mic to experience the demo',
    [STATES.RECORDING]: 'Recording… tap again to stop',
    [STATES.PROCESSING]: 'Processing your question…',
    [STATES.SPEAKING]: 'Playing response…',
  }

  async function startRecording() {
    setError('')
    setTranscript('')
    setReply('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = e => chunksRef.current.push(e.data)
      recorder.onstop = () => handleStop(stream)
      recorder.start()
      mediaRef.current = recorder
      setStatus(STATES.RECORDING)
    } catch {
      setError('Microphone access denied.')
    }
  }

  function stopRecording() {
    mediaRef.current?.stop()
  }

  async function handleStop(stream) {
    stream.getTracks().forEach(t => t.stop())
    setStatus(STATES.PROCESSING)
    try {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      const text = await transcribeAudio(blob)
      setTranscript(text)
      const response = await chatWithAgent(text)
      setReply(response)
      const audioUrl = await speakText(response)
      setStatus(STATES.SPEAKING)
      const audio = new Audio(audioUrl)
      audio.onended = () => setStatus(STATES.IDLE)
      audio.play()
    } catch (e) {
      setError(e?.response?.data?.detail || 'Something went wrong. Please try again.')
      setStatus(STATES.IDLE)
    }
  }

  function handleMicClick() {
    if (status === STATES.IDLE || status === STATES.SPEAKING) startRecording()
    else if (status === STATES.RECORDING) stopRecording()
  }

  const isActive = status === STATES.RECORDING
  const isBusy = status === STATES.PROCESSING

  return (
    <section className="hero" id="hero">
      <div className="hero__grid" aria-hidden="true" />
      <div className="hero__blob hero__blob--green" aria-hidden="true" />
      <div className="hero__blob hero__blob--gold"  aria-hidden="true" />

      <div className="container hero__inner">
        <div className="hero__badge">
          <span className="hero__badge-dot" />
          India's First Voice AI for Farmers &nbsp;🌾
        </div>

        <h1 className="hero__title">
          Bolo, Samjho,<br />
          <span className="highlight">Badlo Apni Zindagi</span>
        </h1>

        <p className="hero__sub">
          Sirf bolne se paayein sarkari yojanaon ki jankari,<br className="hero__br" />
          mausam, mandi bhav aur fasal salah — Hindi, Punjabi ya apni bhasha mein.
        </p>

        <div className="hero__mic-wrap">
          <div className="hero__mic-ring hero__mic-ring--3" />
          <div className="hero__mic-ring hero__mic-ring--2" />
          <div className="hero__mic-ring hero__mic-ring--1" />
          <button
            className={`hero__mic-btn${isActive ? ' hero__mic-btn--active' : ''}`}
            aria-label="Start speaking"
            onClick={handleMicClick}
            disabled={isBusy}
          >
            {isBusy ? <Loader size={36} className="spin" /> : isActive ? <MicOff size={36} /> : <Mic size={36} />}
          </button>
        </div>

        <p className="hero__mic-hint">{hints[status]}</p>

        {transcript && <p className="hero__transcript">🗣 {transcript}</p>}
        {reply      && <p className="hero__reply">🤖 {reply}</p>}
        {error      && <p className="hero__error">⚠️ {error}</p>}

        <div className="hero__cta-row">
          <a href="#features" className="btn-primary">Explore Features</a>
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
        <ArrowDown size={18} />
      </a>
    </section>
  )
}
