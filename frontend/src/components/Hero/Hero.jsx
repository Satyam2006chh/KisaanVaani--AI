import { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, Square, Loader, AlertCircle, TrendingUp, Image as ImageIcon, X, Volume2 } from 'lucide-react'
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

  const mediaRecorderRef = useRef(null)
  const mediaStreamRef   = useRef(null)
  const chunksRef        = useRef([])
  const isRecordingRef   = useRef(false)
  const audioCtxRef      = useRef(null)
  const analyzerRef      = useRef(null)
  const animFrameRef     = useRef(null)
  const chatEndRef       = useRef(null)
  const audioRef         = useRef(new Audio()) 
  const queueActiveRef   = useRef(false) 
  const prefetchedUrls   = useRef({}) 

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
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
    
    // Reset conversation states for new question
    setTranscript('')
    setReply('')
    setChatHistory([])
    setError('')
    
    // Stop any currently playing audio immediately
    try {
      audioRef.current.pause()
      audioRef.current.src = "data:audio/wav;base64,UklGRigAAABXQVZFRm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAA=="
      audioRef.current.load()
    } catch (e) {
      console.warn('[Audio] Stop failed:', e)
    }

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
      // Set to a tiny silent WAV to unlock the context without replaying the old answer
      audioRef.current.src = "data:audio/wav;base64,UklGRigAAABXQVZFRm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAA=="
      audioRef.current.play().catch(() => {})
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
      setReply(aiText)
      // Add AI bubble
      setChatHistory(h => [...h, { role: 'ai', text: aiText }].slice(-MAX_DISPLAY_MSGS))
      setImg(null)
      setImgPreview(null)

      // Step 3: TTS — speak in selected language (split into sequential audio chunks to speak long responses flawlessly)
      try {
        const chunks = splitTextIntoChunks(aiText, selectedLang)
        prefetchedUrls.current = {} // Clear any old prefetch URLs
        if (chunks.length > 0) {
          queueActiveRef.current = true
          playAudioQueue(chunks, 0)
        } else {
          setStatus(S.IDLE)
        }
      } catch (ttsErr) {
        console.warn('[TTS] failed:', ttsErr)
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
    if (status === S.RECORDING) {
      stopRecording()
    } else if (status === S.SPEAKING) {
      queueActiveRef.current = false // Stop the audio queue
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
      }
      // Revoke all prefetched URLs to free browser memory
      Object.values(prefetchedUrls.current).forEach(url => {
        try { URL.revokeObjectURL(url) } catch (e) {}
      })
      prefetchedUrls.current = {}
      setStatus(S.IDLE)
    } else if (status === S.IDLE) {
      startRecording()
    }
  }


  return (
    <div className="hero-container">

      {/* ── Welcome ── */}
      <div className="welcome-msg">
        <h1>Namaste <span className="farmer-name">{user?.name || 'Kisaan'}</span> ji 🌾</h1>
        <p className="hero-subtitle">Mausam, Mandi, aur Fasal ki AI-powered jankari — sirf aapke liye.</p>
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
          <p className="img-hint">📸 Fasal ki photo AI analyze karegi</p>
        </div>
      )}

      {/* ── Active Conversation Area ── */}
      {(transcript || status === S.PROCESSING) && (
        <div className="active-chat-container">
          {/* User Side */}
          {transcript && (
            <div className="chat-bubble user-bubble active-bubble">
              <div className="chat-bubble-label">🎤 AAPNE KAHA</div>
              <p>{transcript}</p>
            </div>
          )}

          {/* AI Side */}
          {status === S.PROCESSING && (
            <div className="chat-bubble ai-bubble typing-bubble active-bubble">
              <div className="chat-bubble-label">AI Soch raha hai...</div>
              <div className="typing-dots"><span /><span /><span /></div>
            </div>
          )}

          {reply && status !== S.PROCESSING && (
            <div className="chat-bubble ai-bubble active-bubble response-highlight">
              <div className="chat-bubble-label">🤖 AI JAWAB</div>
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
          {status === S.RECORDING  ? '🔴 RECORDING — DOBARA DABAYEIN BAND KARNE KE LIYE' :
           status === S.PROCESSING ? '⚙️ AI JAWAB TAIYAAR KAR RAHA HAI...' :
           status === S.SPEAKING   ? '🔊 AI BOL RAHA HAI...' :
                                     '🎙️ BOLNE KE LIYE DABAYEIN'}
        </p>

        {/* Controls row */}
        <div className="voice-controls-row">
          {/* Image upload */}
          <label className="image-upload-btn" id="image-upload-label">
            <ImageIcon size={18} />
            <span>{imgPreview ? 'Photo Badlein' : 'Fasal ki Photo'}</span>
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

// Helper to split a long text into clean sentence chunks under 250 characters for sequential TTS playback
function splitTextIntoChunks(text, lang) {
  if (!text) return [];
  
  // Clean markdown syntax (*, #, _, -) so TTS reads it perfectly smoothly without speaking punctuation
  const cleanText = text.replace(/[\*\#\-\_]/g, " ").replace(/\s+/g, " ").trim();
  
  // Split by sentence delimiters: '।' (Hindi/Punjabi/Odia/Assamese) or '.' (English/others)
  const delimiter = (lang === 'hi-IN' || lang === 'pa-IN' || lang === 'bn-IN') ? '।' : '.';
  const sentences = cleanText.split(delimiter);
  
  const chunks = [];
  let currentChunk = "";
  
  for (let s of sentences) {
    const cleaned = s.trim();
    if (!cleaned) continue;
    
    if ((currentChunk + cleaned).length < 200) {
      currentChunk += (currentChunk ? " " : "") + cleaned + delimiter;
    } else {
      if (currentChunk) chunks.push(currentChunk.trim());
      currentChunk = cleaned + delimiter;
    }
  }
  
  if (currentChunk) {
    chunks.push(currentChunk.trim());
  }
  
  return chunks;
}
