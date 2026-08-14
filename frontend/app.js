// ─────────────────────────────────────────────────────────────
// Story Dice — App Logic
// ─────────────────────────────────────────────────────────────

// Word banks — MUST mirror backend/roll/handler.py so mock mode
// and real backend behave the same way.
const WORD_BANKS = {
  place: [
    "a forgotten lighthouse", "a floating market", "a candy-cane forest",
    "an upside-down library", "a cloud castle", "a sunken pirate ship",
    "a village inside a teapot", "a moonlit train station",
    "a garden that grows umbrellas", "a city built on a turtle's back",
    "a bakery at the edge of the world", "a treehouse in the sky"
  ],
  object: [
    "a rusty key", "a jar of fireflies", "a paper airplane that never lands",
    "a pocket watch that ticks backwards", "a map with no destination",
    "a violin made of glass", "a button that isn't sewn to anything",
    "a teacup that refills itself", "a mitten that hums lullabies",
    "a compass that points to lost things", "a marble full of stars",
    "an umbrella that opens doors"
  ],
  trait: [
    "secretly afraid of silence", "collects other people's shadows",
    "can only whisper the truth", "believes every knock is a friend",
    "hums to make plants grow", "keeps a diary written in riddles",
    "never remembers their own name", "trips over compliments",
    "talks to socks before wearing them", "is allergic to Mondays",
    "sees colors that don't exist yet", "laughs in a different language"
  ],
  twist: [
    "but time runs backwards here", "until the moon starts talking",
    "and nobody notices the town is upside down",
    "but every promise becomes a butterfly",
    "until the shadows start telling secrets",
    "and rain falls upward at midnight",
    "but the map keeps redrawing itself",
    "until laughter becomes currency",
    "and the stars start keeping a diary",
    "but every door leads back to yesterday"
  ]
};

// ── State ──────────────────────────────────────────────────
let currentWords = null;
let currentStory = null;
let mockSavedStories = [
  {
    id: "demo1a2b",
    place: "a floating market",
    object: "a jar of fireflies",
    trait: "collects other people's shadows",
    twist: "until the moon starts talking",
    story: "In a floating market where stalls bobbed like lily pads, a girl named Mira traded a jar of fireflies for a shadow she liked the shape of. She collected shadows the way others collected seashells — the shy ones, the mischievous ones, the ones that danced when no one watched. One evening, the moon leaned close and whispered that Mira's own shadow had gone missing, traded away years ago without her noticing. Mira laughed, unbothered, and simply borrowed a spare from her jar. It fit perfectly, humming softly as it settled onto the cobblestones. From that night on, the moon and Mira exchanged stories every evening, and the market glowed just a little brighter, lit by fireflies and finally, by a talking moon who had found someone worth listening to.",
    createdAt: new Date(Date.now() - 86400000).toISOString()
  }
];

// ── DOM refs ───────────────────────────────────────────────
const els = {
  dice: {
    Place: document.querySelector('.die[data-category="Place"]'),
    Object: document.querySelector('.die[data-category="Object"]'),
    Trait: document.querySelector('.die[data-category="Trait"]'),
    Twist: document.querySelector('.die[data-category="Twist"]')
  },
  wordPlace: document.getElementById('wordPlace'),
  wordObject: document.getElementById('wordObject'),
  wordTrait: document.getElementById('wordTrait'),
  wordTwist: document.getElementById('wordTwist'),
  rollBtn: document.getElementById('rollBtn'),
  rerollBtn: document.getElementById('rerollBtn'),
  generateBtn: document.getElementById('generateBtn'),
  loadingState: document.getElementById('loadingState'),
  loadingText: document.getElementById('loadingText'),
  errorState: document.getElementById('errorState'),
  errorText: document.getElementById('errorText'),
  dismissErrorBtn: document.getElementById('dismissErrorBtn'),
  storyCard: document.getElementById('storyCard'),
  storyText: document.getElementById('storyText'),
  storyElements: document.getElementById('storyElements'),
  saveBtn: document.getElementById('saveBtn'),
  saveStatus: document.getElementById('saveStatus'),
  tabs: document.querySelectorAll('.tab-btn'),
  panels: document.querySelectorAll('.tab-panel'),
  refreshSavedBtn: document.getElementById('refreshSavedBtn'),
  savedLoading: document.getElementById('savedLoading'),
  savedError: document.getElementById('savedError'),
  savedErrorText: document.getElementById('savedErrorText'),
  savedEmpty: document.getElementById('savedEmpty'),
  savedList: document.getElementById('savedList')
};

