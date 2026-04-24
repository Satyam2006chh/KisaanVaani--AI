import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, MapPin, AlertCircle, TrendingUp, Image as ImageIcon, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'
import './Hero.css'

const LANGUAGES = [
  { code: 'hi-IN', label: 'हिंदी (Hindi)' },
  { code: 'pa-IN', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'bn-IN', label: 'বাংলা (Bengali)' },
  { code: 'ta-IN', label: 'தமிழ் (Tamil)' },
  { code: 'te-IN', label: 'తెలుగు (Telugu)' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml-IN', label: 'മലയാളം (Malayalam)' },
  { code: 'mr-IN', label: 'मराठी (Marathi)' },
  { code: 'gu-IN', label: 'ગુજરાતી (Gujarati)' },
  { code: 'od-IN', label: 'ଓଡ଼ିଆ (Odia)' },
  { code: 'en-IN', label: 'English' },
]

const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus]           = useState(S.IDLE)
  const [transcript, setTranscript]   = useState('')
  const [reply, setReply]             = useState('')
  const [error, setError]             = useState('')
  const [location, setLocation]       = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [image, setImg]               = useState(null)
  const [imgPreview, setImgPreview]   = useState(null)
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')

  const mediaRecorderRef = useRef(null)
  const mediaStreamRef   = useRef(null)
  const chunksRef        = useRef([])
  const isRecordingRef   = useRef(false)
  
  const audioCtxRef = useRef(null)
  const analyzerRef = useRef(null)
  const [volume, setVolume] = useState(0)

  // ─── EFFECTS ─────────────────────────────────────────────────────────────
  useEffect(() => {
    // Location detection
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(async ({ coords: { latitude, longitude } }) => {
        try {
          const r = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&accept-language=en`)
          const d = await r.json()
          const city = d.address.city || d.address.town || d.address.village || 'Your Location'
          setLocation({ lat: latitude, lon: longitude, city })
        } catch (e) {}
      })
    }
  }, [])

  // ─── ACTIONS ──────────────────────────────────────────────────────────────
  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImgPreview(URL.createObjectURL(file))
    const reader = new FileReader()
    reader.onloadend = () => setImg(reader.result)
    reader.readAsDataURL(file)
  }

  function startVisualizer(stream) {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyzer = audioCtx.createAnalyser()
      analyzer.fftSize = 64
      source.connect(analyzer)
      audioCtxRef.current = audioCtx
      analyzerRef.current = analyzer
      const dataArray = new Uint8Array(analyzer.frequencyBinCount)
      const updateVolume = () => {
        if (!analyzerRef.current) return
        analyzerRef.current.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i]
        setVolume(sum / dataArray.length)
        if (isRecordingRef.current) requestAnimationFrame(updateVolume)
      }
      updateVolume()
    } catch (e) {}
  }

  async function startRecording() {
    console.log('[MIC] Start Recording triggered')
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      isRecordingRef.current = true
      setStatus(S.RECORDING)
      startVisualizer(stream)

      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        console.log('[MIC] Recorder onstop fired')
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        if (!blob.size) {
          setStatus(S.IDLE)
          return
        }

        setStatus(S.PROCESSING)
        try {
          const res = await transcribeAudio(blob, selectedLang)
          if (res.status === 'SUCCESS' && res.transcript) {
            setTranscript(res.transcript)
            const chatRes = await chatWithAgent(res.transcript, res.english_transcript, selectedLang, image, location)
            setReply(chatRes.response)
            setImg(null); setImgPreview(null)
            const audioUrl = await speakText(chatRes.response, selectedLang)
            playAudio(audioUrl)
          } else {
            setError(res.error || 'Samajh nahi aaya.')
            setStatus(S.IDLE)
          }
        } catch (err) {
          setError('Network issue ya API error. Phir se koshish karein.')
          setStatus(S.IDLE)
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start()
    } catch (err) {
      setError('Mic access denied.')
      setStatus(S.IDLE)
    }
  }

  function stopRecording() {
    console.log('[MIC] Stop Recording triggered')
    isRecordingRef.current = false
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop())
      mediaStreamRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
  }

  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  const handleMicClick = () => {
    if (status === S.RECORDING) {
      stopRecording()
    } else if (status === S.IDLE) {
      startRecording()
    }
  }

  return (
    <div className="hero-container">
      <div className="location-status">
        <MapPin size={14} />
        <span>{location?.city || 'India'}</span>
      </div>

      <div className="welcome-msg">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report.</p>
      </div>

      {error && (
        <div className="alert-card-premium">
          <AlertCircle size={18} />
          <p>{error}</p>
        </div>
      )}

      {(transcript || reply) && (
        <div className="chat-area">
          {transcript && (
            <div className="chat-bubble user-bubble">
              <div className="chat-bubble-label">🎤 AAPNE KAHA</div>
              <p>{transcript}</p>
            </div>
          )}
          {reply && (
            <div className="chat-bubble ai-bubble">
              <div className="chat-bubble-label">🤖 AI JAWAB</div>
              <p>{reply}</p>
            </div>
          )}
          {status === S.PROCESSING && !reply && (
            <div className="chat-bubble ai-bubble">
              <div className="chat-bubble-label">AI Soch raha hai...</div>
              <Loader className="spin" size={18} />
            </div>
          )}
        </div>
      )}

      <div className="interaction-zone">
        {status === S.RECORDING && (
          <div className="visualizer-container">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="vis-bar" style={{ height: `${Math.max(4, volume * (0.4 + Math.random()))}px` }} />
            ))}
          </div>
        )}

        <button
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={handleMicClick}
          disabled={status === S.PROCESSING || status === S.SPEAKING}
        >
          {status === S.RECORDING  ? <Square size={28} /> :
           status === S.PROCESSING ? <Loader className="spin" size={28} /> :
           status === S.SPEAKING   ? <TrendingUp size={28} /> :
                                     <Mic size={32} />}
        </button>

        <p className="status-text">
          {status === S.RECORDING  ? 'BOLNA BAND KAREIN' :
           status === S.PROCESSING ? '⚙️ AI SOCH RAHA HAI...' :
           status === S.SPEAKING   ? '🔊 JAWAB SUN RAHE HAIN...' :
                                     'BOLNE KE LIYE DABAYEIN'}
        </p>

        <div className="voice-controls-row">
          <label className="image-upload-btn">
            <ImageIcon size={18} />
            <span>Fasal ki Photo</span>
            <input type="file" accept="image/*" onChange={handleImage} hidden />
          </label>
          <div className="lang-selector-group">
            <select value={selectedLang} onChange={(e) => setSelectedLang(e.target.value)} className="voice-lang-select">
              {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}
