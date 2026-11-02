"""Hardik's Data Mining Chatbot - Render backend for hybrid deployment."""
import os
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = Path(os.getenv("PDF_DIR", str(BASE_DIR / "knowledge_base")))
PDF_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("DataMiningChatbot")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    # Logs are ephemeral on free hosting; console logs are visible in Render.

# Configure one key, or optional additional keys you own and are authorized to use.
GEMINI_KEYS = []
for number in range(1, 10):
    value = os.getenv(f"GEMINI_KEY_{number}", "").strip()
    if value:
        GEMINI_KEYS.append((f"GEMINI_KEY_{number}", value))
if not GEMINI_KEYS:
    value = os.getenv("GEMINI_API_KEY", "").strip()
    if value:
        GEMINI_KEYS.append(("GEMINI_API_KEY", value))
if not GEMINI_KEYS:
    raise RuntimeError("Missing Gemini key. Add GEMINI_API_KEY in Render Environment settings.")

# Load every PDF in knowledge_base (or the folder specified by PDF_DIR).
PDF_FILES = sorted(PDF_DIR.glob("*.pdf"))
if not PDF_FILES:
    logger.warning("No PDFs found in %s. The chatbot will start, but PDF retrieval is unavailable.", PDF_DIR)

# CELL 4: BACKEND - PDF search, multi-key Gemini generator, ask()

import re
import time
import hashlib
import threading
from collections import OrderedDict
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from rank_bm25 import BM25Okapi
from google import genai
from google.genai import types, errors


# ------------------------------------------
# 1. SETTINGS
# ------------------------------------------

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")   # the model that worked in your API test
MAX_OUT = 2048                    # max answer length in tokens
REQUEST_TIMEOUT_MS = 20000        # give up on one request after 20 seconds
KEY_COOLDOWN = 90                 # seconds to skip a key after a quota error
WEB_COOLDOWN = 600                # seconds to skip web search after it fails
CACHE_SIZE = 200                  # remembered answers
TOP_K = 4                         # PDF passages sent per question
HISTORY_TURNS = 4                 # previous messages sent
HISTORY_CHARS = 600               # max characters kept per previous message
WEB_MODE = "Web Answer (Internet)"

STUDY_MODES = [
    "Exam Answer",
    "Explain Topic",
    "Numerical",
    "Comparison",
    "Quiz",
    "Quick Revision",
    WEB_MODE
]

# ------------------------------------------
# 2. SYSTEM PROMPT
# ------------------------------------------

SYSTEM = """
You are a Data Mining study assistant for an MBA student.

SOURCE RULES:
- Use the provided PDF notes as the primary source.
- Explain concepts in simple, student-friendly language.
- If the notes do not support an answer, say so clearly.
- Do not invent facts or claim unsupported information comes from notes.
- Never display PDF filenames, page numbers, or citations.
- Do not include a references section.

STUDY MODES:

1. Exam Answer:
Give a concise, exam-ready answer with a definition,
headings, important points, and an example where useful.

2. Explain Topic:
Explain step by step using simple language and examples.

3. Numerical:
Show the formula, substitute values, show calculations,
and state the final answer with appropriate units.
Do not invent missing values.

4. Comparison:
Use a clear Markdown table where appropriate.

5. Quiz:
Generate multiple-choice questions with four options
(A, B, C, D), the correct answers, and brief explanations.

6. Quick Revision:
Provide concise revision bullets, important terms,
formulas, and memory aids.

IMAGE SUPPORT:
- Read the uploaded question carefully.
- Interpret readable text, formulas, tables, and diagrams.
- Answer all visible questions when requested.
- Never invent unreadable text.
- Ask for a clearer image when necessary.

EXAMPLES - REQUIRED:
- ALWAYS include at least one practical, real-life example for each topic explained.
- Never leave an "Example", "Application", or "Business Context" section empty.
- If the question asks about multiple topics, give one clear example for each topic.
- Prefer simple, relatable examples from supermarkets, banks, colleges, online shopping, or businesses.
- Briefly explain how the example illustrates the concept; use steps when they make it clearer.
- If the notes do not provide an example, create a simple illustrative example from general knowledge and label it "Illustration".
- For simple questions, keep the answer concise but still include an example.
- Do not fabricate an example and claim it came from the PDF notes.

Keep answers focused on the student's question.
"""

WEB_ON = (
    "\n\nWEB MODE: You may use Google Search for current facts, tools, "
    "datasets, news and real-world examples. Prefer the notes for core "
    "definitions. Say clearly when something comes from the web rather than "
    "the notes. In this mode you may mention website names."
)

WEB_OFF = (
    "\n\nNOTE: Live web search is unavailable right now. Answer from the "
    "notes and general knowledge, and tell the student at the start that "
    "web search could not be used."
)

