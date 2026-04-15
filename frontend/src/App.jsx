import './App.css'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar/Navbar'
import Hero from './components/Hero/Hero'
import About from './components/About/About'
import HowItWorks from './components/HowItWorks/HowItWorks'
import Features from './components/Features/Features'
import Languages from './components/Languages/Languages'
import Quotes from './components/Quotes/Quotes'
import TechStack from './components/TechStack/TechStack'
import Footer from './components/Footer/Footer'
import AuthScreen from './components/Auth/AuthScreen'

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">🌾</div>
      </div>
    )
  }

  // If not authenticated, show auth screen (login/signup)
  if (!isAuthenticated) {
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
        <TechStack />
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
