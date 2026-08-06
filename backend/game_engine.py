import json

# Day 1 - #VoiceForBharat
# Simple flow: Diya asks the user's name, the user answers, Diya greets them by
# name and signs off with "Jay Shri Krishna" + a "see you on Day 2" line, in
# Gujarati (gu-IN) speech via Murf Falcon 2.

def get_initial_state():
    return {
        "phase": "intro",
        "player_name": ""
    }

def get_system_prompt(state, user_text):
    phase = state.get("phase", "intro")

    # CRITICAL INSTRUCTION: Forces Gemini to output Gujarati
    lang_instruction = "CRITICAL: You are Diya, an AI voice agent built for India. You MUST write the 'reply' value entirely in the Gujarati language using the Gujarati script (ગુજરાતી). Never use English in the 'reply' output."

    if phase == "intro":
        return f"""
        You are Diya, a warm and friendly AI voice host.
        {lang_instruction}

        The user just told you their name in this speech input: "{user_text}"

        GOAL:
        1. Extract ONLY their first name from the input.
        2. Reply with a short, warm message (1-2 lines) in Gujarati that:
           - Greets them by their name.
           - Says "જય શ્રી કૃષ્ણ" (Jay Shri Krishna).
           - Tells them you will meet them again on "ડે 2" (Day 2).
        This reply is the FINAL message of today's session.

        OUTPUT JSON:
        {{
            "reply": "(Your warm Gujarati reply greeting them by name, saying 'જય શ્રી કૃષ્ણ', and mentioning you'll meet on Day 2)",
            "player_name": "extracted_first_name",
            "next_phase": "ended"
        }}
        """

    elif phase == "ended":
        return f"""
        {lang_instruction}
        Today's session has already ended. The user said: "{user_text}"
        Politely (in one short line) remind them in Gujarati that Day 1 is complete
        and that you'll meet again on Day 2. Include "જય શ્રી કૃષ્ણ".

        OUTPUT JSON:
        {{
            "reply": "જય શ્રી કૃષ્ણ! આજનું સેશન પૂરું થયું છે. આપણે ડે 2 પર મળીશું!",
            "next_phase": "ended"
        }}
        """

    return '{ "reply": "એરર આવી છે, કૃપા કરીને ફરી શરૂ કરો." }'
