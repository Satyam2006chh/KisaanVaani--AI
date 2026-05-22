import { AlertTriangle, Globe, FileX, ShieldAlert } from 'lucide-react'
import './About.css'

const problems = [
  {
    icon: <Globe size={22} />,
    title: "अंग्रेजी नहीं जानते",
    desc: "65% भारतीय किसान अंग्रेजी नहीं पढ़ सकते। सरकारी वेबसाइटें पूरी तरह अंग्रेजी में हैं।",
  },
  {
    icon: <FileX size={22} />,
    title: "वेबसाइट चलाना मुश्किल",
    desc: "किसी योजना की जानकारी ढूँढने के लिए 10 से ज्यादा बार क्लिक करना पड़ता है।",
  },
  {
    icon: <AlertTriangle size={22} />,
    title: "योजनाएं छूट जाती हैं",
    desc: "किसान पीएम किसान और फसल बीमा की तारीखें चूक जाते हैं — जिससे करोड़ों का नुकसान होता है।",
  },
  {
    icon: <ShieldAlert size={22} />,
    title: "धोखाधड़ी का शिकार",
    desc: "गलत जानकारी तेजी से फैलती है। किसान फर्जी एजेंटों द्वारा ठगे जाते हैं।",
  },
]

export default function About() {
  return (
    <section className="about section" id="about">
      <div className="container">
        <div className="about__layout">

          {/* Left — Text */}
          <div className="about__text">
            <span className="section-label">स्वदेशी AI विजन</span>
            <h2 className="section-title">
              भारत के <span className="highlight">15 करोड़ किसान</span> पीछे क्यों हैं?
            </h2>
            <div className="divider" />
            <p className="section-sub">
              सरकार ने हज़ारों योजनाएं और सुविधाएं बनाई हैं, लेकिन डिजिटल जटिलता और भाषा की वजह से जानकारी किसान तक नहीं पहुंच पाती। किसानवाणी इस दूरी को खत्म करता है — सिर्फ एक बटन दबाकर, अपनी भाषा में बात करके।
            </p>

            <div className="about__solution">
              <div className="about__solution-icon">🌾</div>
              <p>
                <strong>स्वदेशी AI क्रांति:</strong> किसान अपनी बोली में बोलेगा, DeepSeek-R1 और Claude 3.5 Sonnet उसे समझकर सटीक लाइव सरकारी डेटा के साथ जवाब देंगे। कोई मुश्किल फॉर्म नहीं, कोई अंग्रेजी सीखने की जरूरत नहीं।
              </p>
            </div>
          </div>

          {/* Right — Premium Illustrated Image Card */}
          <div className="about__image-container">
            <div className="about__image-glow-wrapper">
              <img src={new URL('../../assets/farmer_ai.png', import.meta.url).href} alt="KisaanVaani AI Indian Farmer" className="about__premium-img" />
              <div className="about__image-overlay-card glass-card">
                <span className="about__overlay-badge">🇮🇳 स्वदेशी AI</span>
                <h4>हिन्दुस्तान की बोली, AI की शक्ति</h4>
                <p>भारत का पेट भरने वाले हाथों को सशक्त बनाने के लिए खास तौर पर डिज़ाइन किया गया।</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
