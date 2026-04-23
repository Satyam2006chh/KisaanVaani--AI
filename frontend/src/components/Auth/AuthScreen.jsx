import { useState } from 'react'
import { Building2, Languages, Loader, Lock, MapPin, Phone, User } from 'lucide-react'
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
  const { sendOTP, verifyOTP, languages: availableLanguages } = useAuth()
  console.log('[AuthScreen] Rendered with languages:', availableLanguages)

  const [step,     setStep]     = useState(STEP.PHONE)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const [phone,    setPhone]    = useState('')
  const [otp,      setOtp]      = useState('')
  const [name,     setName]     = useState('')
  const [city,     setCity]     = useState('')
  const [district, setDistrict] = useState('')
  const [state,    setState]    = useState('')
  const [language, setLanguage] = useState('hi-IN')

  const err = (msg) => { setError(msg); setLoading(false) }

  async function handleSendOTP(e) {
    e.preventDefault()
    if (phone.length < 10) return err('Sahi mobile number bharein.')
    
    setError('')
    // OPTIMISTIC UI: Move to OTP step instantly for zero delay
    setStep(STEP.OTP)
    
    // Call backend in background to wake it up/register the intent
    sendOTP(phone).catch(err => {
      console.warn('[AuthScreen] Background OTP wake-up failed, but demo OTP 123456 will still work.', err)
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
        err(e.response?.data?.detail || 'Galat OTP. Dobara try karein.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleProfile(e) {
    e.preventDefault()
    if (!name.trim())     return err('Apna naam bharein.')
    if (!city.trim())     return err('Shehar / gaon ka naam bharein.')
    if (!district.trim()) return err('Zila ka naam bharein.')
    if (!state)           return err('Rajya chunein.')
    setError('')
    setLoading(true)
    try {
      await verifyOTP(phone, otp, name.trim(), language, district.trim(), state, city.trim())
    } catch (e) {
      err(e.response?.data?.detail || 'Account banane mein error. Dobara try karein.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-container">

        <div className="auth-header">
          <h1 className="auth-logo">🎙️ Kisaan<span className="highlight">Vaani</span></h1>
          <p className="auth-tagline">Bolo, Samjho, Badlo Apni Zindagi</p>
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
              <h2>Kisan Bhai,<br /><span className="highlight">Welcome!</span></h2>
              <p className="auth-subtitle">Apna mobile number daalen shuru karne ke liye</p>
              
              <div className="input-field">
                <label><Phone size={18} /> Mobile Number</label>
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
                {loading ? <Loader size={20} className="spin" /> : <>Bhejo OTP <span className="arrow">→</span></>}
              </button>
              <div className="demo-hint">✨ Demo OTP: 123456</div>
            </form>
          )}

          {step === STEP.OTP && (
            <form onSubmit={handleVerifyOTP} className="auth-form animate-reveal">
              <h2>Suraksha <span className="highlight">Jaanch</span></h2>
              <p className="auth-subtitle">+91 {phone} par bheja gaya code daalen</p>
              
              <div className="input-field">
                <label><Lock size={18} /> 6-Digit Verification Code</label>
                <input
                  type="text"
                  placeholder="• • • • • •"
                  value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required autoFocus
                  className="otp-input"
                  style={{ textAlign: 'center', letterSpacing: '12px', fontSize: '1.8rem', fontWeight: '800' }}
                />
              </div>

              <button className="btn-premium w-full" disabled={loading || otp.length < 6}>
                {loading ? <Loader size={20} className="spin" /> : 'Aage Badhein →'}
              </button>
              
              <button type="button" className="btn-link" onClick={() => setStep(STEP.PHONE)}>
                ← Mobile number badlein
              </button>
            </form>
          )}

          {step === STEP.PROFILE && (
            <form onSubmit={handleProfile} className="auth-form animate-reveal">
              <h2>Apni <span className="highlight">Pehchaan</span></h2>
              <p className="auth-subtitle">Taki AI aapko aur aapke khet ko samajh sake</p>

              <div className="profile-grid">
                <div className="input-field">
                  <label><User size={18} /> Poora Naam</label>
                  <input type="text" placeholder="Ramesh Kumar"
                    value={name} onChange={e => setName(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><Building2 size={18} /> Shehar / Gaon</label>
                  <input type="text" placeholder="Gaon ka naam"
                    value={city} onChange={e => setCity(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> Zila (District)</label>
                  <input type="text" placeholder="Zila"
                    value={district} onChange={e => setDistrict(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> Rajya (State)</label>
                  <select value={state} onChange={e => setState(e.target.value)} required>
                    <option value="">Chunein...</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="language-selector">
                <label><Languages size={18} /> Bhasha (Language)</label>
                <div className="lang-chips">
                  {availableLanguages.map(l => (
                    <button key={l.code} type="button"
                      className={`lang-chip ${language === l.code ? 'active' : ''}`}
                      onClick={() => setLanguage(l.code)}>
                      <span>{l.flag}</span>
                      <span>{l.native}</span>
                    </button>
                  ))}
                </div>
              </div>

              <button className="btn-premium w-full" disabled={loading}>
                {loading ? <Loader size={20} className="spin" /> : 'Kheti Shuru Karein 🌾'}
              </button>
            </form>
          )}
        </div>

      </div>
    </div>
  )
}
