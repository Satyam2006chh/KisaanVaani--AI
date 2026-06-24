<p align="center">
  <img src="frontend/public/logo.png" alt="KisaanVaani Logo" width="150" style="border-radius: 20px; box-shadow: 0 0 20px rgba(0, 240, 255, 0.5);"/>
</p>

<h1 align="center">🌾 KisaanVaani — AI Voice Assistant for Indian Farmers</h1>

<p align="center">
  <b>Empowering 150M+ Indian farmers with a Seamless Voice-First AI — featuring Real-Time Hybrid Scrapers, Multi-Model Cascades, and Context-Aware Intelligence.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Sarvam_AI-Voice-ff6b6b?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/OpenRouter-LLM-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Firecrawl-Scraper-black?style=for-the-badge"/>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [API Endpoints](#-api-endpoints)
- [How It Works (Mermaid Flow)](#-how-it-works)
- [Node Deep-Dives](#-node-deep-dives)
- [Supported Languages](#-supported-languages)
- [Team](#-team)

---

## 🎯 Overview

**KisaanVaani** is a state-of-the-art, voice-first AI assistant designed specifically for Indian farmers. Wrapped in a stunning **Premium Dark Electric Blue Theme**, it provides immediate, real-time agricultural intelligence. Instead of typing, farmers simply **speak** their questions in their native language and receive **spoken answers**. 

> *"Agar kisan bol sakta hai, toh KisaanVaani samajh sakta hai."*
> — If a farmer can speak, KisaanVaani can understand.

### 🚀 Problem Statement
- **70% of Indian farmers** cannot easily navigate text-based apps
- Weather, market prices, and government schemes are scattered and often outdated
- Language barriers prevent access to expert agricultural advice

### 💡 Our Solution
A **single voice command** gives farmers instant access to:
- 🌤️ **Real-time weather** forecasts for their district
- 📊 **Hybrid Mandi Prices** (Official Agmarknet + Live Firecrawl AI Scraper)
- 🌱 **Expert crop disease diagnosis** via photo upload (OpenRouter Vision Cascade)
- 📜 **Government schemes** eligibility & registration help
- 🗣️ All seamlessly delivered with **uninterrupted audio streaming**

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Seamless Voice-First UI** | Speak naturally. Audio streaming supports immediate interruption & smart caching. |
| 🌐 **11 Indian Languages** | Hindi, Punjabi, Bengali, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Odia, Assamese. |
| 🌤️ **Live Weather** | Real-time forecasts using Open-Meteo API. |
| 📈 **Hybrid Mandi Engine** | Fuses *data.gov.in* base prices with **Firecrawl Live Web Scraping** for 100% free, real-time rates. |
| 📸 **Crop Disease Detection** | Upload a photo → AI identifies disease + treatment via OpenRouter Vision Cascade. |
| 🧠 **Context-Aware Logic** | AI automatically detects user's location from their profile if they don't mention a district in their voice query. |
| 🎨 **Premium UI/UX** | Dark Electric Blue theme, glassmorphism UI, audio visualizers, and zero-latency mic interactions. |
| 🔐 **OTP Authentication** | Secure phone-based login via Supabase. |

---

## 🔄 How It Works

```mermaid
graph TD
    A[🎙️ Farmer Speaks] --> B[Audio Recorded in Browser]
    B --> C[Sarvam AI: Speech-to-Text]
    C --> D[Text Translated to English]
    D --> E{🧠 Intent Router <br> OpenRouter: Gemini 2.5 Flash}
    
    E -->|Weather| F[🌤️ Open-Meteo API]
    E -->|Mandi Prices| G[📊 Agmarknet + Firecrawl Hybrid]
    E -->|Crop Disease| H[📸 Vision Node <br> OpenRouter: Gemini 2.5 Flash / GPT-4o]
    E -->|Govt Scheme| I[📜 News Node <br> Firecrawl Scraper]
    E -->|Crop Care| P[🌿 Crop Advice Node <br> OpenRouter: Gemini 2.5 Flash]
    E -->|General| J[💬 General Node <br> OpenRouter: Gemini 2.5 Flash]
    
    F --> K[AI Formats Answer in Regional Language <br> OpenRouter: Gemini 2.5 Flash]
    G --> K
    H --> K
    I --> K
    P --> K
    J --> K
    
    K --> M[Sarvam AI: Text-to-Speech]
    M --> N[🔊 Farmer Hears Seamless Audio]
    
    style A fill:#00f0ff,color:#000,stroke:#fff,stroke-width:2px
    style N fill:#00f0ff,color:#000,stroke:#fff,stroke-width:2px
    style E fill:#0f172a,stroke:#00f0ff,stroke-width:2px,color:#fff
```

---

## 🔍 Node Deep-Dives

Detailed architectural flows for how each core AI node processes information before returning it to the user.

### 🌤️ Weather Node
```mermaid
graph TD
    A[Farmer Asks: 'Aaj barish hogi?'] --> B[Intent Router routes to Weather Node]
    B --> C[Extract Location from Profile or Audio]
    C --> D[Fetch Lat/Lon using Open-Meteo Geocoding API]
    D --> E[Fetch 7-Day Forecast using Open-Meteo Weather API]
    E --> F[Send raw weather data to OpenRouter <br> Gemini 2.5 Flash]
    F --> G[Gemini generates regional audio-friendly response]
```

### 📊 Mandi Node
```mermaid
graph TD
    A[Farmer Asks: 'Lahsun ka rate?'] --> B[Intent Router routes to Mandi Node]
    B --> C[Extract Crop and Location]
    C --> D{Check Official Data}
    D -->|Agmarknet API| E[Get Base Govt Prices]
    D -->|Firecrawl AI Scraper| F[Scrape Live Market Websites]
    E --> G[Merge Data]
    F --> G
    G --> H[Send data to OpenRouter <br> Gemini 2.5 Flash]
    H --> I[Gemini generates regional audio-friendly response]
```

### 🌿 Crop Advice Node
```mermaid
graph TD
    A[Farmer Asks: 'Kapas me phool jhad rahe hai'] --> B[Intent Router routes to Crop Advice Node]
    B --> C[Format highly detailed Expert Agronomist System Prompt]
    C --> D[Send query directly to OpenRouter <br> Gemini 2.5 Flash]
    D --> E[Gemini generates expert advice with exact dosage/chemicals]
```

### 📜 News & Scheme Node
```mermaid
graph TD
    A[Farmer Asks: 'PM Kusum me subsidy kitni hai?'] --> B[Intent Router routes to News Node]
    B --> C[Firecrawl AI Search API]
    C --> D[Scrape live internet for latest scheme details & news]
    D --> E[Send raw scraped articles to OpenRouter <br> Gemini 2.5 Flash]
    E --> F[Gemini summarizes scheme eligibility and benefits]
```

### 📸 Vision Node (LLM Cascade)
```mermaid
graph TD
    A[Farmer uploads crop image] --> B[Direct route to Vision Node]
    B --> C[Send Base64 Image to OpenRouter]
    C --> D{Cascade Routing}
    D -->|Primary| E[Gemini 2.5 Flash Vision]
    D -->|Fallback if fail| F[GPT-4o Vision]
    E --> G[AI Diagnoses Disease and prescribes treatment]
    F --> G
```

---

## 🔧 Tech Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18** | UI Framework |
| **Vite** | Build Tool & Dev Server |
| **Lucide React** | Icon Library |
| **Vanilla CSS** | Premium Dark Glassmorphism Styling |
| **Web Audio API** | Real-time mic recording & visualizers |

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | REST API Server |
| **LangGraph** | AI Agent Orchestration |
| **OpenRouter (Cascade)** | Premium Text & Vision Models |
| **Sarvam AI** | Speech-to-Text & Text-to-Speech |
| **Open-Meteo** | Weather Forecasts |
| **data.gov.in** | Baseline Mandi Price Data |
| **Firecrawl** | Real-Time Web Scraping for Live Mandi Rates & Schemes |
| **Supabase** | Database & Authentication |

---

## ⚡ Setup & Installation

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **npm** or **yarn**

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Satyam2006chh/KisaanVaani--AI.git
cd KisaanVaani--AI
```

### 2️⃣ Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables
Create `backend/.env`:
```env
OPENROUTER_API_KEY=your_openrouter_key
SARVAM_API_KEY=your_sarvam_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
DATAGOV_API_KEY=your_datagov_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

### 4️⃣ Fast Start (Windows)
Instead of starting the backend and frontend manually in separate terminals, we have provided a 1-click fast start script!

Run this in your PowerShell terminal at the root of the project:
```powershell
.\run.ps1
```
This will automatically:
1. Clear any stuck ports (8000, 5174)
2. Open a new terminal and start the FastAPI Backend
3. Open a new terminal and start the React Frontend

### 5️⃣ Open in Browser
```
http://localhost:5174
```

---

## 🛡️ Security

- 🔐 **OTP-based authentication** — No passwords stored
- 🔑 **API keys stored in `.env`** — Never committed to git
- 🛡️ **CORS protection** — Only allowed origins can access APIs
- 📝 **Input sanitization** — All user inputs are validated

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Speech-to-Text Latency | ~1.5s |
| AI Response Time | ~2-3s |
| Text-to-Speech Streaming | ~1s (Continuous background prefetch) |
| Total Round Trip | ~4-6s |

---

<p align="center">
  <b>🌾 KisaanVaani — Har Kisan Ki Awaaz, Har Sawaal Ka Jawaab 🌾</b>
  <br/>
  <i>Every Farmer's Voice, Every Question's Answer</i>
</p>
