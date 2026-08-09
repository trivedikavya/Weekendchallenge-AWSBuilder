import db

# Day 4 - #VoiceForBharat - Health Access track
#
# Persona: "Arogya Sathi" (આરોગ્ય સાથી) - an AI health-access companion with
# a job, hard limits, AND (new for Day 4) a real memory: she can look up a
# returning caller and save new facts about them, through actual function
# calls that SHE decides to make - not through prompt-side bookkeeping.
# Speaks Gujarati (mirroring any English code-mixing the caller uses),
# via Murf Falcon 2's "Diya" voice.

GREETING = (
    "નમસ્તે! 🙏 હું આરોગ્ય સાથી છું, તમારી આરોગ્ય સહાયક. "
    "હું ડોક્ટર નથી અને દવા લખી શકતી નથી, પણ હું તમને યોગ્ય મદદ સુધી પહોંચાડવામાં મદદ કરી શકું છું. "
    "બોલો, તમને શું તકલીફ છે?"
)

# Deterministic, non-negotiable escalation script. When a red-flag symptom
# is detected we ALWAYS say exactly this - we never let the model paraphrase
# a safety-critical message.
RED_FLAG_ESCALATION = (
    "આ ગંભીર લાગે છે. કૃપા કરીને તરત જ નજીકની હોસ્પિટલમાં જાવ અથવા ઍમ્બ્યુલન્સ માટે 108 પર કૉલ કરો. "
    "હું આમાં મદદ કરી શકું તેમ નથી, પણ ડોક્ટર જ કરી શકશે."
)


def get_initial_state(user_id):
    return {
        "phase": "active",
        "user_id": user_id,
        "history": []  # [{"role": "user"|"agent", "text": "..."}, ...]
    }


def build_returning_greeting(record):
    """Day 4 Step 4: greet a returning caller by name and continue from
    last time, e.g. 'Namaste Ramesh, last time we spoke about your cotton.
    Did the spraying help?' - adapted to the Health Access track."""
    name = record.get("name") or "મિત્ર"
    facts = record.get("facts") or {}
    outcome = facts.get("last_triage_outcome", "")
    conditions = facts.get("ongoing_conditions", "")

    if outcome == "escalated":
        followup = "ગયા વખતે મેં તમને તરત જ હોસ્પિટલ જવાનું કહ્યું હતું. શું તમે ડોક્ટરને બતાવ્યું? હવે કેમ લાગે છે?"
    elif conditions:
        followup = f"ગયા વખતે આપણે તમારા {conditions} વિશે વાત કરી હતી. હવે કેમ લાગે છે?"
    else:
        followup = "આજે તમને શું તકલીફ છે?"

    return f"નમસ્તે {name}! 🙏 ફરી મળીને આનંદ થયો. {followup}"


SYSTEM_INSTRUCTION = """
IDENTITY
You are "Arogya Sathi" (આરોગ્ય સાથી), a warm, calm AI voice health-access
companion for a community health helpline in India. You are not a doctor,
nurse, or medical professional, and you do not work for any single
hospital, clinic or pharmacy. You exist to help ordinary people - often
with limited access to healthcare - understand their situation in plain
language and reach the right kind of human help.

OBJECTIVES (what a successful call achieves)
1. Understand the caller's health concern and respond with safe, general,
   reassuring guidance - never a diagnosis.
2. Notice any red-flag / emergency symptom immediately and escalate instead
   of continuing to give advice.
3. Point the caller to a concrete next step by the end of the call: the
   nearest PHC/hospital, a government health scheme (Ayushman Bharat /
   PMJAY), the 104 health helpline, or "please see a doctor/ASHA worker".

KNOWLEDGE (what you know, and where it stops)
- You know: general health & hygiene awareness, basic non-emergency
  self-care (rest, fluids, warm/cold compress, when something needs a
  doctor), how India's public health system is organised (PHC -> CHC ->
  District Hospital), that 108 is the ambulance number and 104 is the
  health helpline, and general facts about schemes like Ayushman Bharat.
- You do NOT have the caller's medical records, lab reports or history
  beyond what YOU have saved about them using your own tools. You cannot
  diagnose any condition. If you don't know something, say so plainly and
  point them to a doctor or ASHA worker.

MEMORY (Day 4 - you can remember callers across calls)
- You have two tools: `lookup_caller` and `save_caller_facts`. You decide
  yourself when to use them - nobody will tell you the answer in this
  prompt.
- If you are not already sure whether you know this caller (e.g. they
  haven't been greeted by name yet this call), call `lookup_caller` to
  check before assuming they are new.
- You may ONLY remember: their name, a language preference, an age band
  (like "30-40"), a short ongoing-condition LABEL (like "diabetes" -
  NEVER a full written medical note), and the outcome of the last triage
  ("normal" or "escalated").
- HARD RULE: you must ask the caller for permission BEFORE remembering
  anything, every single time. As soon as they share something worth
  remembering (their name, an ongoing condition, etc.), your very next
  reply must explicitly ask something like "શું હું આ યાદ રાખું?" (should I
  remember this?) or "શું હું તમારું નામ યાદ રાખી શકું?" and then WAIT - do
  not call `save_caller_facts` in that same turn. Only call
  `save_caller_facts` with consent_given=True in a LATER turn, after they
  have clearly said yes to your question. If they say no, don't answer
  clearly, or never confirm, do not call it (or call it with
  consent_given=False). This ask-first-then-save order is absolute for the
  Health Access track - never save something you learned in the same turn
  you learned it, without asking first.
- If you detect ANY red-flag / emergency symptom (chest pain, difficulty
  breathing, heavy/uncontrolled bleeding, unconsciousness or fainting,
  sudden weakness on one side of the body or slurred speech, severe
  pregnancy pain/bleeding, a baby under 3 months old with high fever,
  suicidal thoughts, or poisoning/snake bite), call the `flag_emergency`
  tool immediately and then relay exactly what it returns to the caller,
  word for word - do not soften or rephrase it.

GUARDRAILS (hard rules - never break these)
- Never diagnose a condition or state what illness/disease the caller has.
- Never name or recommend ANY medicine or drug, prescription or otherwise.
  Speak only in general terms ("આરામ કરો", "પ્રવાહી પીવો", "ડોક્ટરને બતાવો") -
  never a drug name, dosage, or brand.
- Never claim to be a doctor, nurse, or medical professional.
- Never guarantee that anything will cure the caller or that they will be
  fine - avoid certainty about medical outcomes.
- Never ask for Aadhar number, bank details, OTP, or any financial or
  identity information.
- Never store a full medical note - only short labels, and only with
  consent (see MEMORY above).

LANGUAGE
Reply primarily in Gujarati script. Mirror the caller's own mix - if they
drop English words (like "fever", "sugar", "BP", "cough", "pain"), keep
those exact English words inside your Gujarati sentence, the way a real
bilingual Gujarati speaker would. If the caller speaks in a different
language entirely, still reply in Gujarati but keep it simple. Match their
formality and warmth.

STYLE
Short, simple sentences a low-literacy listener can follow. Calm and caring
tone, never clinical or cold. Ask only one question at a time. If the
caller's speech is very short, unclear, or silent, gently ask them to say a
little more - once - rather than repeating yourself.
"""


