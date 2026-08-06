from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
import os
import json
import base64
import asyncio
import websockets
import google.generativeai as genai
import assemblyai as aai
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from dotenv import load_dotenv
import game_engine 
import re
import traceback

load_dotenv()

router = APIRouter()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# gemini-1.5-flash is deprecated for this API key; gemini-flash-lite-latest is
# confirmed available and has free-tier quota.
model = genai.GenerativeModel('gemini-flash-lite-latest')

# Murf Falcon 2 - ultra-low-latency streaming TTS (required track TTS engine)
MURF_FALCON_WS_URL = "wss://global.api.murf.ai/v1/speech/stream-input"

async def generate_murf_speech(text):
    """Generates Gujarati speech using Murf's Falcon 2 model over WebSocket streaming.
    Falcon 2's "Diya" (Gujarati) voice is only available via the streaming API,
    not the legacy REST /v1/speech/generate (Gen2) endpoint."""
    if not text:
        return None

    MURF_API_KEY = os.getenv('MURF_AI_API_KEY')
    if not MURF_API_KEY:
        print("Murf API Error: MURF_AI_API_KEY is not set")
        return None

    # Clean text to prevent TTS errors
    clean_text = re.sub(r'[(){}\[\]]', '', text.replace("₹", " Rupees "))

    uri = (
        f"{MURF_FALCON_WS_URL}?api-key={MURF_API_KEY}&model=falcon-2"
        f"&sample_rate=44100&channel_type=MONO&format=MP3"
    )

    try:
        async with websockets.connect(uri, open_timeout=10) as ws:
            voice_config_msg = {
                "voice_config": {
                    "voiceId": "Diya",
                    "locale": "gu-IN",
                    "style": "Conversational",
                    "rate": 0,
                    "pitch": 0,
                    "variation": 1
                }
            }
            await ws.send(json.dumps(voice_config_msg))
            await ws.send(json.dumps({"text": clean_text, "end": True}))

            audio_bytes = b""
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(response)

                if "error" in data:
                    print(f"Murf Falcon Error: {data['error']}")
                    return None

                if "audio" in data:
                    audio_bytes += base64.b64decode(data["audio"])

                if data.get("final"):
                    break

            if not audio_bytes:
                return None

            encoded = base64.b64encode(audio_bytes).decode("utf-8")
            return f"data:audio/mpeg;base64,{encoded}"

    except Exception as e:
        print(f"TTS Generation Exception: {str(e)}")
        return None

@router.get("/health")
async def health_check():
    return HTMLResponse(content="<h1>VoiceForBharat Host Active 🎙️</h1>")

@router.post("/start-session")
async def start_session():
    initial_state = game_engine.get_initial_state()
    greeting = "નમસ્તે! હું તમારી એઆઈ હોસ્ટ દીયા છું. તમારું નામ શું છે?"
    audio_url = await generate_murf_speech(greeting)
    
    return JSONResponse(content={
        "text": greeting,
        "audioUrl": audio_url,
        "initial_state": initial_state 
    })

@router.post("/chat-with-voice")
async def chat_with_voice(file: UploadFile = File(...), current_state: str = Form(...)):
    try:
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        
        # 1. State Management
        try:
            state = json.loads(current_state)
            if not isinstance(state, dict) or "phase" not in state:
                state = game_engine.get_initial_state()
        except:
            state = game_engine.get_initial_state()

        # 2. Transcribe
        # AssemblyAI's Gujarati (gu) speech model transcribes phonetically but
        # renders output in Devanagari (Hindi) script, not native Gujarati
        # script — this is a known limitation for lower-resource Indic
        # languages. We force language_code="gu" for best phonetic accuracy,
        # then transliterate the Devanagari result into Gujarati script so
        # what's displayed/used matches the language the user actually spoke.
        audio_data = await file.read()
        stt_config = aai.TranscriptionConfig(
            language_code="gu",
            speech_model=aai.SpeechModel.universal
        )
        transcript = aai.Transcriber(config=stt_config).transcribe(audio_data)
        raw_text = transcript.text or ""
        user_text = transliterate(raw_text, sanscript.DEVANAGARI, sanscript.GUJARATI)
        print(f"🎤 User: {user_text}")

        # 3. Generate Content
        system_prompt = game_engine.get_system_prompt(state, user_text)
        
        if not system_prompt:
            reply_text = "માફ કરજો, મને સમજાયું નહીં. ચાલો ફરી શરૂ કરીએ."
            state = game_engine.get_initial_state()
        else:
            result = model.generate_content(
                system_prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            ai_response = json.loads(result.text)
            if isinstance(ai_response, list): ai_response = ai_response[0] if ai_response else {}
            
            reply_text = ai_response.get("reply", "ચાલો આગળ વધીએ.")
            
            # Update State
            if "player_name" in ai_response: state["player_name"] = ai_response["player_name"]
            state["phase"] = ai_response.get("next_phase", state["phase"])

        print(f"🎭 Host: {reply_text}")

        audio_url = await generate_murf_speech(reply_text)

        return {
            "ai_text": reply_text,
            "user_transcript": user_text,
            "audioUrl": audio_url,
            "updated_state": state
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})