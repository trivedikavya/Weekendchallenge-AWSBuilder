"""
Story Dice — /save Lambda
Saves a generated story + its 4 words to DynamoDB with a short
auto-generated ID and a timestamp.
"""
import json
import os
import random
import string
from datetime import datetime, timezone

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "StoryDiceStories")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

REQUIRED_FIELDS = ["place", "object", "trait", "twist", "story"]


def _response(status, body_dict):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body_dict),
    }


def _short_id(length=8):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {})

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body."})

    missing = [f for f in REQUIRED_FIELDS if not body.get(f)]
    if missing:
        return _response(
            400, {"error": f"Missing required field(s): {', '.join(missing)}"}
        )

    item = {
        "id": _short_id(),
        "place": body["place"],
        "object": body["object"],
        "trait": body["trait"],
        "twist": body["twist"],
        "story": body["story"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    try:
        table.put_item(Item=item)
        return _response(200, {"saved": True, "story": item})
    except Exception as exc:  # pragma: no cover - defensive
        print(f"DynamoDB put_item error: {exc}")
        return _response(
            500, {"error": "Couldn't save your story right now. Please try again."}
        )
