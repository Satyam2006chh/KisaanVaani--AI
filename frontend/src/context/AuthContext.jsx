import { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

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

  useEffect(() => {
    // 1. WAKE UP CALL: Immediately ping backend to start the "wake up" process (for Render free tier)
    console.log('[AuthContext] Pre-warming backend...')
    axios.get('https://kisaanvaani-ai-1.onrender.com/').catch(() => {})

    // 2. Check for existing session
    const token = localStorage.getItem('token')
    const saved = localStorage.getItem('user')
    console.log('[AuthContext] Initializing:', { hasToken: !!token, hasSavedUser: !!saved })
    if (token && saved) {
      try { 
        const parsed = JSON.parse(saved)
        console.log('[AuthContext] Restoring user:', parsed.name)
        setUser(parsed) 
      } catch (e) { 
        console.error('[AuthContext] Restore failed:', e)
        localStorage.clear() 
      }
    }
    setLoading(false)
  }, [])

  // FORCE DIRECT URL to bypass Netlify Proxy/Redirect issues
  const API_BASE_URL = 'https://kisaanvaani-ai-1.onrender.com'
  
  const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30s timeout
  })

  const sendOTP = async (phone) => {
    console.log('[AuthContext] Sending OTP to:', `${API_BASE_URL}/api/auth/otp/send`)
    try {
      const { data } = await api.post('/api/auth/otp/send', { phone })
      console.log('[AuthContext] OTP Response:', data)
      return data
    } catch (err) {
      console.error('[AuthContext] OTP Error:', err.response?.data || err.message)
      throw err
    }
  }

  const verifyOTP = async (phone, otp, name, language, district, state, city) => {
    console.log('[AuthContext] Verifying OTP for:', phone)
    try {
      const { data } = await api.post('/api/auth/otp/verify', {
        phone, otp, name, language, district, state, city,
      })
      console.log('[AuthContext] Verify Response:', data)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user',  JSON.stringify(data.user))
      setUser(data.user)
      return data.user
    } catch (err) {
      console.error('[AuthContext] Verify Error:', err.response?.data || err.message)
      throw err
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
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
