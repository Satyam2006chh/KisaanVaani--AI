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
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')

  // EFFECT: LIVE MOVEMENT TRACKER
  useEffect(() => {
    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords
          try {
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
            const geoData = await geoRes.json()
            const readableAddress = geoData.address.city || geoData.address.town || geoData.address.village || 'Sateek Location'
            const cityState = `${readableAddress}, ${geoData.address.state || ''}`
            
            setLocation(prev => {
              if (prev?.lat === latitude && prev?.lon === longitude) return prev
              
              const apiUrl = import.meta.env.VITE_API_URL || ''
              
              // Backend Update
              if (user?.farmer_id) {
                fetch(`${apiUrl}/api/auth/profile/update`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ phone: user.farmer_id, district: readableAddress, state: geoData.address.state, city: cityState, lat: latitude, lon: longitude })
                }).catch(e => {})
              }

              // Weather Refresh
              fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`)
                .then(r => r.json()).then(w => {
                  const prob = w.daily.precipitation_probability_max[0] || 0
                  setWeatherAlert(prob > 50 ? `🚨 ALERT: Aaj baarish hone ke ${prob}% chances hain.` : null)
                }).catch(e => {})

              // Mandi Refresh
              fetch(`${apiUrl}/api/agent/mandis/nearby`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: latitude, lon: longitude })
              }).then(r => r.json()).then(data => setMandiList(data)).catch(e => {})

              return { lat: latitude, lon: longitude, city: cityState }
            })
          } catch (err) {}
        },
        () => setError('GPS required for live data.'),
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
      )
      return () => navigator.geolocation.clearWatch(watchId)
    }
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
         <span className="section-label">📍 Regional Mandi Hubs</span>
         <div className="mandi-carousel">
            {mandiList.length > 0 ? mandiList.map((m, idx) => (
              <div key={idx} className="mandi-card-premium">
                 <TrendingUp size={22} style={{color: 'var(--accent)', marginBottom: '8px'}} />
                 <h4>{m.name}</h4>
                 <p className="mandi-dist">{m.distance} km away</p>
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
