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

What's left is purely **deployment** — turning the code above into running
AWS resources. Follow the steps below in order.

---

## Step 0 — Preview the app right now (no AWS needed)

1. Open the `frontend` folder in File Explorer.
2. Double-click `index.html` (or right-click → Open with → your browser).
   - Opening the file directly works fine for this mock-mode preview.
3. Click **🎲 Roll**, then **✍️ Generate Story**, then **💾 Save Story**,
   then the **📚 Saved Stories** tab. Everything works with fake data.

This confirms the UI/UX before you touch AWS at all.

---

## Step 1 — Create/prepare your AWS account

1. Go to https://aws.amazon.com/ and sign in (or create a free account).
2. You'll deploy everything into **one region**. Use **US East (N. Virginia)
   — `us-east-1`** for this project, since Bedrock Nova models are reliably
   available there. You'll see a region dropdown in the top-right of the AWS
   Console — make sure it says "N. Virginia" before doing anything below.

---

## Step 2 — Turn on Bedrock model access (do this first — it can take a few minutes to activate)

Bedrock models are OFF by default per-account; you must explicitly enable them.

1. In the AWS Console search bar (top center), type **"Bedrock"** and open
   **Amazon Bedrock**.
2. In the left sidebar, scroll down and click **"Model access"** (sometimes
   under a "Bedrock configurations" section).
3. Click the orange **"Enable specific models"** (or "Manage model access")
   button, top-right.
4. Check the box for **"Nova Micro"** (and optionally "Nova Lite" too, in
   case you want to experiment). Amazon's own models typically don't
   require a use-case form — just checkboxes.
5. Scroll down and click **"Next"**, review, then **"Submit"**.
6. Wait on the Model access page until the status next to Nova Micro shows
   a green **"Access granted"** (usually instant to a couple of minutes —
   refresh the page if needed).

> If you skip this step, `/generate` will return a friendly error like
> *"Story generation isn't available yet..."* — that error message means
> come back and finish this step.

---

## Step 3 — Create an IAM user + access keys (so your computer can deploy to AWS)

