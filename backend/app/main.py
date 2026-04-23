from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, voice, agent, history

app = FastAPI(
    title="KisaanVaani AI API",
    description="Voice-based AI assistant for Indian farmers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(voice.router)
app.include_router(agent.router)
app.include_router(history.router)


@app.get("/")
async def root():
    return {"message": "KisaanVaani AI Backend Running 🌾", "status": "healthy"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

