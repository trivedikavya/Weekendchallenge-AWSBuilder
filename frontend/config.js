// ─────────────────────────────────────────────────────────────
// Story Dice — Frontend Config
// ─────────────────────────────────────────────────────────────
// STEP 1 (mock mode): leave USE_MOCK = true and API_BASE_URL empty.
//   The app will work fully offline with fake data so you can build
//   and preview the UI before any backend exists.
//
// STEP 2 (real backend): after you deploy the SAM stack (see README),
//   copy the "ApiUrl" value from the `sam deploy` output and paste it
//   below, then set USE_MOCK = false.
//   Example: "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"
// ─────────────────────────────────────────────────────────────

const CONFIG = {
    USE_MOCK: false,
    API_BASE_URL: "https://hqq262g0kl.execute-api.us-east-1.amazonaws.com/prod"
};
