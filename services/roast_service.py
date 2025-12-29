import os
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

AI_API_URL = "https://api.aimlapi.com/v1/chat/completions"
MODEL_NAME = "google/gemma-2b-it"
API_KEY = os.environ.get("AIML_API_KEY")

MAX_INPUT_CHARS = 3000
AI_TIMEOUT = 8

def is_valid_url(url):
    try:
        u = urlparse(url)
        return u.scheme in ["http", "https"] and u.netloc
    except:
        return False

def fetch_html(url):
    headers = {"User-Agent": "WebsiteRoasterBot/1.0"}
    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    return r.text

def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()

    headings = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(["h1","h2"]))
    paragraphs = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    buttons = " ".join(b.get_text(" ", strip=True) for b in soup.find_all("button"))

    combined = f"""
TITLE:
{title}

META DESCRIPTION:
{meta_desc}

HEADINGS:
{headings}

CTA / BUTTON TEXT:
{buttons}

BODY COPY:
{paragraphs}
"""
    return combined[:MAX_INPUT_CHARS]

def build_prompt(content):
    return f"""
You are a brutally honest website copy reviewer.

Rules:
- Be direct
- No politeness
- No fluff
- Actionable feedback only

Return ONLY valid JSON in this exact format:

{{
  "overall_score": number,
  "main_problems": [short blunt problems],
  "why_people_wont_convert": [reasons],
  "headline_fixes": [3 improved headline options],
  "cta_fix": "one improved CTA",
  "quick_wins": [3 fast improvements]
}}

Website content:
<<<{content}>>>
"""

def call_ai(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_NAME, "messages":[{"role":"user","content":prompt}],
               "temperature":0.6, "max_tokens":300}
    r = requests.post(AI_API_URL, headers=headers, json=payload, timeout=AI_TIMEOUT)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    clean = text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def fallback_roast():
    return {
        "overall_score": 4,
        "main_problems": ["Value proposition is unclear", "Copy is generic and forgettable"],
        "why_people_wont_convert": ["No clear benefit", "Weak or missing CTA"],
        "headline_fixes": [
            "Clear benefit-driven headline needed",
            "State who it is for and why it matters",
            "Remove buzzwords, add specifics"
        ],
        "cta_fix": "Start free",
        "quick_wins": ["Clarify target audience", "Add social proof", "Simplify headline"]
    }

def roast_url(url):
    if not is_valid_url(url):
        return {"error": "Invalid URL"}

    try:
        html = fetch_html(url)
        content = extract_content(html)
        if len(content) < 200:
            return {"error": "Not enough readable content"}

        prompt = build_prompt(content)
        try:
            roast = call_ai(prompt)
        except:
            roast = fallback_roast()

        return roast
    except Exception as e:
        return {"error": str(e)}
        
