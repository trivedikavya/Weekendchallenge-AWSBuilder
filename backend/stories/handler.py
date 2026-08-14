"""
Story Dice — /stories Lambda
Lists previously saved stories from DynamoDB, newest first.
Uses a simple Scan, which is fine for a small hobby-scale table.
"""
import json
import os

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "StoryDiceStories")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def _response(status, body_dict):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body_dict),
    }


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {})

    try:
        result = table.scan()
        items = result.get("Items", [])

        # Paginate through any remaining results (only relevant once the
        # table grows beyond ~1MB of data, but included for correctness).
        while "LastEvaluatedKey" in result:
            result = table.scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            items.extend(result.get("Items", []))

        items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        return _response(200, {"stories": items})
    except Exception as exc:  # pragma: no cover - defensive
        print(f"DynamoDB scan error: {exc}")
        return _response(
            500, {"error": "Couldn't load saved stories right now. Please try again."}
        )