# ------------------------------------------
# 3. LOAD PDFS AND BUILD SEARCHABLE CHUNKS
# ------------------------------------------

documents = []

for pdf_path in PDF_FILES:
    pdf_path = Path(pdf_path)
    try:
        logger.info("Loading PDF: %s", pdf_path.name)
        reader = PdfReader(str(pdf_path))

        if reader.is_encrypted:
            raise ValueError("The PDF is encrypted.")

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                documents.append({
                    "source": pdf_path.name,
                    "page": page_number,
                    "text": page_text
                })

    except Exception:
        logger.exception("Failed to load PDF: %s", pdf_path.name)
        raise

if not documents:
    logger.warning("No extractable PDF text found. Add text-based PDFs; scanned PDFs need OCR.")

CHUNK_SIZE = 220
CHUNK_OVERLAP = 40
CHUNK_STEP = CHUNK_SIZE - CHUNK_OVERLAP

chunks = []

for doc in documents:
    words = doc["text"].split()
    for start in range(0, len(words), CHUNK_STEP):
        part = " ".join(words[start:start + CHUNK_SIZE])
        if part.strip():
            chunks.append({"source": doc["source"], "page": doc["page"], "text": part})

STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from",
    "what", "when", "where", "which", "have", "has", "are",
    "was", "were", "you", "your", "how", "why", "does",
    "did", "can", "could", "would", "should", "about",
    "explain", "define", "give", "tell", "show", "please",
    "into", "then", "than", "also", "some", "more", "most",
    "to", "of", "in", "on", "at", "by", "is", "as", "or", "be"
}


def _tokens(text):
    return [
        w for w in re.findall(r"[a-z0-9]+", text.lower())
        if len(w) > 2 and w not in STOP_WORDS
    ]


_bm25 = BM25Okapi([_tokens(c["text"]) for c in chunks]) if chunks else None


def get_pdf_context(question, previous_question=""):
    """Find the best PDF passages. The previous question is added so that
    follow-ups such as 'explain more' still find the right topic."""
    if not chunks or _bm25 is None:
        return "Course PDF notes are not configured yet. Add your PDF files to the knowledge_base folder (or set PDF_DIR) and redeploy. I can still answer using general knowledge."

    query = _tokens(f"{question} {previous_question}")

    if query:
        scores = _bm25.get_scores(query)
        best = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
        matches = [chunks[i]["text"] for i in best[:TOP_K] if scores[i] > 0]
        if matches:
            return "\n\n---\n\n".join(matches)

    return (
        "No sufficiently relevant passage was found in the PDFs. "
        "Do not claim the notes contain information that was not found."
    )

# ------------------------------------------
# 4. GEMINI CLIENTS, KEY ROTATION AND LOGGING
# ------------------------------------------

GEMINI_CLIENTS = [
    (name, genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS)
    ))
    for name, key in GEMINI_KEYS
]

_current_key_index = 0
_key_blocked_until = {}
_web_blocked_until = 0


def _error_code(exc):
    try:
        return int(getattr(exc, "code", None))
    except (TypeError, ValueError):
        return None


def _log_async(**kwargs):
    """Write Gemini request details to the local chatbot log."""
    safe_details = {
        key: value for key, value in kwargs.items()
        if key not in {"api_key", "client"}
    }
    logger.info("Gemini request: %s", safe_details)


def _call_gemini(client, contents, system, use_web):
    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=MAX_OUT,
        tools=[types.Tool(google_search=types.GoogleSearch())] if use_web else None,
    )
    return client.models.generate_content(
        model=MODEL, contents=contents, config=config
    )


