import { useState, useEffect } from 'react'
import { Building2, Languages, Loader, Lock, MapPin, Phone, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import './AuthScreen.css'
import translations from '../../translations.json'

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
  const [detectingLoc, setDetectingLoc] = useState(false)

  const t = (key) => {
    const langDict = translations[language] || translations['hi-IN']
    return langDict[key] || translations['hi-IN'][key] || key
  }

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
        console.log('[AuthScreen] Geolocation coordinates:', latitude, longitude)
        
        try {
          // Query free OpenStreetMap Nominatim Reverse Geocoding API
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`
          )
          if (!response.ok) throw new Error('Location reverse lookup failed')
          const data = await response.json()
          console.log('[AuthScreen] Reverse geocoding result:', data)
          
          const addr = data.address || {}
          
          // Match State to Indian States
          const rawState = addr.state || ''
          const matchedState = STATES.find(
            s => s.toLowerCase() === rawState.toLowerCase()
          ) || rawState
          
          // Match District (County or District field in address)
          const rawDistrict = addr.county || addr.district || addr.state_district || addr.city_district || ''
          const cleanDistrict = rawDistrict.replace(/\b(District|Zila)\b/gi, '').trim()
          
          // Match Village or City name
          const cityName = addr.city || addr.town || addr.village || addr.suburb || addr.hamlet || cleanDistrict || ''
          
          if (matchedState) setState(matchedState)
          if (cleanDistrict) setDistrict(cleanDistrict)
          if (cityName) setCity(cityName)
          
          console.log('[AuthScreen] Auto-detected details:', { city: cityName, district: cleanDistrict, state: matchedState })
        } catch (err) {
          console.error('[AuthScreen] Geocoding failure:', err)
          setError('Location auto-detect failed. Please type manually.')
        } finally {
          setDetectingLoc(false)
        }
      },
      (geoErr) => {
        console.warn('[AuthScreen] Geolocation prompt error/denied:', geoErr.message)
        setDetectingLoc(false)
        if (geoErr.code === 1) { // PERMISSION_DENIED
          setError(t('loc_err_allow'))
        } else if (geoErr.code === 2 || geoErr.message.includes('unavailable')) { // POSITION_UNAVAILABLE
          setError(t('loc_err_gps'))
        } else {
          setError(t('loc_err_fail'))
        }
      },
      { timeout: 10000, enableHighAccuracy: true }
    )
  }

  useEffect(() => {
    if (step === STEP.PROFILE) {
      console.log('[AuthScreen] Step 3 reached. Running geolocation search...')
      autoDetectLocation()
    }
  }, [step])

  const err = (msg) => { setError(msg); setLoading(false) }

  async function handleSendOTP(e) {
    e.preventDefault()
    if (phone.length < 10) return err(t('err_phone'))
    
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
    if (!name.trim())     return err(t('err_name'))
    if (!city.trim())     return err(t('err_city'))
    if (!district.trim()) return err(t('err_district'))
    if (!state)           return err(t('err_state'))
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
          <p className="auth-tagline">{t('tagline')}</p>
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
              <h2>{t('welcome_title_1')}<br /><span className="highlight">{t('welcome_title_2')}</span></h2>
              <p className="auth-subtitle">{t('welcome_subtitle')}</p>
              
              <div className="input-field">
                <label><Phone size={18} /> {t('mobile_label')}</label>
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
                {loading ? <Loader size={20} className="spin" /> : <>{t('btn_send_otp')}</>}
              </button>
              <div className="demo-hint">{t('demo_hint')}</div>
            </form>
          )}

          {step === STEP.OTP && (
            <form onSubmit={handleVerifyOTP} className="auth-form animate-reveal">
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                <div style={{ background: 'rgba(255, 103, 31, 0.15)', padding: '24px', borderRadius: '50%', color: 'var(--primary)', boxShadow: '0 0 40px rgba(255,103,31,0.2)' }}>
                  <Lock size={48} strokeWidth={1.5} />
                </div>
              </div>
              <h2>{t('otp_title_1')} <span className="highlight">{t('otp_title_2')}</span></h2>
              <p className="auth-subtitle">{t('otp_subtitle')} {phone}</p>
              
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
                {loading ? <Loader size={24} className="spin" /> : t('btn_verify')}
              </button>
              
              <button type="button" className="btn-link" onClick={() => setStep(STEP.PHONE)}>
                {t('btn_change_num')}
              </button>
            </form>
          )}

          {step === STEP.PROFILE && (
            <form onSubmit={handleProfile} className="auth-form animate-reveal">
              <h2>{t('profile_title_1')} <span className="highlight">{t('profile_title_2')}</span></h2>
              <p className="auth-subtitle">{t('profile_subtitle')}</p>

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
                <span>{detectingLoc ? t('btn_detecting') : t('btn_detect_loc')}</span>
              </button>

              <div className="profile-grid">
                <div className="input-field">
                  <label><User size={18} /> {t('name_label')}</label>
                  <input type="text" placeholder=""
                    value={name} onChange={e => setName(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><Building2 size={18} /> {t('city_label')}</label>
                  <input type="text" placeholder=""
                    value={city} onChange={e => setCity(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> {t('district_label')}</label>
                  <input type="text" placeholder=""
                    value={district} onChange={e => setDistrict(e.target.value)} required />
                </div>

                <div className="input-field">
                  <label><MapPin size={18} /> {t('state_label')}</label>
                  <select value={state} onChange={e => setState(e.target.value)} required>
                    <option value="">{t('state_select')}</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="language-selector">
                <label><Languages size={18} /> {t('lang_label')}</label>
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
                {loading ? <Loader size={20} className="spin" /> : t('btn_start')}
              </button>
            </form>
          )}
        </div>

      </div>
    </div>
  )
}
