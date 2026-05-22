import { Mic, Cpu, Volume2 } from 'lucide-react'
import './HowItWorks.css'

const steps = [
  {
    icon: <Mic size={28} />,
    num: '01',
    title: 'अपनी बात बोलें',
    desc: 'माइक बटन दबाइये और अपनी भाषा में अपना सवाल बोलिये — हिंदी, पंजाबी या कोई भी भारतीय भाषा।',
    color: 'saffron',
  },
  {
    icon: <Cpu size={28} />,
    num: '02',
    title: 'AI समझेगा और ढूंढेगा',
    desc: 'हमारा स्मार्ट AI सहायक आपकी बात समझता है और सटीक जानकारी (योजना, मौसम या मंडी भाव) निकालता है।',
    color: 'blue',
  },
  {
    icon: <Volume2 size={28} />,
    num: '03',
    title: 'आवाज़ में जवाब मिलेगा',
    desc: 'किसानवाणी आपको जवाब आपकी भाषा की आवाज़ में बोलकर सुनाएगा। ना पढ़ने का झंझट, ना लिखने की तकलीफ।',
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
            सिर्फ <span className="highlight">तीन स्टेप्स</span> में
          </h2>
          <div className="divider" />
          <p className="section-sub">
            किसी तकनीकी ज्ञान की जरूरत नहीं। एक टच, एक आवाज़ — बस इतना काफी है।
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
          {['🎤 बोलें', '→', '🧠 AI समझे', '→', '🔍 ढूंढे', '→', '🔊 जवाब दे'].map((item, i) => (
            <span key={i} className={item === '→' ? 'hiw__arrow' : 'hiw__flow-step'}>
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
