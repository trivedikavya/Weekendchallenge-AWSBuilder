
# Arogya Sathi (આરોગ્ય સાથી) VoiceForBharat Day 4

Welcome to my Day 4 submission for the **10 Days of Voice Agents - #VoiceForBharat Edition** challenge!

For Day 4, the objective was to give the agent long-term memory. Arogya Sathi now recognizes returning callers, remembers context from previous sessions, and utilizes native LLM function calling—all while strictly adhering to data privacy and consent rules.

## Day 4 Upgrades: Memory, Tool Calling & Consent

Arogya Sathi has transitioned from a stateless bot to a context-aware assistant. Key architectural updates include:

*   **Persistent SQLite Database (`backend/db.py`):** A local `callers.db` safely stores `user_id`, `name`, `language_preference`, and specific `facts` (restricted strictly to `age_band`, `ongoing_conditions`, and `last_triage_outcome` to prevent logging full medical notes).
*   **Native Gemini Function Calling:** The agent autonomously executes 3 specific tools:
    *   `lookup_caller()`: Retrieves past facts upon connection.
    *   `save_caller_facts()`: Commits new facts to the DB.
    *   `flag_emergency()`: Preserved Day 2 escalation logic, now wired as a direct tool.
*   **Strict Health Privacy (Explicit Consent):** Before saving *any* information, the agent must proactively ask for user consent (e.g., "શું હું આ યાદ રાખું?"). If consent is denied, the function is bypassed and 0 rows are created.
*   **Frontend Identity Persistence:** `frontend/index.js` now stores a persistent `caller_id` in the browser's `localStorage` to simulate returning users seamlessly.

## Tech Stack

*   **Frontend:** HTML5, JavaScript, Tailwind CSS (with `localStorage` session handling)
*   **Backend:** Python, FastAPI, SQLite3
*   **Voice & LLM:** Murf AI (Model: GEN2, Voice: Diya, Locale: gu-IN), Google Gemini 1.5 Flash (with `enable_automatic_function_calling=True`)
*   **Speech-to-Text (STT):** AssemblyAI API

## Prerequisites

To run this project locally, you will need API keys for:
*   [Murf AI](https://murf.ai/)
*   [AssemblyAI](https://www.assemblyai.com/)
*   [Google Gemini](https://aistudio.google.com/)

## Local Setup Instructions

**1. Clone the repository**
```bash
git clone [https://github.com/Dharm3112/voice-for-bharat-MurfAI-Day-4.git](https://github.com/Dharm3112/voice-for-bharat-MurfAI-Day-4.git)
cd voice-for-bharat-MurfAI-Day-4
```

**2. Configure Environment Variables**
Ensure your `.env` file in the `backend` directory contains:

```env
MURF_AI_API_KEY=your_murf_api_key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GOOGLE_API_KEY=your_google_api_key

```

**3. Run the Backend & Frontend**

```bash
cd backend
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

pip install -r requirement.txt
python main.py

```

*(Note: The SQLite database `callers.db` will be auto-generated upon the first save action).*
Open `frontend/index.html` using Live Server to start interacting.

## Day 4 Test Scenarios (Demo Script)

To verify the memory and consent tools, perform the following sequence:

**Call 1: The Introduction & Consent**

1. **User:** "મારું નામ રમેશ છે અને મને ડાયાબિટીસ છે." (My name is Ramesh and I have diabetes.)
2. **Agent:** Responds with advice and asks, "શું હું આ માહિતી યાદ રાખું?" (May I remember this information?)
3. **User:** "હા, યાદ રાખો." (Yes, remember it.)
*(Agent triggers `save_caller_facts` and writes to SQLite)*.

**Call 2: The Contextual Greeting**

1. *Refresh the page and click 'Connect' again.*
2. **Agent Proactive Greeting:** "નમસ્તે રમેશ! ફરી મળીને આનંદ થયો. ગયા વખતે આપણે તમારા ડાયાબિટીસ વિશે વાત કરી હતી. હવે કેમ લાગે છે?" (Namaste Ramesh! Good to see you again. Last time we spoke about your diabetes. How are you feeling now?)

**Call 3: Refusing Consent**

1. *Clear your localStorage or use an incognito window.*
2. **User:** Tell the agent a symptom and your name.
3. **Agent:** Asks for consent.
4. **User:** "ના, યાદ ના રાખો." (No, do not remember.)
*(Check the DB: No record will be saved for this new user ID)*.

---

*Built for the 10 Days of Voice Agents Challenge by Murf AI.*
