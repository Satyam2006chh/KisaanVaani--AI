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
    tag: 'USP',
  },
  {
    icon: <Brain size={24} />,
    title: 'LangGraph AI Agent',
    desc: 'Multi-step reasoning agent jo intent samajhta hai aur sahi tool chunfta hai automatically.',
    tag: 'AI Core',
  },
  {
    icon: <FileText size={24} />,
    title: 'Govt Scheme RAG',
    desc: 'PM Kisan, PMFBY aur 50+ schemes ki jankari — real-time, accurate, aur cited.',
    tag: 'Knowledge',
  },
  {
    icon: <CloudSun size={24} />,
    title: 'Mausam Jankari',
    desc: "Farmer ke district ke hisaab se aaj aur kal ka mausam — khet ke kaam ke liye tailored.",
    tag: 'Weather',
  },
  {
    icon: <TrendingUp size={24} />,
    title: 'Mandi Bhav',
    desc: 'Agmarknet se real-time mandi rates. Sahi time pe bechne ka sahi faisla karein.',
    tag: 'Market',
  },
  {
    icon: <ShieldCheck size={24} />,
    title: 'Scheme Eligibility Checker',
    desc: 'Apna profile dalo — AI batayega kaun si yojana ke liye aap eligible hain.',
    tag: 'Smart',
  },
  {
    icon: <MessageSquare size={24} />,
    title: 'Voice Chat History',
    desc: 'Purani baatein yaad rahengi. "Dobara Suno" button se koi bhi jawab dubara sunein.',
    tag: 'Memory',
  },
  {
    icon: <Zap size={24} />,
    title: 'Fasal Salah',
    desc: 'Season, mausam aur location ke hisaab se best crop recommendation paayein.',
    tag: 'Crops',
  },
]

export default function Features() {
  return (
    <section className="features section" id="features">
      <div className="container">
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
      </div>
    </section>
  )
}
