from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice, agent, history

app = FastAPI(
    title="KisaanVaani AI API",
    description="Voice-based AI assistant backend for Indian farmers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(voice.router)
app.include_router(agent.router)
app.include_router(history.router)

@app.get("/")
async def root():
    return {"message": "KisaanVaani AI Backend Running 🌾", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
