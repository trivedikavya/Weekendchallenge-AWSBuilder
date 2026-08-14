"""
Story Dice — /generate Lambda
Accepts the 4 rolled words as JSON and calls Amazon Bedrock (Nova Micro/Lite)
to write a short whimsical story. Uses the Bedrock "Converse" API, which
has the same request/response shape across all supported models.
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1"))
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

REQUIRED_FIELDS = ["place", "object", "trait", "twist"]


def _response(status, body_dict):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body_dict),
    }


def build_prompt(words):
    return (
        "Write a whimsical short story (150-200 words) for all ages using "
        "these elements: "
        f"Place: {words['place']}, Object: {words['object']}, "
        f"Character trait: {words['trait']}, Twist: {words['twist']}. "
        "Make it playful and imaginative. Only return the story text, "
        "with no title and no preamble."
    )


def handler(event, context):
    # Handle CORS preflight
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

    prompt = build_prompt(body)

    try:
        result = bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.8, "topP": 0.9},
        )
        story = result["output"]["message"]["content"][0]["text"].strip()
        return _response(200, {"story": story})

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        print(f"Bedrock ClientError: {exc}")

        if error_code == "AccessDeniedException":
            message = (
                "Story generation isn't available yet — this AWS account "
                "doesn't have access to the Bedrock model. Enable model "
                "access in the Bedrock console and try again."
            )
        elif error_code == "ThrottlingException":
            message = "Too many story requests right now — please wait a moment and try again."
        elif error_code == "ValidationException":
            message = "The story request was invalid. Please reroll and try again."
        else:
            message = "Our storyteller hit a snag. Please try again in a moment."

        return _response(502, {"error": message})

    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error: {exc}")
        return _response(
            500, {"error": "Something went wrong while writing your story. Please try again."}
        )
