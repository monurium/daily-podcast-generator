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
    """Fetches real-time RSS news from top outlets and generates B2-level educational monologue scripts via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Fetches news published in the last 24 hours from BBC, NYT, Al Jazeera."""
        print(f"🌐 Scanning RSS feeds for news published in the last {hours_limit} hours...")
        articles = []
        now = datetime.date.today()
        now_dt = datetime.now(timezone.utc)
        cutoff_time = now_dt - timedelta(hours=hours_limit)

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
        """Generates single-narrator educational B2 monologue script using DeepSeek API."""
        print("🤖 Writing single-speaker educational B2 English lesson script using DeepSeek...")
        
        today_date = datetime.now().strftime("%B %d, %Y")
        
        if not self.api_key:
            print("⚠️ HATA: DEEPSEEK_API_KEY ortam değişkeni bulunamadı. Örnek script kullanılıyor.")
            fallback_script = (
                f"Hello and welcome to your Daily B2 English Digest for {today_date}.\n\n"
                f"Today we will explore three key stories from around the world while learning important intermediate English vocabulary.\n\n"
                f"Our first story focuses on global renewable energy progress. Solar and wind power installations have increased significantly this year. "
                f"Notice our key B2 word: 'significantly', which means in a noticeable or important way.\n\n"
                f"Our second story covers international trade agreements. Countries are working together to streamline commercial transport. "
                f"Here, the key word is 'streamline', which means to make a process smoother and more efficient.\n\n"
                f"To recap, today we learned 'significantly' and 'streamline'. Thank you for listening, and keep practicing your English every day!"
            )
            return {
                "title": f"B2 English News Lesson - {today_date}",
                "summary": f"Single-speaker educational B2 English news lesson for {today_date}.",
                "script": fallback_script,
                "date": today_date
            }

        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

        system_prompt = f"""
You are an expert, encouraging English language teacher presenting a daily news-based English lesson for B2-level learners. Today is {today_date}.

STRUCTURE AND PEDAGOGY RULES:
1. SINGLE SPEAKER NARRATOR: Do NOT use dialogue tags (no "Alex:" or "Sam:"). Write as a continuous, clear, educational monologue spoken by one friendly teacher.
2. SELECT THE TOP 3 STORIES: Choose the 3 most significant news stories from today's provided articles.
3. CLEAR EDUCATIONAL STRUCTURE:
   - Introduction: Warmly welcome the listener to today's English news bulletin.
   - Story 1: Present the news clearly, then highlight 1 key B2 vocabulary word used in the story. Explain its definition and give an easy example sentence.
   - Story 2: Present the news clearly, highlight 1 key B2 vocabulary word, explain definition and example.
   - Story 3: Present the news clearly, highlight 1 key B2 vocabulary word, explain definition and example.
   - Vocabulary Recap & Conclusion: Briefly review the 3 B2 words learned today and give an encouraging closing statement.
4. LANGUAGE LEVEL: B2 English level. Clear pronunciation-friendly sentences, natural phrasing, 400-500 words total.
5. Do NOT include sound effects or markdown formatting like **bold** names.
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
        title = f"B2 English Daily Lesson - {today_date}"
        summary = f"Educational B2 English monologue news lesson for {today_date} featuring key vocabulary explanations."

        return {
            "title": title,
            "summary": summary,
            "script": script_text,
            "date": today_date
        }
