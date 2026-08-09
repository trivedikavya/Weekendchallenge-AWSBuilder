from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
import os
import json
import base64
import asyncio
import uuid
import websockets
import google.generativeai as genai
import assemblyai as aai
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from dotenv import load_dotenv
import health_agent
import db
import re
import traceback

load_dotenv()

router = APIRouter()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# gemini-1.5-flash is deprecated for this API key; gemini-flash-lite-latest is
# confirmed available and has free-tier quota. This model also supports
# function calling, which we rely on for Day 4's memory tools.
GEMINI_MODEL_NAME = "gemini-flash-lite-latest"
GEMINI_REQUEST_OPTIONS = {"timeout": 20}

db.init_db()

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
async def start_session(user_id: str = None):
    # Day 4 Step 4: greet returning callers by name and continue from last
    # time. `user_id` is a persistent ID the frontend keeps in localStorage
    # so the same browser = the same "caller" across separate calls/visits.
    caller_id = user_id or str(uuid.uuid4())
    record = db.get_caller(caller_id) if user_id else None

    initial_state = health_agent.get_initial_state(caller_id)

    if record and record.get("name"):
        greeting = health_agent.build_returning_greeting(record)
        db.touch_last_interaction(caller_id)
    else:
        greeting = health_agent.GREETING

    audio_url = await generate_murf_speech(greeting)

    return JSONResponse(content={
        "text": greeting,
        "audioUrl": audio_url,
        "initial_state": initial_state,
        "caller_id": caller_id
    })

@router.post("/chat-with-voice")
async def chat_with_voice(file: UploadFile = File(...), current_state: str = Form(...)):
    try:
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        
        # 1. State Management
        try:
            state = json.loads(current_state)
            if not isinstance(state, dict) or "history" not in state or "user_id" not in state:
                state = health_agent.get_initial_state(str(uuid.uuid4()))
        except:
            state = health_agent.get_initial_state(str(uuid.uuid4()))

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
        # Day 4: the model gets real tools (lookup_caller / save_caller_facts /
        # flag_emergency) bound to this caller's user_id, and decides itself
        # when to call them - we never parse memory decisions out of a JSON
        # prompt response.
        if not user_text.strip():
            reply_text = "માફ કરશો, મને સંભળાયું નહીં. શું તમે ફરી બોલી શકશો?"
            escalate = False
        else:
            user_id = state.get("user_id")
            escalated_flag = {"value": False}
            tools = health_agent.make_tools(user_id, escalated_flag)

            chat_model = genai.GenerativeModel(
                GEMINI_MODEL_NAME,
                tools=tools,
                system_instruction=health_agent.SYSTEM_INSTRUCTION
            )
            chat = chat_model.start_chat(enable_automatic_function_calling=True)
            turn_message = health_agent.build_turn_message(state, user_text)
            result = chat.send_message(turn_message, request_options=GEMINI_REQUEST_OPTIONS)

            escalate = escalated_flag["value"]

            # Guardrail: the emergency escalation script is deterministic and
            # is never left to the model to paraphrase.
            if escalate:
                reply_text = health_agent.RED_FLAG_ESCALATION
            else:
                reply_text = result.text.strip() if result.text else "માફ કરશો, ફરી કહેશો?"

            # Track conversation history for context in future turns
            state["history"].append({"role": "user", "text": user_text})
            state["history"].append({"role": "agent", "text": reply_text})

        print(f"🩺 Arogya Sathi: {reply_text}")

        audio_url = await generate_murf_speech(reply_text)

        return {
            "ai_text": reply_text,
            "user_transcript": user_text,
            "escalate": escalate,
            "audioUrl": audio_url,
            "updated_state": state
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})