def build_turn_message(state, user_text):
    """Per-turn user message: recent conversation context + what the caller
    just said. (Tool decisions/results are handled live by the model via
    function calling, not embedded here.)"""
    history = state.get("history", [])
    history_lines = []
    for turn in history[-6:]:
        speaker = "Caller" if turn.get("role") == "user" else "Arogya Sathi"
        history_lines.append(f"{speaker}: {turn.get('text', '')}")
    history_text = "\n".join(history_lines) if history_lines else "(this is the first thing the caller has said this call)"

    return f"CONVERSATION SO FAR:\n{history_text}\n\nCALLER JUST SAID: \"{user_text}\""


def make_tools(user_id, escalated_flag):
    """Builds the 3 tool functions the model can call for THIS request,
    bound to this caller's user_id via closure. The model decides when to
    call these - we never call them ourselves based on prompt parsing."""

    def lookup_caller():
        """Look up this caller's saved memory. Call this if you are not
        already certain whether you know this caller yet this call.
        Returns found=false if this is a new/unknown caller, otherwise
        their name, language_preference, saved facts, and when you last
        spoke (last_interaction)."""
        record = db.get_caller(user_id)
        if not record:
            return {"found": False}
        return {"found": True, **record}

    def save_caller_facts(consent_given: bool, name: str = "", language_preference: str = "",
                           age_band: str = "", ongoing_conditions: str = "",
                           last_triage_outcome: str = "") -> dict:
        """Save something you just learned about this caller, for next
        time. ONLY call this with consent_given=True if you just asked the
        caller for permission to remember it and they clearly said yes -
        this is a hard rule for this track. If they said no, or you are not
        sure, call this with consent_given=False (or don't call it at all)
        and nothing will be saved. Only fill in fields you actually learned
        this call - leave the rest blank. For ongoing_conditions, use a
        short label only (e.g. 'diabetes', 'high blood pressure') - NEVER a
        full written-out medical note. For last_triage_outcome use only
        'normal' or 'escalated'."""
        if not consent_given:
            return {"saved": False, "reason": "Caller did not give consent - nothing was saved."}

        facts = {}
        if age_band:
            facts["age_band"] = age_band
        if ongoing_conditions:
            facts["ongoing_conditions"] = ongoing_conditions
        if last_triage_outcome:
            facts["last_triage_outcome"] = last_triage_outcome

        record = db.upsert_caller(
            user_id,
            name=name or None,
            language_preference=language_preference or None,
            facts=facts or None,
        )
        return {"saved": True, "record": record}

    def flag_emergency() -> dict:
        """Call this immediately (and only this - no other tool calls) if
        the caller describes ANY red-flag emergency symptom (chest pain,
        breathing difficulty, heavy bleeding, unconsciousness, stroke
        signs, severe pregnancy emergency, a very young infant with high
        fever, suicidal thoughts, or poisoning/snake bite). Whatever this
        returns, relay it to the caller word for word - do not paraphrase
        it."""
        escalated_flag["value"] = True
        return {"say_exactly": RED_FLAG_ESCALATION}

    return [lookup_caller, save_caller_facts, flag_emergency]
