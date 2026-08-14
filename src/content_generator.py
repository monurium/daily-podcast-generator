import os
import time
import feedparser
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from openai import OpenAI

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

class ContentGenerator:
    """Fetches real-time RSS news from top outlets and generates B2-level dialogue scripts via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Fetches news published in the last 24 hours from BBC, NYT, Al Jazeera."""
        print(f"🌐 Scanning RSS feeds for news published in the last {hours_limit} hours...")
        articles = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours_limit)

        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')

                    if published_parsed:
                        pub_date = datetime.fromtimestamp(time.mktime(published_parsed), tz=timezone.utc)
                        if pub_date < cutoff_time:
                            continue

                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))
                    pub_date_str = entry.get('published', 'Last 24 hours')

                    if title and summary:
                        articles.append(f"Title: {title}\nDate: {pub_date_str}\nSummary: {summary}\n")

            except Exception as e:
                print(f"⚠️ RSS Feed error ({feed_url}): {e}")

        print(f"✅ Found {len(articles)} fresh articles from the last {hours_limit} hours.")
        return "\n---\n".join(articles)

    def generate_script(self, raw_news: str) -> Dict[str, Any]:
        """Generates two-host (Alex & Sam) B2 dialogue script using DeepSeek API."""
        print("🤖 Writing B2 English podcast script using DeepSeek...")
        
        today_date = datetime.now().strftime("%B %d, %Y")
        
        if not self.api_key:
            print("⚠️ HATA: DEEPSEEK_API_KEY ortam değişkeni bulunamadı. Örnek script kullanılıyor.")
            fallback_script = (
                f"Alex: Welcome to today's daily news podcast for {today_date}.\n"
                f"Sam: Hi Alex! Today we are looking at key developments across international affairs and technology.\n"
                f"Alex: Renewable energy initiatives have accelerated globally this week, opening up new infrastructure investments.\n"
                f"Sam: That's right, Alex. International cooperation continues to reshape modern sustainable development."
            )
            return {
                "title": f"B2 Daily News Digest - {today_date}",
                "summary": f"Daily B2 English news podcast covering world highlights for {today_date}.",
                "script": fallback_script,
                "date": today_date
            }

        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

        system_prompt = f"""
You are an expert news editor and English language teacher. Today is {today_date}.
Create a daily news podcast script for B2-level English learners based ONLY on today's provided news.

CRITICAL FORMATTING RULES:
1. Use 2 hosts: Alex (Male) and Sam (Female).
2. Format EVERY dialogue line strictly starting with "Alex:" or "Sam:" like below:
   Alex: Welcome to today's digest.
   Sam: Thanks Alex, let's start with climate news.
3. Select the top 3 most important news stories.
4. Keep vocabulary strictly at B2 level. Naturally explain 3 key B2 vocabulary words during the podcast.
5. Length: 400-500 words.
Do NOT use Markdown bolding on names (e.g. do NOT write **Alex:**). Do NOT include sound effect notes like [Music] or (laughs).
"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Today's Fresh News:\n{raw_news}"}
            ],
            temperature=0.7
        )

        script_text = response.choices[0].message.content
        title = f"B2 Daily News Digest - {today_date}"
        summary = f"Learn B2 English with today's top world news highlights for {today_date} featuring hosts Alex and Sam."

        return {
            "title": title,
            "summary": summary,
            "script": script_text,
            "date": today_date
        }
