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
              <img src="/logo.png" alt="Logo" className="footer__logo-img" />
              <span className="footer__logo-text">
                किसान<span className="highlight">वाणी</span>
              </span>
            </div>
            <p className="footer__tagline">
              किसान का अपना AI दोस्त — बोलें और पाएं अपना हक़।
            </p>
          </div>

          {/* Links */}
          <div className="footer__col">
            <h4 className="footer__col-title">प्रोडक्ट</h4>
            <ul className="footer__links">
              <li><a href="#features">फीचर्स</a></li>
              <li><a href="#how-it-works">यह कैसे काम करता है</a></li>
              <li><a href="#languages">भाषाएं</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">सरकारी सुविधाएं</h4>
            <ul className="footer__links">
              <li><a href="https://pmkisan.gov.in" target="_blank" rel="noreferrer">पीएम किसान</a></li>
              <li><a href="https://pmfby.gov.in" target="_blank" rel="noreferrer">फसल बीमा</a></li>
              <li><a href="https://data.gov.in" target="_blank" rel="noreferrer">डेटा पोर्टल</a></li>
              <li><a href="https://mkisan.gov.in" target="_blank" rel="noreferrer">एम-किसान</a></li>
            </ul>
          </div>

          <div className="footer__col">
            <h4 className="footer__col-title">हमसे जुड़ें</h4>
            <ul className="footer__links">
              <li><a href="https://github.com/Satyam2006chh/KisaanVaani--AI" target="_blank" rel="noreferrer">GitHub</a></li>
              <li><a href="#about">हमारे बारे में</a></li>
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
