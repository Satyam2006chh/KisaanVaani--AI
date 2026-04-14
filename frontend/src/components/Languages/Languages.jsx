import './Languages.css'

const languages = [
  { name: 'Hindi',     native: 'हिंदी',     flag: '🇮🇳', code: 'hi-IN', speakers: '600M+' },
  { name: 'Punjabi',   native: 'ਪੰਜਾਬੀ',    flag: '🏔️', code: 'pa-IN', speakers: '125M+' },
  { name: 'Bengali',   native: 'বাংলা',      flag: '🌊', code: 'bn-IN', speakers: '230M+' },
  { name: 'Tamil',     native: 'தமிழ்',      flag: '🌺', code: 'ta-IN', speakers: '80M+'  },
  { name: 'Telugu',    native: 'తెలుగు',     flag: '🌴', code: 'te-IN', speakers: '95M+'  },
  { name: 'Kannada',   native: 'ಕನ್ನಡ',      flag: '🪔', code: 'kn-IN', speakers: '45M+'  },
  { name: 'Malayalam', native: 'മലയാളം',    flag: '🌿', code: 'ml-IN', speakers: '38M+'  },
  { name: 'Marathi',   native: 'मराठी',     flag: '🦁', code: 'mr-IN', speakers: '83M+'  },
  { name: 'Gujarati',  native: 'ગુજરાતી',    flag: '🕌', code: 'gu-IN', speakers: '55M+'  },
  { name: 'Odia',      native: 'ଓଡ଼ିଆ',      flag: '🐘', code: 'od-IN', speakers: '35M+'  },
  { name: 'English',   native: 'English',    flag: '📖', code: 'en-IN', speakers: '125M+' },
]

export default function Languages() {
  return (
    <section className="langs section" id="languages">
      <div className="container">
        <div className="langs__header">
          <span className="section-label">Supported Languages</span>
          <h2 className="section-title">
            <span className="highlight">11 Bhaashaaon</span> Mein Baat Karein
          </h2>
          <div className="divider" />
          <p className="section-sub">
            Sarvam AI ki taakat se — India ki har major language mein bolein aur sunein.
          </p>
        </div>

        <div className="langs__grid">
          {languages.map((l, i) => (
            <div key={i} className="glass-card langs__card">
              <span className="langs__flag">{l.flag}</span>
              <div>
                <p className="langs__name">{l.name}</p>
                <p className="langs__native">{l.native}</p>
              </div>
              <span className="langs__speakers">{l.speakers}</span>
            </div>
          ))}
        </div>

        {/* Powered by badge */}
        <div className="langs__powered">
          <span className="langs__powered-text">Powered by</span>
          <span className="langs__powered-badge">Sarvam AI</span>
          <span className="langs__powered-text">— India's leading multilingual voice AI</span>
        </div>
      </div>
    </section>
  )
}
