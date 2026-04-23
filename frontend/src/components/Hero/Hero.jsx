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
  
  // VERSION: 2.0.2 - GOD LEVEL (Punjab Precision)
  const V = "2.0.2 - God Level"

  // SPATIAL STATES
  const [location, setLocation] = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [mandiList, setMandiList] = useState([]) 
  
  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const recognitionRef = useRef(null)
  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')

  // EFFECT: LIVE GEOLOCATION (HIGH ACCURACY)
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords
          try {
            // 1. REVERSE GEOCODE (OSM)
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
            const geoData = await geoRes.json()
            const readableAddress = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.suburb || 'Sateek Location'
            const cityState = `${readableAddress}, ${geoData.address.state || ''}`
            
            setLocation({ lat: latitude, lon: longitude, city: cityState })

            // 2. BACKEND PROFILE SYNC
            const apiUrl = import.meta.env.VITE_API_URL || ''
            if (user?.farmer_id) {
               fetch(`${apiUrl}/api/auth/profile/update`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ 
                    phone: user.farmer_id, 
                    district: readableAddress,
                    state: geoData.address.state,
                    city: cityState
                  })
               }).catch(e => console.log("DB Sync failed"))
            }

            // 3. REAL WEATHER ALERT (OPEN-METEO)
            try {
              const wRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max&timezone=Asia%2FKolkata&forecast_days=1`)
              const wData = await wRes.json()
              const rainProb = wData.daily.precipitation_probability_max[0] || 0
              if (rainProb > 50) {
                setWeatherAlert(`🚨 REAL ALERT: Baarish ki sambhavna ${rainProb}% hai. Fasal dhak lein!`)
              }
            } catch (e) {}

            // 4. DYNAMIC MANDI DISCOVERY (PROXIMITY)
            try {
              const mRes = await fetch(`${apiUrl}/api/agent/mandis/nearby`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: latitude, lon: longitude })
              })
              const mData = await mRes.json()
              setMandiList(mData) // This will now show Patiala/Rajpura/Banur for Punjab
            } catch (e) {}

          } catch (err) {
            setLocation({ lat: latitude, lon: longitude, city: 'Farm Location Active' })
          }
        },
        () => setError('GPS Permission Denied. Please enable for Punjab data.'),
        { enableHighAccuracy: true, timeout: 20000 }
      )
    }
  }, [user])

  // RECORDING LOGIC
  async function startRecording() {
    setError(''); setTranscript(''); setReply(''); 
    chunksRef.current = []
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
             setStatus(S.PROCESSING)
             const audioUrl = await speakText(chatRes.response, selectedLang)
             playAudio(audioUrl)
          }
        } catch (err) { setStatus(S.IDLE); setError('Kuch galti hui. Phir se koshish karein.') }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) { setError('Mic access denied!') }
  }

  function stopRecording() { if (mediaRecorderRef.current) mediaRecorderRef.current.stop() }
  
  function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    audioRef.current = audio
    setStatus(S.SPEAKING)
    audio.onended = () => setStatus(S.IDLE)
    audio.play().catch(() => setStatus(S.IDLE))
  }

  return (
    <div className="hero-container">
      
      {/* VERSION BADGE FOR VERIFICATION */}
      <div style={{fontSize: '10px', color: 'var(--text-dim)', position: 'absolute', top: '10px'}}>{V}</div>

      {/* LOCATION BADGE */}
      <div className="location-status animate-reveal">
        <MapPin size={16} />
        <span>{location ? location.city : 'Detecting Farm Location...'}</span>
      </div>

      {/* WELCOME BLOCK */}
      <div className="welcome-msg animate-reveal" style={{animationDelay: '0.1s'}}>
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji</h1>
        <p className="hero-subtitle">Mausam, Mandi ya Kheti ki har sateek jankari ab aapki bhasha mein.</p>
      </div>

      {/* REAL-TIME ALERT */}
      {weatherAlert && (
        <div className="alert-card-premium animate-reveal" style={{animationDelay: '0.2s'}}>
          <AlertCircle size={20} />
          <p>{weatherAlert}</p>
        </div>
      )}

      {/* MANDI SECTION */}
      <div className="mandi-section animate-reveal" style={{animationDelay: '0.3s'}}>
         <span className="section-label">📍 Kareebi Mandiyan</span>
         <div className="mandi-carousel">
            {mandiList.length > 0 ? mandiList.map((m, idx) => (
              <div key={idx} className="mandi-card-premium">
                 <TrendingUp size={24} style={{color: 'var(--accent)', marginBottom: '10px'}} />
                 <h4>{m.name}</h4>
                 <p className="mandi-dist">{m.distance} km door</p>
              </div>
            )) : (
              <p style={{fontSize: '0.8rem', color: 'var(--text-dim)'}}>Mandiyan fetch ho rahi hain...</p>
            )}
         </div>
      </div>

      {/* TRANSCRIPT BUBBLE */}
      {(transcript || reply) && (
        <div className="glass-panel" style={{padding: '1.5rem', width: '100%', maxWidth: '380px', animation: 'fadeIn 0.5s'}}>
           <p style={{fontSize: '0.85rem', color: 'var(--accent-gold)', marginBottom: '5px'}}>{reply ? 'Senior Scientist:' : 'Aapne kaha:'}</p>
           <p style={{lineHeight: '1.5'}}>{reply || transcript}</p>
        </div>
      )}

      {/* INTERACTION ZONE */}
      <div className="interaction-zone animate-reveal">
        <button 
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing' : ''}`}
          onClick={status === S.RECORDING ? stopRecording : startRecording}
          disabled={status === S.PROCESSING}
        >
          {status === S.RECORDING ? <Square size={32} /> : 
           status === S.PROCESSING ? <Loader className="spin" size={32} /> : <Mic size={36} />}
        </button>
        <p style={{fontSize: '0.9rem', color: 'var(--text-dim)', fontWeight: '600'}}>
          {status === S.RECORDING ? 'Suno rha hoon...' : 
           status === S.PROCESSING ? 'AI soch rha hai...' : 
           status === S.SPEAKING ? 'Jawab suniye...' : 'Asali Location ke liye touch karein'}
        </p>

        {/* LANG SELECTOR */}
        <select 
          value={selectedLang} 
          onChange={(e) => setSelectedLang(e.target.value)}
          style={{background: 'none', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '10px', fontSize: '12px'}}
        >
          <option value="hi-IN">🇮🇳 Hindi</option>
          <option value="pa-IN">🇮🇳 Punjabi</option>
          <option value="en-IN">🇮🇳 English</option>
        </select>
      </div>

      {error && <div style={{background: 'rgba(239,68,68,0.2)', padding: '10px 20px', borderRadius: '10px', fontSize: '12px', border: '1px solid var(--alert-red)'}}>⚠️ {error}</div>}

    </div>
  )
}