// ── Helpers ────────────────────────────────────────────────
function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function showError(msg) {
  els.errorText.textContent = msg;
  els.errorState.classList.remove('hidden');
}
function hideError() {
  els.errorState.classList.add('hidden');
}

function apiUrl(path) {
  return `${CONFIG.API_BASE_URL}${path}`;
}

// ── Tabs ───────────────────────────────────────────────────
els.tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    els.tabs.forEach(b => b.classList.remove('active'));
    els.panels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'saved') {
      loadSavedStories();
    }
  });
});

// ── Rolling dice ───────────────────────────────────────────
async function rollWords() {
  hideError();
  els.rollBtn.disabled = true;
  els.rerollBtn.disabled = true;
  els.generateBtn.disabled = true;

  // Trigger the flip animation on all dice
  Object.values(els.dice).forEach(die => {
    die.classList.remove('rolling');
    void die.offsetWidth; // restart animation
    die.classList.add('rolling');
  });

  let words;
  try {
    if (CONFIG.USE_MOCK) {
      // simulate a tiny delay so the animation feels natural
      await new Promise(res => setTimeout(res, 250));
      words = {
        place: pickRandom(WORD_BANKS.place),
        object: pickRandom(WORD_BANKS.object),
        trait: pickRandom(WORD_BANKS.trait),
        twist: pickRandom(WORD_BANKS.twist)
      };
    } else {
      const res = await fetch(apiUrl('/roll'));
      if (!res.ok) throw new Error('Roll request failed');
      words = await res.json();
    }
  } catch (err) {
    console.error(err);
    showError("Couldn't roll the dice — please try again.");
    els.rollBtn.disabled = false;
    return;
  }

  currentWords = words;

  setTimeout(() => {
    els.wordPlace.textContent = words.place;
    els.wordObject.textContent = words.object;
    els.wordTrait.textContent = words.trait;
    els.wordTwist.textContent = words.twist;
  }, 300);

  setTimeout(() => {
    Object.values(els.dice).forEach(die => die.classList.remove('rolling'));
    els.rollBtn.disabled = false;
    els.rerollBtn.disabled = false;
    els.generateBtn.disabled = false;
  }, 700);
}

els.rollBtn.addEventListener('click', rollWords);
els.rerollBtn.addEventListener('click', () => {
  els.storyCard.classList.add('hidden');
  currentStory = null;
  rollWords();
});
els.dismissErrorBtn.addEventListener('click', hideError);

// ── Generate story ─────────────────────────────────────────
const LOADING_MESSAGES = [
  "Rolling the dice of imagination...",
  "Consulting the story sprites...",
  "Sprinkling in some whimsy...",
  "Untangling the plot threads..."
];

function startLoading() {
  let i = 0;
  els.loadingText.textContent = LOADING_MESSAGES[0];
  els.loadingState.classList.remove('hidden');
  return setInterval(() => {
    i = (i + 1) % LOADING_MESSAGES.length;
    els.loadingText.textContent = LOADING_MESSAGES[i];
  }, 1400);
}
function stopLoading(intervalId) {
  clearInterval(intervalId);
  els.loadingState.classList.add('hidden');
}

function mockStory(words) {
  const templates = [
    `Once upon a time, in ${words.place}, someone stumbled upon ${words.object}. Its owner was known for being ${words.trait}, which made everything stranger — ${words.twist}. What followed was a tale nobody quite believed, yet everybody wanted to hear again.`,
    `Deep within ${words.place} sat ${words.object}, waiting for the right hands. A wanderer, ${words.trait}, finally found it — and ${words.twist}. From that moment, the ordinary rules simply stopped applying.`,
    `They say ${words.place} holds secrets, and none stranger than ${words.object}. Its keeper, ${words.trait}, guarded it well, ${words.twist}. By the story's end, even the skeptics admitted something magical had happened.`
  ];
  return pickRandom(templates);
}

