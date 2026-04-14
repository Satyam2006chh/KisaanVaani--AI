# 🌾 KisaanVaani AI

> **Voice-First AI Assistant for Indian Farmers** — Bolo, Samjho, Badlo Apni Zindagi

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-ff6b35)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-f76707)](https://groq.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-Voice-22c55e)](https://sarvam.ai)

---

## 🎯 Problem

India ke 600M+ farmers:
- English nahi jaante
- Complex govt websites navigate nahi kar paate  
- PM Kisan, PMFBY jaise schemes miss ho jaate hain
- Scam ka shikar ho jaate hain

## 💡 Solution

**Farmer bolega → AI samjhega → Voice mein jawab milega**

No typing. No English. Pure voice-based system in 11 Indian languages.

---

## 🏗️ Architecture

```
React (Voice UI) → FastAPI → LangGraph Agent → Groq LLaMA 3.3
                                   ├── Scheme RAG (FAISS)
                                   ├── Weather (OpenWeatherMap)
                                   ├── Mandi Price (data.gov.in)
                                   └── Crop Advisor (LLM)
                          → Sarvam AI (STT + TTS Hindi/Punjabi)
                          → MongoDB (Chat History)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| AI Agent | LangGraph + LangChain |
| LLM | Groq (LLaMA-3.3-70B) |
| Voice STT/TTS | Sarvam AI (11 Indian Languages) |
| Embeddings | Sentence Transformers (multilingual) |
| Vector DB | FAISS |
| Scraping | Firecrawl |
| Database | MongoDB Atlas |

---

## 🔑 Required API Keys

Create a `.env` file in `/backend` using `.env.example` as template:

| Key | Get From | Free Tier |
|-----|---------|----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Yes |
| `SARVAM_API_KEY` | [sarvam.ai](https://sarvam.ai) | ✅ Free credits |
| `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) | ✅ 500 pages/month |
| `OPENWEATHER_API_KEY` | [openweathermap.org](https://openweathermap.org/api) | ✅ 1M/month |
| `MONGODB_URI` | [MongoDB Atlas](https://cloud.mongodb.com) | ✅ 512MB free |
| `DATA_GOV_API_KEY` | [data.gov.in](https://data.gov.in) | ✅ Free |

---

## 🚀 Getting Started

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Fill in your API keys
uvicorn app.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

---

## 📁 Project Structure

```
KisaanVaani--AI/
├── frontend/               # React + Vite
│   └── src/
│       └── components/
│           ├── Navbar/
│           ├── Hero/
│           ├── About/
│           ├── HowItWorks/
│           ├── Features/
│           ├── Languages/
│           ├── Quotes/
│           ├── TechStack/
│           └── Footer/
└── backend/                # FastAPI
    └── app/
        ├── main.py
        ├── config.py
        ├── routers/
        │   ├── voice.py    # Sarvam STT + TTS
        │   ├── agent.py    # LangGraph chat
        │   └── history.py  # MongoDB CRUD
        ├── agents/
        │   ├── graph.py    # LangGraph StateGraph
        │   └── tools.py    # Weather + Mandi tools
        ├── db/
        │   └── mongo.py
        └── models/
            └── schemas.py
```

---

## 🗣️ How It Works

1. **Farmer presses mic** → Browser records audio (MediaRecorder API)
2. **Audio → Sarvam STT** → Hindi/Punjabi text
3. **Text → LangGraph Agent** → Detects intent
4. **Agent routes to right tool:** RAG / Weather / Mandi / Crop Advisor
5. **Groq LLM generates Hindi answer**
6. **Answer → Sarvam TTS** → Audio plays back to farmer
7. **Chat saved** to MongoDB (with "Dobara Suno" replay support)

---

## 👨‍💻 Developer

Built with ❤️ for India's farmers.

**GitHub:** [Satyam2006chh](https://github.com/Satyam2006chh)
