# 🌾 KisaanVaani AI — Voice-First AI Assistant for Indian Farmers

---

## 📌 What is KisaanVaani?

KisaanVaani is a **voice-first AI assistant built specifically for Indian farmers**. Most farmers in rural India are not comfortable typing — they speak. KisaanVaani lets farmers **speak in their regional language** (Hindi, Punjabi, Bengali, Tamil, Telugu, and more) and get instant, accurate answers about:

- 🌦️ **Live weather** for their district
- 💰 **Mandi prices & MSP** (Minimum Support Price) for their crops
- 🌱 **Crop advice** based on their location and season
- 📋 **Government schemes** like PM Kisan, PMFBY, Kisan Credit Card, and more
- ✅ **Eligibility checks** for various agricultural schemes

The farmer speaks → the AI understands → the AI responds back in voice, in their own language. No typing. No English. No complexity.

---

## 🔄 How Does It Work — Full Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FARMER (Browser)                             │
│                                                                     │
│  1. Opens KisaanVaani web app                                       │
│  2. Logs in via Phone OTP                                           │
│  3. Presses mic button → speaks in Hindi/regional language          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Audio (WebM/WAV)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND — FastAPI                                 │
│                                                                     │
│  POST /api/voice/transcribe                                         │
│  └─► Sarvam AI STT (saarika:v2.5)                                  │
│       Converts speech → text in farmer's language                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Transcribed Text
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                                   │
│                                                                     │
│  POST /api/agent/chat                                               │
│                                                                     │
│  Step 1: intent_router                                              │
│  └─► Classifies query into one of 5 intents:                       │
│       • weather      → "mausam", "baarish", "rain"                 │
│       • mandi        → "bhav", "mandi", "price", "daam"            │
│       • crop_advice  → "fasal", "kheti", "ugao"                    │
│       • eligibility  → "eligible", "patrata", "apply"              │
│       • scheme       → everything else (default)                   │
│                                                                     │
│  Step 2: Route to correct node                                      │
│  ├─► weather_node    → Open-Meteo API (free, no key needed)        │
│  ├─► mandi_node      → Hardcoded Govt MSP 2024-25 data             │
│  ├─► crop_advice_node→ Groq LLM (Llama 3.3 70B)                   │
│  └─► llm_node        → Groq LLM (Llama 3.3 70B) for schemes/general│
│                                                                     │
│  Step 3: format_answer → Final response text                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Response Text
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VOICE RESPONSE                                    │
│                                                                     │
│  POST /api/voice/speak                                              │
│  └─► Sarvam AI TTS (bulbul:v2)                                     │
│       Converts text → speech in farmer's language                   │
│       Returns WAV audio stream                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Audio plays in browser
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA PERSISTENCE                                  │
│                                                                     │
│  MongoDB Atlas                                                      │
│  ├─► users collection    → farmer profile, language, district       │
│  └─► messages collection → full chat history per session            │
└─────────────────────────────────────────────────────────────────────┘
```

### Auth Flow
```
Farmer enters phone number
        │
        ▼
POST /api/auth/otp/send  →  OTP generated (123456 in dev)
        │
        ▼
POST /api/auth/otp/verify  →  JWT token returned (30 days)
        │
        ▼
All subsequent requests use Bearer token in Authorization header
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | REST API framework |
| **LangGraph** | Agentic AI workflow (intent routing + tool calling) |
| **Groq API** (Llama 3.3 70B) | LLM for scheme info, crop advice, eligibility |
| **Sarvam AI STT** (saarika:v2.5) | Speech-to-Text in 10+ Indian languages |
| **Sarvam AI TTS** (bulbul:v2) | Text-to-Speech in 10+ Indian languages |
| **Open-Meteo API** | Free real-time weather by district |
| **MongoDB Atlas** (Motor) | Async database for users & chat history |
| **PyJWT** | JWT-based authentication |
| **httpx** | Async HTTP client for external APIs |
| **Python 3.11+** | Runtime |

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI framework |
| **Vite** | Build tool |
| **React Router v7** | Client-side routing |
| **Axios** | HTTP requests to backend |
| **Lucide React** | Icons |
| **Web Audio API** | Browser mic recording (MediaRecorder) |

### Infrastructure & APIs
| Service | Purpose |
|---|---|
| **MongoDB Atlas** | Cloud database |
| **Groq Cloud** | Fast LLM inference |
| **Sarvam AI** | Indian language STT + TTS |
| **Open-Meteo** | Free weather API (no key needed) |

---

## 📡 API Endpoints

### 🔐 Auth — `/api/auth`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/otp/send` | Send OTP to farmer's phone number | ❌ |
| `POST` | `/api/auth/otp/verify` | Verify OTP, returns JWT token + user profile | ❌ |
| `GET` | `/api/auth/me` | Get current logged-in farmer's profile | ✅ Bearer |
| `POST` | `/api/auth/refresh` | Refresh JWT token | ✅ Bearer |

**OTP Send body:**
```json
{ "phone": "9876543210" }
```

**OTP Verify body:**
```json
{
  "phone": "9876543210",
  "otp": "123456",
  "name": "Ramesh Kumar",
  "language": "hi-IN",
  "district": "Ludhiana",
  "state": "Punjab"
}
```

---

### 🎙️ Voice — `/api/voice`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/voice/transcribe` | Upload audio file → get text transcript (Sarvam STT) | ❌ |
| `POST` | `/api/voice/speak` | Send text → get WAV audio back (Sarvam TTS) | ❌ |
| `GET` | `/api/voice/config-check` | Check if all API keys are configured | ❌ |

**Transcribe** — multipart form:
```
audio: <audio file (WebM/WAV)>
language: hi-IN
```

**Speak body:**
```json
{ "text": "Aaj gehun ka bhav 2275 rupaye per quintal hai.", "language": "hi-IN" }
```

Supported language codes: `hi-IN`, `pa-IN`, `bn-IN`, `ta-IN`, `te-IN`, `kn-IN`, `ml-IN`, `mr-IN`, `gu-IN`, `od-IN`, `en-IN`

---

### 🤖 Agent — `/api/agent`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/agent/chat` | Main AI chat — processes farmer query through LangGraph | ❌ |

**Chat body:**
```json
{
  "farmer_id": "9876543210",
  "session_id": "session_abc123",
  "message": "Aaj gehun ka mandi bhav kya hai?",
  "language": "hi-IN"
}
```

**Response:**
```json
{
  "response": "Ludhiana mein Gehun ke bhav: Sarkari MSP (2024-25): Rs 2275 per quintal...",
  "session_id": "session_abc123",
  "tool_used": "mandi"
}
```

`tool_used` values: `weather` | `mandi` | `crop_advice` | `eligibility` | `scheme`

---

### 📜 History — `/api/history`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/history/{farmer_id}` | Get last 50 messages for a farmer | ❌ |
| `GET` | `/api/history/{farmer_id}/session/{session_id}` | Get all messages for a specific session | ❌ |
| `DELETE` | `/api/history/{farmer_id}` | Clear all chat history for a farmer | ❌ |

---

## 🚀 Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (`.env`)
```
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
MONGODB_URI=your_mongodb_atlas_uri
SECRET_KEY=your_jwt_secret
APP_ENV=development
```

---

## 🌍 Supported Languages

Hindi • Punjabi • Bengali • Tamil • Telugu • Kannada • Malayalam • Marathi • Gujarati • Odia • English (Indian)
