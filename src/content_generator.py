import os
import time
import feedparser
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
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

class ContentGenerator:
    """Fetches real-time tech and world politics RSS feeds and generates 8-story B2 English educational lessons (7-8 minutes audio duration) via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Fetches news published in the last 24 hours across expanded tech & world news sources."""
        print(f"🌐 Scanning {len(RSS_FEEDS)} tech & world news RSS feeds (last {hours_limit} hours)...")
        articles = []
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
        """Generates single-narrator educational B2 monologue script covering 8 top stories (target 7-8 min audio) using DeepSeek API."""
        print("🤖 Writing 8-story tech & world politics educational B2 English lesson (7-8 min audio) using DeepSeek...")
        
        today_date = datetime.now().strftime("%B %d, %Y")
        
        if not self.api_key:
            print("⚠️ HATA: DEEPSEEK_API_KEY ortam değişkeni bulunamadı. Örnek script kullanılıyor.")
            fallback_script = (
                f"Hello and welcome to your Daily B2 English Digest for {today_date}.\n\n"
                f"Today we explore eight major stories across technology, AI breakthroughs, and world affairs.\n\n"
                f"Story 1: Artificial intelligence models are advancing rapidly in software development. Key B2 Word: 'accelerate' (to happen faster).\n\n"
                f"Story 2: Global semiconductor supply chains are expanding in Europe and Asia. Key B2 Word: 'resilient' (able to recover quickly).\n\n"
                f"Story 3: International climate summits have reached new consensus on clean energy. Key B2 Word: 'consensus' (general agreement).\n\n"
                f"Story 4: Autonomous robotics technology is transforming industrial automation. Key B2 Word: 'autonomous' (independent, self-governing).\n\n"
                f"Story 5: Major trade treaties are being updated for digital services. Key B2 Word: 'implementation' (putting a decision or plan into effect).\n\n"
                f"Story 6: Breakthroughs in quantum computing research show promising encryption results. Key B2 Word: 'promising' (showing sign of future success).\n\n"
                f"Story 7: International space agencies announce collaborative lunar exploration missions. Key B2 Word: 'collaborative' (produced by working together).\n\n"
                f"Story 8: New cybersecurity frameworks are adopted across infrastructure networks. Key B2 Word: 'comprehensive' (including all or nearly all elements).\n\n"
                f"To recap, today we learned accelerate, resilient, consensus, autonomous, implementation, promising, collaborative, and comprehensive. Keep practicing!"
            )
            return {
                "title": f"B2 English Tech & World Bulletin (7-8 Min) - {today_date}",
                "summary": f"Single-speaker 8-story educational B2 English lesson for {today_date}.",
                "script": fallback_script,
                "date": today_date
            }

        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

        system_prompt = f"""
You are an expert, encouraging English language teacher presenting a daily news-based English lesson for B2-level learners. Today is {today_date}.

PRIORITY SELECTION & AUDIO LENGTH RULES:
1. TARGET LENGTH: 950 to 1100 words total (designed for approximately 7 to 8 minutes of spoken educational audio).
2. SELECTION PRIORITY: Select exactly TOP 8 STORIES from today's provided news. Prioritize:
   - Technology, AI breakthroughs, software, engineering, and innovation.
   - Critical major world politics and international relations developments.
3. SINGLE SPEAKER NARRATOR: Do NOT use dialogue tags (no "Alex:" or "Sam:"). Write as a clear, educational monologue spoken by one friendly teacher.
4. STRUCTURE:
   - Introduction: Warmly welcome the listener to today's 7-8 minute top tech and world news English lesson.
   - 8 Stories (Story 1 through Story 8): For EACH story, explain the news in detailed B2 English, then highlight 1 key B2 vocabulary word used, providing its definition and a clear example sentence.
   - Comprehensive Vocabulary Recap & Conclusion: Review all 8 B2 words learned today with an encouraging closing thought.
5. LEVEL & STYLE: B2 English level. Clear pronunciation-friendly sentences, rich educational content.
6. Do NOT include sound effects or markdown formatting like **bold** names.
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
        title = f"B2 English Tech & World Bulletin (7-8 Min) - {today_date}"
        summary = f"Educational 8-story B2 English lesson (~7-8 minutes) focusing on Technology, AI, and World Politics for {today_date}."

        return {
            "title": title,
            "summary": summary,
            "script": script_text,
            "date": today_date
        }
