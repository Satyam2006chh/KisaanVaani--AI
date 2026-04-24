import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, MapPin, AlertCircle, TrendingUp, Image as ImageIcon, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'
import './Hero.css'

// All Sarvam-supported languages used in app
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

const API_URL = import.meta.env.VITE_API_URL || 'https://kisaanvaani-ai-1.onrender.com'

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

  // ─── STEP 1: Reverse geocode coords to city name ──────────────────────────
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

  // ─── STEP 2: Fetch weather alert using raw GPS coords ─────────────────────
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



  // ─── MAIN: All location-based data fetch ──────────────────────────────────
  async function onNewPosition(lat, lon, accuracy = null) {
    setLocLoading(true)
    setError('')
    const geo = await geocodeCoords(lat, lon)
    setLocation({ lat, lon, accuracy, city: geo.display, place: geo.place, state: geo.state, updatedAt: Date.now() })

    // Sync live location to backend profile (non-blocking)
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

    // Parallel: weather
    fetchWeather(lat, lon);
    setLocLoading(false)
  }

  // ─── GEOLOCATION EFFECT ───────────────────────────────────────────────────
  useEffect(() => {
    if (!navigator.geolocation) {
      setError('GPS not supported on this device.')
      setLocLoading(false)
      return
    }

    const GEO_OPTS = { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 }

    // Immediate fetch — show location ASAP
    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude, longitude, accuracy } }) => {
        lastPosRef.current = { lat: latitude, lon: longitude, accuracy, timestamp: Date.now() }
        onNewPosition(latitude, longitude, accuracy)
      },
      (err) => {
        setLocLoading(false)
        if (err.code === 1) setError('Location access denied. Please allow location in browser settings.')
        else setError('Could not get your location. Please check GPS.')
      },
      GEO_OPTS
    )

    // Live movement watch — refresh on movement, better GPS accuracy, or stale fix
    const wid = navigator.geolocation.watchPosition(
      ({ coords: { latitude, longitude, accuracy } }) => {
        const last = lastPosRef.current
        const movedMeters = !last ? Infinity : distanceMeters(last.lat, last.lon, latitude, longitude)
        const accuracyImproved = typeof accuracy === 'number'
          && (typeof last?.accuracy !== 'number' || accuracy + 15 < last.accuracy)
        const staleFix = !last?.timestamp || (Date.now() - last.timestamp) > 60000
        if (movedMeters > 50 || accuracyImproved || staleFix) {
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

  // ─── VOICE RECORDING ──────────────────────────────────────────────────────
  function stopMediaStream() {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
  }

  function clearProcessingWatchdog() {
    if (processingTimerRef.current) {
      clearTimeout(processingTimerRef.current)
      processingTimerRef.current = null
    }
  }

  async function startRecording() {
    console.log('[VOICE] Starting recording...')
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []
    clearProcessingWatchdog()
    try {
      console.log('[VOICE] Requesting microphone access...')
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true })
      console.log('[VOICE] Microphone stream acquired')
      mediaStreamRef.current = stream

      // Robust MimeType Selection (Crucial for mobile/Safari compatibility)
      const types = ['audio/webm', 'audio/ogg', 'audio/mp4', 'audio/wav']
      const supportedMime = types.find(t => MediaRecorder.isTypeSupported(t)) || ''
      console.log('[VOICE] Supported MimeType found:', supportedMime || 'default')
      
      const recorder = new MediaRecorder(stream, supportedMime ? { mimeType: supportedMime } : {})
      
      recorder.ondataavailable = (e) => { 
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
          console.log('[VOICE] Audio chunk received:', e.data.size, 'bytes')
        }
      }

      recorder.onstop = async () => {
        stopMediaStream()
        // Use the actual mimeType the recorder used
        const blobType = recorder.mimeType || supportedMime || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: blobType })
        console.log('[VOICE] Recording stopped. Blob size:', blob.size, 'bytes', 'Type:', blobType)
        
        if (!blob.size) {
          console.error('[VOICE] Blob is empty - audio capture failed')
          setStatus(S.IDLE)
          setError('Audio capture failed. Please try again.')
          return
        }

        setStatus(S.PROCESSING)
        console.log('[VOICE] Status set to PROCESSING. Starting transcription...')
        
        processingTimerRef.current = setTimeout(() => {
          console.error('[VOICE] Processing timeout - response took >90s')
          setStatus(S.IDLE)
          setError('Processing took too long. Please try again.')
        }, 90000)

        try {
          console.log('[VOICE] Calling transcribeAudio with language:', selectedLang)
          const res = await transcribeAudio(blob, selectedLang)
          console.log('[VOICE] Transcription response:', { status: res.status, hasTranscript: !!res.transcript, error: res.error })
          
          if (res.status === 'SUCCESS' && res.transcript) {
            console.log('[VOICE] Transcription SUCCESS:', res.transcript)
            setTranscript(res.transcript)
            // Agent always receives English meaning via english_message.
            const englishTranscript = res.english_transcript || res.transcript
            console.log('[VOICE] Calling agent with:', { userMessage: res.transcript, englishMessage: englishTranscript, lang: selectedLang })
            
            const chatRes = await chatWithAgent(res.transcript, englishTranscript, selectedLang, image, location)
            console.log('[VOICE] Agent response:', { hasResponse: !!chatRes.response })
            
            setReply(chatRes.response)
            clearImg() // Clear after processing
            
            try {
              console.log('[VOICE] Calling speak with language:', selectedLang)
              const audioUrl = await speakText(chatRes.response, selectedLang)
              console.log('[VOICE] Audio URL generated, starting playback')
              playAudio(audioUrl)
            } catch (ttsErr) {
              console.error('[VOICE] TTS failed, showing text response only:', ttsErr?.message || ttsErr)
              setStatus(S.IDLE)
              setError('Audio response is unavailable right now. Text answer is shown below.')
            }
          } else if (res.status === 'SILENCE_DETECTED') {
            console.warn('[VOICE] Silence detected')
            setStatus(S.IDLE)
            setError(res.silence_reply || 'Voice not understood. Please speak clearly.')
          } else {
            console.error('[VOICE] Error response:', res.error)
            setStatus(S.IDLE)
            setError(res.error || 'Voice not understood. Please speak clearly.')
          }
        } catch (err) {
          console.error('[VOICE] Exception during processing:', err.message || err)
          setStatus(S.IDLE)
          setError('Error processing voice. Try again.')
        } finally {
          clearProcessingWatchdog()
        }
      }
      
      recorder.onerror = (e) => {
        console.error('[VOICE] MediaRecorder error:', e.error)
        setError('Recording error. Please try again.')
        stopMediaStream()
      }
      
      mediaRecorderRef.current = recorder
      recorder.start(100)  // Request data every 100ms for safety
      setStatus(S.RECORDING)
      console.log('[VOICE] Recording started - awaiting stop signal')
    } catch (err) {
      console.error('[VOICE] Recording failed:', err.message || err)
      stopMediaStream()
      setError('Mic access blocked. Please allow microphone.')
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('[VOICE] Stop signal sent to MediaRecorder')
      mediaRecorderRef.current.stop()
    } else {
      console.warn('[VOICE] Stop called but recorder is not in recording state:', mediaRecorderRef.current?.state)
    }
  }

  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.onerror = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  useEffect(() => {
    return () => {
      clearProcessingWatchdog()
      stopMediaStream()
    }
  }, [])

  return (
    <div className="hero-container">

      {/* LIVE LOCATION PILL */}
      <div className="location-status animate-reveal">
        <MapPin size={15} />
        <span>
          {locLoading && !location ? 'Detecting live location...' : (location?.city || 'Location unavailable')}
          {typeof location?.accuracy === 'number' ? ` (±${Math.round(location.accuracy)}m)` : ''}
        </span>
        {locLoading && location && (
          <span style={{ fontSize: '9px', opacity: 0.6, marginLeft: '4px' }}>updating...</span>
        )}
      </div>

      {/* WELCOME */}
      <div className="welcome-msg animate-reveal">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report — Royale Edition.</p>
      </div>

      {/* GPS ERROR */}
      {error && (
        <div className="alert-card-premium animate-reveal">
          <AlertCircle size={18} />
          <p>{error}</p>
        </div>
      )}

      {/* WEATHER ALERT — only shows when rain > 50% */}
      {weatherAlert && !error && (
        <div className="alert-card-premium animate-reveal">
          <AlertCircle size={18} />
          <p>{weatherAlert}</p>
        </div>
      )}

      {/* IMAGE PREVIEW */}
      {imgPreview && (
        <div className="img-preview-container animate-reveal">
          <img src={imgPreview} alt="Crop" />
          <button className="clear-img-btn" onClick={clearImg}><X size={14} /></button>
          <div className="img-badge">Fasal ki photo taiyar hai 📸</div>
        </div>
      )}

      {/* RESPONSE AREA */}
      {(transcript || reply) && (
        <div className="glass-panel animate-reveal" style={{ padding: '1.2rem', width: '100%', borderLeft: '3px solid var(--primary)' }}>
          <p style={{ fontSize: '0.7rem', color: 'var(--primary)', marginBottom: '6px', fontWeight: '800', letterSpacing: '1px' }}>
            {reply ? '🤖 AI JAWAB:' : '🎤 AAPNE KAHA:'}
          </p>
          <p style={{ fontSize: '0.95rem', lineHeight: '1.6', color: 'var(--text-main)' }}>{reply || transcript}</p>
        </div>
      )}

      {/* MIC + CONTROLS */}
      <div className="interaction-zone animate-reveal">
        <button
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={status === S.RECORDING ? stopRecording : startRecording}
          disabled={status === S.PROCESSING || status === S.SPEAKING}
          title={status === S.IDLE ? 'Baat karna shuru karein' : ''}
        >
          {status === S.RECORDING  ? <Square size={28} /> :
           status === S.PROCESSING ? <Loader className="spin" size={28} /> :
           status === S.SPEAKING   ? <TrendingUp size={28} /> :
                                     <Mic size={32} />}
        </button>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', letterSpacing: '1.5px', fontWeight: '700' }}>
          {status === S.RECORDING  ? '⏹ BAND KARNE KE LIYE DABAYEIN' :
           status === S.PROCESSING ? '⚙️ AI SOCH RAHA HAI...' :
           status === S.SPEAKING   ? '🔊 JAWAB SUN RAHE HAIN...' :
                                     'BOLNE KE LIYE DABAYEIN'}
        </p>

        <div className="voice-controls-row">
          <label className="image-upload-btn">
            <ImageIcon size={18} />
            <span>Photo</span>
            <input type="file" accept="image/*" onChange={handleImage} hidden />
          </label>

          {/* Selected language controls translation + Sarvam TTS output language */}
          <label style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: '700' }}>
            Kis bhasha mein sawal-jawab karna chahoge?
          </label>
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
  )
}
