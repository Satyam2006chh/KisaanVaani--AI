import './TechStack.css'

const stack = [
  { name: 'React',        role: 'Frontend UI',         color: '#61dafb', icon: '⚛️' },
  { name: 'FastAPI',      role: 'Backend Server',       color: '#009688', icon: '⚡' },
  { name: 'LangGraph',    role: 'AI Agent Orchestration',color: '#ff6b35',icon: '🧠' },
  { name: 'OpenRouter AI',  role: 'Premium LLM Cascade',   color: '#f76707', icon: '🚀' },
  { name: 'Sarvam AI',    role: 'Hindi Voice STT + TTS', color: '#22c55e', icon: '🎙️' },
  { name: 'Supabase',     role: 'PostgreSQL Database',   color: '#3ecf8e', icon: '�' },
  { name: 'Open-Meteo',   role: 'Weather API (Free)',    color: '#74c0fc', icon: '🌦️' },
  { name: 'PyJWT',        role: 'Secure Auth Tokens',    color: '#f59e0b', icon: '�' },
]

export default function TechStack() {
  return (
    <section className="tech section" id="tech">
      <div className="container">
        <div className="tech__header">
          <span className="section-label">Tech Stack</span>
          <h2 className="section-title">
            Built With <span className="highlight">Best-in-Class</span> Tools
          </h2>
          <div className="divider" />
          <p className="section-sub">
            Every tool chosen for a reason — speed, accuracy, and Indian language support.
          </p>
        </div>

        <div className="tech__grid">
          {stack.map((t, i) => (
            <div key={i} className="glass-card tech__card">
              <span className="tech__icon">{t.icon}</span>
              <div className="tech__info">
                <p className="tech__name" style={{ color: t.color }}>{t.name}</p>
                <p className="tech__role">{t.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