1. In the Console search bar, type **"IAM"** and open **IAM**.
2. Left sidebar → **Users** → **Create user** (orange button, top-right).
3. Username: `story-dice-deployer` → **Next**.
4. Choose **"Attach policies directly"**.
5. For a weekend project, search for and check **`AdministratorAccess`**
   (simplest option — not least-privilege, but fine for a personal
   hobby project you'll clean up afterward). → **Next** → **Create user**.
6. Click into the new user → tab **"Security credentials"**.
7. Scroll to **"Access keys"** → **"Create access key"**.
8. Choose **"Command Line Interface (CLI)"** → check the confirmation box →
   **Next** → **Create access key**.
9. **Copy the Access Key ID and Secret Access Key now** (the secret is only
   shown once) — save them somewhere safe temporarily.

---

## Step 4 — Install the AWS CLI and AWS SAM CLI on your computer

1. **AWS CLI**: install from the official AWS docs page —
   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
   (Windows: download and run the `.msi` installer, then restart your
   terminal.)
2. **AWS SAM CLI**: install from the official AWS docs page —
   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
   (Windows: download and run the `.msi` installer.)
3. Verify both installed correctly by opening a **new** PowerShell window
   and running:
   ```powershell
   aws --version
   sam --version
   ```
4. Configure your credentials:
   ```powershell
   aws configure
   ```
   - AWS Access Key ID: *(paste from Step 3)*
   - AWS Secret Access Key: *(paste from Step 3)*
   - Default region name: `us-east-1`
   - Default output format: `json`

---

## Step 5 — Deploy the backend (API Gateway + Lambdas + DynamoDB)

Open PowerShell in the `story-dice/backend` folder:

```powershell
cd path\to\story-dice\backend
sam build
sam deploy --guided
```

Answer the guided prompts like this:

| Prompt | Answer |
|---|---|
| Stack Name | `story-dice` |
| AWS Region | `us-east-1` |
| Parameter BedrockModelId | *(press Enter to accept default `amazon.nova-micro-v1:0`)* |
| Parameter StageName | *(press Enter to accept default `prod`)* |
| Confirm changes before deploy | `Y` |
| Allow SAM CLI IAM role creation | `Y` |
| Disable rollback | `N` |
| Save arguments to configuration file | `Y` |
| SAM configuration file / environment | *(press Enter for defaults)* |

Wait for it to finish (a couple of minutes). At the very end, look for the
**Outputs** section printed in the terminal:

```
Outputs
-----------------------------------------------------------------
Key                 ApiUrl
Description         Base URL for the Story Dice API — paste this into frontend/config.js
Value               https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
-----------------------------------------------------------------
Key                 TableName
Value               StoryDiceStories
-----------------------------------------------------------------
```

**Copy the `ApiUrl` value** — you'll need it in Step 7.

> Re-running `sam deploy` any time after code changes will update the stack
> in place (no need to repeat the guided prompts — just run `sam build`
> then `sam deploy`).

---

## Step 6 — Sanity-check the API before touching the frontend

In PowerShell (replace the URL with your real `ApiUrl`):

```powershell
# Should return 4 random words as JSON
Invoke-RestMethod -Uri "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/roll"

# Should return a generated story
Invoke-RestMethod -Uri "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/generate" `
  -Method POST -ContentType "application/json" `
  -Body '{"place":"a floating market","object":"a rusty key","trait":"secretly afraid of silence","twist":"until the moon starts talking"}'

# Should return an empty list the first time: {"stories":[]}
Invoke-RestMethod -Uri "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/stories"
```

If `/generate` errors with something about Bedrock access, go back to
**Step 2** and confirm Nova Micro shows "Access granted" in `us-east-1`.

---

## Step 7 — Point the frontend at your real backend

1. Open `frontend/config.js` in a text editor.
2. Change it to:
   ```js
   const CONFIG = {
     USE_MOCK: false,
     API_BASE_URL: "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"
   };
   ```
   (no trailing slash on the URL)
3. Save the file.

---

## Step 8 — Test the full app end-to-end, locally

Serving over a local web server (rather than double-clicking the file) is
recommended once you're hitting a real API, to avoid browser file:// quirks:

```powershell
cd path\to\story-dice\frontend
python -m http.server 8080
```

Then open **http://localhost:8080** in your browser and:

1. Click **🎲 Roll** → 4 real random words appear with a flip animation.
2. Click **✍️ Generate Story** → loading message appears → a real
   Bedrock-generated story appears in the card.
3. Click **💾 Save Story** → should show "✅ Saved!".
4. Click the **📚 Saved Stories** tab → your story should appear (click
   **🔄 Refresh** if needed).
5. Click **🔄 Reroll** to start a new round.

---

## Step 9 (optional) — Host the frontend on the internet with S3

If you just want to run it locally, you can skip this. To make it a real
public URL:

1. AWS Console search bar → **"S3"** → **Create bucket**.
2. Bucket name: something globally unique, e.g. `story-dice-yourname-2026`.
   Region: `us-east-1`.
3. Under **"Block Public Access settings for this bucket"**, uncheck
   **"Block all public access"** and check the acknowledgment box.
4. Click **Create bucket**.
5. Open the bucket → tab **"Properties"** → scroll to **"Static website
   hosting"** → **Edit** → **Enable** → Index document: `index.html` →
   **Save changes**.
6. Tab **"Permissions"** → **"Bucket policy"** → **Edit** → paste (replace
   `YOUR-BUCKET-NAME`):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Sid": "PublicReadGetObject",
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
     }]
   }
   ```
   → **Save changes**.
7. Tab **"Objects"** → **Upload** → add `index.html`, `styles.css`,
   `app.js`, `config.js` from your `frontend/` folder → **Upload**.
8. Back in **Properties → Static website hosting**, copy the **"Bucket
   website endpoint"** URL — that's your live app link.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "Story generation isn't available yet..." | Bedrock model access not granted, or granted in the wrong region. Redo Step 2 in `us-east-1`. |
| CORS error in browser console | Make sure you ran `sam build && sam deploy` after any `template.yaml` change so the API's CORS/OPTIONS routes redeploy. |
| `/stories` always empty after saving | Confirm `TableName` output matches `StoryDiceStories` and that `/save` returned `"saved": true` with no error. |
| `sam deploy --guided` fails on IAM permissions | Your IAM user needs enough permissions to create Lambda/API Gateway/DynamoDB/IAM roles — re-check Step 3 (`AdministratorAccess`). |
| Access key errors when running `aws`/`sam` commands | Re-run `aws configure` and double check the keys, or that you copied them without extra spaces. |

---

## Cost notes (Free Tier friendly)

- **Lambda**: 128MB memory, short timeouts — well within the 1M free
  requests/month free tier.
- **API Gateway**: REST API free tier covers 1M calls/month for 12 months.
- **DynamoDB**: `PAY_PER_REQUEST` billing — a handful of saved stories a day
  costs effectively nothing (a few cents/month at most for a hobby project).
- **Bedrock (Nova Micro)**: not part of the AWS Free Tier, but Nova Micro is
  Amazon's cheapest model — generating a ~200 word story costs a small
  fraction of a cent per request.

## Cleaning up (avoid ongoing charges)

```powershell
cd path\to\story-dice\backend
sam delete
```

This removes the Lambda functions, API Gateway, and DynamoDB table (you'll
be asked to confirm deleting the table, since it may contain your saved
stories). If you set up S3 static hosting in Step 9, also empty and delete
that bucket from the S3 console.