async function generateStory() {
  if (!currentWords) return;
  hideError();
  els.generateBtn.disabled = true;
  els.rerollBtn.disabled = true;
  els.storyCard.classList.add('hidden');
  els.saveStatus.textContent = '';

  const loadingId = startLoading();

  try {
    let story;
    if (CONFIG.USE_MOCK) {
      await new Promise(res => setTimeout(res, 1600));
      story = mockStory(currentWords);
    } else {
      const res = await fetch(apiUrl('/generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentWords)
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.error || 'Story generation failed');
      }
      const data = await res.json();
      story = data.story;
    }

    currentStory = story;
    renderStory(story, currentWords);
  } catch (err) {
    console.error(err);
    showError("The story sprites got tangled up! Please try again in a moment.");
  } finally {
    stopLoading(loadingId);
    els.generateBtn.disabled = false;
    els.rerollBtn.disabled = false;
  }
}

function renderStory(story, words) {
  els.storyText.textContent = story;
  els.storyElements.innerHTML = `
    <span>📍 ${words.place}</span>
    <span>🔑 ${words.object}</span>
    <span>🧑 ${words.trait}</span>
    <span>🌀 ${words.twist}</span>
  `;
  els.storyCard.classList.remove('hidden');
}

els.generateBtn.addEventListener('click', generateStory);

// ── Save story ─────────────────────────────────────────────
els.saveBtn.addEventListener('click', async () => {
  if (!currentStory || !currentWords) return;
  els.saveBtn.disabled = true;
  els.saveStatus.textContent = 'Saving...';

  try {
    if (CONFIG.USE_MOCK) {
      await new Promise(res => setTimeout(res, 500));
      mockSavedStories.unshift({
        id: Math.random().toString(36).slice(2, 10),
        ...currentWords,
        story: currentStory,
        createdAt: new Date().toISOString()
      });
    } else {
      const res = await fetch(apiUrl('/save'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentWords, story: currentStory })
      });
      if (!res.ok) throw new Error('Save failed');
    }
    els.saveStatus.textContent = '✅ Saved!';
  } catch (err) {
    console.error(err);
    els.saveStatus.textContent = '';
    showError("Couldn't save your story — please try again.");
  } finally {
    els.saveBtn.disabled = false;
  }
});

// ── Saved stories list ───────────────────────────────────────
async function loadSavedStories() {
  els.savedError.classList.add('hidden');
  els.savedEmpty.classList.add('hidden');
  els.savedList.innerHTML = '';
  els.savedLoading.classList.remove('hidden');

  try {
    let stories;
    if (CONFIG.USE_MOCK) {
      await new Promise(res => setTimeout(res, 400));
      stories = mockSavedStories;
    } else {
      const res = await fetch(apiUrl('/stories'));
      if (!res.ok) throw new Error('Failed to fetch stories');
      const data = await res.json();
      stories = data.stories || [];
    }

    if (!stories.length) {
      els.savedEmpty.classList.remove('hidden');
    } else {
      els.savedList.innerHTML = stories.map(renderSavedItem).join('');
    }
  } catch (err) {
    console.error(err);
    els.savedErrorText.textContent = "Couldn't load saved stories — please try again.";
    els.savedError.classList.remove('hidden');
  } finally {
    els.savedLoading.classList.add('hidden');
  }
}

function renderSavedItem(s) {
  const date = new Date(s.createdAt).toLocaleString();
  return `
    <div class="saved-item">
      <div class="saved-date">${date} · #${s.id}</div>
      <div class="saved-tags">
        <span>📍 ${s.place}</span>
        <span>🔑 ${s.object}</span>
        <span>🧑 ${s.trait}</span>
        <span>🌀 ${s.twist}</span>
      </div>
      <div class="saved-story">${s.story}</div>
    </div>
  `;
}

els.refreshSavedBtn.addEventListener('click', loadSavedStories);
