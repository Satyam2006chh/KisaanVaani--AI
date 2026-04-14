import { Mic, Cpu, Volume2 } from 'lucide-react'
import './HowItWorks.css'

const steps = [
  {
    icon: <Mic size={28} />,
    num: '01',
    title: 'Apni Baat Bolein',
    desc: 'Mic button dabaaiye aur apni bhasha mein apna sawaal boliye — Hindi, Punjabi ya koi bhi Indian language.',
    color: 'green',
  },
  {
    icon: <Cpu size={28} />,
    num: '02',
    title: 'AI Samjhega aur Dhundhega',
    desc: 'Hamaara LangGraph agent aapki baat samajhta hai, sahi tool chunfta hai — scheme, mausam ya mandi bhav.',
    color: 'gold',
  },
  {
    icon: <Volume2 size={28} />,
    num: '03',
    title: 'Awaaz Mein Jawab Milega',
    desc: 'Sarvam AI aapko jawab aapki bhasha ki awaaz mein dega. Koi padhai nahi, koi typing nahi.',
    color: 'green',
  },
]

export default function HowItWorks() {
  return (
    <section className="hiw section" id="how-it-works">
      <div className="container">
        <div className="hiw__header">
          <span className="section-label">How It Works</span>
          <h2 className="section-title">
            Sirf <span className="highlight">Teen Steps</span> Mein
          </h2>
          <div className="divider" />
          <p className="section-sub">
            Koi technical knowledge ki zaroorat nahi. Ek touch, ek awaaz — bas itna kaafi hai.
          </p>
        </div>

        <div className="hiw__steps">
          {steps.map((s, i) => (
            <div key={i} className="hiw__step">
              {/* Connector line */}
              {i < steps.length - 1 && <div className="hiw__connector" />}

              <div className={`hiw__icon hiw__icon--${s.color}`}>{s.icon}</div>
              <span className="hiw__num">{s.num}</span>
              <h3 className="hiw__step-title">{s.title}</h3>
              <p  className="hiw__step-desc">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Flow diagram */}
        <div className="hiw__flow glass-card">
          {['🎤 Bolo', '→', '🧠 AI Samjhe', '→', '🔍 Dhundhe', '→', '🔊 Jawab Do'].map((item, i) => (
            <span key={i} className={item === '→' ? 'hiw__arrow' : 'hiw__flow-step'}>
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
