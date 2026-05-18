import React, { useState } from 'react'
import './App.css'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar/Navbar'
import Hero from './components/Hero/Hero'
import About from './components/About/About'
import HowItWorks from './components/HowItWorks/HowItWorks'
import Features from './components/Features/Features'
import Languages from './components/Languages/Languages'
import Quotes from './components/Quotes/Quotes'
import Footer from './components/Footer/Footer'
import AuthScreen from './components/Auth/AuthScreen'
import WelcomeSplash from './components/Splash/WelcomeSplash'

function AppContent() {
  const { isAuthenticated, loading } = useAuth()
  const [showSplash, setShowSplash] = useState(true)

  if (loading) {
    return (
      <div className="app loading" style={{ background: 'var(--bg-primary)', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
        <div className="loading-spinner" style={{ fontSize: '2rem' }}>🌾 Loading KisaanVaani...</div>
      </div>
    )
  }

  if (showSplash) {
    return <WelcomeSplash onEnter={() => setShowSplash(false)} />
  }

  if (!isAuthenticated) {
    return <AuthScreen />
  }

  return (
    <div className="app">
      <Navbar />
      <main>
        <Hero />
        <About />
        <Features />
        <HowItWorks />
        <Languages />
        <Quotes />
      </main>
      <Footer />
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
