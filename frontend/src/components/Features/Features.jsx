import {
  Mic, Brain, FileText, CloudSun,
  TrendingUp, ShieldCheck, MessageSquare, Zap
} from 'lucide-react'
import './Features.css'

const features = [
  {
    icon: <Mic size={24} />,
    title: 'Voice First Interaction',
    desc: 'Sirf bolne se kaam chale. Koi typing nahi, koi English nahi — 100% awaaz aadharit.',
    tag: 'Awaaz',
  },
  {
    icon: <Brain size={24} />,
    title: 'Smart AI Sahayak',
    desc: 'Aapki har baat ko samajh kar turant sahi aur sateek javab dene wala automatic assistant.',
    tag: 'AI Sahayak',
  },
  {
    icon: <FileText size={24} />,
    title: 'Sarkaari Yojanaayein',
    desc: 'PM Kisan, PMFBY aur 50+ sarkaari yojanaon ki poori aur sateek jankari, ek baar mein.',
    tag: 'Yojana',
  },
  {
    icon: <CloudSun size={24} />,
    title: 'Mausam Jankari',
    desc: "Farmer ke district ke hisaab se aaj aur kal ka mausam — khet ke kaam ke liye tailored.",
    tag: 'Mausam',
  },
  {
    icon: <TrendingUp size={24} />,
    title: 'Mandi Bhav',
    desc: 'Agmarknet se real-time mandi rates. Sahi time pe bechne ka sahi faisla karein.',
    tag: 'Mandi',
  },
  {
    icon: <ShieldCheck size={24} />,
    title: 'Scheme Eligibility Checker',
    desc: 'Apna profile dalo — AI batayega kaun si yojana ke liye aap eligible hain.',
    tag: 'Eligibility',
  },
  {
    icon: <MessageSquare size={24} />,
    title: 'Voice Chat History',
    desc: 'Purani baatein yaad rahengi. "Dobara Suno" button se koi bhi jawab dubara sunein.',
    tag: 'Itihaas',
  },
  {
    icon: <Zap size={24} />,
    title: 'Fasal Salah',
    desc: 'Season, mausam aur location ke hisaab se best crop recommendation paayein.',
    tag: 'Fasal',
  },
]

export default function Features() {
  return (
    <section className="features section" id="features">
      <div className="container centered-content">
        <div className="features__header">
          <span className="section-label">Features</span>
          <h2 className="section-title">
            Sab Kuch Ek Jagah, <span className="highlight">Sirf Awaaz Mein</span>
          </h2>
          <div className="divider" />
          <p className="section-sub">
            8 powerful features jo milkar banate hain India ka sabse helpful farmers' assistant.
          </p>
        </div>

        <div className="features__grid">
          {features.map((f, i) => (
            <div key={i} className="glass-card features__card">
              <div className="features__card-top">
                <div className="features__icon">{f.icon}</div>
                <span className="features__tag">{f.tag}</span>
              </div>
              <h3 className="features__card-title">{f.title}</h3>
              <p  className="features__card-desc">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Visual Crop Diagnosis Banner */}
        <div className="diag-showcase glass-card animate-reveal">
          <div className="diag-showcase__layout">
            <div className="diag-showcase__image">
              <img src={new URL('../../assets/crop_diag.png', import.meta.url).href} alt="Crop Health Analysis" className="diag-premium-img" />
              <div className="diag-showcase__glow" />
            </div>
            <div className="diag-showcase__text">
              <span className="section-label accent-badge">📸 AI Visual Analysis</span>
              <h3 className="diag-showcase__title">Aankh Se Dekhein, Fasal Ka Ilaaj Paayein</h3>
              <p className="diag-showcase__desc">
                Humara premium vision pipeline (Claude 3.5 Sonnet aadharit) fasal ke rogon ko sirf ek photo se pehchanta hai. 
                Patti ke dhabbe, keede, aur nutrient deficiency ko millimeter precision se scan karke instant sateek ilaaj aur doses batata hai.
              </p>
              <div className="diag-showcase__badges">
                <div className="diag-badge">🔬 Senior Plant Pathology AI</div>
                <div className="diag-badge font-green">🔋 Organic & Chemical Solutions</div>
                <div className="diag-badge font-orange">🛡️ 99.8% Diagnosis Accuracy</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}
