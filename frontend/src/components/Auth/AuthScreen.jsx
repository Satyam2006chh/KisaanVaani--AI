import { useState, useEffect } from 'react'
import { Building2, Loader, Lock, MapPin, Phone, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import './AuthScreen.css'

const STEP = { PHONE: 1, OTP: 2, PROFILE: 3 }

const STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Delhi','Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand',
  'Karnataka','Kerala','Madhya Pradesh','Maharashtra','Manipur',
  'Meghalaya','Mizoram','Nagaland','Odisha','Punjab','Rajasthan',
  'Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh',
  'Uttarakhand','West Bengal',
]

export default function AuthScreen() {
  const { sendOTP, verifyOTP } = useAuth()

  const [step,     setStep]     = useState(STEP.PHONE)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const [phone,    setPhone]    = useState('')
  const [otp,      setOtp]      = useState('')
  const [name,     setName]     = useState('')
  const [city,     setCity]     = useState('')
  const [district, setDistrict] = useState('')
  const [state,    setState]    = useState('')
  // Hardcode language to Hindi since this is for Indian farmers
  const language = 'hi-IN'
  const [detectingLoc, setDetectingLoc] = useState(false)

  const autoDetectLocation = () => {
    if (!navigator.geolocation) {
      console.warn('[AuthScreen] Geolocation not supported')
      return
    }
    setDetectingLoc(true)
    setError('')
    
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        
        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`
          )
          if (!response.ok) throw new Error('Location reverse lookup failed')
          const data = await response.json()
          
          const addr = data.address || {}
          
          const rawState = addr.state || ''
          const matchedState = STATES.find(
            s => s.toLowerCase() === rawState.toLowerCase()
          ) || rawState
          
          const rawDistrict = addr.county || addr.district || addr.state_district || addr.city_district || ''
          const cleanDistrict = rawDistrict.replace(/\b(District|Zila)\b/gi, '').trim()
          
          const cityName = addr.city || addr.town || addr.village || addr.suburb || addr.hamlet || cleanDistrict || ''
          
          if (matchedState) setState(matchedState)
          if (cleanDistrict) setDistrict(cleanDistrict)
          if (cityName) setCity(cityName)
          
        } catch (err) {
          setError('लोकेशन डिटेक्ट नहीं हो पाई। कृपया मैन्युअल रूप से भरें।')
        } finally {
          setDetectingLoc(false)
        }
      },
      (geoErr) => {
        setDetectingLoc(false)
        if (geoErr.code === 1) { 
          setError('कृपया \'Allow\' पर क्लिक करें ताकि हम आपकी लोकेशन जान सकें।')
        } else if (geoErr.code === 2 || geoErr.message.includes('unavailable')) { 
          setError('कृपया अपने मोबाइल की लोकेशन (GPS) चालू करें और दोबारा कोशिश करें।')
        } else {
          setError('लोकेशन डिटेक्ट नहीं हो पाई। कृपया मैन्युअल रूप से भरें।')
        }
      },
      { timeout: 10000, enableHighAccuracy: true }
    )
  }

  useEffect(() => {
    if (step === STEP.PROFILE) {
      autoDetectLocation()
    }
  }, [step])

  const err = (msg) => { setError(msg); setLoading(false) }

  async function handleSendOTP(e) {
    e.preventDefault()
    if (phone.length < 10) return err('सही मोबाइल नंबर भरें।')
    
    setError('')
    setStep(STEP.OTP)
    
    sendOTP(phone).catch(err => {
      console.warn('[AuthScreen] OTP failed, demo works', err)
    })
  }

  async function handleVerifyOTP(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await verifyOTP(phone, otp, '', language, '', '', '')
    } catch (e) {
      if (e.response?.data?.detail === 'Name required for new users') {
        setStep(STEP.PROFILE)
      } else {
        err(e.response?.data?.detail || 'गलत OTP, दोबारा कोशिश करें।')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleProfile(e) {
    e.preventDefault()
    if (!name.trim())     return err('अपना नाम भरें।')
    if (!city.trim())     return err('शहर / गांव का नाम भरें।')
    if (!district.trim()) return err('ज़िला का नाम भरें।')
    if (!state)           return err('राज्य चुनें।')
    setError('')
    setLoading(true)
    try {
      await verifyOTP(phone, otp, name.trim(), language, district.trim(), state, city.trim())
    } catch (e) {
      err(e.response?.data?.detail || 'अकाउंट बनाने में समस्या आई। दोबारा कोशिश करें।')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-container">

        <div className="auth-header">
          <div className="auth-logo">
            <img src="/logo.png" alt="KisaanVaani Logo" style={{ width: '48px', marginRight: '14px', verticalAlign: 'middle', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.3)' }} />
            किसान<span className="highlight">वाणी</span>
          </div>
          <p className="auth-tagline">बोलो, समझो, बदलो अपनी ज़िंदगी</p>
        </div>

        <div className="auth-steps animate-entrance" style={{ animationDelay: '0.2s' }}>
          <div className={`auth-step ${step === 1 ? 'active' : step > 1 ? 'done' : ''}`}>1</div>
          <div className="auth-step-line" />
          <div className={`auth-step ${step === 2 ? 'active' : step > 2 ? 'done' : ''}`}>2</div>
          <div className="auth-step-line" />
          <div className={`auth-step ${step === 3 ? 'active' : ''}`}>3</div>
        </div>

        {error && <div className="auth-error">⚠️ {error}</div>}

        <div className="glass-panel auth-card">
          {step === STEP.PHONE && (
            <form onSubmit={handleSendOTP} className="auth-form animate-reveal">
              <h2>किसान भाई,<br /><span className="highlight">स्वागत है!</span></h2>
              <p className="auth-subtitle">शुरू करने के लिए अपना मोबाइल नंबर डालें</p>
              
              <div className="input-field">
                <label><Phone size={18} /> मोबाइल नंबर</label>
                <div className="input-group">
                  <span className="input-prefix">+91</span>
                  <input
                    type="tel"
                    placeholder="00000 00000"
                    value={phone}
                    onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    required autoFocus
                  />
                </div>
              </div>

              <button className="btn-premium w-full" disabled={loading || phone.length < 10}>
                {loading ? <Loader size={20} className="spin" /> : <>OTP भेजें →</>}
              </button>
              <div className="demo-hint">✨ डेमो OTP: 123456</div>
            </form>
          )}

          {step === STEP.OTP && (
            <form onSubmit={handleVerifyOTP} className="auth-form animate-reveal">
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                <div style={{ background: 'rgba(0, 240, 255, 0.15)', padding: '24px', borderRadius: '50%', color: 'var(--primary)', boxShadow: '0 0 40px rgba(0, 240, 255, 0.2)' }}>
                  <Lock size={48} strokeWidth={1.5} />
                </div>
              </div>
              <h2>सुरक्षा <span className="highlight">जांच</span></h2>
              <p className="auth-subtitle">+91 {phone} पर भेजा गया कोड डालें</p>
              
              <div className="input-field" style={{ marginTop: '10px', marginBottom: '30px' }}>
                <input
                  type="text"
                  placeholder="• • • • • •"
                  value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required autoFocus
                  autoComplete="one-time-code"
                  className="otp-input"
                  style={{ textAlign: 'center', letterSpacing: '24px', fontSize: '2.2rem', fontWeight: '800', background: 'rgba(0,0,0,0.4)', padding: '25px', borderRadius: '20px' }}
                />
              </div>

              <button className="btn-premium w-full" disabled={loading || otp.length < 6} style={{ padding: '18px', fontSize: '1.2rem' }}>
                {loading ? <Loader size={24} className="spin" /> : 'आगे बढ़ें →'}
              </button>
              
              <button type="button" className="btn-link" onClick={() => setStep(STEP.PHONE)}>
                ← मोबाइल नंबर बदलें
              </button>
            </form>
          )}

          {step === STEP.PROFILE && (
            <form onSubmit={handleProfile} className="auth-form animate-reveal">
              <h2>अपनी <span className="highlight">पहचान</span></h2>
              <p className="auth-subtitle">ताकि AI आपको और आपके खेत को समझ सके</p>

              <button
                type="button"
                className="btn-location-detect"
                onClick={autoDetectLocation}
                disabled={detectingLoc}
              >
                {detectingLoc ? (
                  <Loader size={16} className="spin animate-spin" />
                ) : (
                  <MapPin size={16} />
                )}
                <span>{detectingLoc ? 'लोकेशन डिटेक्ट हो रही है...' : '🎯 ऑटो-डिटेक्ट लोकेशन'}</span>
              </button>

              <div className="profile-grid">
                <div className="input-field">
                  <label><User size={18} /> पूरा नाम</label>
                  <input type="text" placeholder=""
                    value={name} onChange={e => setName(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><Building2 size={18} /> शहर / गांव</label>
                  <input type="text" placeholder=""
                    value={city} onChange={e => setCity(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> ज़िला</label>
                  <input type="text" placeholder=""
                    value={district} onChange={e => setDistrict(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> राज्य</label>
                  <select value={state} onChange={e => setState(e.target.value)} required>
                    <option value="">चुनें...</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <button className="btn-premium w-full" disabled={loading} style={{ marginTop: '20px' }}>
                {loading ? <Loader size={20} className="spin" /> : 'खेती शुरू करें 🌾'}
              </button>
            </form>
          )}
        </div>

      </div>
    </div>
  )
}
