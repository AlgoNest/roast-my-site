import os
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from openai import OpenAI

BASE_URL = "https://api.aimlapi.com/v1/"
MODEL_NAME = "google/gemma-2b-it"
api_key = os.environ.get("AIML_API_KEY")

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

def get_client(api_key: str) -> OpenAI:
    """Initialize and return an OpenAI client with the given API key."""
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def call_ai(prompt):
            client = get_client(api_key)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                top_p=0.8,
                max_tokens=600,
                timeout=20,
            )

            content = response.choices[0].message.content.strip()

            try:
                clean_text = content.replace("```json", "").replace("```", "").strip()
                print(clean_text)
                return json.loads(clean_text)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format", "raw": content}


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
        prompt = build_prompt(extract_content(html))
        return call_ai(prompt)
    except Exception as e:
        return {"error": str(e)}
        
