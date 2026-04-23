import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, MapPin, AlertCircle, TrendingUp } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'

const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus] = useState(S.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  const V = "V2.0.4 - Royale Elite"

  const [location, setLocation] = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [mandiList, setMandiList] = useState([]) 
  
  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const lastPosRef = useRef(null) // Track last position to avoid redundant calls
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')

  // CORE FUNCTION: Fetch all location-based data for given coordinates
  async function fetchLocationData(latitude, longitude) {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    try {
      // 1. Reverse geocode with Nominatim
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&accept-language=en`,
        { headers: { 'User-Agent': 'KisaanVaani/1.0' } }
      )
      const geoData = await geoRes.json()
      const addr = geoData.address || {}
      const readableAddress = addr.city || addr.town || addr.village || addr.county || addr.suburb || 'Live Location'
      const stateName = addr.state || ''
      const cityState = stateName ? `${readableAddress}, ${stateName}` : readableAddress

      setLocation({ lat: latitude, lon: longitude, city: cityState })

      // 2. Sync to backend DB
      if (user?.farmer_id) {
        fetch(`${apiUrl}/api/auth/profile/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone: user.farmer_id, district: readableAddress, state: stateName, city: cityState, lat: latitude, lon: longitude })
        }).catch(() => {})
      }

      // 3. Real weather alert
      try {
        const wRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`)
        const wData = await wRes.json()
        const prob = wData?.daily?.precipitation_probability_max?.[0] || 0
        setWeatherAlert(prob > 50 ? `🚨 Aaj baarish ke ${prob}% chances hain. Fasal sambhal ke rakhein.` : null)
      } catch (e) {}

      // 4. Nearest mandis from backend (uses expanded all-India database)
      try {
        const mRes = await fetch(`${apiUrl}/api/agent/mandis/nearby`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lat: latitude, lon: longitude })
        })
        const mData = await mRes.json()
        if (Array.isArray(mData)) setMandiList(mData)
      } catch (e) {}

    } catch (err) {
      // Geocoding failed — still store coords
      setLocation({ lat: latitude, lon: longitude, city: `${latitude.toFixed(3)}°N, ${longitude.toFixed(3)}°E` })
    }
  }

  // EFFECT: GET POSITION IMMEDIATELY + WATCH FOR MOVEMENT
  useEffect(() => {
    if (!navigator.geolocation) {
      setError('GPS not supported on this device.')
      return
    }

    const GEO_OPTS = { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }

    // Step 1: Get current position immediately for fast first load
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        lastPosRef.current = { lat: latitude, lon: longitude }
        fetchLocationData(latitude, longitude)
      },
      () => setError('GPS access denied. Please enable location.'),
      GEO_OPTS
    )

    // Step 2: Keep watching for movement (e.g. user travels to another city)
    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        const last = lastPosRef.current
        // Only refresh if moved more than ~500 meters to avoid hammering APIs
        const moved = !last || Math.abs(last.lat - latitude) > 0.005 || Math.abs(last.lon - longitude) > 0.005
        if (moved) {
          lastPosRef.current = { lat: latitude, lon: longitude }
          fetchLocationData(latitude, longitude)
        }
      },
      () => {}, // Silent fail for watch (already handled in getCurrentPosition)
      GEO_OPTS
    )

    return () => navigator.geolocation.clearWatch(watchId)
  }, [user])

  async function startRecording() {
    setError(''); setTranscript(''); setReply(''); chunksRef.current = []
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setStatus(S.PROCESSING)
        try {
          const res = await transcribeAudio(blob, 'unknown')
          if (res.status === 'SUCCESS') {
             setTranscript(res.transcript)
             const chatRes = await chatWithAgent(res.transcript, null, selectedLang, null, location)
             setReply(chatRes.response)
             const audioUrl = await speakText(chatRes.response, selectedLang)
             playAudio(audioUrl)
          }
        } catch (err) { setStatus(S.IDLE); setError('Error processing voice.') }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) { setError('Mic access blocked.') }
  }

  function stopRecording() { if (mediaRecorderRef.current) mediaRecorderRef.current.stop() }
  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  return (
    <div className="hero-container">
      {/* Subtle Version Info */}
      <div style={{fontSize: '8px', color: 'rgba(255,255,255,0.2)', position: 'absolute', top: '10px'}}>{V}</div>

      {/* LOCATION */}
      <div className="location-status animate-reveal">
        <MapPin size={16} />
        <span>{location ? location.city : 'Detecting Farm...'}</span>
      </div>

      {/* WELCOME */}
      <div className="welcome-msg animate-reveal">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report — Royale Edition.</p>
      </div>

      {/* WEATHER ALERT */}
      {weatherAlert && (
        <div className="alert-card-premium animate-reveal">
          <AlertCircle size={20} />
          <p>{weatherAlert}</p>
        </div>
      )}

      {/* MANDI CAROUSEL */}
      <div className="mandi-section animate-reveal" style={{animationDelay: '0.1s'}}>
         <span className="section-label">📍 Kareebi Mandiyan</span>
         <div className="mandi-carousel">
            {mandiList.length > 0 ? mandiList.map((m, idx) => (
              <div key={idx} className="mandi-card-premium">
                 <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px'}}>
                   <TrendingUp size={18} style={{color: 'var(--accent)'}} />
                   <span style={{fontSize:'9px', fontWeight:'800', padding:'2px 7px', borderRadius:'20px',
                     background: m.source === 'live' ? 'rgba(34,197,94,0.12)' : 'rgba(255,255,255,0.04)',
                     color: m.source === 'live' ? '#4ade80' : 'var(--text-dim)',
                     border: m.source === 'live' ? '1px solid rgba(34,197,94,0.25)' : 'var(--border-glass)'
                   }}>{m.source === 'live' ? '🟢 LIVE' : 'OFFLINE'}</span>
                 </div>
                 <h4>{m.name}</h4>
                 {m.distance != null && <p className="mandi-dist">{m.distance} km away</p>}
                 {m.price && <p style={{fontSize:'0.78rem', color:'var(--accent)', fontWeight:'700', marginTop:'6px'}}>{m.price}</p>}
              </div>
            )) : <p style={{fontSize: '0.75rem', color: 'var(--text-dim)'}}>Fetching nearby marketplaces...</p>}
         </div>
      </div>

      {/* RESPONSE AREA */}
      {(transcript || reply) && (
        <div className="glass-panel animate-reveal" style={{padding: '1.2rem', width: '100%', borderLeft: '4px solid var(--accent)'}}>
           <p style={{fontSize: '0.75rem', color: 'var(--accent-light)', marginBottom: '4px', fontWeight: '800'}}>{reply ? 'SCIENTIST:' : 'YOU:'}</p>
           <p style={{fontSize: '0.95rem', lineHeight: '1.5'}}>{reply || transcript}</p>
        </div>
      )}

      {/* MIC CONTROL */}
      <div className="interaction-zone animate-reveal">
        <button 
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={status === S.RECORDING ? stopRecording : startRecording}
          disabled={status === S.PROCESSING}
        >
          {status === S.RECORDING ? <Square size={30} /> : 
           status === S.PROCESSING ? <Loader className="spin" size={30} /> : <Mic size={34} />}
        </button>
        <p style={{fontSize: '0.8rem', color: 'var(--text-dim)', letterSpacing: '1px', fontWeight: '600'}}>
          {status === S.RECORDING ? 'RECORDING LIVE...' : 
           status === S.PROCESSING ? 'AI REASONING...' : 
           status === S.SPEAKING ? 'PLAYING VOICE...' : 'TOUCH TO START'}
        </p>

        <select 
          value={selectedLang} 
          onChange={(e) => setSelectedLang(e.target.value)}
          style={{background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', color: '#fff', padding: '6px 12px', borderRadius: '10px', fontSize: '11px'}}
        >
          <option value="hi-IN">HINDI</option>
          <option value="pa-IN">PUNJABI</option>
          <option value="en-IN">ENGLISH</option>
        </select>
      </div>

    </div>
  )
}
