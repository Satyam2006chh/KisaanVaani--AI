import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, CloudRain, TrendingUp, Sprout, Volume2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'
import './Hero.css'

const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus] = useState(S.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const audioRef = useRef(null)

  // Language based on user profile
  const langCode = user?.language || 'hi-IN'

  function stopAll() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
  }

  async function startRecording() {
    stopAll()
    setError(''); setTranscript(''); setReply(''); 
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setStatus(S.PROCESSING)
        
        try {
          // Use 'unknown' to trigger Sarvam Auto-detection
          const res = await transcribeAudio(blob, 'unknown')
          if (res.status === 'SUCCESS') {
             setTranscript(res.transcript)
             await handleChat(res.transcript, res.detected_language)
          } else if (res.status === 'SILENCE_DETECTED') {
             setReply(res.silence_reply)
             setStatus(S.SPEAKING)
          } else {
             throw new Error(res.error || 'Transcription failed')
          }
        } catch (err) {
          setError('Maaf kijiye, main sun nahi paaya. Dubara koshish karein.')
          setStatus(S.IDLE)
        }
        
        // Stop all tracks to release mic
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) {
      setError('Mic access denied! Please check browser permissions.')
      setStatus(S.IDLE)
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
  }

  async function handleChat(text, detectedLang = null) {
    try {
      const res = await chatWithAgent(text, null, detectedLang || langCode)
      setReply(res.response)
      
      // Start TTS immediately after receiving text
      setStatus(S.PROCESSING) // Keep processing state while audio loads
      try {
        const audioUrl = await speakText(res.response)
        await playAudio(audioUrl)
      } catch (audioErr) {
        console.error('TTS Failed:', audioErr)
        setStatus(S.IDLE)
      }
    } catch (err) {
      setError('System busy. Phir se try karein.')
      setStatus(S.IDLE)
    }
  }

  async function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    audioRef.current = audio
    setStatus(S.SPEAKING)
    audio.onended = () => { setStatus(S.IDLE); audioRef.current = null }
    audio.onerror = () => { setStatus(S.IDLE); audioRef.current = null }
    try { await audio.play() } catch { setStatus(S.IDLE) }
  }

  return (
    <div className="hero-section">
      <div className="container centered-content">
        
        {/* Header */}
        <div className="hero-header animate-reveal">
          <div className="badge">🌾 Bharat Ka AI Agricultural Expert</div>
          <h1>Namaste <span className="highlight">{user?.name || 'Kisaan'}</span> ji</h1>
          <p className="hero-subtitle">Mausam, Mandi ya Kheti ki koi bhi jankari ke liye mic dabaiye.</p>
        </div>

        {/* Central Engine */}
        <div className="voice-engine-container animate-reveal" style={{ animationDelay: '0.2s' }}>
          <div className={`mic-aura ${status === S.RECORDING ? 'pulsing' : ''}`} />
          
          <button 
            className={`mic-trigger-v2 ${status === S.RECORDING ? 'active' : ''} ${status === S.PROCESSING ? 'loading' : ''}`}
            onClick={status === S.RECORDING ? stopRecording : startRecording}
            disabled={status === S.PROCESSING}
          >
            {status === S.RECORDING ? <Square size={32} fill="white" /> : 
             status === S.PROCESSING ? <Loader size={36} className="spin" /> : <Mic size={36} />}
            <div className="mic-status-v2">
              {status === S.RECORDING ? 'Suno rha hoon...' : 
               status === S.PROCESSING ? (reply ? 'Awaaz taiyar ho rahi hai...' : 'Samajh rha hoon...') : 
               status === S.SPEAKING ? 'Bol rha hoon...' : 'Touch to Speak'}
            </div>
          </button>

          {/* Transcript/Reply Bubble */}
          <div className={`transcript-bubble ${ (transcript || reply) ? 'visible' : ''}`}>
             <span className="bubble-label">{reply ? 'AI Scientist' : 'Aapne Bola'}</span>
             <p>{reply || transcript || 'Aapki baat yaha dikhegi...'}</p>
          </div>
        </div>

        {error && <div className="error-toast glass-panel">⚠️ {error}</div>}

        {/* Features */}
        <div className="feature-grid animate-reveal" style={{ animationDelay: '0.4s' }}>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><CloudRain size={24} /></div>
            <h3>Mausam</h3>
            <p>Hoshangabad mein kal ki baarish aur kheti ki advice.</p>
          </div>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><TrendingUp size={24} /></div>
            <h3>Mandi Bhav</h3>
            <p>Apne zila ki mandi mein fasal ke sahi daam.</p>
          </div>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><Sprout size={24} /></div>
            <h3>Fasal Salah</h3>
            <p>Mitti ke anusar behtar paidavar ki expert tips.</p>
          </div>
        </div>

        {/* Steps */}
        <div className="steps-row animate-reveal" style={{ animationDelay: '0.6s' }}>
          <div className={`step-item ${status === S.IDLE ? 'active' : ''}`}>
            <span className="step-num">01</span>
            <p>Mic dabao</p>
          </div>
          <div className="step-line" />
          <div className={`step-item ${status === S.PROCESSING ? 'active' : ''}`}>
             <span className="step-num">02</span>
             <p>AI samjhega</p>
          </div>
          <div className="step-line" />
          <div className={`step-item ${status === S.SPEAKING ? 'active' : ''}`}>
             <span className="step-num">03</span>
             <p>Jawab suno</p>
          </div>
        </div>

      </div>
    </div>
  )
}
