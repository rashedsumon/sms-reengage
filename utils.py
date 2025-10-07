# utils.py
import os
import openai
from datetime import datetime
import pytz

openai.api_key = os.getenv("OPENAI_API_KEY")

REASONS = ["price", "moved", "service quality", "safety concerns", "crowded location", "other"]

def classify_reply(text):
    """
    Uses OpenAI to return a dict: {"reason":..., "sentiment":..., "note":...}
    Provide a short, deterministic prompt so results are stable.
    """
    prompt = f"""
You are a helpful assistant that reads a short customer SMS reply and returns a JSON object with fields:
- reason: one of {REASONS}
- sentiment: "positive", "negative", or "neutral"
- note: a short human-readable phrase summarizing the customer's reason.

Reply ONLY with JSON.

Example:
Customer: "Your prices went way up and I couldn't afford it."
-> {{"reason": "price", "sentiment": "negative", "note":"prices increased / unaffordable"}}

Now classify this customer reply:
\"\"\"{text}\"\"\"
"""
    resp = openai.ChatCompletion.create(
        model="gpt-5-thinking-mini", # replace with appropriate model in your environment
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=150
    )
    content = resp["choices"][0]["message"]["content"].strip()
    # try to parse JSON robustly
    import json
    try:
        parsed = json.loads(content)
    except Exception:
        # fallback parsing: naive extraction
        parsed = {"reason":"other","sentiment":"neutral","note": content[:200]}
    return parsed
