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

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  // Diagnostic logging
  console.log('[App] Auth State:', { isAuthenticated, loading })

  if (loading) {
    return (
      <div className="app loading" style={{ background: '#060d06', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#22c55e' }}>
        <div className="loading-spinner" style={{ fontSize: '2rem' }}>🌾 Loading KisaanVaani...</div>
      </div>
    )
  }

  // If not authenticated, show auth screen (login/signup)
  if (!isAuthenticated) {
    console.log('[App] Rendering AuthScreen')
    return <AuthScreen />
  }

  // If authenticated, show main app
  return (
    <div className="app">
      <Navbar />
      <main>
        <Hero />
        <About />
        <HowItWorks />
        <Features />
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
