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
  const { sendOTP, verifyOTP, languages } = useAuth()

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
    setError('')
    setLoading(true)
    try {
      await sendOTP(phone)
      setStep(STEP.OTP)
    } catch (e) {
      err(e.response?.data?.detail || 'OTP bhejne mein error. Dobara try karein.')
    } finally {
      setLoading(false)
    }
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

        <div className="auth-steps">
          <div className={`auth-step ${step === 1 ? 'active' : step > 1 ? 'done' : ''}`}>1</div>
          <div className="auth-step-line" />
          <div className={`auth-step ${step === 2 ? 'active' : step > 2 ? 'done' : ''}`}>2</div>
          <div className="auth-step-line" />
          <div className={`auth-step ${step === 3 ? 'active' : ''}`}>3</div>
        </div>

        {error && <div className="auth-error">⚠️ {error}</div>}

        {step === STEP.PHONE && (
          <form onSubmit={handleSendOTP} className="auth-form">
            <h2>Mobile Number Daalen</h2>
            <p className="auth-subtitle">OTP aapke number par bheja jaayega</p>
            <div className="input-group">
              <Phone size={18} className="input-icon" />
              <span className="input-prefix">+91</span>
              <input
                className="with-prefix"
                type="tel"
                placeholder="10-digit mobile number"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                required autoFocus
              />
            </div>
            <button className="auth-btn" disabled={loading || phone.length < 10}>
              {loading ? <Loader size={18} className="spin" /> : 'OTP Bhejo →'}
            </button>
            <p className="auth-note">Testing OTP: <strong>123456</strong></p>
          </form>
        )}

        {step === STEP.OTP && (
          <form onSubmit={handleVerifyOTP} className="auth-form">
            <h2>OTP Daalen</h2>
            <p className="auth-subtitle">+91 {phone} par bheja gaya</p>
            <div className="input-group">
              <Lock size={18} className="input-icon" />
              <input
                type="text"
                placeholder="6-digit OTP"
                value={otp}
                onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required autoFocus
              />
            </div>
            <button className="auth-btn" disabled={loading || otp.length < 6}>
              {loading ? <Loader size={18} className="spin" /> : 'Verify Karein →'}
            </button>
            <button type="button" className="auth-link" onClick={() => { setStep(STEP.PHONE); setOtp('') }}>
              ← Phone number badlein
            </button>
          </form>
        )}

        {step === STEP.PROFILE && (
          <form onSubmit={handleProfile} className="auth-form">
            <h2>Apni Jaankari Bharein</h2>
            <p className="auth-subtitle">Yeh jaankari aapki madad ke liye zaroori hai</p>

            <div className="input-group">
              <User size={18} className="input-icon" />
              <input type="text" placeholder="Poora naam (e.g. Ramesh Kumar)"
                value={name} onChange={e => setName(e.target.value)} required autoFocus />
            </div>

            <div className="input-group">
              <Building2 size={18} className="input-icon" />
              <input type="text" placeholder="Shehar / Gaon (e.g. Ludhiana)"
                value={city} onChange={e => setCity(e.target.value)} required />
            </div>

            <div className="input-group">
              <MapPin size={18} className="input-icon" />
              <input type="text" placeholder="Zila / District (e.g. Amritsar)"
                value={district} onChange={e => setDistrict(e.target.value)} required />
            </div>

            <div className="input-group">
              <MapPin size={18} className="input-icon" />
              <select className="state-select" value={state} onChange={e => setState(e.target.value)} required>
                <option value="">-- Rajya chunein --</option>
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="language-section">
              <p className="section-label"><Languages size={14} /> Bhasha chunein</p>
              <div className="language-grid">
                {languages.map(l => (
                  <button key={l.code} type="button"
                    className={`language-btn ${language === l.code ? 'active' : ''}`}
                    onClick={() => setLanguage(l.code)}>
                    <span className="lang-flag">{l.flag}</span>
                    <span className="lang-name">{l.name}</span>
                    <span className="lang-native">{l.native}</span>
                  </button>
                ))}
              </div>
            </div>

            <button className="auth-btn" disabled={loading}>
              {loading ? <Loader size={18} className="spin" /> : '🌾 Account Banao'}
            </button>
          </form>
        )}

      </div>
    </div>
  )
}
