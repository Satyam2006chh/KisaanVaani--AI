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
            <span className="section-label">The Problem</span>
            <h2 className="section-title">
              India ke <span className="highlight">600 Crore Kisaan</span> peeche kyun hain?
            </h2>
            <div className="divider" />
            <p className="section-sub">
              Sarkaar ne kai yojanaein banaayi hain, lekin jankari tak pahunchna mushkil hai.
              KisaanVaani is gap ko bharta hai — sirf awaaz se.
            </p>

            <div className="about__solution">
              <div className="about__solution-icon">🌾</div>
              <p>
                <strong>Hamaara solution:</strong> Farmer bolega, AI samjhega, aur bolke jawab dega.
                Koi typing nahi. Koi English nahi. Pure voice mein.
              </p>
            </div>
          </div>

          {/* Right — Problem cards */}
          <div className="about__cards">
            {problems.map((p, i) => (
              <div key={i} className="glass-card about__card">
                <span className="about__card-icon">{p.icon}</span>
                <div>
                  <h3 className="about__card-title">{p.title}</h3>
                  <p  className="about__card-desc">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
