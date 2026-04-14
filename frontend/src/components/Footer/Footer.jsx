import { Mic, MessageCircle, Info, Heart } from 'lucide-react'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__top">

          {/* Brand */}
          <div className="footer__brand">
            <div className="footer__logo">
              <span className="footer__logo-icon"><Mic size={18} /></span>
              <span className="footer__logo-text">
                Kisaan<span className="highlight">Vaani</span>
              </span>
            </div>
            <p className="footer__tagline">
              Kisan Ka Apna AI Dost — bolo aur paao apna haq.
            </p>
            <div className="footer__socials">
              <a href="https://github.com/Satyam2006chh/KisaanVaani--AI" target="_blank" rel="noreferrer" className="footer__social-link" aria-label="GitHub">
                <Info size={18} />
              </a>
              <a href="#" className="footer__social-link" aria-label="Twitter"><MessageCircle size={18} /></a>
              <a href="#" className="footer__social-link" aria-label="LinkedIn"><MessageCircle size={18} /></a>
            </div>
          </div>

          {/* Links */}
          <div className="footer__col">
            <h4 className="footer__col-title">Product</h4>
            <ul className="footer__links">
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="#languages">Languages</a></li>
              <li><a href="#tech">Tech Stack</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">Tech</h4>
            <ul className="footer__links">
              <li><a href="https://sarvam.ai" target="_blank" rel="noreferrer">Sarvam AI</a></li>
              <li><a href="https://groq.com"  target="_blank" rel="noreferrer">Groq AI</a></li>
              <li><a href="https://langchain.com" target="_blank" rel="noreferrer">LangChain</a></li>
              <li><a href="https://www.firecrawl.dev" target="_blank" rel="noreferrer">Firecrawl</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">Govt Resources</h4>
            <ul className="footer__links">
              <li><a href="https://pmkisan.gov.in"   target="_blank" rel="noreferrer">PM Kisan</a></li>
              <li><a href="https://pmfby.gov.in"     target="_blank" rel="noreferrer">PMFBY</a></li>
              <li><a href="https://data.gov.in"      target="_blank" rel="noreferrer">Data.gov.in</a></li>
              <li><a href="https://mkisan.gov.in"    target="_blank" rel="noreferrer">mKisan</a></li>
            </ul>
          </div>
        </div>

        <div className="footer__bottom">
          <p className="footer__copy">
            © {new Date().getFullYear()} KisaanVaani AI. Made with <Heart size={13} className="footer__heart" /> for India's farmers.
          </p>
          <p className="footer__apis">
            <span className="footer__api-badge">Open Source</span>
            <span className="footer__api-badge">11 Languages</span>
            <span className="footer__api-badge">Voice First</span>
          </p>
        </div>
      </div>
    </footer>
  )
}
