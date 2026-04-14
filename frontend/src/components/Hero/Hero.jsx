import { Mic, ArrowDown } from 'lucide-react'
import './Hero.css'

export default function Hero() {
  return (
    <section className="hero" id="hero">
      {/* Background grid */}
      <div className="hero__grid" aria-hidden="true" />

      {/* Glow blobs */}
      <div className="hero__blob hero__blob--green" aria-hidden="true" />
      <div className="hero__blob hero__blob--gold"  aria-hidden="true" />

      <div className="container hero__inner">
        {/* Badge */}
        <div className="hero__badge">
          <span className="hero__badge-dot" />
          India's First Voice AI for Farmers &nbsp;🌾
        </div>

        {/* Headline */}
        <h1 className="hero__title">
          Bolo, Samjho,<br />
          <span className="highlight">Badlo Apni Zindagi</span>
        </h1>

        <p className="hero__sub">
          Sirf bolne se paayein sarkari yojanaon ki jankari,<br className="hero__br" />
          mausam, mandi bhav aur fasal salah — Hindi, Punjabi ya apni bhasha mein.
        </p>

        {/* Mic visual */}
        <div className="hero__mic-wrap">
          <div className="hero__mic-ring hero__mic-ring--3" />
          <div className="hero__mic-ring hero__mic-ring--2" />
          <div className="hero__mic-ring hero__mic-ring--1" />
          <button className="hero__mic-btn" aria-label="Start speaking">
            <Mic size={36} />
          </button>
        </div>

        <p className="hero__mic-hint">Tap the mic to experience the demo</p>

        {/* CTAs */}
        <div className="hero__cta-row">
          <a href="#features" className="btn-primary">Explore Features</a>
          <a href="#how-it-works" className="btn-outline">How It Works</a>
        </div>

        {/* Stats */}
        <div className="hero__stats">
          {[
            { num: '11',   label: 'Indian Languages' },
            { num: '5+',   label: 'AI Tools' },
            { num: '600M', label: 'Potential Users' },
            { num: '100%', label: 'Voice Driven' },
          ].map(s => (
            <div key={s.label} className="hero__stat">
              <span className="hero__stat-num">{s.num}</span>
              <span className="hero__stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <a href="#about" className="hero__scroll" aria-label="Scroll down">
        <ArrowDown size={18} />
      </a>
    </section>
  )
}
