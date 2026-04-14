import './App.css'
import Navbar from './components/Navbar/Navbar'
import Hero from './components/Hero/Hero'
import About from './components/About/About'
import HowItWorks from './components/HowItWorks/HowItWorks'
import Features from './components/Features/Features'
import Languages from './components/Languages/Languages'
import Quotes from './components/Quotes/Quotes'
import TechStack from './components/TechStack/TechStack'
import Footer from './components/Footer/Footer'

function App() {
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

export default App
