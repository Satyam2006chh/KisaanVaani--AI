import {
  Mic, Brain, FileText, CloudSun,
  TrendingUp, ShieldCheck, MessageSquare, Zap
} from 'lucide-react'
import './Features.css'

const features = [
  {
    icon: <Mic size={24} />,
    title: 'आवाज़ से काम',
    desc: 'सिर्फ बोलने से काम चले। कोई टाइपिंग नहीं, कोई अंग्रेजी नहीं — 100% आवाज़ आधारित।',
    tag: 'आवाज़',
  },
  {
    icon: <Brain size={24} />,
    title: 'स्मार्ट AI सहायक',
    desc: 'आपकी हर बात को समझ कर तुरंत सही और सटीक जवाब देने वाला ऑटोमैटिक असिस्टेंट।',
    tag: 'AI सहायक',
  },
  {
    icon: <FileText size={24} />,
    title: 'सरकारी योजनाएं',
    desc: 'पीएम किसान, फसल बीमा और 50+ सरकारी योजनाओं की पूरी और सटीक जानकारी, एक बार में।',
    tag: 'योजना',
  },
  {
    icon: <CloudSun size={24} />,
    title: 'मौसम की जानकारी',
    desc: "किसान के जिले के हिसाब से आज और कल का मौसम — खेत के काम के लिए सटीक।",
    tag: 'मौसम',
  },
  {
    icon: <TrendingUp size={24} />,
    title: 'मंडी भाव',
    desc: 'एगमार्कनेट से रियल-टाइम मंडी रेट। सही समय पर बेचने का सही फैसला करें।',
    tag: 'मंडी',
  },
  {
    icon: <ShieldCheck size={24} />,
    title: 'योजना पात्रता जांचें',
    desc: 'अपनी प्रोफाइल डालें — AI बताएगा कि आप किस योजना के लिए पात्र हैं।',
    tag: 'पात्रता',
  },
  {
    icon: <MessageSquare size={24} />,
    title: 'वॉयस चैट इतिहास',
    desc: 'पुरानी बातें याद रहेंगी। "दोबारा सुनो" बटन से कोई भी जवाब फिर से सुनें।',
    tag: 'इतिहास',
  },
  {
    icon: <Zap size={24} />,
    title: 'फसल की सलाह',
    desc: 'मौसम और लोकेशन के हिसाब से सबसे अच्छी फसल की सलाह पाएं।',
    tag: 'फसल',
  },
]

export default function Features() {
  return (
    <section className="features section" id="features">
      <div className="container centered-content">
        <div className="features__header">
          <span className="section-label">Features</span>
          <h2 className="section-title">
            सब कुछ एक जगह, <span className="highlight">सिर्फ आवाज़ में</span>
          </h2>
          <div className="divider" />
          <p className="section-sub">
            8 शानदार फीचर्स जो मिलकर बनाते हैं भारत का सबसे मददगार किसान असिस्टेंट।
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
              <span className="section-label accent-badge">📸 AI विजुअल एनालिसिस</span>
              <h3 className="diag-showcase__title">आंख से देखें, फसल का इलाज पाएं</h3>
              <p className="diag-showcase__desc">
                हमारा एडवांस विजन AI फसल के रोगों को सिर्फ एक फोटो से पहचानता है। 
                पत्ती के धब्बे, कीड़े और पोषक तत्वों की कमी को स्कैन करके तुरंत सटीक इलाज बताता है।
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
