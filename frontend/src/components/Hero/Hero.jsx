import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, MapPin, AlertCircle, TrendingUp, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'

const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus] = useState(S.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  
  // VERSION: 2.0.3 - GOD LEVEL (Live Tracker)
  const V = "2.0.3 - Real-Time Tracker"

  // SPATIAL STATES
  const [location, setLocation] = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [mandiList, setMandiList] = useState([]) 
  
  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')

  // EFFECT: CONTINUOUS LIVE TRACKING (watchPosition)
  useEffect(() => {
    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords
          try {
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
            const geoData = await geoRes.json()
            const readableAddress = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.suburb || 'Sateek Location'
            const cityState = `${readableAddress}, ${geoData.address.state || ''}`
            
            // IF MOVED, UPDATE EVERYTHING
            setLocation(prev => {
              if (prev?.lat === latitude && prev?.lon === longitude) return prev
              
              const apiUrl = import.meta.env.VITE_API_URL || ''
              
              // Sync to DB
              if (user?.farmer_id) {
                fetch(`${apiUrl}/api/auth/profile/update`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ phone: user.farmer_id, district: readableAddress, state: geoData.address.state, city: cityState, lat: latitude, lon: longitude })
                }).catch(e => {})
              }

              // Refresh Weather
              fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`)
                .then(r => r.json())
                .then(w => {
                  const prob = w.daily.precipitation_probability_max[0] || 0
                  setWeatherAlert(prob > 50 ? `🚨 REAL ALERT: Aaj baarish ki umeed ${prob}% hai.` : null)
                }).catch(e => {})

              // Refresh Mandis
              fetch(`${apiUrl}/api/agent/mandis/nearby`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: latitude, lon: longitude })
              })
                .then(r => r.json()).then(data => setMandiList(data)).catch(e => {})

              return { lat: latitude, lon: longitude, city: cityState }
            })
          } catch (err) {}
        },
        () => setError('GPS Permission Denied. Live tracking off.'),
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
      )
      return () => navigator.geolocation.clearWatch(watchId)
    }
  }, [user])

  // RECORDING LOGIC
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
        } catch (err) { setStatus(S.IDLE); setError('Retrying...') }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) { setError('Mic issue!') }
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
      <div style={{fontSize: '9px', color: 'var(--accent-cyan)', position: 'absolute', top: '5px', opacity: 0.6}}>{V}</div>

      <div className="location-status animate-reveal">
        <MapPin size={16} />
        <span>{location ? location.city : 'Tracking Farm...'}</span>
      </div>

      <div className="welcome-msg animate-reveal">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam aur Mandi ki sateek report — Jahan aap, wahan KisaanVaani.</p>
      </div>

      {weatherAlert && (
        <div className="alert-card-premium animate-reveal">
          <AlertCircle size={20} />
          <p>{weatherAlert}</p>
        </div>
      )}

      <div className="mandi-section animate-reveal" style={{animationDelay: '0.2s'}}>
         <span className="section-label">📍 Kareebi Mandiyan</span>
         <div className="mandi-carousel">
            {mandiList.length > 0 ? mandiList.map((m, idx) => (
              <div key={idx} className="mandi-card-premium">
                 <TrendingUp size={22} style={{color: 'var(--accent-neon)', marginBottom: '8px'}} />
                 <h4>{m.name}</h4>
                 <p className="mandi-dist">{m.distance} km door</p>
              </div>
            )) : <p style={{fontSize: '0.75rem', color: 'var(--text-muted)'}}>{location ? 'Searching nearby mandis...' : 'Waiting for GPS...'}</p>}
         </div>
      </div>

      {(transcript || reply) && (
        <div className="glass-panel animate-reveal" style={{padding: '1.2rem', width: '100%', maxWidth: '360px', borderLeft: '4px solid var(--accent-neon)'}}>
           <p style={{fontSize: '0.75rem', color: 'var(--accent-cyan)', marginBottom: '4px', fontWeight: '800'}}>{reply ? 'VIGYAANIK:' : 'AAPNA KAHA:'}</p>
           <p style={{fontSize: '0.95rem', lineHeight: '1.4'}}>{reply || transcript}</p>
        </div>
      )}

      <div className="interaction-zone animate-reveal">
        <button 
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={status === S.RECORDING ? stopRecording : startRecording}
          disabled={status === S.PROCESSING}
        >
          {status === S.RECORDING ? <Square size={32} /> : 
           status === S.PROCESSING ? <Loader className="spin" size={32} /> : <Mic size={38} />}
        </button>
        <p style={{fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px'}}>
          {status === S.RECORDING ? 'TRACKING VOICE...' : 
           status === S.PROCESSING ? 'SATEEK ANALYSIS...' : 
           status === S.SPEAKING ? 'PLAYING RESPONSE...' : 'TOUCH TO ACTIVATE'}
        </p>

        <select 
          value={selectedLang} 
          onChange={(e) => setSelectedLang(e.target.value)}
          style={{background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--accent-neon)', padding: '6px 12px', borderRadius: '8px', fontSize: '11px', fontWeight: '700'}}
        >
          <option value="hi-IN">HINDI</option>
          <option value="pa-IN">PUNJABI</option>
          <option value="en-IN">ENGLISH</option>
        </select>
      </div>

      {error && <div style={{color: 'var(--danger-neon)', fontSize: '11px', fontWeight: '700'}}>! {error}</div>}
    </div>
  )
}
