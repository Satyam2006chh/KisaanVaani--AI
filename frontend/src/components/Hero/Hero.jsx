import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, MapPin, AlertCircle, TrendingUp, Image as ImageIcon, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'

// All 11 Sarvam-supported languages
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

// IMPORTANT: Backend URL must come from env var for deployed app
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
  async function onNewPosition(lat, lon) {
    setLocLoading(true)
    const geo = await geocodeCoords(lat, lon)
    setLocation({ lat, lon, city: geo.display, place: geo.place, state: geo.state })

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

    const GEO_OPTS = { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }

    // Immediate fetch — show location ASAP
    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude, longitude } }) => {
        lastPosRef.current = { lat: latitude, lon: longitude }
        onNewPosition(latitude, longitude)
      },
      (err) => {
        setLocLoading(false)
        if (err.code === 1) setError('Location access denied. Please allow location in browser settings.')
        else setError('Could not get your location. Please check GPS.')
      },
      GEO_OPTS
    )

    // Live movement watch — refresh if moved >500m (~0.005 deg)
    const wid = navigator.geolocation.watchPosition(
      ({ coords: { latitude, longitude } }) => {
        const last = lastPosRef.current
        const moved = !last
          || Math.abs(last.lat - latitude) > 0.005
          || Math.abs(last.lon - longitude) > 0.005
        if (moved) {
          lastPosRef.current = { lat: latitude, lon: longitude }
          onNewPosition(latitude, longitude)
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
  async function startRecording() {
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setStatus(S.PROCESSING)
        try {
          const res = await transcribeAudio(blob, selectedLang)
          if (res.status === 'SUCCESS') {
            setTranscript(res.transcript)
            // Pass full live location and image to agent
            const chatRes = await chatWithAgent(res.transcript, null, selectedLang, image, location)
            setReply(chatRes.response)
            clearImg() // Clear after processing
            const audioUrl = await speakText(chatRes.response, selectedLang)
            playAudio(audioUrl)
          } else {
            setStatus(S.IDLE)
            setError('Voice not understood. Please speak clearly.')
          }
        } catch (err) { setStatus(S.IDLE); setError('Error processing voice. Try again.') }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) { setError('Mic access blocked. Please allow microphone.') }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
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

  return (
    <div className="hero-container">

      {/* LIVE LOCATION PILL */}
      <div className="location-status animate-reveal">
        <MapPin size={15} />
        <span>
          {locLoading && !location ? 'Detecting live location...' : (location?.city || 'Location unavailable')}
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

        <div style={{ display: 'flex', gap: '10px', width: '100%', maxWidth: '280px' }}>
          <label className="image-upload-btn">
            <ImageIcon size={18} />
            <span>Photo</span>
            <input type="file" accept="image/*" onChange={handleImage} hidden />
          </label>

          {/* ALL 11 SARVAM LANGUAGES */}
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            style={{
              background: 'rgba(139,92,246,0.08)',
              border: '1px solid rgba(139,92,246,0.3)',
              color: '#fff',
              padding: '8px 14px',
              borderRadius: '12px',
              fontSize: '0.82rem',
              fontWeight: '600',
              cursor: 'pointer',
              outline: 'none',
              flex: 1
            }}
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
