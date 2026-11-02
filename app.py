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
/* Overall responsive page */
.gradio-container {
    width: 100% !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
