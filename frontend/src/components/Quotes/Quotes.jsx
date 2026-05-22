import { Quote } from 'lucide-react'
import './Quotes.css'

const quotes = [
  {
    text: "पहले योजना के लिए 3 बार तहसील जाता था। अब फोन पर बोलने से सब पता चल जाता है।",
    author: "रमेश कुमार",
    role: "गेहूं किसान, हरियाणा",
    avatar: "🧑‍🌾",
  },
  {
    text: "मुझे अंग्रेजी नहीं आती, पर किसानवाणी ने मुझे पंजाबी में बताया कि पीएम किसान के पैसे कब आएंगे।",
    author: "गुरप्रीत सिंह",
    role: "धान किसान, पंजाब",
    avatar: "👨‍🌾",
  },
  {
    text: "मंडी का भाव पहले दलाल बताता था, अब खुद पता कर लेता हूँ। बहुत फायदा हुआ।",
    author: "सुनीता देवी",
    role: "सब्जी किसान, यूपी",
    avatar: "👩‍🌾",
  },
]

export default function Quotes() {
  return (
    <section className="quotes section">
      <div className="container">
        <div className="quotes__header">
          <span className="section-label">किसानों की कहानी</span>
          <h2 className="section-title">
            उनकी <span className="highlight">आवाज़</span>, हमारा मक़सद
          </h2>
          <div className="divider" />
        </div>

        <div className="quotes__grid">
          {quotes.map((q, i) => (
            <div key={i} className="glass-card quotes__card">
              <Quote size={28} className="quotes__icon" />
              <p className="quotes__text">"{q.text}"</p>
              <div className="quotes__author">
                <span className="quotes__avatar">{q.avatar}</span>
                <div>
                  <p className="quotes__name">{q.author}</p>
                  <p className="quotes__role">{q.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Impact banner */}
        <div className="quotes__impact">
          {[
            { num: '600M+', label: 'किसानों की मदद' },
            { num: '₹6000',  label: 'औसत पीएम किसान लाभ' },
            { num: '50+',    label: 'सरकारी योजनाएं' },
            { num: '11',     label: 'भाषाएं उपलब्ध' },
          ].map((s, i) => (
            <div key={i} className="quotes__impact-item">
              <span className="quotes__impact-num">{s.num}</span>
              <span className="quotes__impact-label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
