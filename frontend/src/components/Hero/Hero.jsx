import { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, Square, Loader, AlertCircle, TrendingUp, Image as ImageIcon, X, Volume2, Play } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { chatWithAgent, transcribeAudio, speakText } from '../../api'
import './Hero.css'

// All 11 languages supported by Sarvam TTS/STT
const LANGUAGES = [
  { code: 'hi-IN', label: 'हिंदी (Hindi)' },
  { code: 'pa-IN', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'bn-IN', label: 'বাংলা (Bengali)' },
  { code: 'ta-IN', label: 'தமிழ் (Tamil)' },
  { code: 'te-IN', label: 'తెలుగు (Telugu)' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml-IN', label: 'മലയാളം (Malayalam)' },
  { code: 'mr-IN', label: 'मराठी (Marathi)' },
  { code: 'gu-IN', label: 'ગુજરાતી (Gujarati)' },
  { code: 'od-IN', label: 'ଓଡ଼ିଆ (Odia)' },
  { code: 'as-IN', label: 'অসমীয়া (Assamese)' },
  { code: 'en-IN', label: 'English' },
]


const S = { IDLE: 'IDLE', RECORDING: 'RECORDING', PROCESSING: 'PROCESSING', SPEAKING: 'SPEAKING' }

// Chat history per session (in-memory for UI display)
const MAX_DISPLAY_MSGS = 6

export default function Hero() {
  const { user } = useAuth()
  const [status, setStatus]               = useState(S.IDLE)
  const [transcript, setTranscript]       = useState('')
  const [reply, setReply]                 = useState('')
  const [error, setError]                 = useState('')
  const [image, setImg]                   = useState(null)
  const [imgPreview, setImgPreview]       = useState(null)
  const [selectedLang, setSelectedLang]   = useState(user?.language || 'hi-IN')
  const [chatHistory, setChatHistory]     = useState([]) // [{role, text}]
  const [volume, setVolume]               = useState(0)
  
  const [introLang, setIntroLang]         = useState('hi-IN')
  const [isPlayingIntro, setIsPlayingIntro] = useState(false)
  const [isIntroLoading, setIsIntroLoading] = useState(false)

  const mediaRecorderRef = useRef(null)
  const mediaStreamRef   = useRef(null)
  const chunksRef        = useRef([])
  const isRecordingRef   = useRef(false)
  const audioCtxRef      = useRef(null)
  const analyzerRef      = useRef(null)
  const animFrameRef     = useRef(null)
  const chatEndRef       = useRef(null)
  const audioRef         = useRef(new Audio()) 
  const introAudioRef    = useRef(new Audio())
  const queueActiveRef   = useRef(false) 
  const prefetchedUrls   = useRef({}) 

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
      }
      if (introAudioRef.current) {
        introAudioRef.current.pause()
        introAudioRef.current.src = ""
      }
    }
  }, [])

  // ─── Scroll chat to bottom ────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, reply, transcript])


  // ─── Image handler ───────────────────────────────────────────────────────
  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImgPreview(URL.createObjectURL(file))
    const reader = new FileReader()
    reader.onloadend = () => setImg(reader.result)
    reader.readAsDataURL(file)
  }

  const clearImage = () => {
    setImg(null)
    setImgPreview(null)
  }

  // ─── Audio Visualizer ────────────────────────────────────────────────────
  const startVisualizer = (stream) => {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const source   = audioCtx.createMediaStreamSource(stream)
      const analyzer = audioCtx.createAnalyser()
      analyzer.fftSize = 64
      source.connect(analyzer)
      audioCtxRef.current = audioCtx
      analyzerRef.current = analyzer
      const dataArray = new Uint8Array(analyzer.frequencyBinCount)

      const tick = () => {
        if (!analyzerRef.current || !isRecordingRef.current) return
        analyzerRef.current.getByteFrequencyData(dataArray)
        const avg = dataArray.reduce((s, v) => s + v, 0) / dataArray.length
        setVolume(avg)
        animFrameRef.current = requestAnimationFrame(tick)
      }
      tick()
    } catch {}
  }

  const stopVisualizer = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
    analyzerRef.current = null
    setVolume(0)
  }

  // ─── Core recording logic ─────────────────────────────────────────────────
  const startRecording = async () => {
    setError('')
    chunksRef.current = []

    // 🔴 FORCIBLY STOP ANY ONGOING AI SPEECH 🔴
    queueActiveRef.current = false
    if (audioRef.current) {
      try {
        audioRef.current.onended = null
        audioRef.current.onerror = null
        audioRef.current.pause()
        audioRef.current.removeAttribute('src')
        audioRef.current.load()
      } catch (e) {
        console.warn('[Audio] Stop failed:', e)
      }
    }
    Object.values(prefetchedUrls.current).forEach(url => {
      try { URL.revokeObjectURL(url) } catch (e) {}
    })
    prefetchedUrls.current = {}

    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (micErr) {
      console.error('[Mic] Permission error:', micErr.name, micErr.message)
      if (micErr.name === 'NotAllowedError') {
        setError('🎙️ Mic permission chahiye — Browser popup mein "Allow" dabayein, phir mic button dabayein.')
      } else if (micErr.name === 'NotFoundError') {
        setError('🎙️ Koi microphone nahi mila. Headset lagayein ya mic check karein.')
      } else {
        setError(`🎙️ Mic error: ${micErr.message}. Page reload karein (F5) aur phir se try karein.`)
      }
      return
    }

    mediaStreamRef.current = stream
    isRecordingRef.current = true
    setStatus(S.RECORDING)
    
    // Keep previous chat history so it doesn't look like the app restarted
    setTranscript('')
    setReply('')
    setError('')

    startVisualizer(stream)

    // Use timeslice=250ms so data is buffered in small chunks, not all at end
    const recorder = new MediaRecorder(stream, { mimeType: getSupportedMime() })
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = async () => {
      const blobType = recorder.mimeType || 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: blobType })
      chunksRef.current = []

      if (!blob.size || blob.size < 500) {
        setError('Awaaz record nahi hui. Phir se koshish karein.')
        setStatus(S.IDLE)
        return
      }

      setStatus(S.PROCESSING)
      await processAudio(blob)
    }

    mediaRecorderRef.current = recorder
    recorder.start(250) // chunk every 250ms
  }

  const stopRecording = useCallback(() => {
    isRecordingRef.current = false
    stopVisualizer()

    const rec = mediaRecorderRef.current
    if (rec && rec.state === 'recording') {
      try { rec.requestData() } catch {} // flush last chunk
      rec.stop()
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop())
      mediaStreamRef.current = null
    }
    mediaRecorderRef.current = null

    // Pre-unlock audio context for later AI speech with SILENCE, not the old audio
    try {
      if (audioRef.current) {
        audioRef.current.onended = null
        audioRef.current.onerror = null
        audioRef.current.src = "data:audio/wav;base64,UklGRigAAABXQVZFRm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAA=="
        audioRef.current.play().catch(() => {})
      }
    } catch (e) {
      console.warn('[Audio] Unlock failed:', e)
    }
  }, [])

  const getSupportedMime = () => {
    const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
    return types.find(t => MediaRecorder.isTypeSupported(t)) || ''
  }

  // ─── Process audio pipeline ───────────────────────────────────────────────
  const processAudio = async (blob) => {
    try {
      // Step 1: STT — send in selected language so Sarvam understands it
      const sttRes = await transcribeAudio(blob, selectedLang)

      if (sttRes.status === 'SILENCE_DETECTED' || !sttRes.transcript) {
        const msg = sttRes.silence_reply || 'Kuch samajh nahi aaya. Phir se bolein.'
        setError(msg)
        setStatus(S.IDLE)
        return
      }

      const userText = sttRes.transcript
      setTranscript(userText)
      // Add user bubble immediately
      setChatHistory(h => [...h, { role: 'user', text: userText }].slice(-MAX_DISPLAY_MSGS))

      const chatRes = await chatWithAgent(
        userText,
        sttRes.english_transcript || userText,
        selectedLang,
        image
      )

      const aiText = chatRes.response

      // Step 3: TTS — Pre-fetch first audio chunk to sync text and voice perfectly
      try {
        const chunks = splitTextIntoChunks(aiText, selectedLang)
        prefetchedUrls.current = {} 

        if (chunks.length > 0) {
          // Keep showing typing dots while fetching the first audio chunk
          const firstAudioUrl = await speakText(chunks[0], selectedLang)
          prefetchedUrls.current[0] = firstAudioUrl

          // Audio is ready! Now show the text and start playing instantly
          setReply(aiText)
          setChatHistory(h => [...h, { role: 'ai', text: aiText }].slice(-MAX_DISPLAY_MSGS))
          setImg(null)
          setImgPreview(null)
          
          queueActiveRef.current = true
          playAudioQueue(chunks, 0)
        } else {
          setReply(aiText)
          setChatHistory(h => [...h, { role: 'ai', text: aiText }].slice(-MAX_DISPLAY_MSGS))
          setImg(null)
          setImgPreview(null)
          setStatus(S.IDLE)
        }
      } catch (ttsErr) {
        console.warn('[TTS] failed:', ttsErr)
        setReply(aiText)
        setChatHistory(h => [...h, { role: 'ai', text: aiText }].slice(-MAX_DISPLAY_MSGS))
        setImg(null)
        setImgPreview(null)
        setError('Awaaz nahi chal saki, lekin jawab upar likha hai.')
        setStatus(S.IDLE)
      }
    } catch (err) {
      console.error('[Pipeline] Error:', err)
      setError('Network issue ya API error. Internet check karein aur phir se koshish karein.')
      setStatus(S.IDLE)
    }
  }

  // ─── Audio Queue Playback (Handles speaking long text continuously without lags/timeouts) ───────────────────
  const playAudioQueue = async (chunks, index = 0) => {
    if (!queueActiveRef.current || index >= chunks.length) {
      setStatus(S.IDLE)
      queueActiveRef.current = false
      return
    }
    
    try {
      setStatus(S.SPEAKING)
      const chunkText = chunks[index]
      
      // Use prefetched URL if available, otherwise fetch it now
      let audioUrl = prefetchedUrls.current[index]
      if (!audioUrl) {
        audioUrl = await speakText(chunkText, selectedLang)
      }
      
      // Make sure user didn't hit STOP while we were fetching the audio
      if (!queueActiveRef.current) {
        URL.revokeObjectURL(audioUrl)
        setStatus(S.IDLE)
        return
      }
      
      // Trigger background PREFETCH for the NEXT chunk immediately
      const nextIndex = index + 1
      if (nextIndex < chunks.length && !prefetchedUrls.current[nextIndex]) {
        speakText(chunks[nextIndex], selectedLang).then(url => {
          prefetchedUrls.current[nextIndex] = url
        }).catch(err => {
          console.warn('[Prefetch] failed for chunk:', nextIndex, err)
        })
      }
      
      const audio = audioRef.current
      audio.pause()
      audio.src = audioUrl
      audio.load()
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        delete prefetchedUrls.current[index] // Clean cache
        playAudioQueue(chunks, index + 1) // Play next chunk
      }
      
      audio.onerror = (e) => {
        console.error('[Audio Queue] Playback error, skipping chunk:', e)
        URL.revokeObjectURL(audioUrl)
        delete prefetchedUrls.current[index]
        playAudioQueue(chunks, index + 1)
      }
      
      const playPromise = audio.play()
      if (playPromise !== undefined) {
        playPromise.catch(err => {
          console.error('[Audio Queue] Play failed, skipping chunk:', err)
          URL.revokeObjectURL(audioUrl)
          delete prefetchedUrls.current[index]
          playAudioQueue(chunks, index + 1)
        })
      }
    } catch (err) {
      console.warn('[Audio Queue] Fetch/Play failed, skipping chunk:', err)
      playAudioQueue(chunks, index + 1)
    }
  }

  // ─── Single mic toggle ────────────────────────────────────────────────────
  const handleMicClick = () => {
    if (isPlayingIntro) {
      introAudioRef.current.pause()
      setIsPlayingIntro(false)
    }

    if (status === S.RECORDING) {
      stopRecording()
    } else if (status === S.SPEAKING || status === S.IDLE) {
      // If it was speaking, halt the playback queue entirely
      if (status === S.SPEAKING) {
        queueActiveRef.current = false
        if (audioRef.current) {
          try {
            audioRef.current.onended = null
            audioRef.current.onerror = null
            audioRef.current.pause()
            audioRef.current.removeAttribute('src')
          } catch(e) {}
        }
        Object.values(prefetchedUrls.current).forEach(url => {
          try { URL.revokeObjectURL(url) } catch (e) {}
        })
        prefetchedUrls.current = {}
      }
      // Instantly start listening to the new question
      startRecording()
    }
  }

  const getIntroText = (langCode) => {
    const greetings = "नमस्कार, ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ, Hello, வணக்கம்! ";
    switch(langCode) {
      case 'hi-IN': return greetings + "किसान वाणी में आपका स्वागत है। यह ऐप 12 अलग-अलग भाषाओं में काम करता है। आप बोलकर मौसम की जानकारी, लाइव मंडी भाव, फसल की बीमारियों का इलाज, और खेती-बाड़ी की ताज़ा खबरें जान सकते हैं। बस माइक बटन दबाइए और अपना सवाल पूछिए!";
      case 'pa-IN': return greetings + "ਕਿਸਾਨ ਵਾਣੀ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਇਹ ਐਪ 12 ਵੱਖ-ਵੱਖ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਕੰਮ ਕਰਦਾ ਹੈ। ਤੁਸੀਂ ਬੋਲ ਕੇ ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ, ਲਾਈਵ ਮੰਡੀ ਭਾਅ, ਫਸਲਾਂ ਦੀਆਂ ਬਿਮਾਰੀਆਂ ਦਾ ਇਲਾਜ, ਅਤੇ ਖੇਤੀਬਾੜੀ ਦੀਆਂ ਤਾਜ਼ਾ ਖ਼ਬਰਾਂ ਜਾਣ ਸਕਦੇ ਹੋ। ਬੱਸ ਮਾਈਕ ਬਟਨ ਦਬਾਓ ਅਤੇ ਆਪਣਾ ਸਵਾਲ ਪੁੱਛੋ!";
      case 'en-IN': return greetings + "Welcome to Kisaan Vaani. This app works in 12 different languages. You can ask for weather updates, live mandi prices, crop disease treatments, and latest farming news using voice. Just press the mic button and ask your question!";
      case 'mr-IN': return greetings + "किसान वाणी मध्ये आपले स्वागत आहे. हे ॲप 12 वेगवेगळ्या भाषांमध्ये काम करते. तुम्ही बोलून हवामानाची माहिती, थेट बाजारभाव, पिकांच्या आजारांवर उपाय, आणि शेतीविषयक ताज्या बातम्या जाणून घेऊ शकता. फक्त माईक बटण दाबा आणि तुमचा प्रश्न विचारा!";
      case 'gu-IN': return greetings + "કિસાન વાણીમાં તમારું સ્વાગત છે. આ એપ 12 વિવિધ ભાષાઓમાં કામ કરે છે. તમે બોલીને હવામાનની માહિતી, લાઇવ મંડી ભાવ, પાકના રોગોની સારવાર, અને ખેતી વિશેના તાજા સમાચાર જાણી શકો છો. બસ માઇક બટન દબાવો અને તમારો પ્રશ્ન પૂછો!";
      case 'ta-IN': return greetings + "கிசான் வாணிக்கு உங்களை வரவேற்கிறோம். இந்த செயலி 12 வெவ்வேறு மொழிகளில் வேலை செய்கிறது. வானிலை தகவல், நேரடி மண்டி விலைகள், பயிர் நோய்களுக்கான சிகிச்சை மற்றும் விவசாய செய்திகளை குரல் மூலம் நீங்கள் கேட்கலாம். மைக் பட்டனை அழுத்தி உங்கள் கேள்வியைக் கேளுங்கள்!";
      case 'te-IN': return greetings + "కిసాన్ వాణికి స్వాగతం. ఈ యాప్ 12 విభిన్న భాషలలో పనిచేస్తుంది. మీరు వాతావరణ సమాచారం, లైవ్ మండి ధరలు, పంట వ్యాధుల చికిత్స మరియు వ్యవసాయ వార్తలను వాయిస్ ద్వారా అడగవచ్చు. మైక్ బటన్ నొక్కి మీ ప్రశ్న అడగండి!";
      case 'bn-IN': return greetings + "কিসান বাণীতে আপনাকে স্বাগত। এই অ্যাপটি 12টি ভিন্ন ভাষায় কাজ করে। আপনি ভয়েসের মাধ্যমে আবহাওয়ার তথ্য, লাইভ মান্ডি দাম, ফসলের রোগের চিকিৎসা এবং কৃষির খবর জানতে পারেন। শুধু মাইক বোতামটি চাপুন এবং আপনার প্রশ্ন করুন!";
      default: return greetings + "किसान वाणी में आपका स्वागत है। यह ऐप 12 अलग-अलग भाषाओं में काम करता है। आप बोलकर मौसम की जानकारी, लाइव मंडी भाव, फसल की बीमारियों का इलाज, और खेती-बाड़ी की ताज़ा खबरें जान सकते हैं। बस माइक बटन दबाइए और अपना सवाल पूछिए!";
    }
  }

  const handlePlayIntro = async () => {
    if (isPlayingIntro) {
      introAudioRef.current.pause();
      setIsPlayingIntro(false);
      return;
    }
    
    // Stop main audio if playing
    if (status === S.SPEAKING && audioRef.current) {
       audioRef.current.pause();
       setStatus(S.IDLE);
       queueActiveRef.current = false;
    }

    try {
      setIsIntroLoading(true);
      const text = getIntroText(introLang);
      const url = await speakText(text, introLang);
      
      setIsIntroLoading(false);
      setIsPlayingIntro(true);
      introAudioRef.current.src = url;
      introAudioRef.current.play();
      introAudioRef.current.onended = () => {
        setIsPlayingIntro(false);
        URL.revokeObjectURL(url);
      };
      introAudioRef.current.onerror = () => {
        setIsPlayingIntro(false);
        URL.revokeObjectURL(url);
      };
    } catch (e) {
      console.error(e);
      setIsIntroLoading(false);
      setIsPlayingIntro(false);
    }
  }


  return (
    <div className="hero-container">

      {/* ── Welcome ── */}
      <div className="welcome-msg">
        <h1>नमस्ते <span className="farmer-name">{user?.name || 'किसान'}</span> जी 🌾</h1>
        <p className="hero-subtitle">मौसम, मंडी, और फसल की AI-पॉवर्ड जानकारी — सिर्फ आपके लिए।</p>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="alert-card-premium error-banner">
          <AlertCircle size={18} />
          <p>{error}</p>
          <button className="dismiss-btn" onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {/* ── Image preview ── */}
      {imgPreview && (
        <div className="img-preview-container">
          <img src={imgPreview} alt="Fasal preview" />
          <button className="img-remove-btn" onClick={clearImage}><X size={16} /></button>
          <p className="img-hint">📸 AI फसल की फोटो का विश्लेषण करेगा</p>
        </div>
      )}

      {/* ── Active Conversation Area ── */}
      {(transcript || status === S.PROCESSING) && (
        <div className="active-chat-container">
          {/* User Side */}
          {transcript && (
            <div className="chat-bubble user-bubble active-bubble">
              <div className="chat-bubble-label">🎤 आपने कहा</div>
              <p>{transcript}</p>
            </div>
          )}

          {/* AI Side */}
          {status === S.PROCESSING && (
            <div className="chat-bubble ai-bubble typing-bubble active-bubble">
              <div className="chat-bubble-label">AI सोच रहा है...</div>
              <div className="typing-dots"><span /><span /><span /></div>
            </div>
          )}

          {reply && status !== S.PROCESSING && (
            <div className="chat-bubble ai-bubble active-bubble response-highlight">
              <div className="chat-bubble-label">🤖 AI का जवाब</div>
              <p>{reply}</p>
            </div>
          )}
        </div>
      )}

      {/* ── Interaction Zone ── */}
      <div className="interaction-zone">
        {/* Visualizer bars */}
        {status === S.RECORDING && (
          <div className="visualizer-container">
            {[...Array(16)].map((_, i) => (
              <div
                key={i}
                className="vis-bar"
                style={{
                  height: `${Math.max(4, volume * (0.3 + (i % 3) * 0.2) * (Math.random() * 0.4 + 0.8))}px`,
                  opacity: 0.6 + Math.random() * 0.4,
                }}
              />
            ))}
          </div>
        )}

        {/* MIC BUTTON */}
        <button
          id="mic-toggle-btn"
          className={`mic-button-premium ${status === S.RECORDING ? 'pulsing recording' : ''} ${status === S.SPEAKING ? 'speaking' : ''}`}
          onClick={handleMicClick}
          disabled={status === S.PROCESSING}
          aria-label={status === S.RECORDING ? 'Mic band karein' : 'Bolna shuru karein'}
        >
          {status === S.RECORDING  ? <Square size={30} fill="white" /> :
           status === S.PROCESSING ? <Loader className="spin" size={28} /> :
           status === S.SPEAKING   ? <Volume2 size={28} className="wave-icon" /> :
                                     <Mic size={32} />}
        </button>

        <p className="status-text">
          {status === S.RECORDING  ? '🔴 रिकॉर्डिंग — बंद करने के लिए दोबारा दबाएं' :
           status === S.PROCESSING ? '⚙️ AI जवाब तैयार कर रहा है...' :
           status === S.SPEAKING   ? '🔊 AI बोल रहा है...' :
                                     '🎙️ बोलने के लिए दबाएं'}
        </p>

        {/* Controls row */}
        <div className="voice-controls-row">
          {/* Image upload */}
          <label className="image-upload-btn" id="image-upload-label">
            <ImageIcon size={18} />
            <span>{imgPreview ? 'फोटो बदलें' : 'फसल की फोटो'}</span>
            <input type="file" accept="image/*" onChange={handleImage} hidden />
          </label>

          {/* Language dropdown */}
          <div className="lang-selector-wrapper">
            <select
              id="language-selector"
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="voice-lang-select"
            >
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ── App Intro Audio ── */}
      <div className="intro-audio-card">
        <h3>🎧 नए यूज़र्स यहाँ सुनें: यह ऐप क्या करता है?</h3>
        <div className="intro-audio-controls">
          <button 
            onClick={handlePlayIntro} 
            disabled={isIntroLoading}
            className={`play-intro-btn ${isPlayingIntro ? 'playing' : ''} ${isIntroLoading ? 'loading' : ''}`}
            style={{ opacity: isIntroLoading ? 0.7 : 1 }}
          >
            {isIntroLoading ? <Loader size={18} className="spin" color="white" /> :
             isPlayingIntro ? <Square size={18} fill="white" /> : <Play size={18} fill="white" />}
            {isIntroLoading ? 'तैयार कर रहा है...' : isPlayingIntro ? 'रोकें' : 'सुनें'}
          </button>
          
          <div className="lang-selector-wrapper" style={{ flex: 'none', width: '180px' }}>
            <select
              value={introLang}
              onChange={(e) => {
                setIntroLang(e.target.value)
                if (isPlayingIntro) {
                  introAudioRef.current.pause();
                  setIsPlayingIntro(false);
                }
              }}
              className="voice-lang-select"
            >
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Floating Decorative Badges (Desktop Only) */}
      <div className="floating-badge badge-left-top glass-card">
        <span className="badge-icon">🌦️</span>
        <div className="badge-text">
          <span className="badge-title">Mausam Alert</span>
          <span className="badge-status">Delhi NCR • Safe</span>
        </div>
      </div>

      <div className="floating-badge badge-left-bottom glass-card">
        <span className="badge-icon">🌾</span>
        <div className="badge-text">
          <span className="badge-title">Live Mandi Bhav</span>
          <span className="badge-status">Gehu: ₹2,400/Q</span>
        </div>
      </div>

      <div className="floating-badge badge-right-top glass-card">
        <span className="badge-icon">🛡️</span>
        <div className="badge-text">
          <span className="badge-title">Crop Diagnosis</span>
          <span className="badge-status">100% Secure</span>
        </div>
      </div>

      <div className="floating-badge badge-right-bottom glass-card">
        <span className="badge-icon">🤖</span>
        <div className="badge-text">
          <span className="badge-title">Sarvam Voice AI</span>
          <span className="badge-status">250ms Response</span>
        </div>
      </div>

    </div>
  )
}

