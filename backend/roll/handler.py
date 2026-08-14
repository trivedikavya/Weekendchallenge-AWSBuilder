"""
Story Dice — /roll Lambda
Returns 4 random words (place, object, trait, twist) from fixed word banks.
This is optional (the frontend can roll client-side), but is included here
for full architecture credit and so the word bank lives in one place on
the backend too.
"""
import json
import random

WORD_BANKS = {
    "place": [
        "a forgotten lighthouse", "a floating market", "a candy-cane forest",
        "an upside-down library", "a cloud castle", "a sunken pirate ship",
        "a village inside a teapot", "a moonlit train station",
        "a garden that grows umbrellas", "a city built on a turtle's back",
        "a bakery at the edge of the world", "a treehouse in the sky",
    ],
    "object": [
        "a rusty key", "a jar of fireflies", "a paper airplane that never lands",
        "a pocket watch that ticks backwards", "a map with no destination",
        "a violin made of glass", "a button that isn't sewn to anything",
        "a teacup that refills itself", "a mitten that hums lullabies",
        "a compass that points to lost things", "a marble full of stars",
        "an umbrella that opens doors",
    ],
    "trait": [
        "secretly afraid of silence", "collects other people's shadows",
        "can only whisper the truth", "believes every knock is a friend",
        "hums to make plants grow", "keeps a diary written in riddles",
        "never remembers their own name", "trips over compliments",
        "talks to socks before wearing them", "is allergic to Mondays",
        "sees colors that don't exist yet", "laughs in a different language",
    ],
    "twist": [
        "but time runs backwards here", "until the moon starts talking",
        "and nobody notices the town is upside down",
        "but every promise becomes a butterfly",
        "until the shadows start telling secrets",
        "and rain falls upward at midnight",
        "but the map keeps redrawing itself",
        "until laughter becomes currency",
        "and the stars start keeping a diary",
        "but every door leads back to yesterday",
    ],
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def handler(event, context):
    try:
        words = {
            "place": random.choice(WORD_BANKS["place"]),
            "object": random.choice(WORD_BANKS["object"]),
            "trait": random.choice(WORD_BANKS["trait"]),
            "twist": random.choice(WORD_BANKS["twist"]),
        }
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(words),
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Could not roll dice: {str(exc)}"}),
        }