def _generate(contents, system, use_web=False):
    global _current_key_index, _web_blocked_until

    if use_web and time.time() < _web_blocked_until:
        use_web = False

    last_error = None
    tried = 0
    total = len(GEMINI_CLIENTS)

    for offset in range(total):
        index = (_current_key_index + offset) % total
        key_name, client = GEMINI_CLIENTS[index]

        if time.time() < _key_blocked_until.get(key_name, 0):
            continue   # this key is cooling down after a quota error

        tried += 1
        start = time.time()

        try:
            try:
                response = _call_gemini(
                    client, contents,
                    system + (WEB_ON if use_web else ""), use_web
                )
            except errors.APIError as exc:
                # Web search failed: pause it and answer without it
                if use_web and _error_code(exc) != 400:
                    _web_blocked_until = time.time() + WEB_COOLDOWN
                    logger.warning("Web search failed, pausing it: %s", exc)
                    use_web = False
                    response = _call_gemini(
                        client, contents, system + WEB_OFF, False
                    )
                else:
                    raise

            answer = (response.text or "").strip()
            if not answer:
                raise RuntimeError(f"{MODEL} returned an empty answer.")

            candidate = response.candidates[0] if response.candidates else None
            if "MAX_TOKENS" in str(getattr(candidate, "finish_reason", "")):
                answer += "\n\n*(The answer was cut off. Ask me to continue.)*"

            usage = getattr(response, "usage_metadata", None)
            _log_async(
                key_name=key_name, status="Success",
                elapsed=time.time() - start,
                input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            )
            _current_key_index = index
            logger.info("Gemini success: key=%s time=%.2fs", key_name, time.time() - start)
            return answer

        except errors.APIError as exc:
            last_error = exc
            code = _error_code(exc)
            if code == 429:
                _key_blocked_until[key_name] = time.time() + KEY_COOLDOWN
            _log_async(
                key_name=key_name, status="Failed",
                elapsed=time.time() - start, error=f"API error {code}: {exc}"
            )
            logger.warning("Gemini API error: key=%s code=%s", key_name, code)
            if code in (400, 404):
                break   # a bad request or missing model affects every key

        except Exception as exc:
            last_error = exc
            _log_async(
                key_name=key_name, status="Failed",
                elapsed=time.time() - start,
                error=f"{type(exc).__name__}: {exc}"
            )
            logger.warning("Request failed: key=%s %s", key_name, type(exc).__name__)

    if tried == 0:
        raise RuntimeError("All API keys are cooling down after quota errors.")

    raise RuntimeError("Gemini could not generate an answer.") from last_error

# ------------------------------------------
# 5. ANSWER CACHE
# ------------------------------------------

_cache = OrderedDict()
_cache_lock = threading.Lock()


def _cache_get(key):
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    return None


def _cache_put(key, value):
    with _cache_lock:
        _cache[key] = value
        if len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)

# ------------------------------------------
# 6. ASK (used by the chat window)
# ------------------------------------------

def ask(question, history=None, mode="Exam Answer", image_path=None):
    question = (question or "").strip()

    if not question and not image_path:
        return "Please type a question or upload an image."

    if image_path and not question:
        question = "Read the question or questions in the uploaded image and answer them."

    greeting = question.lower().strip(" !.,?")

    if not image_path and greeting in {
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good afternoon", "good evening"
    }:
        return (
            "Hello! 👋 Welcome to your Data Mining Study Assistant. "
            "What would you like to learn today?"
        )

    if not image_path and greeting in {"thanks", "thank you", "thankyou"}:
        return "You're welcome! Ask me another question."

    try:
        # Recent conversation (trimmed to save tokens)
        previous, last_user = [], ""

        for item in (history or [])[-HISTORY_TURNS:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            content = item.get("content", "")
            if role in {"user", "assistant"} and isinstance(content, str):
                content = content[:HISTORY_CHARS]
                previous.append(f"{role.title()}: {content}")
                if role == "user":
                    last_user = content

        previous_text = "\n".join(previous) or "No previous conversation."

        # Repeated text questions are answered from the cache
        cache_key = None
        if not image_path:
            cache_key = hashlib.sha256(
                f"{mode}|{question.lower()}|{previous_text}".encode()
            ).hexdigest()
            cached = _cache_get(cache_key)
            if cached:
                logger.info("Cache hit. Mode: %s", mode)
                return cached

        context = get_pdf_context(question, last_user)

        prompt = f"""
Selected study mode: {mode}

Previous conversation:
{previous_text}

Student's current question:
{question}

Relevant passages retrieved from the course notes:
{context}

Instructions:
1. Answer the current question in the selected study mode.
2. Use the retrieved passages as the primary source. If none are relevant, say so honestly.
3. If an image is attached, inspect it and answer its visible questions.
4. Follow the mode rules and example rules in your system instructions.
"""
        contents = [prompt]

        if image_path:
            with Image.open(image_path) as img:
                image_copy = img.convert("RGB").copy()
            image_copy.thumbnail((1280, 1280))   # fewer image tokens
            contents.append(image_copy)

        answer = _generate(contents, SYSTEM, use_web=(mode == WEB_MODE))

        if cache_key:
            _cache_put(cache_key, answer)

        logger.info("Answer generated. Mode: %s", mode)
        return answer

    except Exception as exc:
        logger.exception("Answer generation failed. Mode: %s", mode)

        if "cooling down" in str(exc):
            return (
                "All API keys are over their quota right now. "
                "Please wait a minute or two and try again."
            )

        return (
            "Sorry, I couldn't generate a response right now. "
            "Please try again. If the problem continues, check the Render logs "
            "and your Gemini API key/quota settings."
        )


print("Backend loaded successfully.")
print("Readable PDF pages:", len(documents))
print("Searchable sections:", len(chunks))
print("Model:", MODEL, "| API key slots:", len(GEMINI_CLIENTS))
print("Study modes:", STUDY_MODES)
# CELL 5: CHATBOT UI (design, chat function, Gradio app)

import gradio as gr

# ==========================================
# 1. CUSTOM CSS
# ==========================================

CUSTOM_CSS = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto !important;
}

