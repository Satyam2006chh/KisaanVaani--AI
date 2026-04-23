import { Mic, Heart } from 'lucide-react'
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
          </div>

          {/* Links */}
          <div className="footer__col">
            <h4 className="footer__col-title">Product</h4>
            <ul className="footer__links">
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="#languages">Languages</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">Govt Resources</h4>
            <ul className="footer__links">
              <li><a href="https://pmkisan.gov.in" target="_blank" rel="noreferrer">PM Kisan</a></li>
              <li><a href="https://pmfby.gov.in" target="_blank" rel="noreferrer">PMFBY</a></li>
              <li><a href="https://data.gov.in" target="_blank" rel="noreferrer">Data.gov.in</a></li>
              <li><a href="https://mkisan.gov.in" target="_blank" rel="noreferrer">mKisan</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">Connect</h4>
            <ul className="footer__links">
              <li><a href="https://github.com/Satyam2006chh/KisaanVaani--AI" target="_blank" rel="noreferrer">GitHub</a></li>
              <li><a href="#about">About Us</a></li>
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
