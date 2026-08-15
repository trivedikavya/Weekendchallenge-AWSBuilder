# 🎲 Story Dice

A colorful, whimsical collaborative story generator. Roll 4 dice (Place,
Object, Trait, Twist), then let Amazon Bedrock (Nova Micro) turn them into a
150–200 word story. Save your favorites to DynamoDB and browse them later.

Everything in this repo is **already built and working in mock mode**. This
README walks you through turning on the real AWS backend, step by step, with
exact clicks/commands — no prior AWS experience assumed.

```
story-dice/
├── frontend/                 # Static site — HTML/CSS/JS, no build step
│   ├── index.html
│   ├── styles.css
│   ├── app.js                # All app logic (works in mock OR real mode)
│   └── config.js             # <-- flip ONE flag + paste ONE url here later
└── backend/
    ├── template.yaml         # AWS SAM template (API Gateway + 4 Lambdas + DynamoDB)
    ├── roll/handler.py        # GET  /roll      (optional, frontend can roll locally too)
    ├── generate/handler.py    # POST /generate   (calls Amazon Bedrock Nova Micro)
    ├── save/handler.py        # POST /save        (writes to DynamoDB)
    └── stories/handler.py     # GET  /stories     (reads from DynamoDB)
```

## How this was built 

1. ✅ **Frontend with mock data** — `frontend/` runs 100% standalone. Rolling,
   generating, saving and viewing stories all work with fake/local data
   because `config.js` has `USE_MOCK: true`.
2. ✅ **Lambda functions** — 4 Python handlers in `backend/`, one per endpoint.
3. ✅ **Wiring** — `app.js` already knows how to call the real API; you just
   flip a flag once your backend is deployed (Step 5 below).
4. ✅ **DynamoDB save/load** — `save/handler.py` and `stories/handler.py`.


