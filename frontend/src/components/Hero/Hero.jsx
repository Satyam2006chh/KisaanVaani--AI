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

const API_URL = import.meta.env.VITE_API_URL || ''

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus]           = useState(S.IDLE)
  const [transcript, setTranscript]   = useState('')
  const [reply, setReply]             = useState('')
  const [error, setError]             = useState('')
  const [location, setLocation]       = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [locLoading, setLocLoading]   = useState(true)
  const [image, setImg]               = useState(null)
  const [imgPreview, setImgPreview]   = useState(null)

  const mediaRecorderRef = useRef(null)
  const mediaStreamRef   = useRef(null)
  const processingTimerRef = useRef(null)
  const chunksRef        = useRef([])
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')
  
  // Visualizer & Hybrid Recognition
  const audioCtxRef = useRef(null)
  const analyzerRef = useRef(null)
  const [volume, setVolume] = useState(0)
  const recognitionRef = useRef(null)
  const browserTranscriptRef = useRef('')

  function withTimeout(promise, timeoutMs, timeoutMessage) {
    let timer = null
    const timeoutPromise = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)
    })
    return Promise.race([promise, timeoutPromise]).finally(() => {
      if (timer) clearTimeout(timer)
    })
  }

  // --- HYBRID RECOGNITION SETUP ---
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = selectedLang

      recognition.onresult = (event) => {
        let interimTranscript = ''
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            browserTranscriptRef.current += event.results[i][0].transcript
          } else {
            interimTranscript += event.results[i][0].transcript
          }
        }
        // Show interim results in the UI immediately
        setTranscript(browserTranscriptRef.current + interimTranscript)
      }

      recognition.onerror = (event) => {
        console.warn('[HYBRID] Browser Recognition Error:', event.error)
      }

      recognitionRef.current = recognition
    }
  }, [selectedLang])

  // Geolocation & Weather (Condensed for brevity)
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocLoading(false)
      return
    }
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude, longitude, accuracy } }) => {
        try {
          const r = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&accept-language=en`)
          const d = await r.json()
          const city = d.address.city || d.address.town || d.address.village || 'Your Location'
          setLocation({ lat: latitude, lon: longitude, city })
          
          const wr = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`)
          const wd = await wr.json()
          const prob = wd?.daily?.precipitation_probability_max?.[0] || 0
          if (prob > 50) setWeatherAlert(`🌧️ Aaj ${prob}% baarish ke chances hain.`)
        } catch (e) {}
        setLocLoading(false)
      },
      () => setLocLoading(false)
    )
  }, [])

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
      const bufferLength = analyzer.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      const updateVolume = () => {
        if (!analyzerRef.current) return
        analyzerRef.current.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i]
        setVolume(sum / bufferLength)
        if (mediaStreamRef.current) requestAnimationFrame(updateVolume)
      }
      updateVolume()
    } catch (e) {}
  }

  async function processVoice(finalText) {
    setStatus(S.PROCESSING)
    try {
      const chatRes = await withTimeout(
        chatWithAgent(finalText, null, selectedLang, image, location),
        55000,
        'AI sochne mein der laga raha hai.'
      )
      setReply(chatRes.response)
      setImg(null); setImgPreview(null)
      const audioUrl = await speakText(chatRes.response, selectedLang)
      playAudio(audioUrl)
    } catch (err) {
      setStatus(S.IDLE)
      setError(`Galti: ${err.message}. Kripya dobara bolein.`)
    }
  }

  async function startRecording() {
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []; browserTranscriptRef.current = ''
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      startVisualizer(stream)

      // Start Browser Recognition Parallel
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start()
        } catch (e) {
          console.warn('Recognition start error (likely already started):', e)
        }
      }

      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        if (recognitionRef.current) recognitionRef.current.stop()
        stopMediaStream()

        // HYBRID LOGIC: If Browser already got the text, use it! No need to wait for upload.
        if (browserTranscriptRef.current.trim().length > 2) {
          console.log('[HYBRID] Using Browser Recognition:', browserTranscriptRef.current)
          await processVoice(browserTranscriptRef.current)
          return
        }

        // Fallback to Sarvam Upload
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        if (!blob.size) { setStatus(S.IDLE); return }
        setStatus(S.PROCESSING)
        try {
          const res = await withTimeout(transcribeAudio(blob, selectedLang), 50000, 'Network slow hai.')
          if (res.status === 'SUCCESS' && res.transcript) {
            setTranscript(res.transcript)
            await processVoice(res.transcript)
          } else {
            setStatus(S.IDLE)
            setError(res.error || 'Samajh nahi aaya.')
          }
        } catch (e) {
          setStatus(S.IDLE)
          setError('Network issue. Kripya check karein.')
        }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) { setError('Mic permission nahi mili.') }
  }

  const handleMicToggle = async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    console.log('[VOICE] Mic Toggle Clicked. Current Status:', status);
    
    if (status === S.RECORDING) {
      stopRecording();
    } else if (status === S.IDLE) {
      startRecording();
    }
  };

  function stopRecording() {
    console.log('[VOICE] Force Stopping Recording...');
    
    // 1. Stop Speech Recognition first
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) { console.warn('Recognition stop error:', e); }
    }

    // 2. Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    } else {
      // If for some reason recorder is already inactive, manually clean up
      stopMediaStream();
      setStatus(S.IDLE);
    }
  }

  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  return (
    <div className="hero-container">
      <div className="location-status">
        <MapPin size={14} />
        <span>{location?.city || (locLoading ? 'Detecting...' : 'India')}</span>
      </div>

      <div className="welcome-msg">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report — Royale Edition.</p>
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
            <div className="chat-bubble ai-bubble typing-bubble">
              <div className="chat-bubble-label">AI Soch raha hai...</div>
              <Loader className="spin" size={18} />
            </div>
          )}
        </div>
      )}

      <div className="interaction-zone">
        {status === S.RECORDING && (
          <div className="visualizer-container">
            {[...Array(15)].map((_, i) => (
              <div 
                key={i} 
                className="vis-bar" 
                style={{ height: `${Math.max(4, volume * (0.4 + Math.random()))}px` }}
              />
            ))}
          </div>
        )}

        <button
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={handleMicToggle}
          disabled={status === S.PROCESSING || status === S.SPEAKING}
        >
          {status === S.RECORDING  ? <Square size={28} /> :
           status === S.PROCESSING ? <Loader className="spin" size={28} /> :
           status === S.SPEAKING   ? <TrendingUp size={28} /> :
                                     <Mic size={32} />}
        </button>

        <p className="status-text" style={{ pointerEvents: 'none' }}>
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
          {imgPreview && <div className="img-mini-preview"><img src={imgPreview} alt="crop" /></div>}
        </div>

        <div className="lang-selector-group">
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="voice-lang-select"
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
