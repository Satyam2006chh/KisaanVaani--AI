import { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

const LANGUAGES = [
  { name: 'Hindi',   native: 'हिंदी',   flag: '🇮🇳', code: 'hi-IN' },
  { name: 'English', native: 'English', flag: '📖',  code: 'en-IN' },
]

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const saved = localStorage.getItem('user')
    if (token && saved) {
      try { setUser(JSON.parse(saved)) } catch { localStorage.clear() }
    }
    setLoading(false)
  }, [])

  const sendOTP = async (phone) => {
    const { data } = await axios.post('/api/auth/otp/send', { phone })
    return data
  }

  const verifyOTP = async (phone, otp, name, language, district, state, city) => {
    const { data } = await axios.post('/api/auth/otp/verify', {
      phone, otp, name, language, district, state, city,
    })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user',  JSON.stringify(data.user))
    setUser(data.user)
    return data.user
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
