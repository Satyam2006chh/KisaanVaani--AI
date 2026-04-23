import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader, CloudRain, TrendingUp, Sprout, Camera, Image, X, MapPin, AlertCircle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'
import './Hero.css'

const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus] = useState(S.IDLE)
  const [transcript, setTranscript] = useState('')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  const [image, setImage] = useState(null) // Base64
  const [showVisionMenu, setShowVisionMenu] = useState(false)
  
  // GOD LEVEL STATES
  const [location, setLocation] = useState(null)
  const [weatherAlert, setWeatherAlert] = useState(null)
  const [mandiList, setMandiList] = useState([
    { id: 1, name: 'Rewari Anaj Mandi', distance: '3.2 km', price: 'Sarson: ₹5450' },
    { id: 2, name: 'Bawal Mandi', distance: '12.5 km', price: 'Kapas: ₹7200' },
    { id: 3, name: 'Dharuhera Mandi', distance: '8.1 km', price: 'Gehu: ₹2275' }
  ])
  const fileInputRef = useRef(null)
  
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const audioRef = useRef(null)
  const recognitionRef = useRef(null)

  const [selectedLang, setSelectedLang] = useState(user?.language || 'hi-IN')
  const { languages } = useAuth()

  // GOD LEVEL: AUTO-LOCATION ENGINE
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords
          
          // Reverse Geocoding to get City/Village Name
          try {
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
            const geoData = await geoRes.json()
            const readableAddress = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.suburb || 'Sateek Location'
            
            setLocation({ 
              lat: latitude, 
              lon: longitude, 
              city: `${readableAddress}, ${geoData.address.state || ''}` 
            })
          } catch (err) {
            setLocation({ lat: latitude, lon: longitude, city: user?.city || 'Sateek Location' })
          }
          
          // Trigger a sample alert for demo (75% Rain Probability)
          setTimeout(() => {
            setWeatherAlert("🚨 ALERT: Agle 1 ghante mein baarish hone ki sambhavna hai (77%). Fasal dhak lein!")
          }, 3000)
        },
        () => setError('Location access denied. Please allow GPS for local updates.')
      )
    }
  }, [user])

  function stopAll() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
  }

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setImage(reader.result)
        setShowVisionMenu(false)
      }
      reader.readAsDataURL(file)
    }
  }

  const triggerCamera = () => {
    if (fileInputRef.current) {
      fileInputRef.current.setAttribute('capture', 'environment')
      fileInputRef.current.click()
    }
  }

  const triggerGallery = () => {
    if (fileInputRef.current) {
      fileInputRef.current.removeAttribute('capture')
      fileInputRef.current.click()
    }
  }

  async function startRecording() {
    stopAll()
    setError(''); setTranscript(''); setReply(''); 
    chunksRef.current = []

    try {
      // 1. Start Browser Recognition for LIVE feedback (Visual only)
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.lang = selectedLang
        recognition.interimResults = true
        recognition.continuous = true
        recognition.onresult = (e) => {
          const text = Array.from(e.results).map(r => r[0].transcript).join('')
          setTranscript(text) // Live UI update
        }
        recognitionRef.current = recognition
        recognition.start()
      }

      // 2. Start MediaRecorder for BACKEND accuracy
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setStatus(S.PROCESSING)
        
        try {
          const res = await transcribeAudio(blob, 'unknown')
          if (res.status === 'SUCCESS') {
             setTranscript(res.transcript)
             await handleChat(res.transcript, res.detected_language)
          } else if (res.status === 'SILENCE_DETECTED') {
             setReply(res.silence_reply)
             setStatus(S.SPEAKING)
          } else {
             throw new Error(res.error || 'Transcription failed')
          }
        } catch (err) {
          setError('Maaf kijiye, main sun nahi paaya. Dubara koshish karein.')
          setStatus(S.IDLE)
        }
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setStatus(S.RECORDING)
    } catch (err) {
      setError('Mic access denied! Please check browser permissions.')
      setStatus(S.IDLE)
    }
  }

  function stopRecording() {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
  }

  async function handleChat(text, detectedLang = null) {
    try {
      // Pass location (lat/lon) to AI for automatic hyper-local context
      const res = await chatWithAgent(text, null, selectedLang, image, location)
      setReply(res.response)
      
      // Start TTS immediately after receiving text
      setStatus(S.PROCESSING)
      try {
        const audioUrl = await speakText(res.response, selectedLang)
        await playAudio(audioUrl)
      } catch (audioErr) {
        console.error('TTS Failed:', audioErr)
        setStatus(S.IDLE)
      }
    } catch (err) {
      setError('System busy. Phir se try karein.')
      setStatus(S.IDLE)
    }
  }

  async function playAudio(url) {
    if (!url) { setStatus(S.IDLE); return }
    const audio = new Audio(url)
    audioRef.current = audio
    setStatus(S.SPEAKING)
    audio.onended = () => { setStatus(S.IDLE); audioRef.current = null }
    audio.onerror = () => { setStatus(S.IDLE); audioRef.current = null }
    try { await audio.play() } catch { setStatus(S.IDLE) }
  }

  return (
    <div className="hero-section">
      <div className="container centered-content">
        
        {/* TOP STATUS BAR: LOCATION */}
        <div className="top-status-bar animate-reveal">
           {location ? (
             <div className="location-badge glass-panel">
               <MapPin size={14} style={{color: 'var(--accent)'}} />
               <span>{location.city} • {location.lat.toFixed(2)}, {location.lon.toFixed(2)}</span>
             </div>
           ) : (
             <div className="location-badge glass-panel loading">Detecting Farm Location...</div>
           )}
        </div>

        {/* Header */}
        <div className="hero-header animate-reveal">
          <div className="badge">🌾 Bharat Ka AI Agricultural Expert</div>
          <h1>Namaste <span className="highlight">{user?.name || 'Kisaan'}</span> ji</h1>
          <p className="hero-subtitle">Mausam, Mandi ya Kheti ki har "Tagdi" jankari ab aapki apni bhasha mein.</p>
        </div>

        {/* PREDICTIVE WEATHER ALERT BAR */}
        {weatherAlert && (
          <div className="alert-card-premium animate-reveal">
            <AlertCircle size={24} style={{color: '#ef4444'}} />
            <p>{weatherAlert}</p>
          </div>
        )}

        {/* Central Engine */}
        <div className="voice-engine-container animate-reveal" style={{ animationDelay: '0.2s' }}>
          <div className={`mic-aura ${status === S.RECORDING ? 'pulsing' : ''}`} />
          
          {/* Image Preview */}
          {image && (
            <div className="vision-preview">
              <img src={image} alt="Crop Preview" />
              <button className="remove-photo" onClick={() => setImage(null)}><X size={14} /></button>
              {status === S.PROCESSING && !reply && <div className="analyzing-indicator">Analyzing...</div>}
            </div>
          )}

          <div className="controls-v2">
            {/* Vision Trigger */}
            <div className="secondary-trigger-wrapper">
              <button 
                className={`secondary-trigger ${image ? 'active' : ''}`}
                onClick={() => setShowVisionMenu(!showVisionMenu)}
                disabled={status === S.RECORDING}
              >
                <Camera size={24} />
              </button>

              {showVisionMenu && (
                <div className="vision-menu">
                  <div className="vision-option" onClick={triggerCamera}>
                    <Camera size={18} /> Take Photo
                  </div>
                  <div className="vision-option" onClick={triggerGallery}>
                    <Image size={18} /> From Gallery
                  </div>
                </div>
              )}
            </div>

            {/* Main Mic Trigger */}
            <button 
              className={`mic-trigger-v2 ${status === S.RECORDING ? 'active' : ''} ${status === S.PROCESSING ? 'loading' : ''}`}
              onClick={status === S.RECORDING ? stopRecording : startRecording}
              disabled={status === S.PROCESSING}
            >
              {status === S.RECORDING ? <Square size={32} fill="white" /> : 
               status === S.PROCESSING ? <Loader size={36} className="spin" /> : <Mic size={36} />}
              <div className="mic-status-v2">
                {status === S.RECORDING ? 'Suno rha hoon...' : 
                 status === S.PROCESSING ? (reply ? 'Awaaz taiyar...' : 'Samajh rha hoon...') : 
                 status === S.SPEAKING ? 'Bol rha hoon...' : 'Touch to Speak'}
              </div>
            </button>

            {/* Hidden File Input */}
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              accept="image/*" 
              onChange={handleImageSelect} 
            />
          </div>

          {/* Language Selector Dropdown */}
          <div className="lang-selector-container animate-reveal" style={{ animationDelay: '0.3s' }}>
            <span className="lang-label">Response Language:</span>
            <select 
              value={selectedLang} 
              onChange={(e) => setSelectedLang(e.target.value)}
              className="premium-lang-select"
            >
              {languages.map(l => (
                <option key={l.code} value={l.code}>{l.flag} {l.name}</option>
              ))}
            </select>
          </div>

          <div className={`transcript-bubble ${ (transcript || reply) ? 'visible' : ''}`}>
             <span className="bubble-label">{reply ? 'AI Scientist' : 'Kisaan'}</span>
             <p>{reply || transcript || 'Aapki awaaz yaha dikhegi...'}</p>
          </div>
        </div>

        {/* MANDI DISCOVERY CAROUSEL */}
        <div className="mandi-section animate-reveal" style={{ animationDelay: '0.4s' }}>
           <h3 className="section-label">📍 Kareebi Mandiyan</h3>
           <div className="mandi-carousel">
              {mandiList.map(m => (
                <div key={m.id} className="mandi-card-premium">
                   <TrendingUp size={24} style={{color: 'var(--accent)', marginBottom: '12px'}} />
                   <h4 style={{fontSize: '1.2rem', marginBottom: '4px'}}>{m.name}</h4>
                   <p className="mandi-dist" style={{fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '10px'}}>{m.distance} door</p>
                   <div className="mandi-rate" style={{fontWeight: '800', color: 'var(--accent)', fontSize: '1rem'}}>{m.price}</div>
                </div>
              ))}
           </div>
        </div>

        {error && <div className="error-toast glass-panel">⚠️ {error}</div>}

        {/* Features Grid */}
        <div className="feature-grid animate-reveal" style={{ animationDelay: '0.6s' }}>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><CloudRain size={24} /></div>
            <h3>Sateek Mausam</h3>
            <p>Lat/Long ke hisab se agle 48 ghante ki farm-level advice.</p>
          </div>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><TrendingUp size={24} /></div>
            <h3>Mandi Rate</h3>
            <p>Aapke khet se sabse pas wali 3 mandiyon ka live muqabla.</p>
          </div>
          <div className="glass-panel feature-card">
            <div className="icon-wrapper"><Sprout size={24} /></div>
            <h3>Pest Alert</h3>
            <p>Radius-based alerts jo padosi kheton mein bimari detect karte hain.</p>
          </div>
        </div>

        {/* Steps */}
        <div className="steps-row animate-reveal" style={{ animationDelay: '0.6s' }}>
          <div className={`step-item ${status === S.IDLE ? 'active' : ''}`}>
            <span className="step-num">01</span>
            <p>Mic dabao</p>
          </div>
          <div className="step-line" />
          <div className={`step-item ${status === S.PROCESSING ? 'active' : ''}`}>
             <span className="step-num">02</span>
             <p>AI samjhega</p>
          </div>
          <div className="step-line" />
          <div className={`step-item ${status === S.SPEAKING ? 'active' : ''}`}>
             <span className="step-num">03</span>
             <p>Jawab suno</p>
          </div>
        </div>

      </div>
    </div>
  )
}