// Helper to extract a warm, concise voice summary from a long response
function getVoiceSummary(text, lang) {
  if (!text) return "";
  if (text.length <= 250) return text;
  
  // If it has multiple paragraphs, let's take the first paragraph!
  const paragraphs = text.split(/\n+/);
  if (paragraphs.length > 0) {
    const firstPara = paragraphs[0].trim();
    if (firstPara.length >= 40 && firstPara.length <= 400) {
      return firstPara;
    }
  }
  
  // Otherwise, split by sentence delimiters: '।' (Hindi/Punjabi/Odia/etc) or '.' (English/others)
  const delimiter = (lang === 'hi-IN' || lang === 'pa-IN' || lang === 'bn-IN') ? '।' : '.';
  const sentences = text.split(delimiter);
  
  let summary = "";
  for (let s of sentences) {
    const cleaned = s.trim();
    if (!cleaned) continue;
    if ((summary + cleaned).length <= 250) {
      summary += (summary ? " " : "") + cleaned + delimiter;
    } else {
      break;
    }
  }
  
  return summary.trim() || text.substring(0, 200) + "...";
}

// Helper to split a long text into clean sentence & clause chunks under 120 characters for sequential TTS playback
function splitTextIntoChunks(text, lang) {
  if (!text) return [];
  
  // Clean markdown syntax (*, #, _, -) so TTS reads it perfectly smoothly without speaking punctuation
  const cleanText = text.replace(/[\*\#\-\_\:]/g, " ").replace(/\s+/g, " ").trim();
  
  // Split by primary sentence delimiters: '।' (Hindi/Punjabi/Odia/Assamese/Bengali) or '.' or '?' or '!'
  const sentences = cleanText.split(/([।\.\?\!])/g);
  
  const rawSentences = [];
  for (let i = 0; i < sentences.length; i += 2) {
    const s = sentences[i]?.trim();
    const delim = sentences[i+1] || "";
    if (s) {
      rawSentences.push(s + delim);
    }
  }
  
  const finalSegments = [];
  
  // Further split any raw sentence that is too long (>= 450 chars) to prevent TTS limits
  for (let sentence of rawSentences) {
    if (sentence.length < 450) {
      finalSegments.push(sentence);
    } else {
      // Split by clause punctuation (commas, semicolons, dashes)
      const clauses = sentence.split(/([\,\;\，\、])/g);
      let currentSubChunk = "";
      
      for (let j = 0; j < clauses.length; j += 2) {
        const clause = clauses[j]?.trim();
        const punct = clauses[j+1] || "";
        if (!clause) continue;
        
        const fullClause = clause + punct;
        if ((currentSubChunk + fullClause).length < 450) {
          currentSubChunk += (currentSubChunk ? " " : "") + fullClause;
        } else {
          if (currentSubChunk) finalSegments.push(currentSubChunk.trim());
          
          // If a single clause is still too long, split by spaces
          if (fullClause.length >= 450) {
            const words = fullClause.split(/\s+/);
            let wordChunk = "";
            for (let word of words) {
              if ((wordChunk + word).length < 400) {
                wordChunk += (wordChunk ? " " : "") + word;
              } else {
                if (wordChunk) finalSegments.push(wordChunk.trim());
                wordChunk = word;
              }
            }
            currentSubChunk = wordChunk;
          } else {
            currentSubChunk = fullClause;
          }
        }
      }
      if (currentSubChunk) {
        finalSegments.push(currentSubChunk.trim());
      }
    }
  }
  
  // Group small segments together so they aren't TOO short (keep chunks around 350-450 chars)
  const chunks = [];
  let currentChunk = "";
  
  for (let segment of finalSegments) {
    if ((currentChunk + segment).length < 450) {
      currentChunk += (currentChunk ? " " : "") + segment;
    } else {
      if (currentChunk) chunks.push(currentChunk.trim());
      currentChunk = segment;
    }
  }
  if (currentChunk) {
    chunks.push(currentChunk.trim());
  }
  
  return chunks;
}
