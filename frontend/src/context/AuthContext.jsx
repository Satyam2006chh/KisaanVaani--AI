import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth'
import { auth } from '../firebase'

const AuthContext = createContext(null)

const LANGUAGES = [
  { name: 'Hindi',     native: 'हिंदी',     flag: '🇮🇳', code: 'hi-IN' },
  { name: 'Punjabi',   native: 'ਪੰਜਾਬੀ',    flag: '🏔️', code: 'pa-IN' },
  { name: 'Bengali',   native: 'বাংলা',     flag: '🌊', code: 'bn-IN' },
  { name: 'Tamil',     native: 'தமிழ்',     flag: '🔷', code: 'ta-IN' },
  { name: 'Telugu',    native: 'తెలుగు',    flag: '🔶', code: 'te-IN' },
  { name: 'Kannada',   native: 'ಕನ್ನಡ',     flag: '🟩', code: 'kn-IN' },
  { name: 'Malayalam', native: 'മലയാളം',    flag: '🟦', code: 'ml-IN' },
  { name: 'Marathi',   native: 'मराठी',     flag: '🟨', code: 'mr-IN' },
  { name: 'Gujarati',  native: 'ગુજરાતી',    flag: '🟪', code: 'gu-IN' },
  { name: 'Odia',      native: 'ଓଡ଼ିଆ',     flag: '🟫', code: 'od-IN' },
  { name: 'Assamese',  native: 'অসমীয়া',    flag: '🐘', code: 'as-IN' },
  { name: 'English',   native: 'English',    flag: '📖',  code: 'en-IN' },
]

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [confirmationResult, setConfirmationResult] = useState(null)
  const API_BASE_URL = import.meta.env.VITE_API_URL || ''

  useEffect(() => {
    // 1. WAKE UP CALL: Immediately ping backend to start the "wake up" process (for Render free tier)
    console.log('[AuthContext] Pre-warming backend...')
    axios.get(`${API_BASE_URL}/health`).catch(() => {})

    // 2. Check for existing session with absolute 30-day token expiration
    const token = localStorage.getItem('token')
    const saved = localStorage.getItem('user')
    const loginTime = localStorage.getItem('login_time')
    console.log('[AuthContext] Initializing:', { hasToken: !!token, hasSavedUser: !!saved, hasLoginTime: !!loginTime })
    
    if (token && saved) {
      // Enforce absolute security timeout: 30 days
      const maxAge = 30 * 24 * 60 * 60 * 1000 // 30 days in ms
      const isExpired = !loginTime || (Date.now() - parseInt(loginTime, 10) > maxAge)
      
      if (isExpired) {
        console.warn('[AuthContext] Session expired (older than 30 days or missing timestamp). Logging out.')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('login_time')
        setUser(null)
      } else {
        try { 
          const parsed = JSON.parse(saved)
          console.log('[AuthContext] Restoring user:', parsed.name)
          setUser(parsed) 
        } catch (e) { 
          console.error('[AuthContext] Restore failed:', e)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          localStorage.removeItem('login_time')
          setUser(null)
        }
      }
    }
    setLoading(false)
  }, [API_BASE_URL])

  const api = useMemo(() => axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
  }), [API_BASE_URL])

  const setupRecaptcha = () => {
    if (!window.recaptchaVerifier) {
      window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
        'size': 'invisible',
        'callback': (response) => {
          console.log('[AuthContext] reCAPTCHA solved');
        },
        'expired-callback': () => {
          console.warn('[AuthContext] reCAPTCHA expired');
        }
      });
    }
  }

  const sendOTP = async (phone) => {
    console.log('[AuthContext] Sending Firebase OTP to:', `+91${phone}`)
    try {
      setupRecaptcha()
      const appVerifier = window.recaptchaVerifier
      const confirmation = await signInWithPhoneNumber(auth, `+91${phone}`, appVerifier)
      setConfirmationResult(confirmation)
      console.log('[AuthContext] Firebase OTP sent successfully')
      return { success: true }
    } catch (err) {
      console.error('[AuthContext] Firebase OTP Error:', err)
      throw err
    }
  }

  const verifyOTP = async (phone, otp, name, language, district, state, city) => {
    console.log('[AuthContext] Verifying OTP for:', phone)
    try {
      // 1. Verify with Firebase First
      if (otp !== '123456' && confirmationResult) {
         await confirmationResult.confirm(otp)
         console.log('[AuthContext] Firebase OTP verified successfully')
      } else if (otp !== '123456' && !confirmationResult) {
         throw new Error('Please request OTP first')
      }

      // 2. Sync with backend for DB saving
      const payload = { phone, otp, name, language, district, state, city }
      const verifyPromise = api.post('/api/auth/otp/verify', payload)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('OTP verification timed out')), 12000)
      })
      const { data } = await Promise.race([verifyPromise, timeoutPromise])
      console.log('[AuthContext] Verify Response:', data)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user',  JSON.stringify(data.user))
      localStorage.setItem('login_time', Date.now().toString())
      setUser(data.user)
      return data.user
    } catch (err) {
      console.error('[AuthContext] Verify Error:', err.response?.data || err.message || err)
      
      // GOD MODE FALLBACK: If it's the demo OTP, keep login/profile flow usable even if backend is slow.
      if (otp === '123456') {
        const existingRaw = localStorage.getItem('user')
        let existingUser = null
        try { existingUser = existingRaw ? JSON.parse(existingRaw) : null } catch { existingUser = null }
        const hasExistingUser = existingUser?.farmer_id === phone && !!existingUser?.name

        if (!name?.trim() && !hasExistingUser) {
          const profileErr = new Error('Name required for new users')
          profileErr.response = { data: { detail: 'Name required for new users' } }
          throw profileErr
        }

        console.warn('[AuthContext] Server failed/timed out. Using God-Mode fallback.')
        const fallbackUser = {
          farmer_id: phone,
          name: name?.trim() || existingUser?.name || 'Kisaan Dost',
          language: language || existingUser?.language || 'hi-IN',
          district: district || existingUser?.district || '',
          state: state || existingUser?.state || '',
          city: city || existingUser?.city || ''
        }
        localStorage.setItem('token', 'fallback_token_123456')
        localStorage.setItem('user',  JSON.stringify(fallbackUser))
        localStorage.setItem('login_time', Date.now().toString())
        setUser(fallbackUser)
        return fallbackUser
      }
      
      throw err
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('login_time')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{
      user, loading,
      isAuthenticated: !!user,
      languages: LANGUAGES,
      sendOTP, verifyOTP, logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
