import os
import re
import time
import json
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from openai import OpenAI

# Expanded news sources focusing on Technology, AI, Science, and World Geopolitics
RSS_FEEDS = [
    # Technology & Science
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://feeds.arstechnica.com/arstechnica/index",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    # World Politics & Major Affairs
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

def clean_html_text(raw_html: str) -> str:
    """Strips HTML tags and unescapes entities for cleaner prompt tokens."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def fetch_single_feed(feed_url: str, cutoff_time: datetime) -> List[str]:
    """Fetches and parses a single RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')

            if published_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(published_parsed), tz=timezone.utc)
                if pub_date < cutoff_time:
                    continue

            title = clean_html_text(entry.get('title', ''))
            summary = clean_html_text(entry.get('summary', entry.get('description', '')))
            pub_date_str = entry.get('published', 'Last 24 hours')

            if title and summary:
                articles.append(f"Title: {title}\nDate: {pub_date_str}\nSummary: {summary}\n")

    except Exception as e:
        print(f"⚠️ RSS Feed error ({feed_url}): {e}")
    
    return articles

class ContentGenerator:
    """Fetches real-time tech and world politics RSS feeds in parallel and generates 8-story B2 English educational lessons via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Fetches news published in the last 24 hours across expanded tech & world news sources in parallel."""
        print(f"🌐 Scanning {len(RSS_FEEDS)} tech & world news RSS feeds in parallel (last {hours_limit} hours)...")
        all_articles = []
        now_dt = datetime.now(timezone.utc)
        cutoff_time = now_dt - timedelta(hours=hours_limit)

        with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as executor:
            future_to_url = {executor.submit(fetch_single_feed, url, cutoff_time): url for url in RSS_FEEDS}
            for future in as_completed(future_to_url):
                all_articles.extend(future.result())

        print(f"✅ Found {len(all_articles)} fresh articles from the last {hours_limit} hours.")
        return "\n---\n".join(all_articles[:30])

    def generate_script(self, raw_news: str) -> Dict[str, Any]:
        """Generates educational monologue script AND clean news summaries / vocabulary list using DeepSeek API with pedagogical excellence."""
        print("🤖 Writing 8-story pedagogically optimized B2 English lesson using DeepSeek...")
        
        today_date = datetime.now().strftime("%B %d, %Y")
        
        if not self.api_key:
            print("⚠️ HATA: DEEPSEEK_API_KEY ortam değişkeni bulunamadı. Örnek script kullanılıyor.")
            fallback_script = (
                f"Hello and welcome to your Daily B2 English News Lesson for {today_date}. "
                f"I'm your host, and today we will cover eight major global developments while upgrading your upper-intermediate vocabulary.\n\n"
                f"Story 1: Artificial intelligence models are advancing rapidly in software engineering. "
                f"Notice our first target B2 word: 'accelerate' (ac-cel-er-ate). It means to happen or cause to happen faster. For instance: 'AI tools accelerate software testing.'\n\n"
                f"Story 2: Global semiconductor supply chains are expanding. "
                f"Our key word is 'resilient' (re-sil-ient), meaning able to withstand or recover quickly from difficult conditions.\n\n"
                f"Story 3: Climate summits achieve new accord on clean energy. Key word: 'consensus' (general agreement).\n\n"
                f"Story 4: Robotics technology transforms industrial manufacturing. Key word: 'autonomous' (self-governing, independent).\n\n"
                f"Story 5: Digital trade treaties updated worldwide. Key word: 'implementation' (the process of putting a decision into effect).\n\n"
                f"Story 6: Quantum computing encryption shows progress. Key word: 'promising' (showing signs of future success).\n\n"
                f"Story 7: International lunar exploration missions announced. Key word: 'collaborative' (produced by working together).\n\n"
                f"Story 8: Cybersecurity standards adopted globally. Key word: 'comprehensive' (including all or nearly all elements).\n\n"
                f"To review today's lesson, our 8 target words were: accelerate, resilient, consensus, autonomous, implementation, promising, collaborative, and comprehensive. "
                f"Try using one of these words in your daily English conversation today! Happy learning!"
            )
            fallback_summary = (
                "<h3>📰 Today's 8 News Highlights</h3><ul>"
                "<li><b>1. AI Software Breakthroughs</b>: Rapid advancements in developer tools.</li>"
                "<li><b>2. Semiconductor Expansion</b>: Supply chains growing resilient across continents.</li>"
                "<li><b>3. Global Climate Accord</b>: International consensus on renewable energy goals.</li>"
                "<li><b>4. Industrial Robotics</b>: Autonomous systems boosting automation.</li>"
                "<li><b>5. Digital Trade Treaties</b>: Updated agreements for international e-commerce.</li>"
                "<li><b>6. Quantum Encryption</b>: Promising developments in cybersecurity.</li>"
                "<li><b>7. Lunar Exploration</b>: Collaborative space missions announced.</li>"
                "<li><b>8. Infrastructure Security</b>: Adoption of comprehensive cyber standards.</li></ul>"
                "<h3>📚 B2 Vocabulary Spotlight</h3><ul>"
                "<li><b>accelerate</b> /əkˈsel.ə.reɪt/ - To happen or make something happen faster. <i>Example: Technology continues to accelerate innovation.</i></li>"
                "<li><b>resilient</b> /rɪˈzɪl.jənt/ - Able to withstand or recover quickly from difficulty. <i>Example: Modern networks must be resilient against outages.</i></li>"
                "</ul>"
            )
            return {
                "title": f"B2 English Tech & World Bulletin (7-8 Min) - {today_date}",
                "summary": f"Single-speaker 8-story educational B2 English lesson for {today_date}.",
                "script": fallback_script,
                "bulletin_summary": fallback_summary,
                "date": today_date
            }

        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

        system_prompt = f"""
You are an elite EFL/ESL Master Educator specializing in CEFR B2 (Upper-Intermediate) English acquisition and authentic listening comprehension. Today is {today_date}.

YOUR PEDAGOGICAL MISSION:
Create a 7-8 minute (950-1100 words) spoken English lesson based on today's news. Your output must be a valid JSON object with two keys: "script" and "bulletin_summary".

PEDAGOGICAL & CONTENT GUIDELINES:
1. SELECTION PRIORITY: Select exactly TOP 8 STORIES from today's provided news. Prioritize Technology, AI, Engineering, and Major Geopolitics.
2. PEDAGOGICAL STRUCTURE FOR "script":
   - Warm Introduction: Greet the learner warmly, state today's date ({today_date}), set the learning objective (8 news stories + 8 B2 vocabulary items).
   - 8 News Modules (Story 1 to 8): For EACH story:
     a) Explain the news event clearly using authentic B2-level syntax.
     b) Explicitly highlight 1 target B2 vocabulary word. Pronounce it slowly with syllable emphasis (e.g., 're-sil-ient'), define it in clear English, state its synonym, and provide a practical real-world example sentence.
   - Pedagogical Signposting: Use clear oral transitional signals ("Moving on to our second story...", "Let me draw your attention to...", "In our final news item today...").
   - Review & Practice Call-to-Action: Recap all 8 B2 words in bulleted order and challenge the learner to use at least one word today.
3. STRUCTURE FOR "bulletin_summary" (HTML for Email Body):
   - Section 1: <h3>📰 Today's 8 News Summaries</h3> with a clean <ul> containing 8 <li> items (Bold Story Title + 2-sentence summary).
   - Section 2: <h3>📚 B2 Vocabulary Spotlight</h3> with a <ul> containing 8 <li> items (Bold Word + Syllable/IPA hint + Clear B2 Definition + Contextual Example Sentence).

JSON RESPONSE SCHEMA (Strictly return JSON only):
{{
  "script": "spoken monologue text (950-1100 words)...",
  "bulletin_summary": "<div style='font-family: sans-serif;'>...HTML summary...</div>"
}}
"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Today's Fresh News Articles:\n{raw_news}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        raw_content = response.choices[0].message.content.strip()
        if raw_content.startswith("```"):
            raw_content = re.sub(r'^```(?:json)?\s*', '', raw_content)
            raw_content = re.sub(r'\s*```$', '', raw_content)

        result = json.loads(raw_content)
        title = f"B2 English Tech & World Bulletin (7-8 Min) - {today_date}"
        summary = f"Educational 8-story B2 English lesson (~7-8 minutes) focusing on Technology, AI, and World Politics for {today_date}."

        return {
            "title": title,
            "summary": summary,
            "script": result.get("script", ""),
            "bulletin_summary": result.get("bulletin_summary", result.get("script", "")),
            "date": today_date
        }
