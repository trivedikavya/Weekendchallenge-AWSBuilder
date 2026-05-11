# Improv AI Coach 🎭

Improv AI Coach is a voice-driven roleplay application designed to help users practice the art of improvisation. The agent acts as both a scene partner and a coach, guiding users through various scenarios (e.g., Space Station Emergency, Victorian Tea Party) while enforcing the "Yes, And..." rule of improv. At the end of each session, the AI provides a constructive "Coach Review" of the user's performance.

## 🚀 Features

* **Dynamic Scenarios**: Randomly selects from a library of unique improv scenarios, such as "Supermarket Confrontation" or "Space Station Emergency," to keep practices fresh.
* **"Yes, And..." Logic**: The AI is programmed to follow core improv principles, accepting the user's reality and expanding upon it to build a collaborative story.
* **Voice-to-Voice Roleplay**: Uses **AssemblyAI** for real-time speech transcription and **Murf AI** (using the professional "Marcus" voice) for dramatic, in-character narration.
* **Performance Evaluation**: After 4-5 exchanges, the agent concludes the scene and provides a "Coach Review," assessing the user's ability to stay in character and build the scene.
* **Immersive Theater UI**: Features a stage-themed frontend with live feedback indicators for the current scenario and performance notes.

## 🛠️ Tech Stack

### Backend

* **Framework**: FastAPI.
* **AI Engine**: Google Gemini 2.0 Flash (acting as both Scene Partner and Coach).
* **STT**: AssemblyAI (High-accuracy speech transcription).
* **TTS**: Murf AI (Professional "Marcus" voice in "Promo" style).
* **Dependencies**: `python-dotenv`, `requests`, `python-multipart`.

### Frontend

* **UI**: HTML5 and Tailwind CSS with a theatrical, dark-themed aesthetic.
* **State Management**: Vanilla JavaScript (ES Modules) using Axios for backend communication.
* **Audio**: Web MediaRecorder API for capturing user vocal performances.

## 📂 Project Structure

```text
├── backend/
│   ├── main.py              # FastAPI server and CORS configuration
│   ├── routes.py            # Improv logic, scenario handling, and AI gates
│   ├── improv_scenarios.json # Library of roleplay prompts and objectives
│   ├── requirement.txt      # Python dependencies
│   └── models.py            # Data schemas
├── frontend/
│   ├── index.html           # Theater-themed dashboard
│   ├── index.js             # Voice recording and performance tracking logic
│   └── package.json         # Frontend dependencies
└── .env                     # API keys (Google, AssemblyAI, Murf)

```

## ⚙️ Setup & Installation

### Backend

1. Navigate to the `backend` directory.
2. Install required packages:
```bash
pip install -r requirement.txt

```


3. Configure your `.env` file with the necessary API keys:
```env
GOOGLE_API_KEY=your_gemini_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
MURF_AI_API_KEY=your_murf_key

```


4. Launch the server:
```bash
python main.py

```



### Frontend

1. Navigate to the `frontend` directory.
2. Install Axios:
```bash
npm install

```


3. Open `index.html` via a local development server (e.g., Live Server).

## 📖 How to Practice

1. **Enter Stage**: Click "Enter Stage" to initialize the neural link and receive your scenario assignment.
2. **Act Out**: Use the microphone button to respond to the AI's prompts in character. Remember to "Yes, And..." the situation!.
3. **Monitor Performance**: Watch the "Coach's Notes" panel update as the AI observes your improv skills.
4. **Receive Review**: Once the scene reaches its natural conclusion, listen to the AI's final evaluation of your performance.
