import { Quote } from 'lucide-react'
import './Quotes.css'

const quotes = [
  {
    text: "Pehle scheme ke liye 3 baar tehsil jaata tha. Ab phone pe bolne se sab pata chal jaata hai.",
    author: "Ramesh Kumar",
    role: "Wheat Farmer, Haryana",
    avatar: "🧑‍🌾",
  },
  {
    text: "Mujhe angrezi nahi aati, par KisaanVaani ne Punjabi mein bataya ki PM Kisan ke paise kab aayenge.",
    author: "Gurpreet Singh",
    role: "Rice Farmer, Punjab",
    avatar: "👨‍🌾",
  },
  {
    text: "Mandi ka bhav pehle dalal batata tha, ab khud pata kar leta hoon. Bahut fayda hua.",
    author: "Sunita Devi",
    role: "Vegetable Farmer, UP",
    avatar: "👩‍🌾",
  },
]

export default function Quotes() {
  return (
    <section className="quotes section">
      <div className="container">
        <div className="quotes__header">
          <span className="section-label">Farmer Stories</span>
          <h2 className="section-title">
            Unki <span className="highlight">Awaaz</span>, Hamara Maqsad
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
            { num: '600M+', label: 'Potential Farmers Helped' },
            { num: '₹6000',  label: 'Avg PM Kisan Benefit/Year' },
            { num: '50+',    label: 'Govt Schemes Indexed' },
            { num: '11',     label: 'Languages Supported' },
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
