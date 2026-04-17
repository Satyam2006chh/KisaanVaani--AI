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
  const [error, setError] = useState('')
  const [lastBlob,   setLastBlob]   = useState(null)
  const [micLevel,   setMicLevel]   = useState(0)

  const recognitionRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyzerRef = useRef(null)
  const animationFrameRef = useRef(null)
  const audioRef = useRef(null)
  const fallbackTranscriptRef = useRef('')

  const langCode = user?.language || 'hi-IN'

  useEffect(() => () => {
    stopAll()
  }, [])

  function stopAll() {
    try { recognitionRef.current?.stream?.getTracks?.().forEach(t => t.stop()) } catch {}
    try { recognitionRef.current?.recorder?.stop?.() } catch {}
    try { recognitionRef.current?.recognition?.stop?.() } catch {}
    try { audioContextRef.current?.close() } catch {}
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
    audioRef.current?.pause()
  }

  function encodeWAV(samples) {
    const buffer = new ArrayBuffer(44 + samples.length * 2)
    const view = new DataView(buffer)
    const writeString = (off, s) => { for(let i=0; i<s.length; i++) view.setUint8(off+i, s.charCodeAt(i)) }
    
    writeString(0, 'RIFF')
    view.setUint32(4, 32 + samples.length * 2, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, 1, true)
    view.setUint32(24, 16000, true)
    view.setUint32(28, 32000, true)
    view.setUint16(32, 2, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, samples.length * 2, true)
    
    let offset = 44
    for (let i=0; i<samples.length; i++) {
      let s = Math.max(-1, Math.min(1, samples[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
      offset += 2
    }
    return new Blob([view], { type: 'audio/wav' })
  }

  async function startRecording() {
    stopAll()
    setError(''); setTranscript(''); setReply(''); setLastBlob(null); setMicLevel(0)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Visualization logic
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyzer = audioCtx.createAnalyser()
      analyzer.fftSize = 512
      source.connect(analyzer)
      audioContextRef.current = audioCtx
      analyzerRef.current = analyzer

      // Use standard MediaRecorder
      const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 
                   MediaRecorder.isTypeSupported('audio/ogg') ? 'audio/ogg' : 'audio/mp4'
      const recorder = new MediaRecorder(stream, { mimeType: mime })
      const chunks = []
      
      recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data) }
      recorder.onstart = () => { setStatus(S.RECORDING) }
      
      recorder.onstop = async () => {
        setStatus(S.PROCESSING)
        const audioBlob = new Blob(chunks, { type: mime })
        setLastBlob(audioBlob)

        try {
          const res = await transcribeAudio(audioBlob) 
          
          if (res.status === 'SILENCE_DETECTED') {
            const silenceMsg = res.silence_reply || 'Maaf kijiye, mujhe kuch sunai nahi diya.'
            // Don't setReply here so it stays hidden in UI as requested
            const audioUrl = await speakText(silenceMsg)
            playAudio(audioUrl)
            return
          }

          if (res.status === 'SUCCESS' && res.transcript) {
            setTranscript(res.transcript)
            await handleChat(res.transcript, res.english_transcript)
          } else {
            setError(res.error || 'Kuch sunai nahi diya. Dobara mic dabakar bole kaber.')
            setStatus(S.IDLE)
          }
        } catch (err) {
          setError('Voice error. Internet ya mic setting check karein.')
          setStatus(S.IDLE)
        } finally {
          stream.getTracks().forEach(t => t.stop())
        }
      }

      recognitionRef.current = { recorder, stream }
      recorder.start()
      drawWave()
    } catch (err) {
      setError('Mic blocked! Lock icon par click karke mic allow karein.')
      setStatus(S.IDLE)
    }
  }

  async function playAudio(url) {
    const audio = new Audio(url)
    audioRef.current = audio
    setStatus(S.SPEAKING)
    audio.onended = audio.onerror = () => { setStatus(S.IDLE); audioRef.current = null }
    await audio.play()
  }

  function playBack() {
    if (!lastBlob) return
    const url = URL.createObjectURL(lastBlob)
    const audio = new Audio(url)
    audio.play()
  }

  function drawWave() {
    if (analyzerRef.current) {
        const d = new Uint8Array(analyzerRef.current.frequencyBinCount)
        analyzerRef.current.getByteFrequencyData(d)
        const v = d.reduce((a, b) => a + b) / d.length
        const s = 1 + (v / 60)
        const btn = document.querySelector('.mic-trigger')
        if (btn) btn.style.transform = `scale(${s})`
        animationFrameRef.current = requestAnimationFrame(drawWave)
    }
  }

  async function handleChat(text, englishText = null) {
    try {
      const response = await chatWithAgent(text, englishText)
      const aiReply = response.response
      setReply(aiReply)
      
      try {
        const url = await speakText(aiReply)
        await playAudio(url)
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
      const btn = document.querySelector('.mic-trigger'); if (btn) btn.style.transform = 'scale(1)'
      const cur = recognitionRef.current
      if (cur?.recorder) try { cur.recorder.stop() } catch {}
      if (cur?.recognition) try { cur.recognition.stop() } catch {}
    } else if (status === S.SPEAKING) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
      setStatus(S.IDLE); startRecording()
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
            {(transcript || reply) ? (
              <div className="chat-history">
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
              </div>
            ) : (
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
