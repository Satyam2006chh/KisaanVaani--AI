import { AlertTriangle, Globe, FileX, ShieldAlert } from 'lucide-react'
import './About.css'

const problems = [
  {
    icon: <Globe size={22} />,
    title: "English Nahi Jaante",
    desc: "65% Indian farmers can't read English. Government websites are entirely in English.",
  },
  {
    icon: <FileX size={22} />,
    title: "Websites Nahi Chala Paate",
    desc: "Complex navigation with 10+ clicks just to find a single scheme's information.",
  },
  {
    icon: <AlertTriangle size={22} />,
    title: "Scheme Miss Ho Jaati Hai",
    desc: "Farmers miss PM Kisan, crop insurance deadlines — losing crores of rupees yearly.",
  },
  {
    icon: <ShieldAlert size={22} />,
    title: "Scam Ka Shikar",
    desc: "Misinformation spreads fast. Farmers are cheated by fake scheme agents.",
  },
]

export default function About() {
  return (
    <section className="about section" id="about">
      <div className="container">
        <div className="about__layout">

          {/* Left — Text */}
          <div className="about__text">
            <span className="section-label">Swadeshi AI Vision</span>
            <h2 className="section-title">
              India ke <span className="highlight">15 Crore Kisaan</span> peeche kyun hain?
            </h2>
            <div className="divider" />
            <p className="section-sub">
              Sarkaar ne hazaron yojanaein aur resources banaaye hain, lekin digital complexity aur bhasha ki wajah se jankari kisaan tak nahi pahunch paati.
              KisaanVaani is gap ko khatam karta hai — sirf ek button dabakar, apni bhasha mein baat karke.
            </p>

            <div className="about__solution">
              <div className="about__solution-icon">🌾</div>
              <p>
                <strong>Tiranga AI Revolution:</strong> Farmer apni boli mein bolega, DeepSeek-R1 aur Claude 3.5 Sonnet use samajhkar sateek live sarkaari data ke saath jawaab denge. Koi mushkil form nahi, koi English seekhne ki zaroorat nahi.
              </p>
            </div>
          </div>

          {/* Right — Premium Illustrated Image Card */}
          <div className="about__image-container">
            <div className="about__image-glow-wrapper">
              <img src={new URL('../../assets/farmer_ai.png', import.meta.url).href} alt="KisaanVaani AI Indian Farmer" className="about__premium-img" />
              <div className="about__image-overlay-card glass-card">
                <span className="about__overlay-badge">🇮🇳 Swadeshi AI</span>
                <h4>Hindustan Ki Boli, AI Ki Shakti</h4>
                <p>Designed specially to empower the hands that feed India.</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
