import sys

# Force UTF-8 stdout/stderr so Gujarati text and emoji in logs never crash
# the server on Windows consoles/terminals that default to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import router

# Load environment variables from .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="VoiceForBharat - Arogya Sathi (Health Access) 🩺",
    description=(
        "Day 2 - #VoiceForBharat, Health Access track. 'Arogya Sathi' is a "
        "Gujarati-speaking AI health-access voice companion built with Murf "
        "Falcon 2 TTS and Gemini. She has a job (understand a health concern "
        "and point the caller to the right next step) and hard limits (never "
        "diagnose, never name a medicine, always escalate red-flag symptoms "
        "to a doctor). She is not a doctor and does not replace one."
    ),
    version="2.0.0",
)

# Allow frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from Live Server (port 5500/5501) or any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)

# Run app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)