.hero {
    text-align: center;
    padding: 24px 12px;
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border: 1px solid #fed7aa;
    border-radius: 18px;
    margin-bottom: 16px;
}

.brand-mark {
    font-size: 42px;
}

.hero h1 {
    color: #9a3412;
    font-size: 30px;
}

.hero p {
    color: #57534e;
}


.greeting {
    background: #fff7ed;
    color: #000000 !important;
    border-left: 4px solid #f97316;
    border-radius: 8px;
    padding: 14px;
    margin: 10px 0 18px;
}

.greeting * {
    color: #000000 !important;
}

#send-question {
    min-width: 48px !important;
    height: 46px !important;
    font-size: 22px !important;
}

.footer {
    text-align: center;
    color: #78716c;
    font-size: 12px;
    padding: 18px 0 6px;
}
"""


# ==========================================
# 2. CHAT RESPONSE FUNCTION
# ==========================================

def respond(message, history, mode, image_path):
    history = list(history or [])
    message = (message or "").strip()

    if not message and image_path is None:
        history.append({
            "role": "assistant",
            "content": "Please type a question or upload an image."
        })
        return history, "", None

    user_display = message

    if image_path is not None:
        if not user_display:
            user_display = "Please answer the question in this image."
        user_display += "\n\n📷 Image attached"

    try:
        answer = ask(
            question=message,
            history=history,
            mode=mode,
            image_path=image_path
        )
    except Exception:
        logger.exception("Error while generating chatbot response")
        answer = (
            "Sorry, I couldn't process that request. "
            "Please try again and check the error log if the issue continues."
        )

    history.append({
        "role": "user",
        "content": user_display
    })

    history.append({
        "role": "assistant",
        "content": str(answer)
    })

    return history, "", None

# ==========================================
# 3. CREATE THE GRADIO APP
# ==========================================

# Gradio 6: do not pass theme/css to Blocks()
with gr.Blocks(
    theme=gr.themes.Base(primary_hue="orange", secondary_hue="stone", neutral_hue="stone"),
    css=CUSTOM_CSS,
    head="""<title>Hardik's Data Mining Chatbot</title><meta name="viewport" content="width=device-width, initial-scale=1">"""
) as demo:

    gr.HTML("""
    <div class="hero">
        <div class="brand-mark">🤖</div>
        <h1>Hardik's Chatbot<br>On Data Mining</h1>
        <p>Your study assistant for concepts, numericals
        and exam preparation.</p>
    </div>
    """)

    gr.HTML("""
    <div class="greeting">
        👋 Hi! I'm your Data Mining study buddy.
        Ask questions from your notes or upload an image.
    </div>
    """)

    mode = gr.Dropdown(
        choices=STUDY_MODES,
        value="Exam Answer",
        label="Study Mode"
    )

    # Removed type="messages" for compatibility
    chatbot = gr.Chatbot(
        height=460,
        label="Chatbot",
        type="messages"
    )

    image_input = gr.Image(
        type="filepath",
        label="📷 Upload a question image (optional)",
        sources=["upload"],
        height=190
    )

    with gr.Row():
        message = gr.Textbox(
            placeholder="Ask anything about Data Mining...",
            label="Your question",
            show_label=False,
            lines=1,
            max_lines=5,
            scale=8,
            container=False
        )

        submit_btn = gr.Button(
            "↑",
            variant="primary",
            elem_id="send-question",
            scale=0,
            min_width=48
        )

    clear_btn = gr.Button("Clear Chat")

    gr.HTML("""
    <div class="footer">
        Made by Hardik · Amity Business School
    </div>
    """)

    submit_btn.click(
        fn=respond,
        inputs=[message, chatbot, mode, image_input],
        outputs=[chatbot, message, image_input]
    )

    message.submit(
        fn=respond,
        inputs=[message, chatbot, mode, image_input],
        outputs=[chatbot, message, image_input]
    )

    clear_btn.click(
        fn=lambda: ([], "", None),
        inputs=[],
        outputs=[chatbot, message, image_input]
    )

print("Chatbot UI created successfully.")
print("The demo app is ready.")
# Render supplies PORT. Do not create a temporary Gradio share link in production.
demo.queue(default_concurrency_limit=3, max_size=20)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
        show_error=True,
    )
