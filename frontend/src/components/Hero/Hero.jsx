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

function distanceMeters(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371000
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

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
  const lastPosRef       = useRef(null)
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')
  
  // Visualizer refs
  const audioCtxRef = useRef(null)
  const analyzerRef = useRef(null)
  const [volume, setVolume] = useState(0)

  function withTimeout(promise, timeoutMs, timeoutMessage) {
    let timer = null
    const timeoutPromise = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)
    })
    return Promise.race([promise, timeoutPromise]).finally(() => {
      if (timer) clearTimeout(timer)
    })
  }

  async function geocodeCoords(lat, lon) {
    try {
      const r = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&accept-language=en`,
        { headers: { 'User-Agent': 'KisaanVaani/2.0' } }
      )
      const d = await r.json()
      const a = d.address || {}
      const place = a.city || a.town || a.village || a.county || a.suburb || 'Your Location'
      const state = a.state || ''
      return { place, state, display: state ? `${place}, ${state}` : place }
    } catch {
      return { place: 'Live Location', state: '', display: `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E` }
    }
  }

  async function fetchWeather(lat, lon) {
    try {
      const r = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`
      )
      const d = await r.json()
      const prob = d?.daily?.precipitation_probability_max?.[0] || 0
      setWeatherAlert(prob > 50 ? `🌧️ Aaj ${prob}% baarish ke chances hain. Fasal ko dhak ke rakhein.` : null)
    } catch { setWeatherAlert(null) }
  }

  async function onNewPosition(lat, lon, accuracy = null) {
    setLocLoading(true)
    setError('')
    const geo = await geocodeCoords(lat, lon)
    setLocation({ lat, lon, accuracy, city: geo.display, place: geo.place, state: geo.state, updatedAt: Date.now() })

    if (user?.farmer_id) {
      fetch(`${API_URL}/api/auth/profile/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: user.farmer_id,
          district: geo.place,
          state: geo.state,
          city: geo.display,
          lat, lon
        })
      }).catch(() => {})
    }
    fetchWeather(lat, lon);
    setLocLoading(false)
  }

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('GPS not supported on this device.')
      setLocLoading(false)
      return
    }
    const GEO_OPTS = { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 }
    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude, longitude, accuracy } }) => {
        lastPosRef.current = { lat: latitude, lon: longitude, accuracy, timestamp: Date.now() }
        onNewPosition(latitude, longitude, accuracy)
      },
      (err) => {
        setLocLoading(false)
        if (err.code === 1) setError('Location access denied. Please allow location.')
        else setError('Could not get your location.')
      },
      GEO_OPTS
    )
    const wid = navigator.geolocation.watchPosition(
      ({ coords: { latitude, longitude, accuracy } }) => {
        const last = lastPosRef.current
        const movedMeters = !last ? Infinity : distanceMeters(last.lat, last.lon, latitude, longitude)
        if (movedMeters > 50) {
          lastPosRef.current = { lat: latitude, lon: longitude, accuracy, timestamp: Date.now() }
          onNewPosition(latitude, longitude, accuracy)
        }
      },
      () => {},
      GEO_OPTS
    )
    return () => navigator.geolocation.clearWatch(wid)
  }, [user])

  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImgPreview(URL.createObjectURL(file))
    const reader = new FileReader()
    reader.onloadend = () => setImg(reader.result)
    reader.readAsDataURL(file)
  }

  const clearImg = () => { setImg(null); setImgPreview(null) }

  // ─── VOICE LOGIC ──────────────────────────────────────────────────────────
  function stopMediaStream() {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
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
        const average = sum / bufferLength
        setVolume(average)
        if (mediaStreamRef.current) requestAnimationFrame(updateVolume)
      }
      updateVolume()
    } catch (e) { console.error('Visualizer error:', e) }
  }

  async function startRecording() {
    console.log('[VOICE] Mic Clicked')
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      startVisualizer(stream)

      const types = ['audio/webm', 'audio/ogg', 'audio/mp4', 'audio/wav']
      const supportedMime = types.find(t => MediaRecorder.isTypeSupported(t)) || ''
      const recorder = new MediaRecorder(stream, supportedMime ? { mimeType: supportedMime } : {})
      
      recorder.ondataavailable = (e) => { 
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stopMediaStream()
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        if (!blob.size) {
          setError('Kshama karein, mic ne kuch sunai nahi diya.')
          setStatus(S.IDLE)
          return
        }

        setStatus(S.PROCESSING)
        
        processingTimerRef.current = setTimeout(() => {
          setStatus(S.IDLE)
          setError('Response mein der ho rahi hai. Kripya phir se koshish karein.')
        }, 120000)

        try {
          console.log('[VOICE] Transcribing...', { size: blob.size, lang: selectedLang })
          const res = await withTimeout(
            transcribeAudio(blob, selectedLang),
            55000,
            'Transcription timed out. Network check karein.'
          )
          
          if (res.status === 'SUCCESS' && res.transcript) {
            setTranscript(res.transcript)
            const chatRes = await withTimeout(
              chatWithAgent(res.transcript, res.english_transcript, selectedLang, image, location),
              55000,
              'AI sochne mein der laga raha hai.'
            )
            setReply(chatRes.response)
            clearImg()
            
            try {
              const audioUrl = await withTimeout(speakText(chatRes.response, selectedLang), 30000, 'Audio slow hai.')
              playAudio(audioUrl)
            } catch (ttsErr) {
              setStatus(S.IDLE)
              console.warn('TTS failed:', ttsErr)
            }
          } else {
            setStatus(S.IDLE)
            setError(res.silence_reply || res.error || 'Maaf kijiye, samajh nahi aaya.')
          }
        } catch (err) {
          setStatus(S.IDLE)
          const msg = err?.response?.data?.detail || err?.message || 'Network error'
          setError(`Galti: ${msg}. Kripya net check karein aur dobara bolein.`)
        } finally {
          if (processingTimerRef.current) clearTimeout(processingTimerRef.current)
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start(100)
      setStatus(S.RECORDING)
    } catch (err) {
      setError('Mic access nahi mila. Settings check karein.')
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop()
  }

  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.onerror = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  return (
    <div className="hero-container">
      <div className="location-status animate-reveal">
        <MapPin size={15} />
        <span>{location?.city || 'Detecting Location...'}</span>
      </div>

      <div className="welcome-msg animate-reveal">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report — Royale Edition.</p>
      </div>

      {(error || weatherAlert) && (
        <div className="alert-card-premium animate-reveal">
          <AlertCircle size={18} />
          <p>{error || weatherAlert}</p>
        </div>
      )}

      {imgPreview && (
        <div className="img-preview-container animate-reveal">
          <img src={imgPreview} alt="Crop" />
          <button className="clear-img-btn" onClick={clearImg}><X size={14} /></button>
          <div className="img-badge">Photo taiyar hai 📸</div>
        </div>
      )}

      {(transcript || reply) && (
        <div className="chat-area animate-reveal">
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
              <Loader className="spin" size={20} />
            </div>
          )}
        </div>
      )}

      <div className="interaction-zone animate-reveal">
        {status === S.RECORDING && (
          <div className="visualizer-container">
            {[...Array(12)].map((_, i) => (
              <div 
                key={i} 
                className="vis-bar" 
                style={{ height: `${Math.max(4, volume * (0.5 + Math.random()))}px` }}
              />
            ))}
          </div>
        )}

        <button
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={status === S.RECORDING ? stopRecording : startRecording}
          disabled={status === S.PROCESSING || status === S.SPEAKING}
        >
          {status === S.RECORDING  ? <Square size={28} /> :
           status === S.PROCESSING ? <Loader className="spin" size={28} /> :
           status === S.SPEAKING   ? <TrendingUp size={28} /> :
                                     <Mic size={32} />}
        </button>

        <p className="status-text">
          {status === S.RECORDING  ? 'BOLNA BAND KAREIN' :
           status === S.PROCESSING ? 'AI SOCH RAHA HAI...' :
           status === S.SPEAKING   ? 'JAWAB SUN RAHE HAIN...' :
                                     'BOLNE KE LIYE DABAYEIN'}
        </p>

        <div className="voice-controls-row">
          <div className="secondary-actions">
            <label className="image-upload-btn">
              <ImageIcon size={18} />
              <span>Fasal ki Photo</span>
              <input type="file" accept="image/*" onChange={handleImage} hidden />
            </label>
          </div>
          
          <div className="lang-selector-group">
            <label>Bhasha chunein:</label>
            <select
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="voice-lang-select"
            >
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code} style={{ background: '#0c0c14' }}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}
